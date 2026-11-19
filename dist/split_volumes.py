#!/usr/bin/env python3
"""
RADXOID - Split Large Files into Volumes
Splits files >2GB into 2GB volumes for GitHub release distribution
Usage: python split_volumes.py [source_dir] [output_dir] [volume_size_mb]
"""

import os
import sys
import math
import hashlib
from pathlib import Path

# Default volume size: 1900MB (slightly less than 2GB for safety)
DEFAULT_VOLUME_SIZE = 1900 * 1024 * 1024  # 1900MB in bytes

def split_file(input_path, output_dir, volume_size):
    """Split a file into volumes of specified size"""
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    
    if not input_path.exists():
        print(f"❌ Error: File not found: {input_path}")
        return False
    
    file_size = input_path.stat().st_size
    if file_size <= volume_size:
        print(f"⚠️  Skipping {input_path.name} (already <= {volume_size/1024/1024}MB)")
        return True
    
    # Calculate number of volumes
    num_volumes = math.ceil(file_size / volume_size)
    print(f"📦 Splitting {input_path.name} ({file_size/1024/1024:.1f}MB) into {num_volumes} volumes")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Split file
    with open(input_path, 'rb') as f:
        for i in range(num_volumes):
            volume_name = f"{input_path.name}.{i+1:03d}"
            volume_path = output_dir / volume_name
            
            # Read chunk
            chunk_size = min(volume_size, file_size - i * volume_size)
            chunk = f.read(chunk_size)
            
            # Write volume
            with open(volume_path, 'wb') as vf:
                vf.write(chunk)
            
            print(f"   ✅ Created: {volume_name} ({len(chunk)/1024/1024:.1f}MB)")
    
    return True

def generate_checksums(output_dir):
    """Generate SHA256 checksums for all volumes"""
    output_dir = Path(output_dir)
    checksums = []
    
    for vol_file in sorted(output_dir.glob("*.*")):
        if vol_file.is_file():
            sha256 = hashlib.sha256()
            with open(vol_file, 'rb') as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)
            checksums.append(f"{sha256.hexdigest()}  {vol_file.name}")
    
    # Write checksums file
    checksum_file = output_dir / "SHA256SUMS.txt"
    with open(checksum_file, 'w') as f:
        f.write("\n".join(checksums))
    
    print(f"\n✅ Generated checksums: {checksum_file}")
    return checksum_file

def main():
    if len(sys.argv) < 2:
        print("Usage: python split_volumes.py <source_dir> [output_dir] [volume_size_mb]")
        print(f"Example: python {__file__} /path/to/artifacts dist/volumes 1900")
        sys.exit(1)
    
    source_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("dist/volumes")
    volume_size_mb = int(sys.argv[3]) if len(sys.argv) > 3 else 1900
    volume_size = volume_size_mb * 1024 * 1024
    
    print(f"🎯 Splitting files from {source_dir} into {volume_size_mb}MB volumes")
    print(f"📁 Output directory: {output_dir}")
    print()
    
    # Split all files in source directory
    for file_path in source_dir.glob("*"):
        if file_path.is_file():
            split_file(file_path, output_dir, volume_size)
    
    # Generate checksums
    generate_checksums(output_dir)
    
    print(f"\n✅ All files split into volumes!")
    print(f"📦 Volumes saved to: {output_dir}")

if __name__ == "__main__":
    main()
