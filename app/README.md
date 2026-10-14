# MicroBlocks UNO Q

This Python-only Arduino App serves the real pinned MicroBlocks web IDE and
connects to SmallVM on the STM32. It contains no sketch and does not flash or
reset the MCU when started or restarted.

Use the enclosing community ZIP's START_HERE.md for the separate first-time
runtime installation and LED-trigger snapshot step. Serve port 8080 only on a
private network, or open http://localhost:18080 through the documented SSH tunnel.
Enter the code from this app's private data/access_token file. Hardware blocks
load automatically; use the UNO Q examples selector and Start/Stop buttons.

RGB channels are on/off (0 off, 1..255 on), not proportional PWM. The blue matrix
supports a 13x8 framebuffer with brightness values 0..7. Program storage is RAM.
