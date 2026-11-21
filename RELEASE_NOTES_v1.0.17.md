# RADXOID v1.0.17 — broader Windows removable-media detection

This retry covers SD readers that Windows exposes as SCSI or another bus with a
generic device model.

The installer now accepts a non-system disk when any reliable removable-media
signal exists:

- `BusType` is SD or MMC;
- `Win32_DiskDrive.MediaType` is removable, regardless of bus;
- a partition contains a volume with `DriveType=Removable`; or
- model, friendly name, or PNP identity explicitly identifies SD, SDHC, SDXC,
  MMC, or a card reader.

Every Windows disk scan is now written to the operation log with physical-drive
number, size, model, bus, media type, removable-volume result, and the final
`eligible` or `excluded` decision. Boot, system, read-only, offline, and
unrelated fixed disks remain excluded.

## Required files

- `RADXOID-Installer.exe` or `RADXOID-Installer-linux-x86_64`
- `rk356x_rock_3a_r_20261120.1320_gpt.zip`
- `SHA256SUMS-v1.0.17.txt`
