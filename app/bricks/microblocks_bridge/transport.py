# SPDX-License-Identifier: MIT
"""One serialized RPC owner. The VM is always the physical STM32, never Python."""
import collections,datetime,json,struct,threading,time,zlib
from pathlib import Path
MAX_QUEUE=65536
class Transport:
 def __init__(self,rpc,leds,data):
  self.rpc=rpc;self.leds=leds;self.data=Path(data);self.lock=threading.RLock();self.stop_event=threading.Event();self.thread=None
  self.owner=None;self.tx=bytearray();self.rx=bytearray();self.error=None;self.ready=False;self.hardware=False;self.last_health=0;self.last_host=0;self.last_idle=0;self.last_uptime=None
  self.stats={'input_bytes':0,'output_bytes':0,'idle_discarded_bytes':0,'sessions':0,'rpc_errors':0,'host_actions':0,'host_errors':0}
  self.byte_sequences={"to_vm":0,"from_vm":0};self.host_fault=None;self.health={};self._open_requested=False;self._last_applied=None
  self.data.mkdir(parents=True,exist_ok=True);self.log=(self.data/'events.jsonl').open('a',buffering=1)
 def event(self,event,**fields):
  if event=='bytes':
   d=fields['direction'];self.byte_sequences[d]+=1;raw=bytes.fromhex(fields['hex'])
   fields.update(sequence=self.byte_sequences[d],length=len(raw),crc32=f'{zlib.crc32(raw):08x}')
  self.log.write(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'event':event,**fields})+'\n')
 def call(self,name,*args):return self.rpc.call(name,*args,timeout=2)
 def start(self):
  if self.thread:return
  self.thread=threading.Thread(target=self.run,name='microblocks-rpc-owner',daemon=True);self.thread.start()
 def stop(self):
  self.stop_event.set()
  if self.thread:self.thread.join(5)
  self.log.close()
 def acquire(self,owner):
  with self.lock:
   if self.owner is not None:raise RuntimeError('SmallVM already controlled by another browser')
   if not self.ready:raise RuntimeError(self.error or 'Resident SmallVM unavailable; explicit runtime installation may be required')
   self.owner=owner;self.tx.clear();self.rx.clear();self.error=None;self._open_requested=True
   self.stats['sessions']+=1;self.event('session_acquired',session=self.stats['sessions'])
 def release(self,owner):
  with self.lock:
   if self.owner!=owner:return
   self.event('session_released',pending_input=len(self.tx),pending_output=len(self.rx))
   self.owner=None;self.tx.clear();self.rx.clear();self._open_requested=False
 def push(self,owner,data):
  if type(data) is not bytes or len(data)>8192:raise ValueError('WebSocket binary message must be <=8192 bytes')
  with self.lock:
   if self.owner!=owner or self.error:raise RuntimeError(self.error or 'No stream ownership')
   if len(self.tx)+len(data)>MAX_QUEUE:raise BufferError('Input backpressure queue full; reconnect explicitly')
   self.tx.extend(data)
 def pull(self,owner):
  with self.lock:
   if self.owner!=owner:raise RuntimeError('No stream ownership')
   if self.error:raise RuntimeError(self.error)
   out=bytes(self.rx[:8192]);del self.rx[:len(out)];return out
 def fail(self,message):
  with self.lock:
   self.error=message;self.stats['rpc_errors']+=1
  self.event('transport_error',message=message)
 def status(self):
  with self.lock:
   return {'runtime_ready':self.ready,'hardware_available':self.hardware,'host_service_error':self.host_fault,'controller_connected':self.owner is not None,'error':self.error,'queues':{'input':len(self.tx),'output':len(self.rx)},'limits':{'bridge_chunk':192,'queue_bytes':MAX_QUEUE,'websocket_message':8192},'counters':dict(self.stats),'mcu':dict(self.health),'linux_leds':{'max_brightness':self.leds.max}}
 def initialize(self):
  if self.call('mb_size',0)!=4:raise RuntimeError('Unsupported SmallVM object ABI')
  if self.call('mb_echo',b'\x00\xfa\xfb\xfe\xff')!=b'\x00\xfa\xfb\xfe\xff':raise RuntimeError('Router binary ABI mismatch')
  try:self.hardware=self.call('mb_hw_version')==1
  except (ValueError,TimeoutError,RuntimeError):self.hardware=False
  self.uptime_method='mb_uptime' if self.hardware else 'pb_uptime'
  self.ready=True;self.error=None;self.event('runtime_ready',hardware=self.hardware)
 def host_tick(self):
  request=self.call('mb_host_peek')
  if type(request) is not bytes:raise RuntimeError('Host queue reply must be native binary')
  if not request:return
  if type(request) is not bytes or len(request)!=8:raise RuntimeError('Invalid bounded host-action record')
  sequence,led,r,g,b=struct.unpack('<IBBBB',request);success=False
  try:
   if self._last_applied!=request:
    state=self.leds.set(led,r,g,b);self._last_applied=request;self.stats['host_actions']+=1
    self.event('linux_led_applied',sequence=sequence,led=led,rgb=[r,g,b],physical_state=state)
   success=True
  except (ValueError,OSError,RuntimeError) as exc:
   self.stats['host_errors']+=1;self.event('linux_led_failed',sequence=sequence,message=str(exc))
  # Applying an LED state is idempotent; an ambiguous ACK is not silently resent.
  try:
   if self.call('mb_host_ack',sequence,int(success))!=1:raise RuntimeError('Host-action ACK rejected')
  except (ValueError,TimeoutError,RuntimeError,OSError) as exc:
   self.host_fault='Host ACK failed; restart the App explicitly after checking runtime: '+str(exc)
   raise RuntimeError(self.host_fault) from exc
 def run(self):
  while not self.stop_event.is_set():
   try:self.initialize();break
   except (ValueError,TimeoutError,RuntimeError,OSError) as exc:self.fail(str(exc));self.stop_event.wait(2)
  if self.stop_event.is_set():return
  while not self.stop_event.is_set():
   try:
    now=time.monotonic()
    with self.lock:owner=self.owner;opening=self._open_requested;block=bytes(self.tx[:192]) if owner is not None and not self.error else b''
    if opening:
     if self.call('mb_open')!=1:raise RuntimeError('VM transport reset rejected')
     with self.lock:self._open_requested=False
    if block:
     accepted=self.call('mb_push',block)
     if accepted!=len(block):raise RuntimeError(f'STM32 ingress accepted {accepted}/{len(block)}; no retry')
     with self.lock:del self.tx[:len(block)]
     self.stats['input_bytes']+=len(block);self.event('bytes',direction='to_vm',hex=block.hex())
    if owner is not None and not self.error:
     out=self.call('mb_pull')
     if type(out) is not bytes or len(out)>192:raise RuntimeError('Invalid native binary reply')
     if out:
      with self.lock:
       if self.owner==owner:
        if len(self.rx)+len(out)>MAX_QUEUE:raise BufferError('Output queue full; explicit reconnect required')
        self.rx.extend(out);self.stats['output_bytes']+=len(out);self.event('bytes',direction='from_vm',hex=out.hex())
       else:self.stats['idle_discarded_bytes']+=len(out)
    elif owner is None and now-self.last_idle>=.1:
     self.last_idle=now
     for _ in range(4):
      out=self.call('mb_pull')
      if type(out) is not bytes:raise RuntimeError('Invalid idle binary reply')
      self.stats['idle_discarded_bytes']+=len(out)
      if not out:break
    if self.hardware and self.host_fault is None and now-self.last_host>=.03:
     self.last_host=now;self.host_tick()
    if now-self.last_health>=2:
     self.last_health=now;uptime=self.call(self.uptime_method);fault=self.call('mb_stat',6)
     with self.lock:self.health={'uptime_ms':uptime,'vm_fault':fault,'task_count':self.call('mb_stat',7),'object_store_free':self.call('mb_stat',9)}
     if self.last_uptime is not None and uptime<self.last_uptime:
      self._last_applied=None
      if owner is not None:raise RuntimeError('STM32 restarted; reconnect explicitly')
     self.last_uptime=uptime
     if fault and owner is not None:raise RuntimeError('SmallVM output fault; reconnect explicitly')
     self.event('health',**self.health)
    self.stop_event.wait(.005 if owner is not None else .02)
   except (ValueError,TimeoutError,RuntimeError,BufferError,OSError) as exc:
    self.fail(str(exc));self.stop_event.wait(.2)
