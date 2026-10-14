#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Create a deny-by-default sanitized publication tree and one community ZIP."""
from pathlib import Path
import hashlib,json,re,shutil,zipfile
R=Path(__file__).resolve().parents[1];P=R/'release/uno-q-microblocks-community';P.mkdir(parents=True,exist_ok=True)
profile_file=R/'private-evidence/publication-redactions.json'
profile=json.loads(profile_file.read_text()) if profile_file.exists() else {}
SECRET=profile.get('values',[])
for name in ['access_token','import_access_token']:
 p=R/'private-evidence'/name
 if p.exists():SECRET.append(p.read_text().strip())
def sanitize(s):
 s=s.replace(str(R.parent),'<WORKSPACE>')
 for old,new in profile.get('paths',{}).items():s=s.replace(old,new)
 if profile.get('control_pattern'):s=re.sub(profile['control_pattern'],'<SSH_CONTROL>',s)
 for value in SECRET:s=s.replace(value,'<REDACTED>')
 return s
BADPARTS={'.git','__pycache__','.DS_Store','.venv','.cache','data'}
def copy(src,dst,safe_text=False):
 if src.is_dir():
  for f in src.rglob('*'):
   if f.is_file() and not BADPARTS.intersection(f.relative_to(src).parts) and f.suffix not in ('.pyc','.ttf','.otf','.woff','.woff2','.fon','.pf','.sfd'):copy(f,dst/f.relative_to(src),safe_text)
 else:
  dst.parent.mkdir(parents=True,exist_ok=True)
  if safe_text:
   try:dst.write_text(sanitize(src.read_text()));return
   except UnicodeDecodeError:pass
  shutil.copy2(src,dst)
for f in R.glob('*.md'):copy(f,P/f.name,True)
for name in ['.gitignore','.dockerignore']:copy(R/name,P/name)
for d in ['app','examples','firmware','patches','tests']:copy(R/d,P/d)
# Only public, parameterized tools; the local exact-predecessor deployment helper is private.
for name in ['build_runtime.py','build_web.py','test_host_vm.py','install_runtime.py','prepare_app.py','verify_browser_log.py','test_live_security.py','observe_hardware.py','stdio_rpc.py','write_docs.py','package.py']:
 copy(R/'tools'/name,P/'tools'/name)
copy(R/'dist/microblocks-uno-q-app.zip',P/'dist/microblocks-uno-q-app.zip')
for name,label in [('smallvm_unoq','generic'),('smallvm_combined','with_pacoblaze')]:
 base=R/'build'/('output-'+name)
 for fn in [name+'.ino.elf-zsk.bin','image.json']:copy(base/fn,P/'runtime'/label/fn)
copy(R/'build/web-assets-sha256.json',P/'evidence/web-assets-sha256.json')
# Source required by the real VM and GP builds, not old apps, binaries or raw fonts.
S=R/'sources/smallvm';D=P/'sources/smallvm'
for d in ['vm','ide','Libraries','Examples','translations','img','gp/runtime']:copy(S/d,D/d)
for f in ['LICENSE','Mozilla Public License, version 2.0.html','README.md']:
 if (S/f).exists():copy(S/f,D/f)
for f in (S/'chromeApp/emscripten').iterdir():
 if f.is_file() and f.suffix in ['.c','.h','.sh']:copy(f,D/'chromeApp/emscripten'/f.name)
# Static source/templates, excluding generated GP binaries duplicated in app/web.
for f in (S/'chromeApp/webapp').rglob('*'):
 if f.is_file() and not f.name.startswith('gp_wasm.') and f.suffix not in ['.ttf','.otf','.woff','.woff2']:copy(f,D/'chromeApp/webapp'/f.relative_to(S/'chromeApp/webapp'))
for d in ['precompiled','esp32','chromeApp/MicroBlocks']:(D/d).mkdir(parents=True,exist_ok=True)
copy(R/'sources/arduino-libraries',P/'sources/arduino-libraries')
# Public evidence is a sanitized copy, never a whole private directory/old archive.
files=['baseline-archive-check.json','blueprint-check.json','browser-baseline.json','browser-baseline.frames.json','browser-final-runtime.json','browser-final-runtime.frames.json','events-final-runtime.jsonl','rgb-observations.json','matrix-observations.json','combined-connected.json','combined-disconnected.json','memory-report.json','runtime-startup.json','led-restore-baseline.json','live-security.json','gui-spi-events.json','server-tests-final.log','transport-tests-final.log','installer-guard-tests.log','host-tests-reproduced.json','host-build-reproduced.log','build-smallvm_unoq.log','build-smallvm_combined.log','web-ide-build-final.log','runtime-install.json','runtime-ack-install.json','post-install-mcu-restart.json','app-start-baseline.log','app-restart-baseline.log','app-start-standard-webview.log','app-export-final.log','app-import-final.json','imported-app-start.log','import-runtime-status.log','standard-app-status.log','app-lifecycle.json','final-led-restore.json','docker-after.txt','package-inputs.json','hardware-verification.json','gitleaks-sealed.log','extracted-final-test.json','share-import.json']
files.append('visual-confirmations.json')
for name in files:
 f=R/'private-evidence'/name
 if f.exists():copy(f,P/'evidence'/name,True)
for f in (R/'private-evidence').glob('*.png'):copy(f,P/'evidence/screenshots'/f.name)
copy(S/'Mozilla Public License, version 2.0.html',P/'licenses/MPL-2.0.html')
(P/'LICENSE').write_text('New Python/tools/docs code: MIT (licenses/MIT.txt). SmallVM/GP and derivative firmware/frontend: MPL-2.0. Upstream notices and per-file third-party licenses remain applicable. See LICENSING.md.\n')
(P/'licenses/MIT.txt').write_text('''MIT License
Copyright (c) 2026 UNO Q community contributors
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
''')
(P/'LICENSING.md').write_text('''# Attribution and source availability
MicroBlocks SmallVM and the original GP editor are upstream software from MicroBlocks, pinned as documented in SOURCE_REVISIONS.md. Their MPL-2.0 notice/full license, the build source subset, modified sources and patches accompany the generated assets and runtime. Do not represent them as original community code.

Python Brick, scripts and documentation are MIT. Firmware/platform and browser changes to MPL-covered code retain MPL-2.0. FileSaver.js retains its MIT notice; USB DFU support retains ISC notices. Other upstream per-file notices remain in place. Browser fonts are supplied by the browser/system; no raw font files are redistributed.

The six C++ dependency snapshots include upstream notices/license files. ArduinoCore-Zephyr 1.0.0 and the Arduino LED matrix API are unmodified installed dependencies, with corresponding source at https://github.com/arduino/ArduinoCore-zephyr/tree/1.0.0. Stock Arduino App Lab/App CLI/SDK and compiler are prerequisites, not modified redistributions. Their source revisions and observed image digest are recorded. Do not publish private recovery dumps or secrets as licensing source material.
''')
(P/'prompts').mkdir(exist_ok=True)
(P/'prompts/IMPLEMENTATION.md').write_text('Continue the existing UNO Q SmallVM/PacoBlaze port. Preserve the loader, GPIO wiring, FPGA configuration and previous recovery artifacts. Build the real pinned MicroBlocks GP web editor into a supported Python App Lab Brick. Keep bytecode execution on STM32, use bounded binary Bridge transport, native RGB/matrix primitives and a separate Linux LED action queue. Test actual browser, hardware and App lifecycle. Mark optical or fresh-board assumptions untested. Package only reviewed source, assets, tests, sanitized evidence and explicit app-only installation/recovery tools. Do not auto-flash on App start or browser reconnect.\n')
# Verify forbidden private values and paths, including inside the nested App archive.
errors=[]
def check(data,name):
 for value in SECRET:
  if value.encode() in data:errors.append((name,'private value'))
 for value in [v.encode() for v in profile.get('paths',{})]:
  if value in data:errors.append((name,'machine path'))
for f in P.rglob('*'):
 if not f.is_file():continue
 check(f.read_bytes(),str(f.relative_to(P)))
 if f.suffix=='.zip':
  with zipfile.ZipFile(f) as z:
   if z.testzip():errors.append((f.name,'ZIP CRC'))
   for n in z.namelist():check(z.read(n),f.name+':'+n)
if errors:raise SystemExit('Publication scan failed: '+str(errors[:12]))
manifest={str(f.relative_to(P)):hashlib.sha256(f.read_bytes()).hexdigest() for f in P.rglob('*') if f.is_file() and f.name not in ['SHA256SUMS','BUNDLE_VERIFICATION.json']}
(P/'SHA256SUMS').write_text(''.join(h+'  '+n+'\n' for n,h in sorted(manifest.items())))
(P/'BUNDLE_VERIFICATION.json').write_text(json.dumps({'files':len(manifest),'private_values_found':0,'machine_paths_found':0,'raw_fonts_included':0,'old_flash_backups_included':0,'nested_app_zip_crc':'PASS'},indent=2)+'\n')
archive=R.parent/'uno-q-microblocks-community-2026-10-13.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for f in sorted(P.rglob('*')):
  if f.is_file():z.write(f,str(f.relative_to(P.parent)))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print(json.dumps({'archive':str(archive),'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'files':len(manifest)},indent=2))
