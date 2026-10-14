# SPDX-License-Identifier: MIT
from pathlib import Path
import threading
import uvicorn
from arduino.app_utils import Bridge,brick
from .leds import LinuxLEDs
from .transport import Transport
from .server import create_server
@brick
class MicroBlocksBridge:
 def __init__(self):
  data=Path.cwd()/'data';self.leds=LinuxLEDs(data/'led_original.json');self.transport=Transport(Bridge,self.leds,data)
  self.application=create_server(self.transport,data,Path(__file__).parent/'web')
  self.server=uvicorn.Server(uvicorn.Config(self.application,host='0.0.0.0',port=8080,access_log=False,ws_max_size=8192,ws_max_queue=8))
  self.thread=None
 def start(self):
  self.transport.start();self.thread=threading.Thread(target=self.server.run,name='microblocks-http',daemon=True);self.thread.start()
  print('MicroBlocks: private-network port 8080; open the IDE directly. No MCU upload performed.',flush=True)
 def stop(self):
  self.server.should_exit=True
  if self.thread:self.thread.join(5)
  self.transport.stop();self.leds.restore()
