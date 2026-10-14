"""Build the real wasm32 interpreter and repeat corrected stall/stress tests."""
from pathlib import Path
import subprocess,json,datetime
r=Path(__file__).resolve().parents[1];(r/'private-evidence').mkdir(exist_ok=True);subprocess.run(['python3',str(r/'firmware/prepare.py')],check=True)
s=r/'build/smallvm_unoq/src';args=['emcc','-O1','-U__EMSCRIPTEN__','-DSMALLVM_UNOQ','-I'+str(s),*map(str,sorted((s/'vm').glob('*.c'))),str(r/'firmware/adapter/platform.c'),str(r/'firmware/adapter/uno_hardware.c'),str(r/'firmware/host/vm_host.c'),'-sENVIRONMENT=node','-sASSERTIONS=2','-o',str(r/'build/vm_host.js')]
p=subprocess.run(args,capture_output=True,text=True);(r/'private-evidence/host-build-reproduced.log').write_text(p.stdout+p.stderr);assert p.returncode==0
records=[]
for repeat in range(5):
 for mode in ['ide-reset','fragmented','truncation','backpressure','bulk','hardware','stress']:
  p=subprocess.run(['node',str(r/'build/vm_host.js')]+([] if mode=='stress' else [mode]),capture_output=True,text=True,timeout=5)
  records.append({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'repeat':repeat,'mode':mode,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr});assert p.returncode==0,(mode,p.stderr)
(r/'private-evidence/host-tests-reproduced.json').write_text(json.dumps(records,indent=2)+'\n');print('35 actual interpreter tests PASS')
