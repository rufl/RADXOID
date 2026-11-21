# RADXOID v1.0.22 — Defender-safe source launcher

If Windows Defender terminates or removes the installer during writing, the SD
card must be treated as incomplete unless the durable log contains both:

- `Verified SHA-256:`; and
- `SD-card write and readback verification completed successfully!`

Do not boot an unverified card. Reconnect it and restart the complete operation;
the installer writes from byte zero and does not perform an unsafe partial
resume.

This release adds `RADXOID-Installer.pyw`, a plain Python source fallback for
machines where Defender flags the unsigned PyInstaller one-file executable. The
source launcher:

- contains the same reviewed installer implementation;
- avoids PyInstaller self-extraction;
- requests Administrator privileges through UAC;
- remains fully graphical; and
- shows a clear error if Tcl/Tk is not installed.

Use official Python 3.8+ from python.org with Tcl/Tk enabled. Verify the launcher
against `SHA256SUMS-installers.txt`, then double-click
`RADXOID-Installer.pyw`. Do not disable Defender or add a broad exclusion.

## Required files

- `RADXOID-Installer.pyw` or `RADXOID-Installer.exe`
- `rk356x_rock_3a_r_20261120.1320_gpt.zip`
- `SHA256SUMS-v1.0.22.txt`
