# MicroBlocks on Arduino UNO Q

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
Choose **Draw matrix image** to edit a picture directly in a 13×8 block: click
or drag its pixels, or use the arrow to choose a preset. Press Start to show it.
The image remains a normal saved program input; no MCU update is needed.
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
