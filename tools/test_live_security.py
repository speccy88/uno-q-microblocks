#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Read-only HTTP checks and rejected WS handshakes. Does not send VM bytes."""
import argparse,asyncio,json
from pathlib import Path
import httpx,websockets
p=argparse.ArgumentParser();p.add_argument('--url',default='http://localhost:18080');p.add_argument('--output',type=Path,required=True);a=p.parse_args();results={}
c=httpx.Client(base_url=a.url,trust_env=False)
results['direct_status']=c.get('/api/status').status_code
assert results['direct_status']==200
results['host_rejection']=c.get('/healthz',headers={'Host':'untrusted.invalid'}).status_code;assert results['host_rejection']==403
r=c.get('/microblocks.html');assert r.status_code==200;results['csp']=r.headers['Content-Security-Policy'];results['direct_access_status']=c.get('/api/status').json()
assert not c.cookies
assert results['direct_access_status']['controller_connected'],'Run while the actual browser is connected'
async def check():
 for name,origin in [('origin_rejection','http://untrusted.invalid'),('second_controller',a.url)]:
  try:
   async with websockets.connect(a.url.replace('http','ws',1)+'/ws/vm',origin=origin):raise AssertionError('Unexpected accepted programming connection')
  except websockets.InvalidStatusCode as e:assert e.status_code==403;results[name]=403
asyncio.run(check());c.close();results['result']='PASS';a.output.write_text(json.dumps(results,indent=2)+'\n');print(json.dumps({k:v for k,v in results.items() if k!='direct_access_status'}))
