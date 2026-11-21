# RADXOID v1.0.24 — exclusive Windows write and readback

This release fixes the Windows raw-disk lifecycle exposed by the v1.0.23
post-write SHA-256 mismatch.

Windows now opens the selected `PhysicalDrive` once with exclusive access and
keeps that same handle open through:

1. streaming `gpt.img` from the verified ZIP;
2. `FlushFileBuffers`;
3. rewinding with `SetFilePointerEx`; and
4. reading the complete image-sized prefix back for SHA-256 verification.

The filesystem volume locks also remain held for the entire operation. This
removes the close/reopen gap in which Windows or another process could access
the card between writing and verification.

The operation is successful only when the durable log contains both
`Verified SHA-256:` and
`SD-card write and readback verification completed successfully!`.
A mismatch still means the card contents are not trustworthy; rewrite from byte
zero or test another card/reader.

Persistent Windows log:

```text
%LOCALAPPDATA%\RADXOID\logs\installer-latest.log
```

## Required files

- `RADXOID-Installer.pyw` or `RADXOID-Installer.exe`
- `rk356x_rock_3a_r_20261120.1320_gpt.zip`
- `SHA256SUMS-v1.0.24.txt`
