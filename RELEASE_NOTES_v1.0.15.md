# RADXOID v1.0.15 — Windows PowerShell discovery fix

This release fixes the Windows error shown after successful SHA-256 verification:

```text
Could not start PowerShell: [WinError 2] The system cannot find the file specified
```

The packaged Administrator GUI now locates `powershell.exe` directly through
`%SystemRoot%\System32\WindowsPowerShell\v1.0` or `Sysnative`, then falls back
to `PATH` and PowerShell 7. The same resolved executable is used for SD-card
enumeration and volume dismounting.

## Required files

- `RADXOID-Installer.exe` or `RADXOID-Installer-linux-x86_64`
- `rk356x_rock_3a_r_20261120.1320_gpt.zip`
- `SHA256SUMS-v1.0.15.txt`

The GPT image and write/readback verification pipeline are unchanged from
v1.0.14.
