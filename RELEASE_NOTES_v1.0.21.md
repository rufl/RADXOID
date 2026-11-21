# RADXOID v1.0.21 — lock volumes without dismounting the reader

The v1.0.20 result confirms that this SDXC reader reports Windows error 21 after
an explicit volume dismount, even though the physical disk stays open.

v1.0.21 no longer issues `FSCTL_DISMOUNT_VOLUME`. It removes user-visible mount
points and holds only `FSCTL_LOCK_VOLUME` handles during the complete operation.
Microsoft documents a successful volume lock as sufficient for raw disk writes
inside a mounted volume's extents. The lock also:

- flushes cached filesystem data;
- succeeds only when no files remain open;
- blocks other filesystem access through non-locking handles; and
- remains active until its handle closes.

The locks stay held through native `WriteFile`, `FlushFileBuffers`, and complete
SHA-256 readback, then close in the existing unconditional cleanup path.
Regression coverage requires that `FSCTL_LOCK_VOLUME` is the only volume control
operation issued.

## Required files

- `RADXOID-Installer.exe` or `RADXOID-Installer-linux-x86_64`
- `rk356x_rock_3a_r_20261120.1320_gpt.zip`
- `SHA256SUMS-v1.0.21.txt`
