#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Compile/run the actual GP slot model under Node; no simulated interpreter."""
from pathlib import Path
import json, subprocess

R = Path(__file__).resolve().parents[1]
S = R / 'sources/smallvm'
C = S / 'chromeApp/emscripten'
B = R / 'build/gp-slot-tests'
B.mkdir(parents=True, exist_ok=True)
(R / 'private-evidence').mkdir(exist_ok=True)
names = 'browserPrims cache dict embeddedFS events gp httpPrims interp mem memGC oop parse pathPrims prims serialPortPrims sha1 sha2 soundPrims textAndFontPrims vectorPrims'.split()
cmd = ['emcc', '-std=gnu99', '-O1', '-DNO_JPEG', '-DNO_SDL', '-DNO_SOCKETS', '-DSHA2_USE_INTTYPES_H', '-sUSE_ZLIB=1', '-sFETCH=1', '-sENVIRONMENT=node', '-sALLOW_MEMORY_GROWTH=1', '-lnodefs.js', *[str(C / (name + '.c')) for name in names], '-o', str(B / 'gp-tests.js')]
p = subprocess.run(cmd, capture_output=True, text=True)
(R / 'private-evidence/matrix-slot-build.log').write_text(p.stdout + p.stderr)
if p.returncode:
    raise SystemExit(p.stderr[-2000:])
libs = sorted((S / 'gp/runtime/lib').glob('*.gp')) + sorted((S / 'ide').glob('*.gp'))
p = subprocess.run(['node', str(B / 'gp-tests.js'), *[str(f.relative_to(R)) for f in libs], 'tests/matrix_slot.gp'], cwd=R, capture_output=True, text=True, timeout=15)
(R / 'private-evidence/matrix-slot-tests.log').write_text(p.stdout + p.stderr)
for line in p.stdout.splitlines():
    if not line.startswith('PATTERN_BYTECODE_JSON:'):
        print(line)
if p.returncode or 'PASS: real GP matrix slot' not in p.stdout or 'Error:' in p.stdout or 'Unknown' in p.stdout:
    raise SystemExit(p.stderr or 'GP slot test did not complete successfully')
heart = '00077000770000077770777700077777777777007777777777700077777777700000777777700000007777700000000007000000'
encoded = next(line.split(':', 1)[1] for line in p.stdout.splitlines() if line.startswith('PATTERN_BYTECODE_JSON:'))
bytecode = bytes(json.loads(encoded))
(B / 'pattern.bytecode').write_bytes(bytecode)
if heart.encode() not in bytecode:
    raise SystemExit('Compiler did not preserve the 104-pixel instruction literal')
print('PASS: .ubp save/load and compiled instruction literal preserved')
