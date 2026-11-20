# RADXOID v1.0.0 - Distribution Package

## 📦 Multi-Volume Distribution for GitHub Release

This package contains **RADXOID v1.0.0** split into multiple volumes to comply with GitHub's 2GB file upload limit.

---

## 📚 Package Structure

RADXOID-v1.0.0/
├── installer.py                         # Cross-platform GUI source
├── build_windows.bat                    # Build Windows executable
├── build_linux.sh                        # Build Linux executable
├── volumes/
│   ├── update.img                       # Complete flashable image
│   ├── super.img                        # Dynamic partitions
│   ├── gpt.img.001                      # GPT volume 1
│   ├── gpt.img.002                      # GPT volume 2
│   ├── gpt.img.003                      # GPT volume 3
│   └── SHA256SUMS.txt                   # Checksums
├── README.md                            # This file
├── INSTALLER_README.md                  # Installer details
├── RELEASE_NOTES.md                     # Release notes
└── GITHUB_RELEASE_GUIDE.md              # Publishing guide
```

---

## 🎯 Quick Start

### Windows
1. **Download** all files from the release
2. **Run** `installer/windows/RADXOID-Installer.exe`
3. **Follow** the GUI instructions

### Linux
1. **Download** all files from the release
2. **Make executable**: `chmod +x installer/linux/RADXOID-Installer`
3. **Run**: `./installer/linux/RADXOID-Installer`
4. **Follow** the GUI instructions

### Manual (All Platforms)
```bash
# 1. Download all volumes
# 2. Join volumes
python dist/join_volumes.py dist/volumes dist/joined

# 3. Verify checksums
sha256sum -c dist/volumes/SHA256SUMS.txt

# 4. Flash to SD card (see below)
```

---

## 💾 Flashing to SD Card

### Windows
1. **Use Rufus** (recommended):
   - Download: https://rufus.ie/
   - Select the joined `update.img`
   - Choose your SD card
   - Click "Start"

2. **Or use dd**:
   ```powershell
   # List disks
   wmic diskdrive list brief
   
   # Flash (replace X with your SD card number)
   dd if=update.img of=\\?\Device\HarddiskX\Partition0 bs=1M --progress
   ```

### Linux
```bash
# List disks
lsblk

# Flash (replace sdX with your SD card, e.g., sdb)
# WARNING: This will erase the entire SD card!
sudo dd if=dist/joined/update.img of=/dev/sdX bs=4M status=progress oflag=sync

# Wait for completion
sync
```

### macOS
```bash
# List disks
diskutil list

# Unmount (replace diskX with your SD card)
diskutil unmountDisk /dev/diskX

# Flash
sudo dd if=dist/joined/update.img of=/dev/rdiskX bs=4m

# Wait for completion
sync
```

---

## 📦 File Information

### Original Files
| File | Size | Description |
|------|------|-------------|
| `update.img` | 1.8 GB | Full flashable image |
| `super.img` | 1.6 GB | Dynamic partitions |
| `gpt.img` | 4.1 GB | Partition table |
| `boot.img` | 35 MB | Boot partition |
| `recovery.img` | 110 MB | Recovery partition |
| `dtbo.img` | 607 B | Device tree overlay |

### Split Volumes
| File | Size | Volumes |
|------|------|----------|
| `update.img` | 1.8 GB | 1 volume (1.8GB < 2GB) |
| `super.img` | 1.6 GB | 1 volume (1.6GB < 2GB) |
| `gpt.img` | 4.1 GB | 3 volumes (1.9GB + 1.9GB + 0.3GB) |
| `boot.img` | 35 MB | 1 volume |
| `recovery.img` | 110 MB | 1 volume |
| `dtbo.img` | 607 B | 1 volume |

---

## 🔧 Manual Volume Joining

If you prefer to join volumes manually:

### Windows (PowerShell)
```powershell
# Join update.img volumes
$volumes = Get-ChildItem -Path "volumes" -Filter "update.img.*" | Sort-Object Name
$output = [System.IO.File]::Create("joined/update.img")
foreach ($vol in $volumes) {
    $data = [System.IO.File]::ReadAllBytes($vol.FullName)
    $output.Write($data, 0, $data.Length)
}
$output.Close()
```

### Linux/macOS
```bash
# Join all volumes
cd volumes
for file in *.img.*; do
    base=${file%.*}
    cat ${base}.* > ../joined/${base}
done
```

---

## 📋 Checksums

All volumes include a `SHA256SUMS.txt` file with checksums for verification.

### Verify Checksums
```bash
# Linux/macOS
sha256sum -c volumes/SHA256SUMS.txt

# Windows (PowerShell)
Get-Content volumes/SHA256SUMS.txt | ForEach-Object {
    $expected, $file = $_ -split "  ", 2
    $actual = (Get-FileHash -Path "volumes/$file" -Algorithm SHA256).Hash.ToLower()
    if ($actual -eq $expected.ToLower()) {
        Write-Host "✅ $file"
    } else {
        Write-Host "❌ $file (checksum mismatch)"
    }
}
```

---

## 🎮 After Flashing

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

## ⚠️ Important Notes

1. **Backup your data** - Flashing will erase your SD card
2. **Verify checksums** - Always check file integrity
3. **Use quality SD card** - Class 10 or UHS-I recommended
4. **Power supply** - Ensure stable power during flashing
5. **Patience** - Flashing may take several minutes

---

## 🤝 Support

- **Repository**: https://github.com/rufl/RADXOID
- **Issues**: https://github.com/rufl/RADXOID/issues
- **Documentation**: https://github.com/rufl/RADXOID#readme

---

## 📜 License

- **Code**: Apache 2.0
- **Documentation**: CC-BY-4.0
- **Rockchip BSP**: Proprietary (see Radxa terms)
- **Mali Driver**: Proprietary (see ARM terms)

**Do not redistribute proprietary Rockchip/Mali blobs outside their original license terms.**

---

*RADXOID v1.0.0 - 2026-11-19*
