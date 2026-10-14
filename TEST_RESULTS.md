# Verification results

These are newly executed tests, not simulation relabeled as hardware.

The current graphical matrix input is covered in [MATRIX_EDITOR.md](MATRIX_EDITOR.md).
300 real GP assertions pass. Actual browser clicks, fast drag painting, erasing
and all six presets produced exact 104-byte MCU framebuffer readback. SPI PING
remained 195 with zero VM faults. The editor and status open without credentials
or cookies; updated server tests and live handshakes pass.

The remaining physical results below describe the preserved v0.1.0 runtime
baseline. Current updates changed only Python/web/library files, with one App
restart to remove login and zero MCU/FPGA firmware writes.

| Acceptance item | Result | Evidence/scope |
|---|---|---|
| Existing baseline preserved | PASS | Input archive CRC/1207-file verification; original phase directories/backups kept private |
| Real official browser editor | PASS (physical) | Browser screenshots, code upload CRC replies, Arduino Bridge traffic |
| Browser arithmetic | PASS (physical) | Actual MCU return integer 12; including imported App copy |
| 500 outputs | PASS (physical) | Exactly 1..500 in order, 4392 wire bytes in 4.621589 s, zero task/record CRC errors |
| Browser reconnect | PASS (physical) | 3 opened / 2 closed sessions in frozen final-runtime traffic; no MCU reset |
| Fresh incognito/offline | PASS (browser + physical) | Public HTTPS assets blocked (5 observed); HTTP public dependencies blocked; local editor executes 12 and 500 outputs |
| RGB LED1/2 service | PASS (physical sysfs/MCU) | Native MCU bytecode requests and independently read kernel channel/trigger states |
| RGB LED3/4 | PASS (physical GPIO/MCU) | All expected active-low digitalRead states over 96 RGB observations |
| RGB optical colors/sequence | PASS (physical, owner visual) | Owner: "i see also red green blue, each led at a time" |
| Matrix native API/execution | PASS (physical MCU) | 64 observations; five exact 104-byte framebuffers; exported driver executes |
| Recognizable matrix patterns | PASS (physical, owner visual) | Owner: "i now see heart and checker" |
| Exact matrix orientation | NOT TESTED | Recognition confirmed; orientation was not explicitly reported |
| Combined scheduling | PASS (physical) | Two concurrent hardware tasks; no VM faults/host failures |
| Linux service without browser | PASS (physical) | 99 observations, 21 successful host ACKs and 29 matrix updates during disconnect |
| Existing SPI/PacoBlaze | PASS (physical) | 100 PING/echo cycles, epoch remains 13, errors zero; 80 checks overlap incomplete VM workload |
| App restart/runtime preservation | PASS (physical) | Continuous MCU uptime; no sketch in App; imported copy also executes bytecode |
| Linux status trigger restoration | PASS (physical) | Exact pre-start snapshot equality after stop |
| App Lab export/import + webview | PASS (physical CLI/API/browser) | Final sanitized ZIP imported; functional imported copy started/executed before asset-only privacy cleanup; original App runs final assets; port 8080 reported as webview |
| Native minimal MCU build | PASS (real build) | Two profiles reproduced byte-for-byte with supplied dependency snapshots |
| Generic-profile physical startup | NOT TESTED | Built/analyzed only, preserving this board's external FPGA runtime |
| Interpreter/protocol host tests | PASS (automated) | 35 real wasm32 interpreter runs with simulated services/drivers |
| Server transport/security host tests | PASS (automated) | 3 tests; 1000 random binary roundtrips plus fixtures; explicit simulated echo adapter |
| Graphical matrix editing | PASS (browser + physical MCU) | All six presets, fast stroke, erased pixel and corner pixel; exact readback in matrix-live-observations.json |
| Direct access/origin/second client | PASS (host tests + live HTTP/WS) | Editor and status open without credentials; foreign-origin and concurrent-controller checks retained |
| Installer guard/rollback branches | PASS (automated) | 5 simulated OpenOCD tests; no physical recovery write repeated |

Measured SPI RPC median is 17.3141 ms, maximum 20.8680 ms for this workload.
This includes Linux Router/transport timing and is not a hard scheduling bound.
Framebuffer readback confirms interpreter/native path, not optical grayscale
linearity. IRQ/memory worst-case behavior, a second owner's fresh board, and
full GPIO/sensor support are not certified.

Two application updates occurred. The initial unsigned host ACK caused
`Wrong type parameter in position: 0 (253)`; a bounded signed-int Bridge wrapper
fixed it and subsequent host ACKs passed. An unknown GP primitive namespace
initially failed compiler literal generation; aliasing unoq to empty IO slot 3
fixed it. One initial post-flash registration needed an additional MCU-only
restart; cause unproven, final corrected module registered directly. The old
PWA worker referenced missing Boardie/font assets; registration is disabled in
the final private-server edition. These failures were corrected and were not
marked PASS prematurely. Zero FPGA/loader/bootloader/Linux-image writes occurred.

Raw compiler/test logs are sanitized copies in evidence/. Private originals and
full flash backups remain outside this package. JSON reports give exact hashes,
timestamps, uploaded code and decoded responses. Owner visual confirmations are
recorded in evidence/visual-confirmations.json; exact orientation and optical
grayscale linearity remain unmeasured.
