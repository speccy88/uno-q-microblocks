# SPDX-License-Identifier: MIT
import asyncio,ipaddress
from urllib.parse import urlsplit
from fastapi import FastAPI,Request,WebSocket,WebSocketDisconnect
from fastapi.responses import JSONResponse,RedirectResponse
from starlette.staticfiles import StaticFiles
def create_server(transport,data,web):
 app=FastAPI(docs_url=None,redoc_url=None,openapi_url=None)
 def allowed_host(host):
  try:
   name=urlsplit('//'+host).hostname
   if name=='localhost':return True
   address=ipaddress.ip_address(name)
   return any(address in ipaddress.ip_network(net) for net in ('127.0.0.0/8','10.0.0.0/8','172.16.0.0/12','192.168.0.0/16','::1/128','fc00::/7'))
  except (ValueError,TypeError):return False
 def origin_ok(headers):return headers.get('origin') in ('http://'+headers.get('host',''),'https://'+headers.get('host','')) and allowed_host(headers.get('host',''))
 @app.middleware('http')
 async def guard(request:Request,call_next):
  if not allowed_host(request.headers.get('host','')):return JSONResponse({'error':'Host not allowed; use localhost or a private LAN address'},status_code=403)
  response=await call_next(request)
  response.headers['X-Content-Type-Options']='nosniff';response.headers['Referrer-Policy']='no-referrer'
  response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; connect-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; font-src 'self'; frame-src 'none'; object-src 'none'; base-uri 'self'"
  return response
 @app.get('/signin')
 def old_signin():return RedirectResponse('/microblocks.html',status_code=303)
 @app.get('/healthz')
 def health():return {'service':'microblocks_bridge','running':True}
 @app.get('/api/status')
 def status():return transport.status()
 @app.websocket('/ws/vm')
 async def stream(ws:WebSocket):
  if not origin_ok(ws.headers):await ws.close(code=1008,reason='Origin rejected');return
  owner=object()
  try:transport.acquire(owner)
  except RuntimeError as exc:await ws.close(code=1008,reason=str(exc)[:120]);return
  await ws.accept()
  async def receive():
   while True:
    packet=await ws.receive()
    if packet['type']=='websocket.disconnect':return
    if packet.get('bytes') is None:raise ValueError('Only binary MicroBlocks traffic accepted')
    transport.push(owner,packet['bytes'])
  async def send():
   while True:
    out=transport.pull(owner)
    if out:await asyncio.wait_for(ws.send_bytes(out),timeout=3)
    else:await asyncio.sleep(.005)
  tasks=[asyncio.create_task(receive()),asyncio.create_task(send())]
  try:
   done,pending=await asyncio.wait(tasks,return_when=asyncio.FIRST_COMPLETED)
   for task in done:task.result()
  except asyncio.CancelledError:
   pass # server shutdown/disconnect still releases ownership in finally
  except (WebSocketDisconnect,ValueError,RuntimeError,BufferError,TimeoutError) as exc:
   try:await ws.close(code=1011,reason=str(exc)[:120])
   except RuntimeError:pass
  finally:
   for task in tasks:task.cancel()
   await asyncio.gather(*tasks,return_exceptions=True);transport.release(owner)
 @app.get('/')
 def index():return RedirectResponse('/microblocks.html',status_code=303)
 app.mount('/',StaticFiles(directory=str(web)),name='official_microblocks')
 return app
