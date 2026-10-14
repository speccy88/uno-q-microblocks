# Access and failure behavior

The standard App Lab port is for private LAN or local tunnel use. Use SSH for
encrypted remote access and do not configure Internet forwarding. Numeric
RFC1918/ULA/loopback Host values are accepted; public IPs and other domains are
rejected. The IDE opens directly without a login, password, access token or
session-cookie requirement. WebSocket requests retain their exact Origin check.

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
access. No Docker socket mount or global LED chmod was added. Original LED snapshots, flash backups and machine-specific raw evidence
must remain outside Git and public exports.
