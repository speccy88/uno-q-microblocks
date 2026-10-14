# Access and failure behavior

The standard App Lab port is for private LAN or local tunnel use. Use SSH for
encrypted remote access and do not configure Internet forwarding. Numeric
RFC1918/ULA/loopback Host values are accepted; public IPs and other domains are
rejected. A random 256-bit per-install access code protects the UI and programming
endpoint. HTTP-only, SameSite=Strict sessions and exact WebSocket Origin checks
prevent cross-origin programming. Server restart expires session cookies.

One gateway browser owns the stream. This cannot prevent a separately launched
legacy PTY/direct Router client from bypassing the gateway, so stop that client.
Read-only SPI/hardware test clients deliberately avoid mb_open/push/pull while a
browser owns the stream. No arbitrary Router method or shell execution API exists.

SmallVM is for trusted-owner programs; this milestone does not certify a hostile
bytecode sandbox. Bounded queues, request lengths, callback ranges and explicit
faults limit accidental corruption. Active bytes are never silently retried after
an ambiguous write. Host ACK failures require explicit App restart. A MCU reset
is detected by decreasing uptime, invalidates the active session, and requires
explicit reconnect; no firmware overwrite is attempted.

The Python container uses the stock unprivileged App Lab user/group configuration
(privileged=false, no added capabilities). Existing gpiod permissions provide LED
access. No Docker socket mount or global LED chmod was added. Authentication
codes, original LED snapshots, flash backups and machine-specific raw evidence
must remain outside Git and public exports.
