# SPDX-License-Identifier: MIT
"""Real Brick logic with explicit simulated RPC/LED backends; no hardware claim."""
import importlib.util,json,tempfile,threading,time,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];B=R/'app/bricks/microblocks_bridge'
def module(name):
 s=importlib.util.spec_from_file_location(name,B/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
Transport=module('transport').Transport
class LEDs:
 max={'1r':1}
 def set(self,*args):return {'requested':args}
class RPC:
 def __init__(self):self.calls=[];self.reply=bytearray();self.uptime=100;self.fail_push=False
 def call(self,name,*args,timeout=2):
  self.calls.append((name,args));
  if name=='mb_size':return 4
  if name=='mb_echo':return args[0]
  if name=='mb_hw_version':return 1
  if name=='mb_uptime':self.uptime+=10;return self.uptime
  if name=='mb_stat':return 0
  if name=='mb_open':self.reply.clear();return 1
  if name=='mb_push':
   if self.fail_push:raise TimeoutError('simulated ambiguous push')
   self.reply.extend(args[0]);return len(args[0])
  if name=='mb_pull':out=bytes(self.reply[:192]);del self.reply[:192];return out
  if name=='mb_host_peek':return b''
  raise AssertionError(name)
class Tests(unittest.TestCase):
 def setUp(self):self.dir=tempfile.TemporaryDirectory();self.rpc=RPC();self.t=Transport(self.rpc,LEDs(),self.dir.name);self.t.start();self.wait(lambda:self.t.ready)
 def tearDown(self):self.t.stop();self.dir.cleanup()
 def wait(self,condition):
  deadline=time.monotonic()+3
  while not condition():
   if time.monotonic()>deadline:self.fail('deadline exceeded')
   time.sleep(.005)
 def test_exact_chunks_and_exclusive(self):
  o=object();self.t.acquire(o)
  with self.assertRaises(RuntimeError):self.t.acquire(object())
  data=bytes(range(256))*8;self.t.push(o,data);result=bytearray();deadline=time.monotonic()+3
  while len(result)<len(data) and time.monotonic()<deadline:result.extend(self.t.pull(o));time.sleep(.005)
  self.assertEqual(bytes(result),data);self.assertTrue(all(len(args[0])<=192 for name,args in self.rpc.calls if name=='mb_push'))
  self.t.release(o);self.t.acquire(object())
 def test_bounds(self):
  o=object();self.t.acquire(o)
  with self.assertRaises(ValueError):self.t.push(o,'text')
  with self.assertRaises(ValueError):self.t.push(o,b'x'*8193)
  with self.t.lock:self.t.tx=bytearray(65536)
  with self.assertRaises(BufferError):self.t.push(o,b'x')
 def test_ambiguous_push_no_retry(self):
  o=object();self.t.acquire(o);self.rpc.fail_push=True;self.t.push(o,b'FAKE');self.wait(lambda:self.t.error is not None)
  time.sleep(.25);self.assertEqual(sum(n=='mb_push' for n,a in self.rpc.calls),1)
  with self.assertRaises(RuntimeError):self.t.pull(o)
 def test_idle_draining(self):
  self.rpc.reply.extend(bytes(range(256))*2);self.wait(lambda:self.t.stats['idle_discarded_bytes']==512)
  self.assertFalse(self.t.status()['controller_connected'])
if __name__=='__main__':unittest.main(verbosity=2)
