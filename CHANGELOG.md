# RADXOID Changelog

## [v1.0.23] - Persistent crash-safe log

### Added
- Writes every entry to both a timestamped session log and the stable
  `installer-latest.log` outside the executable directory.
- Flushes and calls `fsync` after every line so Defender termination or process
  failure does not leave important progress only in memory.
- Shows the persistent file path above the GUI log and adds an
  **Open log folder** button.

### Location
- Windows: `%LOCALAPPDATA%\\RADXOID\\logs\\installer-latest.log`
- Linux: `${XDG_STATE_HOME:-$HOME/.local/state}/RADXOID/logs/installer-latest.log`


## [v1.0.22] - Defender-safe source launcher

### Added
- Publishes `RADXOID-Installer.pyw`, a plain-source fallback that avoids the
  PyInstaller one-file self-extraction pattern associated with Defender false
  positives.
- The source launcher requests UAC elevation itself and shows a Windows dialog
  when Python lacks Tcl/Tk.
- Publishes `SHA256SUMS-installers.txt` for the executable, source launcher, and
  Linux binary.

### Recovery
- An interrupted card is explicitly treated as incomplete unless the durable
  log contains both the final verified SHA-256 and the success message.
- Restarting safely rewrites the complete image from byte zero; there is no
  unsafe resume mode.


## [v1.0.21] - Lock volumes without dismounting the reader

### Fixed
- Removes `FSCTL_DISMOUNT_VOLUME` from the Windows SD preparation sequence.
  This SDXC reader returned error 21 after both `mountvol /p` and explicit
  dismounting.
- Retains `FSCTL_LOCK_VOLUME`, which Microsoft documents as sufficient for
  exclusive raw writes to sectors inside mounted volume extents.

### Safety
- Volume locks flush cached data, prove that no files remain open, block other
  filesystem access, and stay held until write plus SHA-256 readback complete.

### Verification
- Regression coverage now requires exactly one control operation per volume:
  `FSCTL_LOCK_VOLUME`.


## [v1.0.20] - Keep Windows removable media online

### Fixed
- Replaces `mountvol /p`, which took the SD volume offline and caused the first
  `WriteFile` call to fail with Windows error 21 (`The device is not ready`).
- Removes mount points without offlining the disk, then holds
  `FSCTL_LOCK_VOLUME` and `FSCTL_DISMOUNT_VOLUME` handles throughout writing
  and SHA-256 readback.

### Diagnostics
- Reports native errors as explicit `Windows error N` messages rather than
  misleading POSIX-derived exception names such as `IsADirectoryError`.
- Tells the user to close Explorer or another process when volume locking fails.

### Verification
- Confirms that `/p` is absent, both volume control codes are issued, and every
  lock is released after success or failure.


## [v1.0.19] - Win32 I/O without the C runtime

### Fixed
- Keeps the successful `CreateFileW` physical-disk handle entirely in Win32
  instead of passing it to `msvcrt.open_osfhandle`, which produced the observed
  `[Errno 13] Permission denied`.
- Writes with `WriteFile`, reads back with `ReadFile`, flushes with
  `FlushFileBuffers`, and closes with `CloseHandle`.

### Performance
- Reuses one 4 MiB buffer for decompression, hashing, writing, and readback
  instead of allocating a new bytes object for every block.

### Verification
- Exercises native `CreateFileW`/`WriteFile`/`ReadFile`/`FlushFileBuffers`/
  `CloseHandle` behavior without any CRT file descriptor.


## [v1.0.18] - Native Windows raw-disk access

### Fixed
- Opens `\\.\PhysicalDriveN` through `CreateFileW` with the Windows DASD
  requirements: Administrator access, `OPEN_EXISTING`, read/write sharing, and
  write-through output.
- Flushes Windows raw-device writes with `FlushFileBuffers` before readback.

### Diagnostics
- Shows the exact exception, device path, native API operation, and Windows
  system error when opening or flushing the selected SD card fails.

### Verification
- Tests the `CreateFileW` access/share/disposition contract and error
  propagation.
- Runs the installer backend tests on both Windows and Linux before packaging.


## [v1.0.17] - Broader Windows removable-media detection

### Fixed
- Accepts removable media on SCSI and other reader buses, not only USB.
- Detects disks containing a Windows volume with `DriveType=Removable` even
  when the device model is generic.

### Diagnostics
- Logs every enumerated physical disk with bus type, media type,
  removable-volume status, and the final eligible/excluded decision.

### Safety
- Boot, system, read-only, offline, and unrelated fixed disks remain excluded.

## [v1.0.16] - Windows SDHC reader detection

### Fixed
- Detects SDHC, SDXC, MMC, and card-reader devices even when Windows reports
  their USB reader as fixed media.
- Collects `Get-Disk` and `Win32_DiskDrive` identity fields, then applies the
  safety filter in Python.

### Safety
- Continues to reject boot, system, read-only, offline, and unrelated fixed
  USB disks.
- Added positive SDHC/card-reader and negative fixed-USB/system-disk tests.

## [v1.0.15] - Windows PowerShell discovery fix

### Fixed
- Locates Windows PowerShell through `%SystemRoot%\System32` or `Sysnative`
  before consulting `PATH`.
- Prevents packaged Administrator GUI processes from reporting
  `[WinError 2]` while enumerating or dismounting SD-card volumes.

### Verified
- Added a regression test with an empty `PATH` and a valid system PowerShell.

## [v1.0.14] - Verified SD-card writer

### Fixed
- Removed the invalid join/output stages; release artifacts are complete files.
- Writes `gpt.img` from the verified GPT ZIP instead of raw-writing the
  Rockchip USB-loader `update.img` package.
- Restored GUI log delivery and added durable per-run log files.
- Moved all Tk updates and dialogs to the main thread.
- Blocks Back and window close while a destructive write is active.
- Revalidates target path, size, and available device identity after unmount.
- Verifies ZIP CRC during streaming and SHA-256 through full device readback.

### Added
- Three-step GUI: select assets, verify checksums, write SD card.
- Byte and percentage progress for writing and readback verification.
- Windows removable-disk handling with Administrator manifest elevation.
- Linux `pkexec`/root raw-write path with explicit whole-disk confirmation.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to a loose semantic versioning.

---

## [Unreleased]

### Added
- `SUMMARY.md` - Executive summary with project overview, metrics, and future work
- `OPTIMIZATIONS.md` - Complete optimization guide with all applied tuning
- `CHANGELOG.md` - This file

### Changed
- `scripts/tune-performance.sh` - Enhanced with SurfaceFlinger vsync, thermal thresholds, display settings, JIT optimizations, TCP keepalive, audio buffer tuning, CPU boost
- `scripts/debloat.sh` - Expanded package removal list from ~36 to ~70 packages
- `scripts/build.sh` - Integrated tune-performance.sh, fixed envsetup.sh sourcing, added lunch call
- `README.md` - Updated with build results, lean flavor details, usage instructions

### Fixed
- Build script now properly sources envsetup.sh and calls lunch before vendor build
- Fixed ZSH_VERSION unbound variable error in envsetup.sh
- Fixed permission issues with root-owned files in out/

---

## [2026-11-19] - Initial Lean Build

### Added
- `config/rock3a-lean.env` - Lean configuration file
- `scripts/debloat.sh` - Package removal script (36 packages initially)
- `scripts/build-incremental.sh` - Incremental build script
- `scripts/validate.sh` - Configuration validation script
- `scripts/flash-rock3a.sh` - Flash script for ROCK 3A
- `scripts/verify-gpu.sh` - GPU verification script
- `README.md` - Initial project documentation
- `Dockerfile` - Docker builder image

### Changed
- `config/rock3a.env` - Updated to use Android11_Radxa_rk12 HEAD
- `scripts/build.sh` - Added fixups for LOCAL_TIDY, recovery partition size, SCHEDUTIL governor, dexpreopt speed-profile

### Build Results
- **Status**: BUILD_EXIT=0
- **Date**: 2026-11-19 12:34-12:51
- **Artifacts**: update.img (1.8GB), super.img (1.6GB), rkupdate.img (1.7GB)
- **Optimizations**: SCHEDUTIL governor, dexpreopt speed-profile, debloat (36 packages)

---

## [2026-11-18] - Project Setup

### Added
- Git repository initialized at `/home/lich/lichforge/code/monorepo/RADXOID`
- GitHub remote: https://github.com/rufl/RADXOID
- Initial source tree prepared at `/run/media/lich/EdgeBKP/radxoid/source` (150GB)

### Build Results
- **Status**: BUILD_EXIT=0
- **Date**: 2026-11-18 10:42
- **Artifacts**: update.img (1.7GB), super.img (1.6GB)
- **Target**: rk356x_rock_3a_r-userdebug

---

## Project Structure

```
RADXOID/
├── config/              # Configuration files
├── scripts/             # Build and utility scripts
├── overlay/             # Overlay files
├── docs/                # Documentation
├── Dockerfile           # Docker builder image
├── README.md            # Main documentation
├── OPTIMIZATIONS.md      # Optimization guide
├── SUMMARY.md           # Executive summary
└── CHANGELOG.md         # This file
```

---

## Commit History

For detailed commit history, see: https://github.com/rufl/RADXOID/commits/main

### Recent Commits
```
e6a703c docs: add SUMMARY.md with executive summary, metrics, and future work
59040c3 docs: update OPTIMIZATIONS.md with all applied tuning and changelog
1100a1b feat(tune): add SurfaceFlinger vsync, thermal, display, JIT, TCP optimizations
803fc22 feat(debloat): expand package removal list for lean gaming image
5da56a3 feat(tune): enhance performance tuning with network, audio, zram, ART optimizations
7d136d5 docs: add OPTIMIZATIONS.md with complete optimization guide
4eab994 feat(tune): add performance tuning script (zram, I/O, SurfaceFlinger, ART)
ab89ba0 Add performance tuning script for ROCK 3A Android 11
d8e3198 docs: add build results, lean flavor details, and usage instructions
f6d1182 feat(lean): add debloat + performance fixups + incremental build loop
44ec0be Update files
5216600 Add SCHEDUTIL governor and dexpreopt fixups to incremental build
5407b14 build-incremental: keep set +u through lunch, use m or make
6d533d8 feat: add incremental build loop and lean debloat workflow
58d9bf4 feat(rock3a): Android 11 lean + debloat + performance fixups
```

---

## Build Statistics

| Date | Commit | Status | Duration | Artifacts |
|------|--------|--------|----------|-----------|
| 2026-11-19 | e6a703c | ✅ BUILD_EXIT=0 | ~2.5h | update.img 1.8GB |
| 2026-11-19 | 1100a1b | ✅ BUILD_EXIT=0 | ~2.5h | update.img 1.8GB |
| 2026-11-18 | 58d9bf4 | ✅ BUILD_EXIT=0 | ~3h | update.img 1.7GB |

---

## Optimization Statistics

| Category | Count | Impact |
|----------|-------|--------|
| Performance Tuning | 12 | CPU, ART, Zram, I/O, SurfaceFlinger, Display, Network, Audio, CPU Boost, Thermal, JIT, Kernel |
| Debloat | ~70 | System image -300-400MB |
| Fixups | 2 | Build reliability |

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

---

## License

See [README.md](README.md) for license information.

---

*Maintained by: rufl*
*Last updated: 2026-11-19*
