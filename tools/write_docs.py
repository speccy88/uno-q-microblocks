# SPDX-License-Identifier: MIT
from pathlib import Path
R=Path(__file__).resolve().parents[1]
docs={
'START_HERE.md':'''# MicroBlocks on Arduino UNO Q

The real, pinned MicroBlocks 2.5.8 browser IDE compiles programs for SmallVM v417
running on the STM32U585. Arduino App Lab hosts the UI and binary transport in a
Python Custom Brick. RGB LED 1/2 commands originate in MCU bytecode and are
serviced by Linux; LED 3/4 and the blue 13x8 matrix use MCU native primitives.

This is an onboard-hardware proof, not complete UNO Q GPIO/sensor support.
Programs live in RAM. Restarting the Python App does not reinstall or reset the
MCU. Opening the IDE can stop/synchronize scripts through normal MicroBlocks
protocol operations. A MCU reset or power cycle loses RAM programs.

## Install the App and runtime

Use a board with the verified ArduinoCore-Zephyr 1.0.0 loader. Other loader hashes
are deliberately refused. Do not upgrade/downgrade firmware to bypass this guard.
Work on UNO Q Linux from the extracted community directory. Copy this directory
to the board using your own SSH alias; no addresses or credentials are embedded.

1. Import `dist/microblocks-uno-q-app.zip` in App Lab, or run:
   `arduino-app-cli app import dist/microblocks-uno-q-app.zip`.
   Import may append a suffix if an app with this name already exists. Record its
   returned ID/path; the commands below use the normal first-import ID.
2. BEFORE the first App start, capture its original Linux LED triggers:
   `python3 tools/prepare_app.py "$HOME/ArduinoApps/microblocks-uno-q"`.
   Keep this private `data/led_original.json` through all restarts. App Lab itself
   changes LED triggers before Python starts, so this preparation step matters.
3. Stop the intended App before an explicit runtime installation. Preserve any
   unrelated running app and its firmware. The runtime installer is separate
   from normal App start and replaces only the MCU application region.
4. For a board without the external FPGA, install the built generic image:

```sh
LOADER="$HOME/.arduino15/packages/arduino/hardware/zephyr/1.0.0/firmwares/zephyr-arduino_uno_q_stm32u585xx.elf"
sudo python3 tools/install_runtime.py --install runtime/generic/image.json --loader "$LOADER" --recovery-dir runtime-recovery/first-install
```

The installer checks the ARM image, checksum, size and exact loader; physically
verifies the loader, saves the complete 768 KiB application region, then writes
and verifies the bounded application image. It verifies the loader again and
restores the full private backup on an installation failure. KEEP the recovery
folder private and backed up. Never include it in exports or Git.

The generic image was built and analyzed, but was not flashed on the test board,
which retains its FPGA service. Existing UNO Q/FPGA users can use
`runtime/with_pacoblaze/image.json` instead: this is the physically tested image.
See RECOVERY.md for first-install registration troubleshooting.

5. Start normally: `arduino-app-cli app start user:microblocks-uno-q`.
   There is no sketch directory or automatic firmware installation in this App.
6. App Lab reports port **8080** as a webview. Use a private LAN numeric address,
   or use an encrypted tunnel from your computer:

```sh
ssh -N -L 18080:127.0.0.1:8080 UNO_Q_SSH_ALIAS
```

Open `http://localhost:18080`. Enter the per-install code from the App's
`data/access_token` file, read privately on your board. Do not save it in Git.
The standard App Lab port publishes on board interfaces; do not forward it to
the Internet. Public IP/domain Host headers are rejected, and programming
requires authentication and an exact WebSocket origin. Close the old desktop
PTY bridge before connecting: exclusivity applies to clients of this gateway,
not every possible direct Router client.

## Use the IDE

Connection is automatic and uses WebSocket/Bridge, without WebSerial selection.
Use Connect to reconnect after a disconnect. After an App restart, reload and
sign in again. The hardware library loads automatically; `UNO Q Hardware` is
also a one-click import. The original editor, compiler, Start/Stop, variables,
and output workflow are preserved. Firmware/BLE installation controls are
blocked; runtime installation is only the explicit procedure above.

Choose **RGB LEDs**, wait for the project to finish loading, then press Start.
Choose **Draw matrix image** to edit the 13x8 graphical block, then press Start.
LED 1 through 4 cycle red/green/blue for 500 ms each. **LED matrix** cycles full,
blank, checkerboard, diagonal and heart. **Combined hardware** runs independent
RGB and matrix tasks. **Arithmetic** contains a clickable `5 + 7` reporter;
**500 outputs** emits exactly 1 through 500. Editable .ubp/.ubl files are under
examples/. See HARDWARE_LIBRARY.md for framebuffer and brightness semantics.

## Verification

Physical tests passed for browser compilation/execution, exactly 500 ordered
outputs, all four RGB command paths (actual GPIO/sysfs states), five exact
matrix framebuffers, concurrent tasks, disconnected Linux services, and 100
FPGA SPI checks. A fresh incognito browser executed programs with public
HTTP/HTTPS dependencies blocked. MCU uptime remained continuous across normal
App lifecycle operations. App Lab import/export and webview metadata were tested.

**Physical visual confirmation received:** the owner recognized the matrix heart
and checkerboard, and observed red, green and blue on each LED in turn. Exact
matrix orientation and optical grayscale linearity were not measured. A second
owner's fresh board and generic-profile physical startup also remain untested.

TEST_RESULTS.md, MEMORY_REPORT.md, SOURCE_REVISIONS.md and evidence/ contain
measured results and limitations. BUILD.md reproduces builds/tests. RECOVERY.md
protects the loader and previous application. PUBLISHING.md gives GitHub steps.
Old phase archives and private flash backups remain in the original workspace;
they are intentionally absent from this community package.
''',
'ARCHITECTURE.md':'''# Architecture and bounded interfaces

The browser runs the original GP editor/compiler. It sends raw binary WebSocket
messages to the Python Brick; Python does not execute MicroBlocks programs.
One worker serializes native binary Bridge calls to physical STM32 SmallVM.
The unchanged minimal interpreter runs bounded vmSlice(1) iterations from the
Arduino loop, with a 256-instruction dispatch budget and delay(1).

Browser/Python queues are 65,536 bytes; WebSocket messages are at most 8,192 bytes.
Bridge transfers are at most 192 bytes, below RPClite's request buffer limit.
MCU ingress/egress queues are 2,048 bytes each. Active stream overflow is a
visible session fault, not silently retried data. An ambiguous mb_push is never
retried. Reconnection explicitly opens a new transport session; it does not
reset MCU firmware. Idle output is deliberately drained/discarded and counted,
so historical console output is not replayed after disconnect.

Existing mb_open/mb_push/mb_pull/mb_stat/mb_var/mb_size/mb_echo stay available.
New fixed methods are mb_hw_version, mb_uptime, mb_host_peek, mb_host_ack,
mb_hw_stat, mb_hw_state, mb_gpio and mb_matrix. GPIO/matrix/status calls are
read-only. The browser cannot supply arbitrary Router method or shell names.

A separate MCU FIFO holds eight Linux LED actions. Each native setRGB for LED1/2
creates exactly eight bytes: LE32 positive sequence, LED, R, G, B. Linux applies
the idempotent state and ACKs the matching head. No nested MCU-to-Linux callback
blocks the interpreter. Queue exhaustion causes a visible VM error. An ambiguous
ACK stops host service until explicit App restart; it is not silently resent.
This service runs with or without a browser while the App is running. If the App
is stopped long enough, scripts producing Linux actions can exhaust the queue.

The original IO primitive enum slot was empty in the minimal port. It now hosts
six named primitives under `unoq`; the GP compiler aliases this name to existing
IO slot 3. Opcode architecture and enum indices are unchanged. Optional legacy
GPIO/sensor/network/display primitives remain unsupported. The combined profile
also preserves the original SPI/PacoBlaze sketch, verified by source checksum.

MicroBlocks protocol short frames are FA/type/id. Incoming long frames use
FB/type/id/LE16 length/body/FE with FE included in length; outgoing long replies
omit FE. The existing parser handles fragmented/expired frames. Actual browser
uploads were matched against the MCU's code CRC replies; output and arithmetic
responses were decoded independently from raw traffic.
''',
'HARDWARE_LIBRARY.md':'''# UNO Q hardware blocks

See MATRIX_EDITOR.md for the clickable 13x8 image input, presets and its acceptance results.

`examples/UNO_Q_Hardware.ubl` is a standard MicroBlocks library.
`UNO_Q_Hardware.ubp` is its editable project. They are embedded in the pinned
editor build and are automatically imported using the upstream library mechanism.

| Block | Semantics |
|---|---|
| set LED 1–4 red/green/blue | Integers 0..255; 0 off, every nonzero value ON. No proportional RGB PWM is claimed. |
| turn LED off / all RGB off | Same MCU primitives; Linux requests are asynchronous and bounded. |
| matrix clear | Clear framebuffer and immediately display blank. |
| matrix set pixel | x 0..12, y 0..7, brightness 0..7; modifies framebuffer only. |
| matrix fill | Set every framebuffer byte to brightness 0..7; call show. |
| matrix draw pattern | Exactly 104 characters, each `0` through `7`, row-major y*13+x; call show. |
| matrix show | Commit the complete framebuffer through Arduino_LED_Matrix.draw. |

Linux LED1/2 use existing user/gpiod permissions and device aliases, with modern
and legacy sysfs name discovery. All six installed channels had max_brightness=1.
The original trigger/brightness snapshot is restored on App stop; LED2 WLAN and
Bluetooth status triggers were physically checked after stopping the App.

LED3/4 use official LED3_R/G/B and LED4_R/G/B macros. HIGH is OFF, LOW is ON.
Physical digitalRead observations independently verified these six pin states.
The matrix initializes once and uses the installed core's exported begin,
3-bit grayscale and framebuffer APIs. Bounds/type checks happen before updates.
Pixel ordering is logical row-major. The owner visually recognized the heart
and checkerboard on the physical matrix; exact orientation was not confirmed.
Matrix brightness API compatibility is established, but optical grayscale
linearity was not measured.
''',
'BUILD.md':'''# Reproduce

Required installed tools: Arduino CLI 1.5.1 on UNO Q, ArduinoCore-Zephyr 1.0.0,
ARM Zephyr GCC 14.3.0/SDK 1.0.1, App CLI 0.13.0 and stock app-bricks 0.12.0.
Builds use supplied snapshots of the six C++ Bridge dependencies through
--libraries, without installing global libraries. No toolchain or loader update
is performed. On Mac the web/host tests used Emscripten 5.0.7 and Node.

```sh
python3 tools/build_runtime.py --target UNO_Q_SSH_ALIAS
# Existing FPGA system only:
python3 tools/build_runtime.py --target UNO_Q_SSH_ALIAS --preserve-pacoblaze
python3 tools/build_web.py
python3 tools/test_host_vm.py
python3 tools/test_matrix_slot.py
python3 tests/test_transport.py
python3 tests/test_installer_guards.py
python3 -m venv .venv
.venv/bin/pip install -r tests/requirements.txt
.venv/bin/python tests/test_server.py
```

These compile and test only; they never flash. Generated build/private-evidence
folders stay outside the publication set. The runtime build invokes the installed
arduino:zephyr:unoq target with wait_linux_boot=no, SMALLVM_UNOQ and the preserved
SPI_MIN_CLOCK_FREQUENCY=100000 handling. Current source/asset SHA256SUMS and
runtime image manifests identify exact inputs and outputs.

Web rebuilding uses upstream buildEmcc.sh and embeds Examples, Libraries, GP
runtime, translations and images. Local integration adds library/example import,
IO-name alias, WebSocket hooks and disables online version checks, firmware/BLE
installation, HTTPS redirect and PWA registration. Browser fonts use the system;
raw font files are not bundled. Nothing is fetched from the public site at runtime.

Known compile warning: the installed package references a missing bootloaders/
ELF. This did not prevent the LLEXT build. The separate, existing firmwares/ ELF
was checksum checked and physically verified; no loader/bootloader was installed.

For hardware observation, tools/observe_hardware.py runs on UNO Q with the
installed Python Router Bridge. Its FPGA fields apply only to the combined
profile. Raw evidence explains which tests used simulated drivers and which
used the physical STM32. Timing is measured RPC/workload timing, not a RTOS WCET.
''',
'RECOVERY.md':'''# Application-only recovery

Normal App start, stop, restart and browser reconnect never invoke these steps.
Do not run an Arduino CLI upload that also replaces the loader to work around
this minimal port. Do not flash FPGA configuration or alter SPI wiring.

The explicit installer accepts only a bounded ARM32 little-endian LLEXT image
with a matching image manifest and this verified core 1.0.0 loader SHA256:
39d4a4fd47241663323f6e04f94dd8f5a9f9ad6582cf1df37f9709b74026adcd.
Its write window is 0x08100000, length at most 0xC0000. It uses the installed
OpenOCD GPIOD configuration, saves all 768 KiB before writing, and verifies the
loader before and after. Its generic guard/recovery branches were host tested
with a simulated OpenOCD; the physical deployment used the pre-existing guarded
workflow with exact predecessor-image verification. Two application updates were
needed: initial hardware support and the verified signed-ACK correction. Zero
FPGA, bootloader, loader or Linux-image writes occurred.

On installation failure the generic installer restores the private full backup.
To restore manually after stopping the intended App:

```sh
sudo python3 tools/install_runtime.py --restore runtime-recovery/first-install/recovery.json --loader "$LOADER" --recovery-dir runtime-recovery/manual-restore
```

It checks backup size/hash and loader hash, then writes/verifies only the full
application region. Keep that backup private; old source/firmware phase archives
remain available separately in the original workspace. An actual recovery write
was not repeated solely for testing in this milestone.

One initial post-flash registration attempt failed; an additional MCU-only
restart restored registration. The cause is unproven. The final corrected image
registered directly after installation. If first-install methods are unavailable,
inspect /api/status and logs; use ONE explicit MCU-only restart as part of
installation, not an automatic App/browser action. On UNO Q, save this config:

```text
gdb port disabled
tcl port disabled
telnet port disabled
reset_config srst_only srst_nogate srst_push_pull connect_assert_srst
init
reset
sleep 100
mww 0x40036400 0xCAFFEEEE
shutdown
```

Run `sudo /opt/openocd/bin/openocd -d2 -s /opt/openocd -f openocd_gpiod.cfg -f restart.cfg`.
It contains no erase/program command. It loses RAM scripts, so reload them
through the IDE afterwards. If this does not recover registration, stop and use
the saved application backup. Never overwrite the matching loader casually.

If Linux LED state was not captured before the FIRST App start, custom original
triggers cannot be reconstructed from a later snapshot. Restore the appropriate
kernel/default status configuration on the board before preparing the App. Do
not change global sysfs permissions. data/led_original.json must survive restarts.
''',
'SOURCE_REVISIONS.md':'''# Pinned inputs

| Component | Exact identity |
|---|---|
| Canonical SmallVM/GP | https://codeberg.org/MicroBlocks/smallvm commit 2071df569623ba9cdcd6f8106b61796e047df38b; IDE 2.5.8, VM v417 |
| ArduinoCore-Zephyr installed | 1.0.0; reference tag commit 79b3f1afdad455f55e4a25030953617152c0227c |
| Installed loader | SHA256 39d4a4fd47241663323f6e04f94dd8f5a9f9ad6582cf1df37f9709b74026adcd |
| Kernel source identity | 1743741760ee; generated version 4.4.2-rc1, despite 4.2-base git description |
| App CLI | 0.13.0, source 1df36867f7a1a09876b1e9e8be28d7fc15fddc72 |
| App Python SDK | app-bricks 0.12.0, reference source 7b1504fa79d6d05169aa286d53fe97c318499b2a |
| Stock Python image observed | sha256:35eb218ee65c4886a2e0ead685ae8d16a68ecd6bc0a0dfc678669f69d7987a7a |
| C++ dependency snapshots | Arduino_RouterBridge 0.4.3, Arduino_RPClite 0.3.0, MsgPack 0.4.2, DebugLog 0.8.4, ArxTypeTraits 0.3.2, ArxContainer 0.7.0 |
| Host tests | fastapi 0.141.1, uvicorn 0.52.1, httpx 0.28.1, websockets 12.0 |

Supplied source subsets and file hashes identify build inputs; .git, old binaries,
raw fonts, old archives and private recovery data are excluded. Firmware adapter
files extend the already-working Phase 4C port. Modified upstream VM files are
listed in firmware/adapter/smallvm.patch; GP changes are in patches/web-ide.patch
and tools/build_web.py. Generated web JS remains available as editable source.
No vendor PacoBlaze or FPGA HDL was modified. The preserved SPI sketch SHA256 is
56230a7cd6ad63239a4473e42720f1e6487885d666843b85b65fa4827ae406e5.

References: https://github.com/arduino/ArduinoCore-zephyr,
https://github.com/arduino/arduino-app-cli,
https://github.com/arduino/app-bricks-py,
https://docs.arduino.cc/tutorials/uno-q/user-manual/,
https://wiki.microblocks.fun/en/create_a_library.
Browser network blocking procedure follows
https://developer.chrome.com/docs/devtools/request-conditions.
''',
'SECURITY.md':'''# Access and failure behavior

The standard App Lab port is for private LAN or local tunnel use. Use SSH for
encrypted remote access and do not configure Internet forwarding. Numeric
RFC1918/ULA/loopback Host values are accepted; public IPs and other domains are
rejected. A random 256-bit per-install access code protects the UI and programming
endpoint. HTTP-only, SameSite=Strict sessions and exact WebSocket Origin checks
prevent cross-origin programming. Server restart expires session cookies.

One gateway browser owns the stream. This cannot prevent a separately launched
legacy PTY/direct Router client from bypassing the gateway, so stop that client.
Read-only SPI/hardware test clients deliberately avoid mb_open/push/pull while a
browser owns the stream. No arbitrary Router method or shell execution API exists.

SmallVM is for trusted-owner programs; this milestone does not certify a hostile
bytecode sandbox. Bounded queues, request lengths, callback ranges and explicit
faults limit accidental corruption. Active bytes are never silently retried after
an ambiguous write. Host ACK failures require explicit App restart. A MCU reset
is detected by decreasing uptime, invalidates the active session, and requires
explicit reconnect; no firmware overwrite is attempted.

The Python container uses the stock unprivileged App Lab user/group configuration
(privileged=false, no added capabilities). Existing gpiod permissions provide LED
access. No Docker socket mount or global LED chmod was added. Authentication
codes, original LED snapshots, flash backups and machine-specific raw evidence
must remain outside Git and public exports.
''',
'MEMORY_REPORT.md':'''# Measured resource footprint

| Profile | Prepared image bytes | Allocatable ELF sections | Nominal 256 KiB LLEXT arena remainder |
|---|---:|---:|---:|
| Generic (built only) | 161828 | 124636 | 137508 |
| Combined SPI/PacoBlaze (physical) | 177164 | 132760 | 129384 |

The section totals come from the actual ARM ELF, not total STM32 SRAM. The arena
remainder is BEFORE alignment, loader bookkeeping and dynamic allocations; it
is not a live free-memory measurement. The earlier combined baseline used
125724 bytes of sections. New static cost is 7036 bytes. Exact section tables
are in evidence/memory-report.json.

The port retains a 16 KiB object store, 16 KiB RAM code storage, ten Task records
(524 bytes each), 2048-byte MCU RX/TX queues and bounded upstream message buffers.
New hardware data comprises a 104-byte matrix framebuffer, 12 requested RGB
bytes and eight 8-byte Linux action records, plus counters and matrix object.
The kernel's 32 KiB main stack and 32 KiB system heap are distinct from the LLEXT
arena. Stack watermarks/live heap are not exported by this installed loader;
no unmeasured free-RAM or worst-case stack claim is made.

Linux/browser queues are limited to 65536 bytes in each direction. One active
WebSocket is permitted. The GP browser allocates its upstream 256 MiB WASM
memory on the computer, not on STM32. Runtime programs are RAM-only.
''',
'PUBLISHING.md':'''# Share on GitHub

Create your own repository and upload this extracted directory, retaining source,
licenses, asset manifests, examples, tests and evidence. Review SHA256SUMS first.
Keep data/, .cache/, .venv/, build/, private-evidence/, runtime-recovery/ and all
credentials/backups out of Git. Do not add old phase ZIPs or raw font files.

Describe this as a community UNO Q port of MicroBlocks, not original authorship
of the upstream editor/interpreter. Identify pinned revisions and measured vs
untested results. The generic profile is compiled but not physically deployed;
the tested combined profile preserves an external FPGA project. The owner
confirmed red/green/blue LED sequences and recognizable heart/checkerboard
patterns. Exact matrix orientation and grayscale were not measured. Do not claim
full GPIO/sensor support.

A release may attach the one community ZIP and the embedded App Lab import ZIP.
Normal app use must remain separate from explicit MCU installation. Publishing
instructions do not authorize automatic repository creation or remote publishing.
''',
'NEXT_VISUAL_TEST.md':'''# Remaining physical observations

The owner has visually confirmed the matrix heart/checkerboard and red, green,
blue on each LED in turn. These observations are recorded as physical visual
PASS in TEST_RESULTS.md and evidence/visual-confirmations.json.

Exact matrix orientation remains unconfirmed. No firmware update is needed:
select LED matrix and Start, then compare the diagonal's physical direction
with the logical upper-left to lower-right framebuffer. Full/blank/diagonal
framebuffers were measured, but only heart/checkerboard were explicitly named
in the owner's visual reply. Optical grayscale linearity was not measured.

A fresh owner's board should separately verify the generic runtime's first
installation, restart registration, private LED backup and recovery procedure.
Do not replace this existing board's combined FPGA runtime merely for that test.
'''
}
for name,text in docs.items():(R/name).write_text(text)
(R/'tests/requirements.txt').write_text('fastapi==0.141.1\nuvicorn==0.52.1\nhttpx==0.28.1\nwebsockets==12.0\n')
(R/'.gitignore').write_text('.venv/\nbuild/\nprivate-evidence/\n.cache/\ndata/\nruntime-recovery/\n__pycache__/\n*.pyc\n.DS_Store\n')
(R/'.dockerignore').write_text('**\n')
print('Wrote',len(docs),'documents')
