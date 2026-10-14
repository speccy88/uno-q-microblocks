# Pinned inputs

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
