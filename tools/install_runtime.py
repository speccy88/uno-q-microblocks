#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Explicit application-only installation on UNO Q Linux. Never called by the App."""
import argparse,datetime,hashlib,json,os,subprocess
from pathlib import Path
LOADER_SHA='39d4a4fd47241663323f6e04f94dd8f5a9f9ad6582cf1df37f9709b74026adcd'
ADDRESS=0x08100000;CAPACITY=0xC0000
START='''gdb port disabled
tcl port disabled
telnet port disabled
reset_config srst_only srst_nogate srst_push_pull connect_assert_srst
init
reset
halt
'''
END='''reset
sleep 100
mww 0x40036400 0xCAFFEEEE
shutdown
'''
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def require(ok,message):
 if not ok:raise RuntimeError(message)
def safe_path(p):
 p=p.resolve();require(not any(c in str(p) for c in '{}\r\n'),'Unsupported path characters');return p
def main():
 a=argparse.ArgumentParser(description=__doc__);g=a.add_mutually_exclusive_group(required=True);g.add_argument('--install',type=Path,help='image.json from a completed build');g.add_argument('--restore',type=Path,help='private recovery manifest');a.add_argument('--loader',type=Path,required=True,help='installed core 1.0.0 firmware ELF');a.add_argument('--recovery-dir',type=Path,default=Path('runtime-recovery'));o=a.parse_args()
 if os.geteuid()!=0:raise SystemExit('Run on UNO Q Linux with sudo; stop the App first.')
 loader=safe_path(o.loader);require(sha(loader)==LOADER_SHA,'Different loader/core. Refuse all writes.')
 o.recovery_dir.mkdir(parents=True,exist_ok=True,mode=0o700);os.chmod(o.recovery_dir,0o700)
 def run(body,label,release=True):
  cfg=o.recovery_dir/(label+'.cfg');cfg.write_text(START+body+END)
  p=subprocess.run(['/opt/openocd/bin/openocd','-d2','-s','/opt/openocd','-f','openocd_gpiod.cfg','-f',str(cfg.resolve())],capture_output=True,text=True,timeout=240)
  (o.recovery_dir/(label+'.json')).write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr},indent=2)+'\n')
  if p.returncode:raise RuntimeError('OpenOCD failed; inspect private recovery log '+label)
 def restore(manifest):
  r=json.loads(manifest.read_text());backup=manifest.parent/r['backup_file']
  backup=safe_path(backup);require(r['loader_sha256']==LOADER_SHA and backup.stat().st_size==CAPACITY and sha(backup)==r['backup_sha256'],'Recovery checksum or bounds mismatch')
  run(f'flash verify_image {{{loader}}}\nflash write_image erase {{{backup.resolve()}}} 0x08100000 bin\nflash verify_image {{{backup.resolve()}}} 0x08100000 bin\nflash verify_image {{{loader}}}\n','restore')
 if o.restore:restore(o.restore.resolve());print('Full application region restored and verified. Loader unchanged.');return
 manifest=o.install.resolve();r=json.loads(manifest.read_text());name='smallvm_combined' if r['preserves_pacoblaze'] else 'smallvm_unoq';image=manifest.parent/(name+'.ino.elf-zsk.bin')
 image=safe_path(image);data=image.read_bytes();require(52<=len(data)<=CAPACITY and data[:6]==b'\x7fELF\x01\x01' and data[18:20]==b'\x28\x00','Invalid ARM32 little-endian bounded LLEXT image')
 require(sha(image)==r['module_sha256'] and image.stat().st_size==r['module_bytes'] and r['loader_sha256']==LOADER_SHA,'Image manifest checksum mismatch')
 backup=safe_path(o.recovery_dir/'before-install-768KiB.bin');record=o.recovery_dir/'recovery.json'
 if backup.exists() or record.exists():raise SystemExit('Existing backup preserved. Select a new recovery directory for another installation.')
 run(f'flash verify_image {{{loader}}}\ndump_image {{{backup.resolve()}}} 0x08100000 0xC0000\n','backup')
 require(backup.stat().st_size==CAPACITY,'Truncated recovery dump; no write allowed')
 record.write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'backup_file':backup.name,'backup_sha256':sha(backup),'loader_sha256':LOADER_SHA,'installed_sha256':sha(image)},indent=2)+'\n');os.chmod(backup,0o600);os.chmod(record,0o600)
 try:
  run(f'flash verify_image {{{loader}}}\nflash write_image erase {{{image}}} 0x08100000 bin\nflash verify_image {{{image}}} 0x08100000 bin\nflash verify_image {{{loader}}}\n','install')
 except BaseException:
  restore(record);raise
 print('Application programmed and readback verified. Start App and check /api/status.')
 print('If methods fail to register immediately after installation, perform the documented single MCU-only restart. Never use that step for browser reconnect or normal App restart.')
if __name__=='__main__':main()
