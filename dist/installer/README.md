# RADXOID Installer

## Safe SD-card installer

This GUI joins RADXOID split volumes and verifies their SHA-256 manifest before
creating `update.img`. It supports Windows and Linux.

Safety model:

- The input manifest is mandatory; checksum paths must be plain filenames.
- Symlinks are rejected for inputs, outputs, and checksum entries.
- Output cannot be inside the input volume directory.
- Linux lists only writable whole disks identified as SD media; system and
  mounted disks are excluded.
- Linux requires an exact `ERASE /dev/...` confirmation, unmounts target
  partitions, checks capacity, writes only `update.img`, then verifies the
  written prefix by SHA-256.
- Windows never performs raw-disk writes. Use Rufus or Etcher after joining.

---

## 📥 Download

### Windows
- **Executable**: `RADXOID-Installer.exe`
- **Requirements**: Windows 7+, Python 3.8+ (for source)
- **Download**: From [GitHub Releases](https://github.com/rufl/RADXOID/releases)

### Linux
- **Executable**: `RADXOID-Installer-linux-x86_64` (standalone binary)
- **Requirements**: Linux with `lsblk`, `findmnt`, `udevadm`, and `sudo`
- **Download**: From [GitHub Releases](https://github.com/rufl/RADXOID/releases)

---

## 🚀 Quick Start

### Windows
1. Download `RADXOID-Installer.exe` from the release.
2. Download the complete `rkupdate.img`, its `.zip` companion, and
  `SHA256SUMS-v1.0.8.txt` into one directory.
3. Run the installer, choose the directory, then choose an output directory.
   The `.img` is already complete; the `.zip` is not a second image part.
4. The installer verifies both assets and writes the complete image as
   `update.img`. Use Rufus or Etcher with that file.
5. Windows never erases or writes disks through this installer.

### Linux
1. Download `RADXOID-Installer-linux-x86_64`.
2. Make it executable: `chmod +x RADXOID-Installer-linux-x86_64`.
3. Run it as a normal user; `sudo` is requested only for unmount, write, and verify.
4. Insert the SD card, select the detected whole disk, and type the exact
   confirmation shown by the GUI.
5. Do not remove power or the card until post-write verification finishes.

---

## 📁 File Structure

```text
RADXOID-v1.0.2/
├── installer/
│   ├── windows/
│   │   └── RADXOID-Installer.exe
│   ├── linux/
│   │   └── RADXOID-Installer-linux-x86_64
│   └── README.md
├── volumes/
│   ├── update.img.001
│   ├── update.img.002
│   └── SHA256SUMS.txt
├── README.md
└── RELEASE_NOTES_v1.0.2.md
```

---


## 📚 Usage and security behavior

### Join and verify
- Select the directory containing the release assets and either
  `SHA256SUMS.txt` or the versioned `SHA256SUMS-v1.0.8.txt` manifest.
- Verification fails closed if the manifest is missing, malformed, incomplete,
  contains a path, or references a missing/symlink file.
- Complete `rkupdate.img` assets are normalized to `update.img`; `.zip`
  companions are verified and copied, never concatenated as image volumes.
- Legacy split files named `.001`, `.002`, ... are still joined in numeric order.
- Select an output directory outside the input directory.
- Joined files are written through temporary files and atomically renamed.
- SHA-256 verification can be skipped only through the explicit warning
  confirmation; skipping removes integrity protection and is not recommended.

### Flashing
- Windows: join only; flash `update.img` with
  [Rufus](https://rufus.ie/) or [balenaEtcher](https://etcher.balena.io/).
- Linux: only whole, writable SD disks are offered. Root disks, mounted disks,
  partitions, USB disks, and unknown media are not offered.
- The selected disk is revalidated immediately before writing. Its partitions
  are unmounted, capacity is checked, and the image-sized region is read back
  and hashed after `dd`.
- Flashing destroys all data on the selected SD card. Back up first.

---

## 🛠️ Building from source

Prerequisites: Python 3.8+ and PyInstaller (`python -m pip install pyinstaller`).

```bash
cd dist/installer
pyinstaller --onefile --windowed --name RADXOID-Installer radxoid_installer.py
```

The repository workflow builds signed-by-GitHub-release Linux and Windows
executables for every `v*` tag. The Linux executable is not an AppImage.
---

## 🎮 After Installation

### Verify GPU
```bash
# Connect to device via ADB
adb devices

# Verify Mali-G52 GPU
./scripts/verify-gpu.sh [device-serial]
```

### Apply Quick Wins (Optional)
```bash
# See NEXT_OPTIMIZATIONS.md for details
./scripts/apply-quick-wins.sh
./scripts/build-incremental.sh
./scripts/flash-rock3a.sh
```

---

## 🐛 Troubleshooting

### No assets found or checksum failure
Keep the complete `.img`, optional `.zip` companion, and
`SHA256SUMS-v1.0.8.txt` in the same directory. The `.img` and `.zip` are
different representations of the same release asset, not two parts to
concatenate. Redownload the manifest and assets together if a checksum fails.

### No SD card shown on Linux
The installer intentionally rejects USB readers, mounted media, partitions,
the system disk, read-only disks, and media whose SD identity cannot be proven.
Check `lsblk --json` and insert a physical SD card directly or through a reader
that exposes SD transport information.

### Permission denied or sudo timeout
Install `sudo`, keep the session local, and ensure your account may unmount and
write removable media. The installer does not silently fall back to unsafe writes.

### Not enough space
The output directory needs space for the joined files. The target SD card must
be at least as large as `update.img`.
---


## 🤝 Support

- **Repository**: https://github.com/rufl/RADXOID
- **Issues**: https://github.com/rufl/RADXOID/issues
- **Documentation**: https://github.com/rufl/RADXOID#readme

---

## 📜 License

- **Code**: Apache 2.0
- **Documentation**: CC-BY-4.0
- **Installer**: Apache 2.0

---

*RADXOID Installer v1.0.2*
