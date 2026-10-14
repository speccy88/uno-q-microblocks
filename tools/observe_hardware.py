#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Bounded, read-only observation of already-running MCU bytecode (board Linux)."""
import argparse,datetime,json,time
from arduino.router_bridge import Bridge
p=argparse.ArgumentParser();p.add_argument('--pacoblaze',action='store_true');p.add_argument('--seconds',type=float,default=15);p.add_argument('--output',required=True);a=p.parse_args();assert 0<a.seconds<=60
b=Bridge();assert b.connect(timeout=5);events=[]
try:
 end=time.monotonic()+a.seconds
 while time.monotonic()<end:
  row={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'uptime':b.call('mb_uptime'),'rgb_requested':b.call('mb_hw_state').hex(),'gpio_actual':b.call('mb_gpio').hex(),'matrix':b.call('mb_matrix').hex(),'tasks':b.call('mb_stat',7),'fault':b.call('mb_stat',6),'queue':b.call('mb_hw_stat',0),'ack_count':b.call('mb_hw_stat',1),'host_failures':b.call('mb_hw_stat',2),'rgb_writes':b.call('mb_hw_stat',3),'matrix_shows':b.call('mb_hw_stat',4)}
  if a.pacoblaze:row.update(fpga_ping=b.call('pb_ping'),fpga_epoch=b.call('pb_epoch'))
  events.append(row);time.sleep(.05)
finally:b.disconnect()
with open(a.output,'w') as f:json.dump(events,f,indent=2);f.write('\n')
print(json.dumps({'observations':len(events),'tasks':sorted(set(r['tasks'] for r in events)),'faults':sorted(set(r['fault'] for r in events)),'fpga_ping':sorted(set(r.get('fpga_ping') for r in events)),'fpga_epoch':sorted(set(r.get('fpga_epoch') for r in events)),'host_failures':sorted(set(r['host_failures'] for r in events))}))
