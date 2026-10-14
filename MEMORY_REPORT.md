# Measured resource footprint

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
