#!/usr/bin/env python3
"""
RADXOID - Join Split Volumes
Joins split volumes back into original files
Usage: python join_volumes.py [volumes_dir] [output_dir]
"""

import os
import sys
import hashlib
import re
from pathlib import Path

def join_file(volume_pattern, output_dir):
    """Join volumes matching pattern into original file"""
    volumes_dir = volume_pattern.parent
    base_name = volume_pattern.stem
    
    # Find all volumes for this file
    volumes = sorted(volumes_dir.glob(f"{base_name}.*"))
    if not volumes:
        print(f"❌ No volumes found for: {base_name}")
        return False
    
    # Extract original filename (remove .001, .002, etc.)
    original_name = base_name
    output_path = output_dir / original_name
    
    print(f"📦 Joining {len(volumes)} volumes into {original_name}")
    
    # Join volumes
    with open(output_path, 'wb') as out_file:
        for vol in volumes:
            print(f"   📄 Reading: {vol.name}")
            with open(vol, 'rb') as vf:
                out_file.write(vf.read())
    
    print(f"   ✅ Created: {original_name} ({output_path.stat().st_size/1024/1024:.1f}MB)")
    return True

def verify_checksums(volumes_dir):
    """Verify SHA256 checksums of all volumes"""
    checksums_file = volumes_dir / "SHA256SUMS.txt"
    if not checksums_file.exists():
        print("⚠️  No checksums file found")
        return True
    
    print("\n🔍 Verifying checksums...")
    with open(checksums_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            expected_hash, filename = line.split("  ", 1)
            filepath = volumes_dir / filename
            
            if not filepath.exists():
                print(f"   ❌ Missing: {filename}")
                return False
            
            sha256 = hashlib.sha256()
            with open(filepath, 'rb') as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)
            
            actual_hash = sha256.hexdigest()
            if actual_hash == expected_hash:
                print(f"   ✅ {filename}")
            else:
                print(f"   ❌ {filename} (checksum mismatch)")
                return False
    
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python join_volumes.py <volumes_dir> [output_dir]")
        print(f"Example: python {__file__} dist/volumes dist/joined")
        sys.exit(1)
    
    volumes_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("dist/joined")
    
    print(f"🎯 Joining volumes from {volumes_dir}")
    print(f"📁 Output directory: {output_dir}")
    print()
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all volume files and group by base name
    volume_files = list(volumes_dir.glob("*.*"))
    base_names = set()
    
    for vol in volume_files:
        # Extract base name (remove .001, .002, etc.)
        match = re.match(r"(.+)\.\d{3}$", vol.name)
        if match:
            base_names.add(match.group(1))
    
    # Join each file
    for base_name in sorted(base_names):
        pattern = volumes_dir / f"{base_name}.001"
        join_file(pattern, output_dir)
    
    # Verify checksums
    if not verify_checksums(volumes_dir):
        print("\n❌ Checksum verification failed!")
        sys.exit(1)
    
    print(f"\n✅ All volumes joined successfully!")
    print(f"📦 Joined files saved to: {output_dir}")

if __name__ == "__main__":
    main()
