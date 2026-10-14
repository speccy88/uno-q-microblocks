# Graphical 13×8 matrix input

Reload the hosted IDE, select **Draw matrix image** from **UNO Q examples**, and
edit the picture in the `UNO Q show image` block. Click to toggle a pixel, or
drag to paint/erase. The arrow offers Heart, Smile, Checkerboard, Diagonal, All on
and Clear. Press Start to execute the picture on STM32 SmallVM.

The existing `matrixPattern` primitive still receives the same 104-character
row-major string, followed by `matrixShow`. The new block helper and input are
editor/library changes. Older pattern strings and untouched brightness values
0–7 survive save/load. The existing micro:bit 5×5 input remains separate.

## Checks performed

- **PASS, executable host test:** 270 assertions use the actual GP source and
  interpreter, with bitmap drawing disabled in this host harness. They cover all
  104 cell hit targets, gaps/bounds, toggling, invalid values, grayscale, six
  presets, original 5×5 behavior, BlockSpec construction and Block input events.
- **PASS, real project/compiler:** four .ubp examples save/load exactly; the
  SmallVM compiler preserves all 104 image bytes and compiles `unoqShowImage`.
- **PASS, build/static:** the pinned GP web IDE rebuilt; JavaScript and Python
  syntax checks passed. Four deployed web assets match local SHA-256 values.
- **PASS, existing physical services:** the MCU remained running and a read-only
  SPI PING returned 195 (`0xC3`) after deployment.
- **PENDING:** clicking/dragging/preset selection in the live browser and reading
  its resulting image from the MCU. The desktop is locked and an existing browser
  owns the exclusive VM connection; unlock it and save/close that tab first.

Run `python3 tools/test_matrix_slot.py` to reproduce the GP/compiler checks.
`evidence/matrix-slot-tests.log` and `matrix-web-deployment.json` contain the
executed results. No MCU/FPGA firmware was written, and the App was not restarted.

## Web-only recovery

The previous five editor assets were saved privately on the board before this
update. Restore `gp_wasm.data`, `gp_wasm.js`, `gp_wasm.wasm`, `web/unoq-network.js`
and the Brick's source `unoq-network.js` from that snapshot, or restore those
files from the v0.1.0 App ZIP. Reload the browser afterward. Keep `data/` and the
MCU runtime intact; no application flashing or FPGA recovery is needed.
