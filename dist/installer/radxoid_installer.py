#!/usr/bin/env python3
"""
RADXOID Installer GUI
Cross-platform installer for RADXOID distribution
Supports Windows and Linux
"""

import os
import sys
import subprocess
import hashlib
import json
import re
import threading
import queue
from pathlib import Path
import shutil
from datetime import datetime

# Check if we're running as a PyInstaller bundle
if getattr(sys, 'frozen', False):
    # Running as bundle
    APP_DIR = Path(sys.executable).parent
else:
    # Running as script
    APP_DIR = Path(__file__).parent

# Configuration
VERSION = "v1.0.4"
REPO_URL = "https://github.com/rufl/RADXOID"
RELEASE_URL = f"{REPO_URL}/releases/tag/{VERSION}"

# Platform detection
PLATFORM = sys.platform
IS_WINDOWS = PLATFORM.startswith('win')
IS_LINUX = PLATFORM.startswith('linux')
IS_MAC = PLATFORM.startswith('darwin')

# GUI imports
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False


class RADXOIDInstaller:
    """Main installer class"""
    
    def __init__(self):
        self.volumes_dir = None
        self.output_dir = None
        self.temp_dir = APP_DIR / "temp"
        self.log_queue = queue.Queue()
        self.running = False
        
        # Create temp directory
        self.temp_dir.mkdir(exist_ok=True)
    
    def log(self, message, level="INFO"):
        """Log a message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_queue.put(f"[{timestamp}] [{level}] {message}")
        print(f"[{timestamp}] [{level}] {message}")
    
    def process_log_queue(self, text_widget=None):
        """Process log queue"""
        while not self.log_queue.empty():
            message = self.log_queue.get()
            if text_widget:
                text_widget.insert(tk.END, message + "\n")
                text_widget.see(tk.END)
            print(message)
    
    def select_volumes_dir(self):
        """Select volumes directory"""
        if GUI_AVAILABLE:
            self.volumes_dir = Path(filedialog.askdirectory(title="Select Volumes Directory"))
        else:
            self.volumes_dir = Path(input("Enter volumes directory path: "))
        
        if not self.volumes_dir.exists():
            self.log("Error: Directory does not exist", "ERROR")
            return False
        
        self.log(f"Selected volumes directory: {self.volumes_dir}")
        return True
    
    def select_output_dir(self):
        """Select output directory"""
        if GUI_AVAILABLE:
            self.output_dir = Path(filedialog.askdirectory(title="Select Output Directory"))
        else:
            self.output_dir = Path(input("Enter output directory path: "))
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log(f"Selected output directory: {self.output_dir}")
        return True
    
    def _has_mountpoints(self, node):
        """Return true when a disk or any child partition is mounted."""
        if any(point for point in node.get("mountpoints", []) if point):
            return True
        return any(self._has_mountpoints(child) for child in node.get("children", []))

    def _is_root_ancestor(self, device, root_source):
        """Return true when device contains the mounted root filesystem."""
        if not root_source:
            return False
        result = subprocess.run(
            ["lsblk", "-s", "-n", "-o", "PATH", device],
            capture_output=True, text=True, check=False,
        )
        return root_source in result.stdout.split()

    def _udev_properties(self, device):
        if IS_MAC:
            return {}
        result = subprocess.run(
            ["udevadm", "info", "--query=property", "--name", device],
            capture_output=True, text=True, check=False,
        )
        properties = {}
        for line in result.stdout.splitlines():
            key, separator, value = line.partition("=")
            if separator:
                properties[key] = value
        return properties

    def list_safe_devices(self):
        """Return removable SD-card whole disks that are writable and unmounted."""
        if IS_WINDOWS:
            script = (
                "Get-Disk | Where-Object { $_.BusType -eq 'SD' "
                "-and -not $_.IsBoot -and -not $_.IsSystem -and "
                "-not $_.IsReadOnly } | "
                "Select-Object Number,Size,Model,BusType | ConvertTo-Json -Compress"
            )
            result = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                capture_output=True, text=True, check=False,
            )
            if result.returncode != 0 or not result.stdout.strip():
                return []
            data = json.loads(result.stdout)
            if isinstance(data, dict):
                data = [data]
            return [
                {
                    "path": f"\\\\.\\PhysicalDrive{item['Number']}",
                    "label": f"\\\\.\\PhysicalDrive{item['Number']} | "
                    f"{item.get('Size', 0) / 1024**3:.1f} GiB | "
                    f"{item.get('Model', '').strip()} | SD",
                    "size": int(item.get("Size", 0)),
                }
                for item in data
            ]

        if not IS_LINUX:
            return []
        result = subprocess.run(
            ["lsblk", "--json", "-o",
             "PATH,NAME,TYPE,SIZE,RM,RO,TRAN,MOUNTPOINTS"],
            capture_output=True, text=True, check=False,
        )
        if result.returncode != 0:
            return []
        root_source = subprocess.run(
            ["findmnt", "-n", "-o", "SOURCE", "/"],
            capture_output=True, text=True, check=False,
        ).stdout.strip()
        data = json.loads(result.stdout).get("blockdevices", [])
        devices = []
        for item in data:
            path = item.get("path")
            mounted = self._has_mountpoints(item)
            props = self._udev_properties(path) if path else {}
            is_sd_media = (
                (item.get("tran") or "").lower() in {"mmc", "sd"}
                or props.get("ID_DRIVE_FLASH_SD") == "1"
            )
            if (
                item.get("type") == "disk"
                and path
                and not item.get("ro")
                and not mounted
                and not self._is_root_ancestor(path, root_source)
                and is_sd_media
            ):
                devices.append({
                    "path": path,
                    "label": f"{path} | {item.get('size', '')} | SD",
                    "size": self._device_size(path),
                })
        return devices

    def select_sd_card(self):
        """Select a safe whole-disk target in CLI mode."""
        devices = self.list_safe_devices()
        if not devices:
            self.log("No removable writable SD-card device found", "ERROR")
            return None
        for index, device in enumerate(devices, 1):
            self.log(f"  {index}. {device['label']}")
        try:
            selected = int(input("Select target number: ")) - 1
            return devices[selected]["path"]
        except (ValueError, IndexError):
            self.log("Invalid target selection", "ERROR")
            return None
    
    def list_volumes(self):
        """List split volume files with numeric suffixes."""
        if not self.volumes_dir:
            return []
        
        return sorted(
            volume
            for volume in self.volumes_dir.iterdir()
            if volume.is_file()
            and not volume.is_symlink()
            and volume.name.rsplit(".", 1)[-1].isdigit()
        )
    
    def group_volumes_by_base(self, volumes):
        """Group volumes by base filename"""
        groups = {}
        for vol in volumes:
            # Extract base name (remove .001, .002, etc.)
            base = vol.name.rsplit('.', 1)[0]
            if base not in groups:
                groups[base] = []
            groups[base].append(vol)
        return groups
    
    def join_volumes(self, volumes, output_path):
        """Join split volumes into a temporary file, then atomically replace output."""
        if output_path.exists() and output_path.is_symlink():
            raise ValueError(f"Refusing symlink output: {output_path}")
        temporary = output_path.with_name(f".{output_path.name}.partial")
        self.log(f"Joining {len(volumes)} volumes into {output_path.name}")
        try:
            with open(temporary, 'wb') as out_file:
                for vol in sorted(volumes):
                    if vol.is_symlink() or not vol.is_file():
                        raise ValueError(f"Refusing unsafe volume: {vol}")
                    self.log(f"  Reading: {vol.name}")
                    with open(vol, 'rb') as vf:
                        shutil.copyfileobj(vf, out_file, length=4 * 1024 * 1024)
            os.replace(temporary, output_path)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        self.log(f"Created: {output_path.name} ({output_path.stat().st_size/1024/1024:.1f}MB)")
        return True
    
    def join_all_volumes(self):
        """Join split volumes and copy complete files safely."""
        if not self.volumes_dir or not self.output_dir:
            self.log("Error: Volumes or output directory not set", "ERROR")
            return False
        volumes_root = self.volumes_dir.resolve()
        output_root = self.output_dir.resolve()
        if output_root == volumes_root or volumes_root in output_root.parents:
            self.log("Error: Output directory cannot be inside volumes directory", "ERROR")
            return False
        
        volumes = self.list_volumes()
        groups = self.group_volumes_by_base(volumes)
        complete_files = [
            item for item in self.volumes_dir.iterdir()
            if item.is_file()
            and not item.is_symlink()
            and not item.name.startswith("SHA256SUMS")
            and not item.name.rsplit(".", 1)[-1].isdigit()
        ]
        if not groups and not complete_files:
            self.log("Error: No distribution files found", "ERROR")
            return False
        
        self.log(f"Joining {len(groups)} split file(s)")
        for base, vols in groups.items():
            self.join_volumes(vols, self.output_dir / base)
        
        for complete_file in complete_files:
            # GitHub releases contain the complete rkupdate image alongside
            # compressed convenience archives. Normalize the flashable image
            # to the name used by the Linux flashing path.
            destination_name = (
                "update.img"
                if complete_file.suffix.lower() == ".img"
                and "rkupdate" in complete_file.stem.lower()
                else complete_file.name
            )
            destination = self.output_dir / destination_name
            if destination.exists() and destination.is_symlink():
                raise ValueError(f"Refusing symlink output: {destination}")
            temporary = destination.with_name(f".{destination.name}.partial")
            shutil.copyfile(complete_file, temporary)
            os.replace(temporary, destination)
            self.log(f"Copied: {complete_file.name} -> {destination.name}")
        
        return True
    
    def verify_checksums(self):
        """Verify SHA256 checksums and reject unsafe manifest paths."""
        candidates = (
            "SHA256SUMS.txt",
            f"SHA256SUMS-{VERSION}.txt",
        )
        checksums_file = next(
            (
                self.volumes_dir / name
                for name in candidates
                if (self.volumes_dir / name).is_file()
                and not (self.volumes_dir / name).is_symlink()
            ),
            None,
        )
        if checksums_file is None:
            self.log(
                "Error: SHA256SUMS.txt or the versioned SHA256SUMS manifest is required",
                "ERROR",
            )
            return False

        self.log("Verifying checksums...")
        verified = 0
        with open(checksums_file, "r", encoding="utf-8") as checksums:
            for line in checksums:
                line = line.strip()
                if not line:
                    continue
                parts = line.split("  ", 1)
                if len(parts) != 2:
                    self.log(f"Error: Invalid checksum entry: {line}", "ERROR")
                    return False

                expected_hash, filename = parts
                if (
                    len(expected_hash) != 64
                    or any(char not in "0123456789abcdefABCDEF" for char in expected_hash)
                    or Path(filename).name != filename
                    or Path(filename).is_absolute()
                ):
                    self.log(f"Error: Unsafe checksum filename: {filename}", "ERROR")
                    return False
                filepath = self.volumes_dir / filename
                if not filepath.is_file() or filepath.is_symlink():
                    self.log(f"Error: Missing or unsafe file: {filename}", "ERROR")
                    return False

                sha256 = hashlib.sha256()
                with open(filepath, "rb") as source:
                    while chunk := source.read(4 * 1024 * 1024):
                        sha256.update(chunk)

                if sha256.hexdigest().lower() != expected_hash.lower():
                    self.log(f"Error: {filename} (checksum mismatch)", "ERROR")
                    return False
                verified += 1
                self.log(f"  OK {filename}")

        if not verified:
            self.log("Error: SHA256SUMS.txt contains no entries", "ERROR")
            return False
        self.log("All checksums verified successfully!")
        return True

    def _device_size(self, device):
        """Return whole-device size in bytes, or zero when unknown."""
        if IS_MAC:
            result = subprocess.run(
                ["diskutil", "info", "-plist", device],
                capture_output=True, text=True, check=False,
            )
            match = re.search(r"<key>DiskSize</key>\s*<real>(\d+)</real>", result.stdout)
            return int(match.group(1)) if match else 0
        result = subprocess.run(
            ["lsblk", "-bno", "SIZE", device],
            capture_output=True, text=True, check=False,
        )
        try:
            return int(result.stdout.strip())
        except ValueError:
            return 0

    def _unmount_partitions(self, device):
        """Unmount only mounted child partitions of the already-approved disk."""
        result = subprocess.run(
            ["lsblk", "--json", "-o", "PATH,TYPE,MOUNTPOINTS", device],
            capture_output=True, text=True, check=False,
        )
        if result.returncode != 0:
            self.log("Error: Could not inspect target partitions", "ERROR")
            return False
        try:
            tree = json.loads(result.stdout).get("blockdevices", [])
        except json.JSONDecodeError:
            self.log("Error: Invalid partition information", "ERROR")
            return False

        partitions = []
        def visit(nodes):
            for node in nodes:
                if node.get("type") != "disk":
                    partitions.extend(
                        mountpoint for mountpoint in node.get("mountpoints", []) if mountpoint
                    )
                visit(node.get("children", []))
        visit(tree)
        for mountpoint in partitions:
            result = subprocess.run(
                ["sudo", "umount", "--", mountpoint],
                capture_output=True, text=True, check=False,
            )
            if result.returncode != 0:
                self.log(f"Error: Could not unmount {mountpoint}: {result.stderr.strip()}", "ERROR")
                return False
        return True

    def _hash_file(self, path):
        digest = hashlib.sha256()
        with open(path, "rb") as source:
            while chunk := source.read(4 * 1024 * 1024):
                digest.update(chunk)
        return digest.hexdigest()

    def _hash_device_prefix(self, device, size):
        """Hash exactly the image-sized prefix of a raw device."""
        block_size = 4 * 1024 * 1024
        count = (size + block_size - 1) // block_size
        process = subprocess.Popen(
            ["sudo", "dd", f"if={device}", "bs=4M", f"count={count}", "status=none"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        digest = hashlib.sha256()
        remaining = size
        while remaining:
            chunk = process.stdout.read(min(block_size, remaining))
            if not chunk:
                break
            digest.update(chunk)
            remaining -= len(chunk)
        _, stderr = process.communicate()
        if process.returncode != 0 or remaining:
            self.log(f"Error: Could not verify written data: {stderr.decode(errors='replace').strip()}", "ERROR")
            return None
        return digest.hexdigest()

    def flash_to_sd_card(self, device):
        """Flash joined image to a freshly revalidated Linux SD-card target."""
        if not device:
            self.log("Error: No SD card device selected", "ERROR")
            return False
        image_file = self.output_dir / "update.img"
        if not image_file.is_file() or image_file.is_symlink():
            self.log("Error: Joined update.img not found or unsafe", "ERROR")
            return False
        if not IS_LINUX:
            self.log(
                "Raw flashing is disabled on this platform. "
                "Use Etcher or Rufus with the joined update.img.",
                "ERROR",
            )
            return False
        if shutil.which("sudo") is None:
            self.log("Error: sudo is required for Linux flashing", "ERROR")
            return False

        safe_devices = {item["path"]: item for item in self.list_safe_devices()}
        selected = safe_devices.get(device)
        if not selected:
            self.log("Refusing target: it is not a detected removable SD disk", "ERROR")
            return False
        image_size = image_file.stat().st_size
        initial_size = selected["size"]
        if not initial_size or image_size > initial_size:
            self.log("Refusing target: SD card is smaller than update.img", "ERROR")
            return False
        if not self._unmount_partitions(device):
            return False
        current_size = self._device_size(device)
        if current_size != initial_size:
            self.log("Refusing target: device identity or size changed", "ERROR")
            return False

        self.log(f"Flashing {image_file.name} to {device}")
        self.log(f"WARNING: This erases the whole SD disk {device}!")
        try:
            cmd = [
                "sudo", "dd", f"if={image_file}", f"of={device}",
                "bs=4M", "status=progress", "oflag=sync",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode != 0:
                self.log(f"Error: {result.stderr.strip()}", "ERROR")
                return False
            subprocess.run(["sync"], check=False)
            expected_hash = self._hash_file(image_file)
            actual_hash = self._hash_device_prefix(device, image_size)
            if actual_hash != expected_hash:
                self.log("Error: Post-write verification failed", "ERROR")
                return False
            self.log("Flashing and post-write verification completed successfully!")
            return True
        except Exception as error:
            self.log(f"Error: {error}", "ERROR")
            return False
    
    
    def run(self):
        """Run the installer"""
        self.log(f"RADXOID Installer {VERSION}")
        self.log(f"Platform: {PLATFORM}")
        self.log("")
        
        # Step 1: Select volumes directory
        if not self.select_volumes_dir():
            return False
        
        # Step 2: Verify checksums
        if not self.verify_checksums():
            return False
        
        # Step 3: Select output directory
        if not self.select_output_dir():
            return False
        
        # Step 4: Join volumes
        if not self.join_all_volumes():
            return False
        
        self.log("\n✅ All volumes joined successfully!")
        self.log(f"Files are in: {self.output_dir}")
        
        return True


class RADXOIDGUI:
    """GUI for the installer"""
    
    def __init__(self, root):
        self.root = root
        self.root.title(f"RADXOID Installer {VERSION}")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Set window icon (if available)
        try:
            self.root.iconbitmap(default='radxoid.ico')
        except:
            pass
        
        # Installer instance
        self.installer = RADXOIDInstaller()
        
        # Create UI
        self.create_ui()
        
        # Start log processing thread
        self.running = True
        self.log_thread = threading.Thread(target=self.process_logs, daemon=True)
        self.log_thread.start()
    
    def create_ui(self):
        """Create the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text=f"RADXOID {VERSION} Installer",
            font=('Helvetica', 16, 'bold')
        )
        title_label.pack(pady=10)
        
        # Description
        desc_label = ttk.Label(
            main_frame,
            text="Lean Android 11 for Radxa ROCK 3A (RK3568) - Gaming & Emulation",
            font=('Helvetica', 10)
        )
        desc_label.pack(pady=5)
        
        # Progress frame
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=10)
        
        # Step indicators
        self.steps = [
            "Select Volumes",
            "Verify Checksums",
            "Select Output",
            "Join Volumes",
            "Flash to SD Card"
        ]
        self.current_step = 0
        
        self.step_labels = []
        for i, step in enumerate(self.steps):
            label = ttk.Label(progress_frame, text=step, padding=5)
            label.grid(row=0, column=i, padx=5)
            self.step_labels.append(label)
        
        # Highlight current step
        self.update_step_indicator()
        
        # Main content frame
        self.content_frame = ttk.Frame(main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Log text
        self.log_text = scrolledtext.ScrolledText(
            self.content_frame,
            wrap=tk.WORD,
            height=15,
            state='disabled'
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Buttons
        self.prev_button = ttk.Button(
            button_frame,
            text="Back",
            command=self.prev_step,
            state='disabled'
        )
        self.prev_button.pack(side=tk.LEFT, padx=5)
        
        self.next_button = ttk.Button(
            button_frame,
            text="Next",
            command=self.next_step
        )
        self.next_button.pack(side=tk.RIGHT, padx=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.pack(fill=tk.X, pady=(0, 10))
        
        # Start with step 0
        self.update_content_frame()
    
    def update_step_indicator(self):
        """Update step indicator"""
        for i, label in enumerate(self.step_labels):
            if i == self.current_step:
                label.config(foreground='blue', font=('Helvetica', 10, 'bold'))
            elif i < self.current_step:
                label.config(foreground='green')
            else:
                label.config(foreground='gray')
    
    def update_content_frame(self):
        """Update the content based on current step"""
        # Clear any existing content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Step 0: Select Volumes Directory
        if self.current_step == 0:
            ttk.Label(
                self.content_frame,
                text="Select the directory containing the volume files",
                padding=5
            ).pack(pady=5)
            
            ttk.Button(
                self.content_frame,
                text="Browse...",
                command=self.browse_volumes
            ).pack(pady=5)
            
            if self.installer.volumes_dir:
                ttk.Label(
                    self.content_frame,
                    text=f"Selected: {self.installer.volumes_dir}",
                    foreground='green'
                ).pack(pady=5)
        
        # Step 1: Verify Checksums
        elif self.current_step == 1:
            ttk.Label(
                self.content_frame,
                text="Verifying checksums of all volume files...",
                padding=5
            ).pack(pady=5)
            
            if not hasattr(self, 'checksum_result'):
                self.checksum_result = None
                threading.Thread(target=self.run_checksums, daemon=True).start()
        
        # Step 2: Select Output Directory
        elif self.current_step == 2:
            ttk.Label(
                self.content_frame,
                text="Select the directory to save joined files",
                padding=5
            ).pack(pady=5)
            
            ttk.Button(
                self.content_frame,
                text="Browse...",
                command=self.browse_output
            ).pack(pady=5)
            
            if self.installer.output_dir:
                ttk.Label(
                    self.content_frame,
                    text=f"Selected: {self.installer.output_dir}",
                    foreground='green'
                ).pack(pady=5)
        
        # Step 3: Join Volumes
        elif self.current_step == 3:
            ttk.Label(
                self.content_frame,
                text="Joining all volumes into original files...",
                padding=5,
            ).pack(pady=5)
            
            if not hasattr(self, 'join_result'):
                self.join_result = None
                threading.Thread(target=self.run_join, daemon=True).start()
            elif self.join_result and self.installer.output_dir:
                ttk.Button(
                    self.content_frame,
                    text="Open output folder",
                    command=self.open_output,
                ).pack(pady=10)
        
        # Step 4: Flash to SD Card
        elif self.current_step == 4:
            ttk.Label(
                self.content_frame,
                text="Flash the joined image to SD card",
                padding=5,
            ).pack(pady=5)
            ttk.Button(
                self.content_frame,
                text="Refresh SD-card list",
                command=self.refresh_devices,
            ).pack(pady=5)
            
            if IS_WINDOWS:
                ttk.Label(
                    self.content_frame,
                    text="Windows does not raw-flash disks. Use Rufus or Etcher "
                    "with the joined update.img.",
                    foreground="blue",
                    padding=5,
                    wraplength=650,
                ).pack(pady=20)
                return

            devices = self.installer.list_safe_devices()
            if not devices:
                ttk.Label(
                    self.content_frame,
                    text="No removable writable SD-card device detected.",
                    foreground="red",
                    padding=5,
                ).pack(pady=5)
                return

            ttk.Label(
                self.content_frame,
                text="Only removable, writable SD whole disks are shown. "
                "System and mounted disks are excluded.",
                foreground="green",
                padding=5,
                wraplength=650,
            ).pack(pady=5)
            self.device_options = {item["label"]: item["path"] for item in devices}
            self.device_var = tk.StringVar()
            self.device_combo = ttk.Combobox(
                self.content_frame,
                textvariable=self.device_var,
                values=list(self.device_options),
                state="readonly",
                width=78,
            )
            self.device_combo.pack(pady=5)
            ttk.Button(
                self.content_frame,
                text="Select target",
                command=self.select_gui_device,
            ).pack(pady=5)
            ttk.Label(
                self.content_frame,
                text="Flashing erases the selected whole disk. "
                "Confirm by typing ERASE <device>.",
                foreground="red",
                padding=5,
                wraplength=650,
            ).pack(pady=5)
            if getattr(self, "sd_card_device", ""):
                ttk.Label(
                    self.content_frame,
                    text=f"Selected: {self.sd_card_device}",
                    foreground="green",
                ).pack(pady=5)
                ttk.Button(
                    self.content_frame,
                    text="Flash Now",
                    command=self.run_flash,
                ).pack(pady=5)
    def process_logs(self):
        """Process log messages from the installer"""
        while self.running:
            try:
                message = self.installer.log_queue.get(timeout=0.1)
                self.log_text.config(state='normal')
                self.log_text.insert(tk.END, message + "\n")
                self.log_text.see(tk.END)
                self.log_text.config(state='disabled')
                self.status_var.set(message.split(']')[-1].strip())
            except queue.Empty:
                pass
    
    def browse_volumes(self):
        """Browse for volumes directory"""
        if self.installer.select_volumes_dir():
            self.update_content_frame()
    
    def browse_output(self):
        """Browse for output directory"""
        if self.installer.select_output_dir():
            self.update_content_frame()
    def open_output(self):
        """Open the joined-file directory in the platform file manager."""
        output_dir = self.installer.output_dir
        if not output_dir:
            return
        try:
            if IS_WINDOWS:
                os.startfile(str(output_dir))
            else:
                subprocess.Popen(["xdg-open", str(output_dir)])
        except (OSError, AttributeError) as error:
            self.installer.log(f"Could not open output directory: {error}", "WARNING")

    def refresh_devices(self):
        """Refresh the removable SD-card list after insertion or removal."""
        self.sd_card_device = ""
        self.update_content_frame()
    
    def run_checksums(self):
        """Run checksum verification"""
        self.installer.log("Starting checksum verification...")
        self.checksum_result = self.installer.verify_checksums()
        self.installer.log("Checksum verification completed")
        self.update_content_frame()
    
    def run_join(self):
        """Run volume joining"""
        self.installer.log("Starting volume joining...")
        self.join_result = self.installer.join_all_volumes()
        self.installer.log("Volume joining completed")
        self.update_content_frame()
    
    def select_gui_device(self):
        """Store the device selected in the safe-device combobox."""
        label = self.device_var.get()
        device = self.device_options.get(label)
        if device:
            self.sd_card_device = device
            self.update_content_frame()

    def run_flash(self):
        """Require an exact confirmation before flashing."""
        device = getattr(self, "sd_card_device", "")
        expected = f"ERASE {device}"
        typed = simpledialog.askstring(
            "Final confirmation",
            f"This erases the whole removable disk:\n\n{device}\n\n"
            f"Type exactly:\n{expected}",
        )
        if typed != expected:
            messagebox.showerror("Cancelled", "Exact confirmation did not match.")
            return
        self.installer.log(f"Starting flash to {device}...")
        result = self.installer.flash_to_sd_card(device)
        if result:
            messagebox.showinfo("Success", "Flashing completed successfully!")
        else:
            messagebox.showerror("Error", "Flashing was refused or failed.")
    
    def next_step(self):
        """Go to next step"""
        # Validate current step
        if self.current_step == 0 and not self.installer.volumes_dir:
            messagebox.showerror("Error", "Please select volumes directory")
            return
        
        if self.current_step == 1:
            if not hasattr(self, 'checksum_result') or self.checksum_result is None:
                messagebox.showerror("Error", "Checksum verification in progress...")
                return
            if not self.checksum_result:
                messagebox.showerror("Error", "Checksum verification failed")
                return
        
        if self.current_step == 2 and not self.installer.output_dir:
            messagebox.showerror("Error", "Please select output directory")
            return
        
        if self.current_step == 3:
            if not hasattr(self, 'join_result') or self.join_result is None:
                messagebox.showerror("Error", "Volume joining in progress...")
                return
            if not self.join_result:
                messagebox.showerror("Error", "Volume joining failed")
                return
        
        # Move to next step
        self.current_step += 1
        self.update_step_indicator()
        self.update_content_frame()
        
        # Update buttons
        self.prev_button.config(state='normal')
        
        if self.current_step == len(self.steps) - 1:
            self.next_button.config(text="Finish")
    
    def prev_step(self):
        """Go to previous step"""
        if self.current_step > 0:
            self.current_step -= 1
            self.update_step_indicator()
            self.update_content_frame()
            
            if self.current_step < len(self.steps) - 1:
                self.next_button.config(text="Next")
    
    def run_app(self):
        """Run the GUI application"""
        self.root.mainloop()


def main():
    """Main entry point"""
    if GUI_AVAILABLE:
        # Run GUI
        root = tk.Tk()
        app = RADXOIDGUI(root)
        app.run_app()
    else:
        # Run CLI
        print("RADXOID Installer - CLI Mode")
        print(f"Version: {VERSION}")
        print(f"Platform: {PLATFORM}")
        print()
        
        installer = RADXOIDInstaller()
        
        # Run steps
        if installer.select_volumes_dir():
            if installer.verify_checksums():
                if installer.select_output_dir():
                    if installer.join_all_volumes():
                        print("\n✅ All done!")
                        print(f"Files are in: {installer.output_dir}")
                        
                        # Ask if user wants to flash
                        if IS_WINDOWS:
                            print("\nNote: Windows joins only. Flash update.img with Rufus or Etcher.")
                        else:
                            device = installer.select_sd_card()
                            if device:
                                if input(f"Flash to {device}? This will ERASE all data! (y/n): ").lower() == 'y':
                                    installer.flash_to_sd_card(device)
    

if __name__ == "__main__":
    main()
