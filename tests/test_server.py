# SPDX-License-Identifier: MIT
import importlib.util,tempfile,unittest,time
from pathlib import Path
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
R=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('mb_server',R/'app/bricks/microblocks_bridge/server.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Transport:
 def __init__(self):self.owner=None;self.rx=bytearray()
 def acquire(self,o):
  if self.owner:raise RuntimeError('Already controlled')
  self.owner=o
 def release(self,o):
  if self.owner==o:self.owner=None
 def push(self,o,data):
  if len(data)>8192:raise ValueError('too large')
  self.rx.extend(data)
 def pull(self,o):r=bytes(self.rx);self.rx.clear();return r
 def status(self):return {'simulated':True}
class Tests(unittest.TestCase):
 def setUp(self):
  self.d=tempfile.TemporaryDirectory();p=Path(self.d.name);(p/'microblocks.html').write_text('real static fixture')
  self.t=Transport();self.client=TestClient(m.create_server(self.t,p,p),base_url='http://localhost')
  self.code=(p/'access_token').read_text().strip();self.headers={'Origin':'http://localhost'}
 def tearDown(self):self.client.close();self.d.cleanup()
 def login(self):self.assertEqual(self.client.post('/login',json={'code':self.code},headers=self.headers).status_code,200)
 def test_auth_origin_host(self):
  self.assertEqual(self.client.get('/api/status').status_code,401)
  self.assertEqual(self.client.get('/healthz',headers={'Host':'untrusted.invalid'}).status_code,403)
  self.assertEqual(self.client.get('/healthz',headers={'Host':'8.8.8.8:8080'}).status_code,403)
  self.assertEqual(self.client.get('/healthz',headers={'Host':'192.168.0.2:8080'}).status_code,200)
  self.assertEqual(self.client.post('/login',json={'code':self.code}).status_code,403)
  self.assertEqual(self.client.post('/login',json={'code':'invalid'},headers=self.headers).status_code,401)
  self.login();self.assertEqual(self.client.get('/api/status').status_code,200)
  self.assertIn("connect-src 'self'",self.client.get('/microblocks.html').headers['Content-Security-Policy'])
  for origin in ['http://evil.invalid','null']:
   with self.assertRaises(WebSocketDisconnect):
    with self.client.websocket_connect('ws://localhost/ws/vm',headers={'Origin':origin}):pass
 def test_binary_exclusive_reconnect(self):
  self.login()
  with self.client.websocket_connect('ws://localhost/ws/vm',headers=self.headers) as ws:
   with self.assertRaises(WebSocketDisconnect):
    with self.client.websocket_connect('ws://localhost/ws/vm',headers=self.headers):pass
   import random
   randomizer=random.Random(20261013)
   for size in [1,256,8192]+[randomizer.randrange(1,2049) for _ in range(1000)]:
    payload=randomizer.randbytes(size);ws.send_bytes(payload);self.assertEqual(ws.receive_bytes(),payload)
   ws.close()
   deadline=time.monotonic()+1
   while self.t.owner is not None and time.monotonic()<deadline:time.sleep(.005)
   self.assertIsNone(self.t.owner)
  with self.client.websocket_connect('ws://localhost/ws/vm',headers=self.headers) as ws:ws.send_bytes(bytes([0,250,251,254,255]));self.assertEqual(ws.receive_bytes(),bytes([0,250,251,254,255]));ws.close();time.sleep(.02)
 def test_invalid_frames_close(self):
  self.login()
  for payload in ['text',b'x'*8193]:
   with self.client.websocket_connect('ws://localhost/ws/vm',headers=self.headers) as ws:
    ws.send_text(payload) if type(payload) is str else ws.send_bytes(payload)
    with self.assertRaises(WebSocketDisconnect):ws.receive_bytes()
if __name__=='__main__':unittest.main(verbosity=2)
