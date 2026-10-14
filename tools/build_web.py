# SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib,json,shutil,subprocess,re
R=Path(__file__).resolve().parents[1];S=R/'sources/smallvm';web=R/'app/bricks/microblocks_bridge/web';web.mkdir(parents=True,exist_ok=True);(R/'private-evidence').mkdir(exist_ok=True);(R/'build').mkdir(exist_ok=True)
# The editable community library/examples are the build's authoritative inputs.
shutil.copy2(R/'examples/UNO_Q_Hardware.ubl',S/'Libraries/UNO_Q_Hardware.ubl')
(S/'Examples/UNO Q').mkdir(parents=True,exist_ok=True)
for example in (R/'examples').glob('*.ubp'):
 shutil.copy2(example,S/'Examples/UNO Q'/example.name)
api=S/'ide/MicroBlocksAPI.gp';text=api.read_text()
needle="\t// Project\n"
addition="""\t// UNO Q: local, pinned files imported through the original editor/compiler.
\t} (endPoint == 'unoq.loadLibrary') {
\t\trespondAPIRequest this id 0
\t\tdata = (readEmbeddedFile 'Libraries/UNO_Q_Hardware.ubl')
\t\tif (notNil data) { importLibraryFromString scripter data 'UNO Q Hardware' '' }
\t} (endPoint == 'unoq.openExample') {
\t\trespondAPIRequest this id 0
\t\tname = (at params 1)
\t\tif (isOneOf name 'arithmetic' 'output' 'rgb' 'matrix' 'combined' 'matrix-drawing') {
\t\t\tdata = (readEmbeddedFile (join 'Examples/UNO Q/' name '.ubp'))
\t\t\tif (notNil data) { openProject editor data (join name '.ubp') }
\t\t}

"""
if 'unoq.loadLibrary' not in text:api.write_text(text.replace(needle,addition+needle,1))
# UNO Q uses the previously empty IO primitive slot (3), retaining VM enum/ABI.
compiler=S/'ide/MicroBlocksCompiler.gp';ct=compiler.read_text()
if "atPut primsets 'unoq'" not in ct:
 ct=ct.replace('\t\tprimSetIndex += 1\n\t}\n}', "\t\tprimSetIndex += 1\n\t}\n\tatPut primsets 'unoq' (at primsets 'io')\n}",1)
 compiler.write_text(ct)
editor=S/'ide/MicroBlocksEditor.gp';et=editor.read_text()
et=et.replace("launch (global 'page') (newCommand 'checkLatestVersion' this) // start version check", "// UNO Q pinned offline edition: no remote version request")
et=re.sub(r"/Users/[^\s']+",'EXAMPLE_FOLDER',et)
editor.write_text(et)
(S/'chromeApp/MicroBlocks').mkdir(exist_ok=True)
# Programming other boards is disabled; do not embed unrelated firmware images.
bs=S/'chromeApp/emscripten/buildEmcc.sh';bt=bs.read_text()
bt='\n'.join(line for line in bt.splitlines() if not line.startswith('cp -r ../../precompiled/') and not line.startswith('cp -r ../../esp32/'))+'\n'
if 'set -e' not in bt:bt=bt.replace('#!/bin/sh','#!/bin/sh\nset -e',1)
bs.write_text(bt)
# Build GP with updated embedded standard-format library/examples, full source provided.
p=subprocess.run(['sh','buildEmcc.sh'],cwd=S/'chromeApp/emscripten',capture_output=True,text=True)
(R/'private-evidence/web-ide-build-final.log').write_text(p.stdout+p.stderr)
if p.returncode:raise SystemExit(p.stderr[-3000:])
shutil.copytree(S/'chromeApp/webapp',web,dirs_exist_ok=True)
html=(web/'microblocks.html').read_text()
a=html.index('\t\t<!-- Force HTTPS.');b=html.index('\t\t<!-- FileUploader -->',a)
html=html[:a]+html[b:]
# Network edition cannot access USB/DFU firmware controls. Dedicated installer only.
html=html.replace('<script type="text/javascript" src="flasher.js" defer></script>','')
html=html.replace('\t\t<!-- GP Init -->','\t\t<script src="unoq-network.js"></script>\n\t\t<!-- GP Init -->')
# Version the GP bundle together: cached JavaScript metadata must match its data file.
bundle_hash=hashlib.sha256(b''.join((web/n).read_bytes() for n in ('gp_wasm.js','gp_wasm.data','gp_wasm.wasm'))).hexdigest()[:16]
html=html.replace('<script type="text/javascript" src="gp_wasm.js"></script>',
 '<script>Module.locateFile=function(name,prefix){return prefix+name+"?v='+bundle_hash+'";};</script>\n\t\t<script type="text/javascript" src="gp_wasm.js?v='+bundle_hash+'"></script>')
(web/'microblocks.html').write_text(html)
# Private resident-board IDE uses direct local assets; no stale cross-session PWA cache.
sp=web/'gpSupport.js';sp.write_text(sp.read_text().replace("navigator.serviceWorker.register('sw.js');","// UNO Q: local server assets, service worker registration disabled."))
shutil.copy2(R/'app/bricks/microblocks_bridge/unoq-network.js',web/'unoq-network.js')
report={str(p.relative_to(web)):hashlib.sha256(p.read_bytes()).hexdigest() for p in web.rglob('*') if p.is_file()}
(R/'build/web-assets-sha256.json').write_text(json.dumps(report,indent=2)+'\n');print('Built official pinned web IDE:',len(report),'local assets')
