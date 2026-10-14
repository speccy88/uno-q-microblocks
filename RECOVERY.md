# Application-only recovery

Normal App start, stop, restart and browser reconnect never invoke these steps.
Do not run an Arduino CLI upload that also replaces the loader to work around
this minimal port. Do not flash FPGA configuration or alter SPI wiring.

The explicit installer accepts only a bounded ARM32 little-endian LLEXT image
with a matching image manifest and this verified core 1.0.0 loader SHA256:
39d4a4fd47241663323f6e04f94dd8f5a9f9ad6582cf1df37f9709b74026adcd.
Its write window is 0x08100000, length at most 0xC0000. It uses the installed
OpenOCD GPIOD configuration, saves all 768 KiB before writing, and verifies the
loader before and after. Its generic guard/recovery branches were host tested
with a simulated OpenOCD; the physical deployment used the pre-existing guarded
workflow with exact predecessor-image verification. Two application updates were
needed: initial hardware support and the verified signed-ACK correction. Zero
FPGA, bootloader, loader or Linux-image writes occurred.

On installation failure the generic installer restores the private full backup.
To restore manually after stopping the intended App:

```sh
sudo python3 tools/install_runtime.py --restore runtime-recovery/first-install/recovery.json --loader "$LOADER" --recovery-dir runtime-recovery/manual-restore
```

It checks backup size/hash and loader hash, then writes/verifies only the full
application region. Keep that backup private; old source/firmware phase archives
remain available separately in the original workspace. An actual recovery write
was not repeated solely for testing in this milestone.

One initial post-flash registration attempt failed; an additional MCU-only
restart restored registration. The cause is unproven. The final corrected image
registered directly after installation. If first-install methods are unavailable,
inspect /api/status and logs; use ONE explicit MCU-only restart as part of
installation, not an automatic App/browser action. On UNO Q, save this config:

```text
gdb port disabled
tcl port disabled
telnet port disabled
reset_config srst_only srst_nogate srst_push_pull connect_assert_srst
init
reset
sleep 100
mww 0x40036400 0xCAFFEEEE
shutdown
```

Run `sudo /opt/openocd/bin/openocd -d2 -s /opt/openocd -f openocd_gpiod.cfg -f restart.cfg`.
It contains no erase/program command. It loses RAM scripts, so reload them
through the IDE afterwards. If this does not recover registration, stop and use
the saved application backup. Never overwrite the matching loader casually.

If Linux LED state was not captured before the FIRST App start, custom original
triggers cannot be reconstructed from a later snapshot. Restore the appropriate
kernel/default status configuration on the board before preparing the App. Do
not change global sysfs permissions. data/led_original.json must survive restarts.
