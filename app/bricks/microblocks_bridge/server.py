# SPDX-License-Identifier: MIT
import asyncio,hashlib,hmac,json,secrets,time,ipaddress
from urllib.parse import urlsplit
from pathlib import Path
from fastapi import FastAPI,Request,WebSocket,WebSocketDisconnect
from fastapi.responses import FileResponse,HTMLResponse,JSONResponse,RedirectResponse
from starlette.staticfiles import StaticFiles
LOGIN='''<!doctype html><html><head><meta charset="utf-8"><title>Connect to UNO Q MicroBlocks</title></head><body><h1>UNO Q MicroBlocks</h1><p>Enter the local access code from this app's data/access_token file.</p><form id="signin"><label>Access code <input id="code" type="password" required autocomplete="off"></label><button>Open MicroBlocks</button></form><p id="error" role="status"></p><script>document.getElementById('signin').onsubmit=async e=>{e.preventDefault();const r=await fetch('/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({code:document.getElementById('code').value})});if(r.ok)location.href='/microblocks.html';else document.getElementById('error').textContent='Access denied. Check the local code.';};</script></body></html>'''
def create_server(transport,data,web):
 data=Path(data);data.mkdir(parents=True,exist_ok=True);tokenfile=data/'access_token'
 if not tokenfile.exists():tokenfile.write_text(secrets.token_urlsafe(32)+'\n');tokenfile.chmod(0o600)
 token=tokenfile.read_text().strip();sessions={};attempts=[];app=FastAPI(docs_url=None,redoc_url=None,openapi_url=None)
 def allowed_host(host):
  try:
   name=urlsplit('//'+host).hostname
   if name=='localhost':return True
   address=ipaddress.ip_address(name)
   return any(address in ipaddress.ip_network(net) for net in ('127.0.0.0/8','10.0.0.0/8','172.16.0.0/12','192.168.0.0/16','::1/128','fc00::/7'))
  except (ValueError,TypeError):return False
 def valid_cookie(cookies):return sessions.get(cookies.get('mb_session',''),0)>time.monotonic()
 def origin_ok(headers):return headers.get('origin') in ('http://'+headers.get('host',''),'https://'+headers.get('host','')) and allowed_host(headers.get('host',''))
 @app.middleware('http')
 async def guard(request:Request,call_next):
  if not allowed_host(request.headers.get('host','')):return JSONResponse({'error':'Host not allowed; use localhost or a private LAN address'},status_code=403)
  if request.url.path not in ('/signin','/login','/healthz') and not valid_cookie(request.cookies):
   return JSONResponse({'error':'Authentication required'},status_code=401) if request.url.path.startswith('/api/') else RedirectResponse('/signin',status_code=303)
  response=await call_next(request)
  response.headers['X-Content-Type-Options']='nosniff';response.headers['Referrer-Policy']='no-referrer'
  response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; connect-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; font-src 'self'; frame-src 'none'; object-src 'none'; base-uri 'self'"
  return response
 @app.get('/signin')
 def signin():return HTMLResponse(LOGIN)
 @app.post('/login')
 async def login(request:Request):
  if not origin_ok(request.headers):return JSONResponse({'error':'Origin rejected'},status_code=403)
  now=time.monotonic();attempts[:]=[t for t in attempts if now-t<60]
  if len(attempts)>=10:return JSONResponse({'error':'Wait before retrying'},status_code=429)
  if len(await request.body())>256:return JSONResponse({'error':'Invalid request'},status_code=400)
  try:code=(await request.json()).get('code','')
  except (ValueError,AttributeError):return JSONResponse({'error':'Invalid request'},status_code=400)
  if type(code) is not str or not hmac.compare_digest(code,token):attempts.append(now);return JSONResponse({'error':'Access denied'},status_code=401)
  sessions.clear() if len(sessions)>16 else None
  session=secrets.token_urlsafe(32);sessions[session]=now+21600
  response=JSONResponse({'ok':True});response.set_cookie('mb_session',session,max_age=21600,httponly=True,samesite='strict',secure=request.url.scheme=='https');return response
 @app.get('/healthz')
 def health():return {'service':'microblocks_bridge','running':True}
 @app.get('/api/status')
 def status():return transport.status()
 @app.websocket('/ws/vm')
 async def stream(ws:WebSocket):
  if not origin_ok(ws.headers) or not valid_cookie(ws.cookies):await ws.close(code=1008,reason='Authentication or Origin rejected');return
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
