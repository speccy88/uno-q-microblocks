# MicroBlocks Bridge

Reusable Python App Lab Brick using the supported @brick start/stop lifecycle.
It hosts the pinned official GP editor and serializes binary Arduino Bridge
transfers to resident STM32 SmallVM. It never installs or resets MCU firmware.

App Lab exposes port 8080 as a webview. Use a private LAN or an encrypted local
SSH tunnel. No login or access code is required. The WebSocket checks the exact origin and accepts one controller.
Default App Lab port publishing binds all board interfaces: keep the board on
a private network and do not forward this port to the Internet.

Before the FIRST App start, run tools/prepare_app.py from the enclosing community
bundle to capture the original Linux LED triggers. Keep data/ persistent between
restarts. Linux LED requests use a separate bounded MCU queue and continue
while the browser is disconnected. Scripts execute in STM32 RAM.

Tested with App CLI 0.13.0 and stock app-bricks 0.12.0. A tiny relay was evaluated,
but this CLI's webview API does not report ports from a local Brick's container.
The final app uses the standard Python Brick port and no companion container.
