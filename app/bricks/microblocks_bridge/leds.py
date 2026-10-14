# SPDX-License-Identifier: MIT
"""Least-privilege kernel LED access; native App Lab device aliases supported."""
import json,os
from pathlib import Path
CHANNELS={1:('red:user','green:user','blue:user'),2:('red:panic','green:wlan','blue:bt')}
MODERN={1:('unoq:user-red1','unoq:user-green1','unoq:user-blue1'),2:('unoq:panic-red2','unoq:wlan-green2','unoq:bt-blue2')}
def discover():
 result={}
 for led in (1,2):
  for i,color in enumerate('rgb'):
   candidates=[Path('/dev/leds/builtin')/f'led{led}_{color}',Path('/sys/class/leds')/MODERN[led][i],Path('/sys/class/leds')/CHANNELS[led][i]]
   p=next((p for p in candidates if (p/'brightness').exists()),None)
   if p is None:raise FileNotFoundError(f'Onboard LED {led} {color} channel unavailable')
   result[f'{led}{color}']=p
 return result
class LinuxLEDs:
 def __init__(self,state_file):
  self.paths=discover();self.state_file=Path(state_file);self.max={k:int((p/'max_brightness').read_text()) for k,p in self.paths.items()}
  self.original=self.snapshot()
  if self.state_file.exists():self.original=json.loads(self.state_file.read_text())
  else:
   self.state_file.parent.mkdir(parents=True,exist_ok=True);self.state_file.write_text(json.dumps(self.original,indent=2)+'\n');self.state_file.chmod(0o600)
 def snapshot(self):
  result={}
  for k,p in self.paths.items():
   trigger=(p/'trigger').read_text();active=trigger.split('[')[1].split(']')[0]
   result[k]={'brightness':int((p/'brightness').read_text()),'trigger':active}
  return result
 def set(self,led,r,g,b):
  if type(led) is not int or led not in (1,2):raise ValueError('Linux LED number must be 1 or 2')
  if any(type(v) is not int or not 0<=v<=255 for v in (r,g,b)):raise ValueError('RGB channels must be integers 0..255')
  for color,v in zip('rgb',(r,g,b)):
   k=f'{led}{color}';p=self.paths[k];maximum=self.max[k]
   level=int(v>0) if maximum==1 else (v*maximum+127)//255
   (p/'trigger').write_text('none');(p/'brightness').write_text(str(level))
  return self.snapshot()
 def restore(self):
  errors=[]
  for k,p in self.paths.items():
   try:
    saved=self.original[k];(p/'trigger').write_text('none');(p/'brightness').write_text(str(saved['brightness']));(p/'trigger').write_text(saved['trigger'])
   except OSError as e:errors.append(f'{k}: {e}')
  if errors:raise RuntimeError('LED restoration: '+'; '.join(errors))
