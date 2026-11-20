# RADXOID v1.0.2 — Fail-closed installer hardening

## Security fixes

- Linux device discovery accepts only writable whole disks identified as SD media (`mmc`/`sd` transport or udev SD identity).
- System/root disks, mounted disks, partitions, read-only devices, USB disks, and unknown media are excluded.
- The target is revalidated immediately before writing and its capacity must remain unchanged.
- Target partitions are unmounted explicitly through `sudo umount`; failure aborts the operation.
- Linux writes only the joined `update.img`, then reads back exactly its size and compares SHA-256.
- `sudo` is required for unmount, raw write, and read-back verification; no unsafe fallback exists.
- Windows raw-disk writing is disabled. The Windows GUI joins and verifies files, then directs the user to Rufus or Etcher.
- `SHA256SUMS.txt` is mandatory, must contain valid SHA-256 entries, and may reference only plain filenames.
- Missing, malformed, path-traversal, symlink, or checksum-mismatched inputs fail closed.
- Symlink volumes and outputs are rejected. Joined files use temporary files and atomic replacement.
- Output directories inside the volume directory are rejected.
- The GUI uses a readonly target list and requires exact `ERASE <device>` confirmation.
- Fixed a GUI initialization error that prevented the log widget from being created.

## Assets

- `RADXOID-Installer-linux-x86_64`
- `RADXOID-Installer.exe`
- `RADXOID-Installer-source-v1.0.2.zip`
- `RELEASE_NOTES_v1.0.2.md`

The Android image assets remain available in the [v1.0.0 image release](https://github.com/rufl/RADXOID/releases/tag/v1.0.0).

## Verification

- Python syntax compilation passed for installer and volume utilities.
- Shell syntax checks passed for distribution scripts.
- Non-destructive volume join and symlink rejection tests passed.
- No physical SD card was written during validation.
