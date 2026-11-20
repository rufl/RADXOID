# RADXOID v1.0.1 — Safe SD-card installer

## Safety fixes

- Linux GUI enumerates only removable, writable whole disks.
- System disk and mounted devices are excluded.
- Image size is checked against the target disk.
- Flashing requires typing the exact confirmation `ERASE <device>`.
- Windows no longer reports a fake successful raw flash; it joins files and directs users to Etcher/Rufus.
- The GUI never selects partitions as targets.
- `update.img` remains the only image written by the Linux backend.

## Assets

The Android image assets remain available in the v1.0.0 release. This release contains the corrected installer binaries and source:

- `RADXOID-Installer-linux-x86_64`
- `RADXOID-Installer.exe`
- `RADXOID-Installer-source-v1.0.1.zip`

## Verification

- Python syntax check passed.
- Volume join test passed with split and complete files.
- GPT chunks reconstructed to the original SHA256.
- GitHub Actions Windows and Linux builds passed for the installer workflow.

Hardware flashing and emulator performance remain unvalidated.
