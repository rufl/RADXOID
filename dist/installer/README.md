# RADXOID Installer

Cross-platform GUI that writes the ROCK 3A SD-card image on Windows and Linux.
It does not join files or create an intermediate image.

## Required release files

Keep these files in one folder:

- `RADXOID-Installer.exe`, or `RADXOID-Installer.pyw` with official Python
  3.8+ installed
- `RADXOID-Installer-linux-x86_64` on Linux
- `rk356x_rock_3a_r_20261120.1320_gpt.zip`
- `SHA256SUMS-v1.0.22.txt`

The GPT ZIP contains one complete `gpt.img`. The installer verifies the ZIP,
streams `gpt.img` directly to the SD card, and reads the written bytes back for
SHA-256 verification. Other build artifacts such as `rkupdate.img`,
`rkupdate.zip`, and `super.img` are not SD-card image parts and are not joined.

## GUI workflow

1. Select the folder containing the GPT ZIP and checksum manifest.
2. Wait for SHA-256 verification. Skipping is available behind an explicit
   warning and is unsafe.
3. Insert an SD card and refresh the device list.
4. Select the whole-disk target.
5. Type the exact `ERASE <device>` confirmation.
6. Keep the card connected until both writing and readback verification reach
   100%.

The GUI shows the active phase, bytes processed, total progress, and an
operation log. Every run also writes a durable log:

- Windows: `%LOCALAPPDATA%\RADXOID\logs`
- Linux: `${XDG_STATE_HOME:-$HOME/.local/state}/RADXOID/logs`

## Safety behavior

- Only whole writable disks identified as SD/MMC media, card readers, or
  removable USB media are listed.
- Windows boot/system/read-only/offline disks and unrelated fixed USB disks are
  excluded.
- The operation log records every Windows physical disk, bus/media metadata,
  removable-volume result, and whether it was eligible or excluded.
- Linux excludes the root disk and read-only media.
- The target path, capacity, and available OS identity are revalidated after
  mounted partitions are removed.
- A target smaller than the uncompressed `gpt.img` is rejected.
- The selected disk is not opened until exact destructive confirmation.
- Closing, Back, target selection, and refresh are disabled during writing.
- The ZIP CRC is checked while streaming.
- The SHA-256 computed from the decompressed source is compared with a
  full readback of the image-sized device prefix.
- Any short write, short read, archive error, write error, or hash mismatch
  fails the operation.

## Platform requirements

### Windows

- Windows 10 or newer.
- The executable manifest and source `.pyw` launcher both request Administrator
  privileges.
- The installer locates Windows PowerShell by its system path even when the
  packaged GUI has a minimal `PATH`.
- Raw physical-disk handles remain entirely in Win32: `CreateFileW`,
  `WriteFile`, `ReadFile`, `FlushFileBuffers`, and `CloseHandle`.
- Mount points are removed without taking removable media offline. Filesystem
  volumes remain exclusively locked until write and readback complete.
- If Defender removes the unsigned PyInstaller executable, do not disable
  Defender. Install Python from python.org with Tcl/Tk, verify
  `SHA256SUMS-installers.txt`, and run `RADXOID-Installer.pyw`.

### Linux

- `lsblk`, `findmnt`, `udevadm`, `dd`, and `sync`.
- Root, graphical `pkexec`, or an already-authenticated noninteractive `sudo`
  session for unmount/write/readback operations.
- SD readers must expose SD/removable-media identity to udev; ambiguous USB
  disks are deliberately not offered.

## Build from source

Python 3.8+ and PyInstaller are required.

```bash
python -m pip install pyinstaller
```

Linux:

```bash
pyinstaller --onefile --windowed --name RADXOID-Installer \
  dist/installer/radxoid_installer.py
```

Windows:

```powershell
pyinstaller --onefile --windowed --uac-admin --name RADXOID-Installer `
  dist/installer/radxoid_installer.py
```

The GitHub workflow builds both executables for each `v*` tag.

## Troubleshooting

### No SD card listed

Reconnect the card, wait for the operating system to enumerate it, and click
Refresh. The installer intentionally rejects fixed disks, system disks,
partitions, read-only media, and devices whose removable SD identity cannot be
established.

### Checksum failure

Download the GPT ZIP and `SHA256SUMS-v1.0.22.txt` again from the same release.
Do not rename the ZIP.

### Write failure

Leave the card inserted, copy the visible operation log or durable session log,
and report the complete error. A failed write must be restarted from the
beginning; the partial card is not bootable.

### Interrupted write

Treat the card as incomplete unless the durable log contains both
`Verified SHA-256:` and
`SD-card write and readback verification completed successfully!`. Reconnect
the card and restart the complete write from the beginning. Do not boot or use
a card whose final readback verification did not finish.

Flashing erases the entire selected SD card. Back it up first.
