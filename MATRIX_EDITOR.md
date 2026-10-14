# Graphical 13×8 matrix input

Open the hosted IDE directly on port 8080. No login or access code is required.
Choose **Draw matrix image** from **UNO Q examples**. Click a pixel to toggle it,
or drag to paint/erase. The arrow offers Heart, Smile, Checkerboard, Diagonal,
All on and Clear. Press Start to execute the picture on STM32 SmallVM.

The existing `matrixPattern` primitive receives the same 104-character row-major
string, followed by `matrixShow`. This update changes the editor/library and
Python server; no MCU or FPGA firmware was written. Older strings and untouched
brightness values 0–7 survive save/load. The micro:bit 5×5 slot remains separate.

## Executed verification (2026-10-14)

- **PASS, actual GP host execution:** 300 assertions, with bitmap rendering
  disabled only in the host harness. Tests cover 104 cell targets, gaps/bounds,
  paint/erase stroke interpolation, invalid input, grayscale, six presets,
  original 5×5 behavior, BlockSpec and Block input events.
- **PASS, real project/compiler:** four .ubp files save/load exactly; the SmallVM
  compiler preserves the 104-byte image and compiles `unoqShowImage`.
- **PASS, actual browser → STM32:** all six presets and a custom fast stroke,
  erased middle pixel and bottom-right pixel match all 104 MCU framebuffer bytes.
  Every readback also reports VM fault 0 and FPGA SPI PING 195 (`0xC3`).
- **PASS, deployment:** five served web assets match local SHA-256 values. GP
  bundle URLs share a content hash so JavaScript metadata and data stay matched.
- **PASS, direct access:** editor/status return HTTP 200 without credentials,
  cookies or login. Three server tests pass, including 1,000 randomized binary
  round trips. Real HTTP/WS checks retain origin and exclusive-controller rules.
- **PASS, preservation:** MCU uptime remained continuous. One Python App restart
  removed login. Zero MCU, FPGA, loader or bootloader writes occurred.

The first fast-drag test failed because only sampled cells were painted. Stroke
interpolation fixes this. During deployment the browser reused an older bundle;
content-versioned URLs fixed that too. The original FAIL record remains in the
log, followed by the corrected real-browser PASS. Optical grayscale linearity
and exact physical orientation remain unmeasured.

## Reproduce

Run `python3 tools/test_matrix_slot.py` and `python3 tools/build_web.py` on the
Mac. Run `python3 tests/test_server.py` with tests/requirements.txt installed.
For read-only live HTTP checks while a browser is connected:

```sh
python3 tools/test_live_security.py --url http://localhost:18080 --output direct-access.json
```

After selecting a preset and pressing Start, read its physical MCU framebuffer
inside the running Python App container on UNO Q Linux:

```sh
docker exec microblocks-uno-q-main-1 python3 -c 'from arduino.app_utils import Bridge; print(Bridge.call("mb_matrix", timeout=3).hex()); print(Bridge.call("mb_stat", 6, timeout=3)); print(Bridge.call("pb_ping", timeout=3))'
```

Each framebuffer byte is brightness 0–7 in row-major order. Compare all 104 bytes
with the selected picture; `examples/patterns.json` documents baseline patterns.
The SPI call is for the combined PacoBlaze profile only. Logs, timestamps and
values are in `evidence/matrix-live-observations.json` and `matrix-slot-tests.log`.

## Web-only recovery

Restore only the five editor assets (`gp_wasm.data`, `gp_wasm.js`, `gp_wasm.wasm`,
web/unoq-network.js and the Brick's source unoq-network.js) from the private
pre-update snapshot or v0.1.0 App ZIP, then reload. Keep the current Python server
if you want direct access without login. Keep data/ and the MCU runtime intact.
No firmware flashing is required. A normal Python App restart is only needed if
restoring Python source; it does not reinstall the MCU application.
