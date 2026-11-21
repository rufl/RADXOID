# RADXOID Distribution

## SD-card package

The SD-card installer consumes one compressed full-disk image:

```text
RADXOID-Installer.exe
RADXOID-Installer.pyw
RADXOID-Installer-linux-x86_64
rk356x_rock_3a_r_20261120.1320_gpt.zip
SHA256SUMS-v1.0.24.txt
```

`gpt.zip` contains the complete 4.1 GiB `gpt.img` but is approximately
768 MiB compressed, so no release file exceeds GitHub's 2 GiB upload limit.
No split volumes or joining stage are required.

## Related build artifacts

- `rkupdate.img` / `update.img`: Rockchip USB-loader upgrade package.
- `rkupdate.zip`: compressed USB-loader package.
- `super.img`: Android dynamic-partition payload.
- `gpt.img` inside `gpt.zip`: raw whole-disk SD-card image used by this
  installer.

These files are separate deployment formats, not pieces to concatenate.

## Installation

1. Download the installer, GPT ZIP, and matching versioned SHA-256 manifest.
2. Put them in one folder.
3. Run the GUI installer.
4. Select the folder and wait for checksum verification.
5. Select the removable SD-card whole disk.
6. Confirm the destructive write and wait for write plus readback verification.

Windows requests Administrator privileges through the executable manifest.
Linux requests privilege only for unmount, raw write, and raw readback.

See [`installer/README.md`](installer/README.md) for the safety model,
requirements, logs, and troubleshooting.
