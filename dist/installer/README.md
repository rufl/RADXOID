# RADXOID Installer

## 📦 Cross-Platform Installer for RADXOID

This installer provides a **graphical user interface (GUI)** for joining split volumes and flashing RADXOID to an SD card on **Windows** and **Linux**.

---

## 🎯 Features

- **Cross-platform**: Works on Windows and Linux
- **GUI Interface**: Easy-to-use graphical interface
- **Volume Joining**: Automatically joins split volumes
- **Checksum Verification**: Verifies file integrity
- **SD Card Flashing**: Direct flashing to SD card (Linux)
- **Progress Tracking**: Shows operation progress

---

## 📥 Download

### Windows
- **Executable**: `RADXOID-Installer.exe`
- **Requirements**: Windows 7+, Python 3.8+ (for source)
- **Download**: From [GitHub Releases](https://github.com/rufl/RADXOID/releases)

### Linux
- **AppImage**: `RADXOID-Installer` (standalone)
- **Requirements**: Linux kernel 3.0+, FUSE (for AppImage)
- **Download**: From [GitHub Releases](https://github.com/rufl/RADXOID/releases)

---

## 🚀 Quick Start

### Windows
1. **Download** `RADXOID-Installer.exe`
2. **Download** all volume files (`.001`, `.002`, etc.)
3. **Run** the installer
4. **Follow** the GUI instructions

### Linux
1. **Download** `RADXOID-Installer` (AppImage)
2. **Make executable**: `chmod +x RADXOID-Installer`
3. **Run**: `./RADXOID-Installer`
4. **Follow** the GUI instructions

---

## 📁 File Structure

```
RADXOID-v1.0.0/
├── installer/
│   ├── windows/
│   │   └── RADXOID-Installer.exe      # Windows GUI installer
│   ├── linux/
│   │   └── RADXOID-Installer           # Linux GUI installer (AppImage)
│   └── README.md                       # This file
├── volumes/
│   ├── update.img.001                  # Volume 1
│   ├── update.img.002                  # Volume 2 (if needed)
│   ├── super.img.001                   # Volume 1
│   ├── super.img.002                   # Volume 2 (if needed)
│   └── SHA256SUMS.txt                  # Checksums
├── README.md                           # Main README
└── LICENSE                             # License
```

---

## 🔧 Building from Source

### Prerequisites
- Python 3.8+
- PyInstaller: `pip install PyInstaller`
- (Optional) linuxdeploy for AppImage

### Windows
```bash
# Run the build script
cd dist/installer
build_windows.bat

# Output: build/windows/RADXOID-Installer.exe
```

### Linux
```bash
# Make build script executable
chmod +x build_linux.sh

# Run the build script
cd dist/installer
./build_linux.sh

# Output: build/linux/RADXOID-Installer
```

### Create AppImage (Optional)
```bash
# Download linuxdeploy
wget https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
chmod +x linuxdeploy-x86_64.AppImage

# Create AppImage
./linuxdeploy-x86_64.AppImage build/linux/RADXOID-Installer -o build/linux/
```

---

## 📚 Usage

### Step 1: Select Volumes Directory
- Browse to the directory containing the volume files (`.001`, `.002`, etc.)
- The installer will automatically detect all volume files

### Step 2: Verify Checksums
- The installer will verify the SHA256 checksums of all volume files
- This ensures file integrity before joining

### Step 3: Select Output Directory
- Choose where to save the joined files
- The installer will create the original files from the volumes

### Step 4: Join Volumes
- The installer will join all volumes into their original files
- Progress will be shown in the log

### Step 5: Flash to SD Card (Optional)
- **Windows**: The installer will show instructions for using Rufus or dd
- **Linux**: The installer can directly flash to the SD card

---

## ⚠️ Important Notes

### Windows
- **Admin Rights**: Flashing requires administrator privileges
- **Rufus Recommended**: Use [Rufus](https://rufus.ie/) for best results
- **dd for Windows**: Alternative if you prefer command line

### Linux
- **Root Required**: Flashing requires root/sudo privileges
- **Device Selection**: Be careful to select the correct device
- **Data Loss**: Flashing will **ERASE ALL DATA** on the selected device

### Both Platforms
- **Backup**: Always backup your data before flashing
- **SD Card**: Use a quality Class 10 or UHS-I SD card
- **Power**: Ensure stable power during flashing
- **Patience**: Flashing may take several minutes

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

### "No volumes found"
- **Solution**: Ensure all volume files are in the selected directory
- **Check**: Files should be named like `update.img.001`, `update.img.002`, etc.

### "Checksum verification failed"
- **Solution**: Download all files again
- **Check**: Ensure all files were downloaded completely

### "Device not found" (Linux)
- **Solution**: Check if the SD card is inserted
- **Check**: Run `lsblk` to see available devices

### "Permission denied" (Linux)
- **Solution**: Run the installer with sudo or as root
- **Check**: The installer needs root for flashing

### "Not enough space"
- **Solution**: Free up space on the output directory
- **Check**: Joined files require ~10GB of free space

---

## 📊 Performance

### Volume Joining
- **Speed**: ~100-200MB/s (depends on disk)
- **Time**: ~1-2 minutes for all files

### Flashing
- **Speed**: ~20-50MB/s (depends on SD card)
- **Time**: ~5-10 minutes for full image

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

*RADXOID Installer v1.0.0 - 2026-11-19*
