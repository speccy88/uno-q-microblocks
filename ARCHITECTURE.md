# Architecture and bounded interfaces

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
