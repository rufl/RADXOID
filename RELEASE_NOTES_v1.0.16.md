# RADXOID v1.0.16 — Windows SDHC reader detection

This release fixes Windows systems where a USB pendrive appeared but an SDHC
card in a built-in or USB card reader did not.

Windows sometimes reports an SD reader as `USB` with `External hard disk media`
instead of removable media. The installer now combines `Get-Disk` and
`Win32_DiskDrive` metadata and recognizes explicit SD, SDHC, SDXC, MMC, and
card-reader identities.

Safety exclusions remain mandatory: boot, system, read-only, offline, and
unrelated fixed USB disks are not listed.

## Required files

- `RADXOID-Installer.exe` or `RADXOID-Installer-linux-x86_64`
- `rk356x_rock_3a_r_20261120.1320_gpt.zip`
- `SHA256SUMS-v1.0.16.txt`

The GPT image and write/readback verification pipeline are unchanged.
