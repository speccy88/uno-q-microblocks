#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build on UNO Q using its installed core. Never uploads firmware."""
from pathlib import Path
import argparse,subprocess,shutil,hashlib,shlex,json,datetime
R=Path(__file__).resolve().parents[1]
(R/'private-evidence').mkdir(exist_ok=True);(R/'build').mkdir(exist_ok=True)
a=argparse.ArgumentParser();a.add_argument('--target',required=True,help='SSH host/alias');a.add_argument('--control-path');a.add_argument('--remote-dir',default='microblocks-runtime-build');a.add_argument('--preserve-pacoblaze',action='store_true');o=a.parse_args()
ssh=['ssh','-o','BatchMode=yes']+(['-S',o.control_path] if o.control_path else [])+[o.target]
scp=['scp','-q']+(['-o','ControlPath='+o.control_path] if o.control_path else [])
subprocess.run(['python3',str(R/'firmware/prepare.py')],check=True)
name='smallvm_combined' if o.preserve_pacoblaze else 'smallvm_unoq';d=R/'build'/name
if o.preserve_pacoblaze:
 shutil.copytree(R/'build/smallvm_unoq',d,dirs_exist_ok=True)
 p=d/'smallvm_unoq.ino';s=p.read_text().replace('void setup(){initTransport();','void phase3Setup();\nvoid setup(){phase3Setup();initTransport();');(d/(name+'.ino')).write_text(s);p.unlink()
 pb=R/'firmware/pacoblaze_upload.ino';assert hashlib.sha256(pb.read_bytes()).hexdigest()=='56230a7cd6ad63239a4473e42720f1e6487885d666843b85b65fa4827ae406e5'
 (d/'src/phase3.cpp').write_text('#include <Arduino.h>\n'+pb.read_text().replace('void setup()','void phase3Setup()').replace('void loop()','void phase3Loop()'))
remote=o.remote_dir
assert remote and not any(c in remote for c in '\n\r{}')
subprocess.run(ssh+[shlex.join(['mkdir','-p',remote])],check=True)
subprocess.run(scp+['-r',str(d),o.target+':'+remote+'/'],check=True)
libs=R/'sources/arduino-libraries'
if libs.exists():subprocess.run(scp+['-r',str(libs),o.target+':'+remote+'/'],check=True)
cmd=['arduino-cli','compile','--fqbn','arduino:zephyr:unoq','--board-options','wait_linux_boot=no','--build-property','compiler.c.extra_flags=-DSMALLVM_UNOQ','--build-property','compiler.cpp.extra_flags=-DSPI_MIN_CLOCK_FREQUENCY=100000','--libraries',remote+'/arduino-libraries','--jobs','2','--warnings','all','--verbose','--build-path',remote+'/build-'+name,'--output-dir',remote+'/output-'+name,remote+'/'+name]
p=subprocess.run(ssh+[shlex.join(cmd)],capture_output=True,text=True,timeout=600)
(R/'private-evidence'/('build-'+name+'.log')).write_text(p.stdout+p.stderr)
if p.returncode:raise SystemExit(p.stderr[-3000:])
out=R/'build'/('output-'+name);out.mkdir(exist_ok=True)
for suffix in ['.elf','.elf-zsk.bin','_debug.elf','.map']:
 f=remote+('/build-' if suffix=='.map' else '/output-')+name+'/'+name+'.ino'+suffix
 subprocess.run(scp+[o.target+':'+f,str(out)],check=True)
b=out/(name+'.ino.elf-zsk.bin');report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'preserves_pacoblaze':o.preserve_pacoblaze,'module_bytes':b.stat().st_size,'module_sha256':hashlib.sha256(b.read_bytes()).hexdigest(),'loader_sha256':'39d4a4fd47241663323f6e04f94dd8f5a9f9ad6582cf1df37f9709b74026adcd'}
(out/'image.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
