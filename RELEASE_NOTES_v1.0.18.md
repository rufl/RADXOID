# RADXOID v1.0.18 — native Windows raw-disk access

This release fixes the Windows write failure observed after target validation and
dismounting: Python's regular file opener returned `[Errno 13] Permission denied`
for `\\.\PhysicalDriveN` before any image bytes were written.

The Windows writer now opens the selected whole disk through native
`CreateFileW` with the documented direct-access contract:

- Administrator access;
- `OPEN_EXISTING` disposition;
- read and write sharing;
- write-through output; and
- `FlushFileBuffers` before SHA-256 readback verification.

The GUI now reports the exact exception, physical-drive path, native operation,
and Windows system error instead of only the generic write-failed message.
Backend tests cover the native access flags, failure details, error propagation,
and the complete write/readback pipeline. Release builds run those tests on both
Windows and Linux before packaging.

## Required files

- `RADXOID-Installer.exe` or `RADXOID-Installer-linux-x86_64`
- `rk356x_rock_3a_r_20261120.1320_gpt.zip`
- `SHA256SUMS-v1.0.18.txt`
