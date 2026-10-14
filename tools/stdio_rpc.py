"""Ephemeral SSH-stdio test gateway to existing Router. Fixed methods; no listener."""
import sys,json
from pathlib import Path
from arduino.router_bridge import Bridge
ALLOWED={'mb_hw_version','mb_uptime','mb_host_peek','mb_host_ack','mb_hw_stat','mb_hw_state','mb_matrix','mb_gpio','mb_push','mb_pull','mb_open','mb_echo','mb_stat','mb_size','mb_var','pb_uptime','pb_echo','pb_ping','pb_info','pb_epoch','pb_errors','pb_sessions','pb_led_register','pb_status','pb_apb1'}
def unpack(v):
 if isinstance(v,dict) and set(v)=={'binary_hex'}:
  b=bytes.fromhex(v['binary_hex'])
  if len(b)>192:raise ValueError('binary payload limit')
  return b
 if type(v) is int:return v
 raise ValueError('parameter type')
def pack(v):return {'binary_hex':v.hex()} if isinstance(v,bytes) else v
b=Bridge();assert b.connect(timeout=5)
try:
 print(json.dumps({'hello':1,'linux_boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}),flush=True)
 while True:
  line=sys.stdin.buffer.readline(4097)
  if not line:break
  req=json.loads(line);id=req['id']
  try:
   if len(line)>4096 or req['method'] not in ALLOWED:raise ValueError('request outside fixed test contract')
   result=b.call(req['method'],*[unpack(v) for v in req['params']],timeout=3)
   reply={'id':id,'result':pack(result)}
  except Exception as e:reply={'id':id,'error':str(e)}
  print(json.dumps(reply),flush=True)
finally:b.disconnect()
