# RADXOID v1.0.19 — Win32 I/O without the C runtime

The v1.0.18 log identified the remaining Windows failure precisely: `CreateFileW`
returned a valid physical-disk handle, then `msvcrt.open_osfhandle` rejected that
handle with `[Errno 13] Permission denied` before the first write.

v1.0.19 removes the C runtime from raw-disk I/O. The selected physical disk now
stays on native Win32 APIs for its entire lifetime:

- `CreateFileW` opens `\\.\PhysicalDriveN`;
- `WriteFile` writes the decompressed GPT image;
- `FlushFileBuffers` commits the write before verification;
- `ReadFile` performs SHA-256 readback; and
- `CloseHandle` releases the disk.

The write and readback paths reuse a single 4 MiB mutable buffer. This also
removes per-block bytes allocation and lets `WriteFile` use the buffer directly.

Backend regression tests exercise the complete native handle lifecycle and prove
that no CRT file descriptor is created. Windows and Linux run the test suite
before the executables are packaged.

## Required files

- `RADXOID-Installer.exe` or `RADXOID-Installer-linux-x86_64`
- `rk356x_rock_3a_r_20261120.1320_gpt.zip`
- `SHA256SUMS-v1.0.19.txt`
