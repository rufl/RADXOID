# RADXOID v1.0.14 — verified GPT SD-card writer

This release replaces the nonfunctional join/output flow and the incorrect raw
`update.img` write with the actual ROCK 3A SD-card format.

## Required files

- `RADXOID-Installer.exe` or `RADXOID-Installer-linux-x86_64`
- `rk356x_rock_3a_r_20261120.1320_gpt.zip`
- `SHA256SUMS-v1.0.14.txt`

No files are joined. The ZIP contains the complete 4,391,454,208-byte
`gpt.img` and is below GitHub's 2 GiB asset limit.

## Implemented workflow

1. Select release assets.
2. Verify the GPT ZIP against the versioned SHA-256 manifest.
3. Select a detected removable SD-card whole disk.
4. Confirm the exact destructive target.
5. Stream-decompress `gpt.img` directly to the card with byte and percentage
   progress.
6. Validate ZIP CRC and compare the decompressed source SHA-256 with a complete
   readback of the written image-sized device prefix.

## Reliability and safety fixes

- Durable per-run logs plus live GUI logging.
- All Tk updates and dialogs run on the Tk main thread.
- Back, Close, refresh, and target controls are blocked during writing.
- Target capacity and available identity are revalidated after unmount.
- Short writes, short reads, archive errors, permission failures, and hash
  mismatches fail closed.
- Windows binaries request Administrator privileges through their manifest.
- Linux uses root, graphical `pkexec`, or an already-authenticated `sudo`
  session for raw operations.

Flashing erases the selected SD card. Keep it connected until readback reaches
100% and the success dialog appears.
