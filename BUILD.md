# Reproduce

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
