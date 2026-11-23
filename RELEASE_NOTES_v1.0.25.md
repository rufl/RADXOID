# RADXOID v1.0.25 — deterministic mismatch diagnostics

This release makes the Windows SD verification more useful when the card still
fails after the exclusive-handle fix.

Changes:

- retries the complete Windows write once after a SHA-256 readback mismatch;
- if the second attempt still differs, compares the written data against the
  source image block-by-block;
- reports the first differing byte in decimal and hexadecimal; and
- keeps the persistent log and source-launcher workflow unchanged.

A successful card still requires both:

- `Verified SHA-256:`; and
- `SD-card write and readback verification completed successfully!`

If mismatch persists, prefer another SD card/reader. If the board still does
not boot after a fully verified write, use Rockchip USB recovery with
`update.img` / `rkdeveloptool` / `RKDevTool` instead of raw SD media.

## Required files

- `RADXOID-Installer.pyw` or `RADXOID-Installer.exe`
- `rk356x_rock_3a_r_20261120.1320_gpt.zip`
- `SHA256SUMS-v1.0.25.txt`
