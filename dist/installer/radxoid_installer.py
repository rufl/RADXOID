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
VERSION = "v1.0.0"
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
    from tkinter import ttk, filedialog, messagebox, scrolledtext
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
    
    def select_sd_card(self):
        """Select SD card device"""
        if IS_WINDOWS:
            # Windows: List physical drives
            try:
                result = subprocess.run(
                    ['wmic', 'diskdrive', 'list', 'brief'],
                    capture_output=True, text=True
                )
                drives = [line.split()[0] for line in result.stdout.strip().split('\n')[1:]]
                self.log("Available drives:")
                for i, drive in enumerate(drives):
                    self.log(f"  {i+1}. {drive}")
                
                if GUI_AVAILABLE:
                    # Show dialog in GUI
                    return None  # Will be handled by GUI
                else:
                    choice = input("Select drive number: ")
                    return drives[int(choice)-1]
            except Exception as e:
                self.log(f"Error listing drives: {e}", "ERROR")
                return None
        
        elif IS_LINUX or IS_MAC:
            # Linux/macOS: List block devices
            try:
                result = subprocess.run(
                    ['lsblk', '-d', '-n', '-o', 'NAME,SIZE,MODEL'],
                    capture_output=True, text=True
                )
                devices = []
                for line in result.stdout.strip().split('\n'):
                    parts = line.split()
                    if len(parts) >= 2:
                        devices.append(parts[0])
                
                self.log("Available block devices:")
                for i, device in enumerate(devices):
                    self.log(f"  {i+1}. /dev/{device}")
                
                if GUI_AVAILABLE:
                    return None  # Will be handled by GUI
                else:
                    choice = input("Select device number (e.g., sdb): ")
                    return f"/dev/{devices[int(choice)-1]}"
            except Exception as e:
                self.log(f"Error listing devices: {e}", "ERROR")
                return None
        
        return None
    
    def list_volumes(self):
        """List split volume files with numeric suffixes."""
        if not self.volumes_dir:
            return []
        
        return sorted(
            volume
            for volume in self.volumes_dir.iterdir()
            if volume.is_file() and volume.name.rsplit(".", 1)[-1].isdigit()
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
        """Join volume files into original file"""
        self.log(f"Joining {len(volumes)} volumes into {output_path.name}")
        
        with open(output_path, 'wb') as out_file:
            for vol in sorted(volumes):
                self.log(f"  Reading: {vol.name}")
                with open(vol, 'rb') as vf:
                    out_file.write(vf.read())
        
        self.log(f"  Created: {output_path.name} ({output_path.stat().st_size/1024/1024:.1f}MB)")
        return True
    
    def join_all_volumes(self):
        """Join split volumes and copy complete files into the output directory."""
        if not self.volumes_dir or not self.output_dir:
            self.log("Error: Volumes or output directory not set", "ERROR")
            return False
        
        volumes = self.list_volumes()
        groups = self.group_volumes_by_base(volumes)
        complete_files = [
            item for item in self.volumes_dir.iterdir()
            if item.is_file()
            and item.name != "SHA256SUMS.txt"
            and not item.name.rsplit(".", 1)[-1].isdigit()
        ]
        
        if not groups and not complete_files:
            self.log("Error: No distribution files found", "ERROR")
            return False
        
        self.log(f"Joining {len(groups)} split file(s)")
        for base, vols in groups.items():
            self.join_volumes(vols, self.output_dir / base)
        
        for complete_file in complete_files:
            shutil.copy2(complete_file, self.output_dir / complete_file.name)
            self.log(f"Copied: {complete_file.name}")
        
        return True
    
    def verify_checksums(self):
        """Verify SHA256 checksums"""
        checksums_file = self.volumes_dir / "SHA256SUMS.txt"
        if not checksums_file.exists():
            self.log("Warning: No checksums file found", "WARNING")
            return True
        
        self.log("Verifying checksums...")
        with open(checksums_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split("  ", 1)
                if len(parts) != 2:
                    continue
                
                expected_hash, filename = parts
                filepath = self.volumes_dir / filename
                
                if not filepath.exists():
                    self.log(f"Error: Missing file: {filename}", "ERROR")
                    return False
                
                sha256 = hashlib.sha256()
                with open(filepath, 'rb') as f:
                    while chunk := f.read(8192):
                        sha256.update(chunk)
                
                actual_hash = sha256.hexdigest()
                if actual_hash == expected_hash:
                    self.log(f"  ✅ {filename}")
                else:
                    self.log(f"  ❌ {filename} (checksum mismatch)", "ERROR")
                    return False
        
        self.log("All checksums verified successfully!")
        return True
    
    def flash_to_sd_card(self, device):
        """Flash joined image to SD card"""
        if not device:
            self.log("Error: No SD card device selected", "ERROR")
            return False
        
        # Only update.img is a complete flashable board image.
        image_file = self.output_dir / "update.img"
        if not image_file.is_file():
            self.log("Error: Joined update.img not found", "ERROR")
            return False
        self.log(f"Flashing {image_file.name} to {device}")
        
        if IS_WINDOWS:
            # Windows: Use dd for Windows
            self.log("Flashing (Windows)...")
            try:
                # Note: This is a placeholder - actual Windows flashing requires admin
                self.log("Note: On Windows, use Rufus or dd for Windows with admin privileges")
                self.log(f"Command: dd if={image_file} of={device} bs=1M --progress")
                return True
            except Exception as e:
                self.log(f"Error: {e}", "ERROR")
                return False
        
        else:
            # Linux/macOS: Use dd
            self.log("Flashing (Linux/macOS)...")
            self.log(f"WARNING: This will erase {device}!")
            
            try:
                cmd = [
                    'sudo', 'dd',
                    f'if={image_file}',
                    f'of={device}',
                    'bs=4M',
                    'status=progress',
                    'oflag=sync'
                ]
                
                # For macOS, use rdisk instead of disk
                if IS_MAC and device.startswith('/dev/disk'):
                    device = device.replace('/dev/disk', '/dev/rdisk')
                    cmd[3] = device
                
                self.log(f"Executing: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.log("Flashing completed successfully!")
                    self.log("Waiting for sync...")
                    subprocess.run(['sync'])
                    return True
                else:
                    self.log(f"Error: {result.stderr}", "ERROR")
                    return False
            except Exception as e:
                self.log(f"Error: {e}", "ERROR")
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
            text=f"RADXOID v{VERSION} Installer",
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
            content_frame,
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
                padding=5
            ).pack(pady=5)
            
            if not hasattr(self, 'join_result'):
                self.join_result = None
                threading.Thread(target=self.run_join, daemon=True).start()
        
        # Step 4: Flash to SD Card
        elif self.current_step == 4:
            ttk.Label(
                self.content_frame,
                text="Flash the joined image to SD card",
                padding=5
            ).pack(pady=5)
            
            if IS_WINDOWS:
                ttk.Label(
                    self.content_frame,
                    text="Note: On Windows, use Rufus or dd for Windows with admin privileges",
                    foreground='orange',
                    padding=5
                ).pack(pady=5)
            else:
                ttk.Label(
                    self.content_frame,
                    text="WARNING: This will erase the selected device!",
                    foreground='red',
                    padding=5
                ).pack(pady=5)
                
                ttk.Button(
                    self.content_frame,
                    text="Select SD Card Device",
                    command=self.select_sd_card
                ).pack(pady=5)
                
                if hasattr(self, 'sd_card_device') and self.sd_card_device:
                    ttk.Label(
                        self.content_frame,
                        text=f"Selected: {self.sd_card_device}",
                        foreground='green'
                    ).pack(pady=5)
                    
                    ttk.Button(
                        self.content_frame,
                        text="Flash Now",
                        command=self.run_flash,
                        style='Danger.TButton'
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
    
    def select_sd_card(self):
        """Select SD card device"""
        device = self.installer.select_sd_card()
        if device:
            self.sd_card_device = device
            self.update_content_frame()
    
    def run_flash(self):
        """Run flashing"""
        if messagebox.askyesno(
            "Confirm",
            f"Are you sure you want to flash to {self.sd_card_device}?\n\nThis will ERASE all data on the device!"
        ):
            self.installer.log(f"Starting flash to {self.sd_card_device}...")
            result = self.installer.flash_to_sd_card(self.sd_card_device)
            if result:
                messagebox.showinfo("Success", "Flashing completed successfully!")
            else:
                messagebox.showerror("Error", "Flashing failed!")
    
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
                            print("\nNote: On Windows, use Rufus or dd for Windows with admin privileges")
                        else:
                            device = installer.select_sd_card()
                            if device:
                                if input(f"Flash to {device}? This will ERASE all data! (y/n): ").lower() == 'y':
                                    installer.flash_to_sd_card(device)
    

if __name__ == "__main__":
    main()
