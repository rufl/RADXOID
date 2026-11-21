# RADXOID v1.0.23 — persistent crash-safe logging

The installer already created timestamped session logs outside its executable
directory. This release makes that persistence explicit and easier to recover
after Defender termination.

Every operation entry is now written to both:

- a timestamped per-run log; and
- the stable `installer-latest.log` file.

Each line is flushed and synchronized to disk immediately. The files survive
quarantine or deletion of the executable.

Windows location:

```text
%LOCALAPPDATA%\RADXOID\logs\installer-latest.log
```

The GUI displays this path above the operation log and provides an **Open log
folder** button.

An interrupted SD card is complete only if the file contains both
`Verified SHA-256:` and
`SD-card write and readback verification completed successfully!`. Otherwise,
restart the complete write from byte zero.

## Required files

- `RADXOID-Installer.pyw` or `RADXOID-Installer.exe`
- `rk356x_rock_3a_r_20261120.1320_gpt.zip`
- `SHA256SUMS-v1.0.23.txt`
