# RADXOID v1.0.20 — keep Windows removable media online

The v1.0.19 log proves that native raw-disk access is working: `CreateFileW`
opened `\\.\PhysicalDrive1`, but the first `WriteFile` returned Windows error 21,
`The device is not ready`.

The cause was the previous preparation command, `mountvol /p`. Windows documents
that `/p` removes the mount point, dismounts the volume, and takes it offline.
That behavior makes some SDXC readers report no ready media to raw writes.

v1.0.20 replaces that sequence:

- removes drive-letter and folder mount points with `Remove-PartitionAccessPath`;
- keeps the physical SD disk online;
- opens each volume by its volume GUID;
- holds `FSCTL_LOCK_VOLUME` and `FSCTL_DISMOUNT_VOLUME` handles for the entire
  write and SHA-256 readback; and
- releases every volume lock on success or failure.

Native failures now include an explicit Windows error number instead of a
misleading POSIX exception class such as `IsADirectoryError`.

Regression tests verify that `mountvol /p` is absent, both FSCTL operations are
issued, native locks are retained through the write, and cleanup always runs.

## Required files

- `RADXOID-Installer.exe` or `RADXOID-Installer-linux-x86_64`
- `rk356x_rock_3a_r_20261120.1320_gpt.zip`
- `SHA256SUMS-v1.0.20.txt`
