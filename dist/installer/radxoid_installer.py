#!/usr/bin/env python3
"""
RADXOID Installer GUI
Cross-platform installer for RADXOID distribution
Supports Windows and Linux
"""

import ctypes
from ctypes import wintypes
import hashlib
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import zipfile
from datetime import datetime
from pathlib import Path

# Configuration
VERSION = "v1.0.22"

# Platform detection
PLATFORM = sys.platform
IS_WINDOWS = PLATFORM.startswith('win')
IS_LINUX = PLATFORM.startswith('linux')

def _ensure_windows_elevation():
    """Request UAC elevation for the source .pyw fallback."""
    if not IS_WINDOWS:
        return True
    try:
        if ctypes.windll.shell32.IsUserAnAdmin():
            return True
        arguments = list(sys.argv[1:])
        if not getattr(sys, "frozen", False):
            arguments.insert(0, str(Path(__file__).resolve()))
        result = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            sys.executable,
            subprocess.list2cmdline(arguments),
            None,
            1,
        )
    except (AttributeError, OSError) as error:
        raise OSError(f"Could not request Administrator privileges: {error}") from error
    if result <= 32:
        raise OSError(
            f"Windows refused the Administrator elevation request (code {result})"
        )
    return False

class _WindowsRawDevice:
    """Minimal unbuffered file object backed only by Win32 device APIs."""

    def __init__(self, kernel32, handle, path, writable):
        self._kernel32 = kernel32
        self._handle = handle
        self._path = path
        self._writable = writable
        self._closed = False

    def __enter__(self):
        return self

    def __exit__(self, _exception_type, _exception, _traceback):
        self.close()

    def _raise_last_error(self, operation):
        error_code = ctypes.get_last_error()
        detail = ctypes.FormatError(error_code).strip()
        raise RuntimeError(
            f"{operation} failed for {self._path} "
            f"(Windows error {error_code}): {detail}"
        )

    def readinto(self, buffer):
        if self._closed:
            raise ValueError("I/O operation on closed raw device")
        view = memoryview(buffer).cast("B")
        if view.readonly:
            raise TypeError("readinto requires a writable buffer")
        raw_buffer = (ctypes.c_char * len(view)).from_buffer(view)
        bytes_read = wintypes.DWORD()
        if not self._kernel32.ReadFile(
            self._handle,
            raw_buffer,
            len(view),
            ctypes.byref(bytes_read),
            None,
        ):
            self._raise_last_error("ReadFile")
        return bytes_read.value

    def write(self, buffer):
        if self._closed:
            raise ValueError("I/O operation on closed raw device")
        if not self._writable:
            raise OSError(f"Raw device is read-only: {self._path}")
        view = memoryview(buffer).cast("B")
        if view.readonly:
            raise TypeError("WriteFile requires a writable buffer")
        raw_buffer = (ctypes.c_char * len(view)).from_buffer(view)
        bytes_written = wintypes.DWORD()
        if not self._kernel32.WriteFile(
            self._handle,
            raw_buffer,
            len(view),
            ctypes.byref(bytes_written),
            None,
        ):
            self._raise_last_error("WriteFile")
        return bytes_written.value

    def flush(self):
        if self._closed:
            raise ValueError("I/O operation on closed raw device")
        if self._writable and not self._kernel32.FlushFileBuffers(self._handle):
            self._raise_last_error("FlushFileBuffers")

    def close(self):
        if not self._closed:
            self._kernel32.CloseHandle(self._handle)
            self._closed = True


# GUI imports
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext, simpledialog, ttk
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False


class RADXOIDInstaller:
    """Main installer class"""
    
    def __init__(self):
        self.volumes_dir = None
        self.verified_files = set()
        self.checksum_skipped = False
        self.log_queue = queue.Queue()
        self.log_lock = threading.Lock()
        self.log_path = self._create_session_log()
        self.last_error = None

    @staticmethod
    def _create_session_log():
        """Create a durable per-run log outside the application directory."""
        if IS_WINDOWS:
            base = Path(
                os.environ.get(
                    "LOCALAPPDATA",
                    Path.home() / "AppData" / "Local",
                )
            )
        else:
            base = Path(
                os.environ.get(
                    "XDG_STATE_HOME",
                    Path.home() / ".local" / "state",
                )
            )
        log_dir = base / "RADXOID" / "logs"
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            return log_dir / f"installer-{timestamp}-{os.getpid()}.log"
        except OSError as error:
            print(f"Could not create installer log directory: {error}", file=sys.stderr)
            return None
    
    def log(self, message, level="INFO"):
        """Record a message in the GUI queue, console, and durable log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] [{level}] {message}"
        self.log_queue.put(entry)
        print(entry, flush=True)
        if self.log_path:
            try:
                with (
                    self.log_lock,
                    open(self.log_path, "a", encoding="utf-8") as log_file,
                ):
                    log_file.write(entry + "\n")
            except OSError as error:
                print(f"Could not write installer log: {error}", file=sys.stderr)
                self.log_path = None
    
    def select_volumes_dir(self):
        """Select the directory containing the release assets."""
        if GUI_AVAILABLE:
            selected = filedialog.askdirectory(title="Select RADXOID Release Assets")
        else:
            selected = input("Enter release-assets directory path: ").strip()
        if not selected:
            return False
        assets_dir = Path(selected)
        if not assets_dir.is_dir():
            self.log("Error: Assets directory does not exist", "ERROR")
            return False
        self.volumes_dir = assets_dir
        self.verified_files.clear()
        self.checksum_skipped = False
        self.log(f"Selected release-assets directory: {self.volumes_dir}")
        return True
    
    
    def _has_mountpoints(self, node):
        """Return true when a disk or any child partition is mounted."""
        if any(point for point in (node.get("mountpoints") or []) if point):
            return True
        return any(
            self._has_mountpoints(child)
            for child in (node.get("children") or [])
        )

    def _is_root_ancestor(self, device, root_source):
        """Return true when device contains the mounted root filesystem."""
        if not root_source:
            return False
        try:
            result = subprocess.run(
                ["lsblk", "-s", "-n", "-o", "PATH", device],
                capture_output=True, text=True, check=False,
            )
        except OSError as error:
            self.log(f"Could not inspect root-disk ancestry: {error}", "ERROR")
            return True
        return root_source in result.stdout.split()

    def _udev_properties(self, device):
        try:
            result = subprocess.run(
                ["udevadm", "info", "--query=property", "--name", device],
                capture_output=True, text=True, check=False,
            )
        except OSError as error:
            self.log(f"Could not inspect SD-card identity: {error}", "ERROR")
            return {}
        properties = {}
        for line in result.stdout.splitlines():
            key, separator, value = line.partition("=")
            if separator:
                properties[key] = value
        return properties
    @staticmethod
    def _powershell_executable():
        """Find Windows PowerShell even when a GUI process has a minimal PATH."""
        system_root = os.environ.get("SystemRoot")
        if system_root:
            root = Path(system_root)
            for system_dir in ("System32", "Sysnative"):
                candidate = (
                    root
                    / system_dir
                    / "WindowsPowerShell"
                    / "v1.0"
                    / "powershell.exe"
                )
                if candidate.is_file():
                    return str(candidate)
        for executable in ("powershell.exe", "pwsh.exe", "powershell", "pwsh"):
            candidate = shutil.which(executable)
            if candidate:
                return candidate
        return None

    @staticmethod
    def _is_windows_sd_candidate(item):
        """Accept SD media and card readers without admitting fixed USB disks."""
        unsafe = any(
            value is True or str(value).lower() == "true"
            for value in (
                item.get("IsBoot"),
                item.get("IsSystem"),
                item.get("IsReadOnly"),
                item.get("IsOffline"),
            )
        )
        if unsafe:
            return False
        bus_type = str(item.get("BusType", "")).upper()
        media_type = str(item.get("MediaType", ""))
        descriptor = " ".join(
            str(item.get(field, ""))
            for field in ("Model", "FriendlyName", "PNPDeviceID")
        )
        sd_identity = re.search(
            r"(?i)(?:^|[^A-Z0-9])(?:SD(?:HC|XC)?|MMC)(?:[^A-Z0-9]|$)"
            r"|CARD[\s_-]*READER|MEMORY[\s_-]*CARD",
            descriptor,
        )
        removable_volume = item.get("HasRemovableVolume")
        return (
            bus_type in {"SD", "MMC"}
            or "removable" in media_type.lower()
            or removable_volume is True
            or str(removable_volume).lower() == "true"
            or sd_identity is not None
        )

    def list_safe_devices(self):
        """Return removable SD-card whole disks that are writable and safe."""
        if IS_WINDOWS:
            script = (
                "$items=@(); Get-Disk | ForEach-Object { $disk=$_; "
                "$drive=Get-CimInstance Win32_DiskDrive "
                "-Filter ('Index=' + $disk.Number); "
                "$hasRemovableVolume=@(Get-Partition -DiskNumber $disk.Number "
                "-ErrorAction SilentlyContinue | Get-Volume "
                "-ErrorAction SilentlyContinue | Where-Object "
                "{$_.DriveType -eq 'Removable'}).Count -gt 0; "
                "$items += [pscustomobject]@{Number=$disk.Number; "
                "Size=$disk.Size; Model=[string]$drive.Model; "
                "FriendlyName=[string]$disk.FriendlyName; "
                "MediaType=[string]$drive.MediaType; "
                "PNPDeviceID=[string]$drive.PNPDeviceID; "
                "BusType=[string]$disk.BusType; "
                "HasRemovableVolume=[bool]$hasRemovableVolume; "
                "IsBoot=[bool]$disk.IsBoot; IsSystem=[bool]$disk.IsSystem; "
                "IsReadOnly=[bool]$disk.IsReadOnly; "
                "IsOffline=[bool]$disk.IsOffline; "
                "UniqueId=[string]$disk.UniqueId; "
                "SerialNumber=[string]$drive.SerialNumber} }; "
                "$items | ConvertTo-Json -Compress"
            )
            powershell = self._powershell_executable()
            if not powershell:
                self.log("Could not find Windows PowerShell", "ERROR")
                return []
            try:
                result = subprocess.run(
                    [powershell, "-NoProfile", "-NonInteractive", "-Command", script],
                    capture_output=True, text=True, check=False,
                )
            except OSError as error:
                self.log(f"Could not start PowerShell: {error}", "ERROR")
                return []
            if result.returncode != 0:
                self.log(
                    f"Could not enumerate Windows SD cards: "
                    f"{result.stderr.strip()}",
                    "ERROR",
                )
                return []
            if not result.stdout.strip():
                return []
            try:
                data = json.loads(result.stdout)
            except json.JSONDecodeError as error:
                self.log(f"Invalid Windows disk information: {error}", "ERROR")
                return []
            if isinstance(data, dict):
                data = [data]
            devices = []
            for item in data:
                number = item.get("Number")
                size = int(item.get("Size") or 0)
                model = str(
                    item.get("Model") or item.get("FriendlyName") or "unknown"
                ).strip()
                eligible = self._is_windows_sd_candidate(item)
                self.log(
                    f"Windows disk scan: PhysicalDrive{number} | "
                    f"{size / 1024**3:.1f} GiB | {model} | "
                    f"bus={item.get('BusType', 'unknown')} | "
                    f"media={item.get('MediaType', 'unknown')} | "
                    f"removable-volume={item.get('HasRemovableVolume', False)} | "
                    f"{'eligible' if eligible else 'excluded'}"
                )
                if not eligible:
                    continue
                devices.append({
                    "path": f"\\\\.\\PhysicalDrive{number}",
                    "label": f"\\\\.\\PhysicalDrive{number} | "
                    f"{size / 1024**3:.1f} GiB | {model} | "
                    f"{item.get('BusType', 'unknown')} SD/removable",
                    "size": size,
                    "identity": (
                        f"{item.get('UniqueId', '')}|"
                        f"{item.get('SerialNumber', '')}"
                    ),
                })
            return devices

        if not IS_LINUX:
            return []
        try:
            result = subprocess.run(
                ["lsblk", "--json", "-o",
                 "PATH,NAME,TYPE,SIZE,RM,RO,TRAN,MOUNTPOINTS,MODEL,SERIAL,WWN"],
                capture_output=True, text=True, check=False,
            )
        except OSError as error:
            self.log(f"Could not start lsblk: {error}", "ERROR")
            return []
        if result.returncode != 0:
            self.log(
                f"Could not enumerate Linux SD cards: {result.stderr.strip()}",
                "ERROR",
            )
            return []
        try:
            root_source = subprocess.run(
                ["findmnt", "-n", "-o", "SOURCE", "/"],
                capture_output=True, text=True, check=False,
            ).stdout.strip()
        except OSError as error:
            self.log(f"Could not identify the system disk: {error}", "ERROR")
            return []
        try:
            data = json.loads(result.stdout).get("blockdevices", [])
        except json.JSONDecodeError as error:
            self.log(f"Invalid Linux disk information: {error}", "ERROR")
            return []
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
                and not self._is_root_ancestor(path, root_source)
                and is_sd_media
            ):
                identity = "|".join(
                    str(value or "")
                    for value in (
                        item.get("serial"),
                        item.get("wwn"),
                        props.get("ID_SERIAL_SHORT"),
                        props.get("ID_SERIAL"),
                    )
                )
                devices.append({
                    "path": path,
                    "label": f"{path} | {item.get('size', '')} | "
                    f"{(item.get('model') or 'SD').strip()}"
                    f"{' mounted' if mounted else ''}",
                    "size": self._device_size(path),
                    "identity": identity,
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
            if selected < 0:
                raise IndexError
            return devices[selected]["path"]
        except (ValueError, IndexError):
            self.log("Invalid target selection", "ERROR")
            return None
    
    def inspect_sd_image(self):
        """Return the verified GPT archive and its single raw-image member."""
        if not self.volumes_dir:
            self.log("Error: Release-assets directory is not selected", "ERROR")
            return None
        if self.verified_files:
            candidates = [
                path for path in self.verified_files
                if path.suffix.lower() == ".zip"
                and "gpt" in path.stem.lower()
            ]
        elif self.checksum_skipped:
            candidates = [
                path for path in self.volumes_dir.iterdir()
                if path.is_file()
                and not path.is_symlink()
                and path.suffix.lower() == ".zip"
                and "gpt" in path.stem.lower()
            ]
        else:
            self.log("Error: Release assets have not been verified", "ERROR")
            return None
        if len(candidates) != 1:
            self.log(
                f"Error: Expected exactly one verified GPT archive, found "
                f"{len(candidates)}",
                "ERROR",
            )
            return None

        archive_path = candidates[0]
        try:
            with zipfile.ZipFile(archive_path) as archive:
                members = [
                    info for info in archive.infolist()
                    if not info.is_dir()
                    and Path(info.filename).name.lower().endswith("gpt.img")
                ]
                if len(members) != 1:
                    self.log(
                        f"Error: Expected exactly one gpt.img in "
                        f"{archive_path.name}, found {len(members)}",
                        "ERROR",
                    )
                    return None
                image_info = members[0]
                if image_info.flag_bits & 0x1:
                    self.log("Error: Encrypted GPT archives are unsupported", "ERROR")
                    return None
                if image_info.file_size <= 0:
                    self.log("Error: GPT image is empty", "ERROR")
                    return None
        except (OSError, zipfile.BadZipFile, NotImplementedError) as error:
            self.log(f"Error: Invalid GPT archive: {error}", "ERROR")
            return None

        self.log(
            f"SD image: {Path(image_info.filename).name} from "
            f"{archive_path.name} ({self._format_bytes(image_info.file_size)})"
        )
        return archive_path, image_info
    
    def verify_checksums(self, progress_callback=None, cancel_event=None):
        """Verify SHA256 checksums and reject unsafe manifest paths."""
        if not self.volumes_dir:
            self.log("Error: Release-assets directory is not selected", "ERROR")
            return False
        self.verified_files.clear()
        self.checksum_skipped = False
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

        entries = []
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
                entries.append((expected_hash, filename, filepath))

        if not entries:
            self.log("Error: checksum manifest contains no entries", "ERROR")
            return False

        total_bytes = sum(filepath.stat().st_size for _, _, filepath in entries)
        processed_bytes = 0
        verified_files = set()
        if progress_callback:
            progress_callback(0.0)
        self.log("Verifying checksums...")
        for expected_hash, filename, filepath in entries:
            if cancel_event and cancel_event.is_set():
                self.checksum_skipped = True
                self.log("WARNING: SHA-256 verification skipped by user", "WARNING")
                return True
            sha256 = hashlib.sha256()
            with open(filepath, "rb") as source:
                while chunk := source.read(4 * 1024 * 1024):
                    if cancel_event and cancel_event.is_set():
                        self.checksum_skipped = True
                        self.log("WARNING: SHA-256 verification skipped by user", "WARNING")
                        return True
                    sha256.update(chunk)
                    processed_bytes += len(chunk)
                    if progress_callback:
                        progress_callback(
                            min(100.0, processed_bytes * 100.0 / total_bytes)
                            if total_bytes else 100.0
                        )

            if sha256.hexdigest().lower() != expected_hash.lower():
                self.log(f"Error: {filename} (checksum mismatch)", "ERROR")
                return False
            self.log(f"  OK {filename}")
            verified_files.add(filepath)

        self.verified_files = verified_files
        if progress_callback:
            progress_callback(100.0)
        self.log("All checksums verified successfully!")
        return True

    def _device_size(self, device):
        """Return whole-device size in bytes, or zero when unknown."""
        try:
            result = subprocess.run(
                ["lsblk", "-bno", "SIZE", device],
                capture_output=True, text=True, check=False,
            )
            return int(result.stdout.strip())
        except (OSError, ValueError) as error:
            self.log(f"Could not determine device size for {device}: {error}", "ERROR")
            return 0

    def _unmount_partitions(self, device):
        """Unmount only mounted child partitions of the already-approved disk."""
        try:
            result = subprocess.run(
                ["lsblk", "--json", "-o", "PATH,TYPE,MOUNTPOINTS", device],
                capture_output=True, text=True, check=False,
            )
        except OSError as error:
            self.log(f"Error: Could not inspect target partitions: {error}", "ERROR")
            return False
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
                        mountpoint
                        for mountpoint in (node.get("mountpoints") or [])
                        if mountpoint
                    )
                visit(node.get("children") or [])
        visit(tree)
        for mountpoint in partitions:
            try:
                command = self._privileged_command(["umount", "--", mountpoint])
            except PermissionError as error:
                self.log(f"Error: {error}", "ERROR")
                return False
            try:
                result = subprocess.run(
                    command, capture_output=True, text=True, check=False
                )
            except OSError as error:
                self.log(f"Error: Could not unmount {mountpoint}: {error}", "ERROR")
                return False
            if result.returncode != 0:
                self.log(
                    f"Error: Could not unmount {mountpoint}: "
                    f"{result.stderr.strip()}",
                    "ERROR",
                )
                return False
        return True

    @staticmethod
    def _format_bytes(value):
        units = ("B", "KiB", "MiB", "GiB")
        amount = float(value)
        for unit in units:
            if amount < 1024 or unit == units[-1]:
                return f"{amount:.1f} {unit}"
            amount /= 1024

    def _emit_flash_progress(
        self, callback, phase, processed, total, detail=None, start=0.0, span=100.0
    ):
        phase_percent = min(100.0, processed * 100.0 / total) if total else 0.0
        overall_percent = start + phase_percent * span / 100.0
        if detail is None:
            detail = f"{self._format_bytes(processed)} / {self._format_bytes(total)}"
        if callback:
            callback(phase, overall_percent, detail)

    def _privileged_command(self, command):
        if not IS_LINUX or os.geteuid() == 0:
            return command
        if shutil.which("pkexec"):
            return ["pkexec", *command]
        if shutil.which("sudo"):
            return ["sudo", "-n", *command]
        raise PermissionError(
            "Linux SD writing requires pkexec or an already-authenticated sudo session"
        )

    @staticmethod
    def _windows_is_admin():
        if not IS_WINDOWS:
            return True
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except (AttributeError, OSError):
            return False

    @staticmethod
    def _windows_disk_number(device):
        match = re.fullmatch(r"\\\\\.\\PhysicalDrive(\d+)", device or "")
        return int(match.group(1)) if match else None

    def _open_windows_device(self, device, writable):
        """Open a physical disk without passing its handle through the CRT."""
        if self._windows_disk_number(device) is None:
            raise ValueError(f"Invalid Windows physical-disk path: {device}")

        generic_read = 0x80000000
        generic_write = 0x40000000
        file_share_read = 0x00000001
        file_share_write = 0x00000002
        open_existing = 3
        file_attribute_normal = 0x00000080
        file_flag_write_through = 0x80000000

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateFileW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.HANDLE,
        ]
        kernel32.CreateFileW.restype = wintypes.HANDLE
        kernel32.ReadFile.argtypes = [
            wintypes.HANDLE,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.LPVOID,
        ]
        kernel32.ReadFile.restype = wintypes.BOOL
        kernel32.WriteFile.argtypes = [
            wintypes.HANDLE,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.LPVOID,
        ]
        kernel32.WriteFile.restype = wintypes.BOOL
        kernel32.FlushFileBuffers.argtypes = [wintypes.HANDLE]
        kernel32.FlushFileBuffers.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL

        access = generic_read | (generic_write if writable else 0)
        attributes = file_flag_write_through if writable else file_attribute_normal
        handle = kernel32.CreateFileW(
            device,
            access,
            file_share_read | file_share_write,
            None,
            open_existing,
            attributes,
            None,
        )
        if handle == ctypes.c_void_p(-1).value:
            error_code = ctypes.get_last_error()
            action = "write" if writable else "read"
            detail = ctypes.FormatError(error_code).strip()
            raise RuntimeError(
                f"CreateFileW could not open {device} for raw {action} "
                f"(Windows error {error_code}): {detail}"
            )
        return _WindowsRawDevice(kernel32, handle, device, writable)

    def _open_device(self, device, writable=False):
        if IS_WINDOWS:
            return self._open_windows_device(device, writable)
        return open(device, "r+b" if writable else "rb", buffering=0)

    @staticmethod
    def _flush_device(target):
        target.flush()
        if not IS_WINDOWS:
            os.fsync(target.fileno())

    @staticmethod
    def _release_windows_volume_locks(locks):
        for kernel32, handle, _path in reversed(locks):
            kernel32.CloseHandle(handle)

    def _lock_windows_volumes(self, device):
        """Remove mount points and hold exclusive volume locks."""
        number = self._windows_disk_number(device)
        if number is None:
            self.log("Error: Invalid Windows physical-disk path", "ERROR")
            return None
        script = (
            "$ErrorActionPreference='Stop'; $volumePaths=@(); "
            f"$partitions=Get-Partition -DiskNumber {number}; "
            "foreach ($partition in $partitions) { "
            "foreach ($path in @($partition.AccessPaths)) { "
            "if ($path -match '^\\\\\\\\\\?\\\\Volume') { "
            "$volumePaths += $path "
            "} elseif ($path) { "
            f"Remove-PartitionAccessPath -DiskNumber {number} "
            "-PartitionNumber $partition.PartitionNumber "
            "-AccessPath $path -Confirm:$false } } }; "
            "$volumePaths | Sort-Object -Unique | ConvertTo-Json -Compress"
        )
        powershell = self._powershell_executable()
        if not powershell:
            self.log("Error: Could not find Windows PowerShell", "ERROR")
            return None
        try:
            result = subprocess.run(
                [powershell, "-NoProfile", "-NonInteractive", "-Command", script],
                capture_output=True, text=True, check=False,
            )
        except OSError as error:
            self.log(f"Error: Could not start PowerShell: {error}", "ERROR")
            return None
        if result.returncode != 0:
            self.log(
                f"Error: Could not remove SD-card mount points: "
                f"{result.stderr.strip() or result.stdout.strip()}",
                "ERROR",
            )
            return None

        try:
            data = json.loads(result.stdout) if result.stdout.strip() else []
        except json.JSONDecodeError as error:
            self.log(f"Error: Invalid Windows volume information: {error}", "ERROR")
            return None
        if isinstance(data, str):
            data = [data]
        volume_paths = []
        for path in data:
            if isinstance(path, str) and path.startswith("\\\\?\\Volume{"):
                volume_paths.append("\\\\.\\" + path[4:].rstrip("\\"))

        if not volume_paths:
            self.log(f"No mounted filesystem volumes found on PhysicalDrive{number}")
            return []

        generic_read = 0x80000000
        generic_write = 0x40000000
        file_share_read = 0x00000001
        file_share_write = 0x00000002
        open_existing = 3
        fsctl_lock_volume = 0x00090018
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateFileW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.HANDLE,
        ]
        kernel32.CreateFileW.restype = wintypes.HANDLE
        kernel32.DeviceIoControl.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.LPVOID,
        ]
        kernel32.DeviceIoControl.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL

        locks = []
        for volume_path in volume_paths:
            handle = kernel32.CreateFileW(
                volume_path,
                generic_read | generic_write,
                file_share_read | file_share_write,
                None,
                open_existing,
                0,
                None,
            )
            if handle == ctypes.c_void_p(-1).value:
                error_code = ctypes.get_last_error()
                detail = ctypes.FormatError(error_code).strip()
                self._release_windows_volume_locks(locks)
                self.log(
                    f"Error: CreateFileW could not open volume {volume_path} "
                    f"(Windows error {error_code}): {detail}",
                    "ERROR",
                )
                return None
            locks.append((kernel32, handle, volume_path))
            returned = wintypes.DWORD()
            if not kernel32.DeviceIoControl(
                handle,
                fsctl_lock_volume,
                None,
                0,
                None,
                0,
                ctypes.byref(returned),
                None,
            ):
                error_code = ctypes.get_last_error()
                detail = ctypes.FormatError(error_code).strip()
                self._release_windows_volume_locks(locks)
                self.log(
                    f"Error: FSCTL_LOCK_VOLUME failed for {volume_path} "
                    f"(Windows error {error_code}): {detail}. "
                    "Close Explorer and any program using the SD card.",
                    "ERROR",
                )
                return None
        self.log(
            f"Locked {len(locks)} volume(s) on PhysicalDrive{number}"
        )
        return locks

    def _hash_device_prefix(self, device, size, progress_callback=None):
        """Hash exactly the image-sized prefix of a raw device."""
        block_size = 4 * 1024 * 1024
        digest = hashlib.sha256()
        remaining = size
        processed = 0
        phase = "Verifying SD-card readback"
        self._emit_flash_progress(
            progress_callback, phase, 0, size, start=50.0, span=50.0
        )

        if IS_WINDOWS or (IS_LINUX and os.geteuid() == 0):
            buffer = bytearray(block_size)
            buffer_view = memoryview(buffer)
            with self._open_device(device) as source:
                while remaining:
                    requested = min(block_size, remaining)
                    read = source.readinto(buffer_view[:requested])
                    if not read:
                        break
                    digest.update(buffer_view[:read])
                    processed += read
                    remaining -= read
                    self._emit_flash_progress(
                        progress_callback,
                        phase,
                        processed,
                        size,
                        start=50.0,
                        span=50.0,
                    )
        else:
            command = self._privileged_command([
                "dd", f"if={device}", "bs=4M", f"count={size}",
                "iflag=count_bytes", "status=none",
            ])
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            try:
                while remaining:
                    chunk = process.stdout.read(min(block_size, remaining))
                    if not chunk:
                        break
                    digest.update(chunk)
                    processed += len(chunk)
                    remaining -= len(chunk)
                    self._emit_flash_progress(
                        progress_callback,
                        phase,
                        processed,
                        size,
                        start=50.0,
                        span=50.0,
                    )
                stderr = process.stderr.read()
                process.wait()
            except Exception:
                process.kill()
                process.wait()
                raise
            if process.returncode != 0:
                self.log(
                    f"Error: Could not verify written data: "
                    f"{stderr.decode(errors='replace').strip()}",
                    "ERROR",
                )
                return None

        if remaining:
            self.log("Error: SD-card readback ended before image size", "ERROR")
            return None
        return digest.hexdigest()

    def _stream_gpt_direct(
        self, archive_path, image_info, device, progress_callback
    ):
        """Decompress gpt.img directly to an already-authorized raw device."""
        digest = hashlib.sha256()
        processed = 0
        size = image_info.file_size
        self._emit_flash_progress(
            progress_callback, "Writing gpt.img", 0, size, start=0.0, span=50.0
        )
        if IS_WINDOWS:
            self.log(f"Opening {device} with native CreateFileW raw-disk access")
        with (
            zipfile.ZipFile(archive_path) as archive,
            archive.open(image_info) as source,
            self._open_device(device, writable=True) as target,
        ):
            if IS_WINDOWS:
                self.log("Raw disk handle opened; writing with Win32 WriteFile")
            buffer = bytearray(4 * 1024 * 1024)
            buffer_view = memoryview(buffer)
            while read := source.readinto(buffer_view):
                chunk = buffer_view[:read]
                digest.update(chunk)
                view = chunk
                while view:
                    written = target.write(view)
                    if not written:
                        raise OSError(f"Short write to {device}")
                    view = view[written:]
                processed += read
                self._emit_flash_progress(
                    progress_callback,
                    "Writing gpt.img",
                    processed,
                    size,
                    start=0.0,
                    span=50.0,
                )
            self._flush_device(target)
        if processed != size:
            raise OSError(
                f"GPT image size mismatch: expected {size}, streamed {processed}"
            )
        return digest.hexdigest()

    def _stream_gpt_with_dd(
        self, archive_path, image_info, device, progress_callback
    ):
        """Decompress gpt.img into a privileged dd process."""
        command = self._privileged_command([
            "dd", f"of={device}", "bs=4M", "status=none", "conv=fsync",
        ])
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        digest = hashlib.sha256()
        processed = 0
        size = image_info.file_size
        self._emit_flash_progress(
            progress_callback, "Writing gpt.img", 0, size, start=0.0, span=50.0
        )
        try:
            with (
                zipfile.ZipFile(archive_path) as archive,
                archive.open(image_info) as source,
            ):
                while chunk := source.read(4 * 1024 * 1024):
                    process.stdin.write(chunk)
                    digest.update(chunk)
                    processed += len(chunk)
                    self._emit_flash_progress(
                        progress_callback,
                        "Writing gpt.img",
                        processed,
                        size,
                        start=0.0,
                        span=50.0,
                    )
            process.stdin.close()
            stderr = process.stderr.read()
            process.wait()
        except Exception:
            process.kill()
            process.wait()
            raise
        if process.returncode != 0:
            detail = stderr.decode(errors="replace").strip()
            raise RuntimeError(f"SD-card write failed: {detail}")
        if processed != size:
            raise OSError(
                f"GPT image size mismatch: expected {size}, streamed {processed}"
            )
        return digest.hexdigest()

    def flash_to_sd_card(self, device, progress_callback=None):
        """Stream the release GPT image to a revalidated SD card and verify it."""
        self.last_error = None
        if not device:
            self.log("Error: No SD card device selected", "ERROR")
            return False
        if not IS_WINDOWS and not IS_LINUX:
            self.log("Error: SD-card writing is supported on Windows and Linux", "ERROR")
            return False
        if IS_WINDOWS and not self._windows_is_admin():
            self.log("Error: Run the installer as Administrator to write an SD card", "ERROR")
            return False

        inspected = self.inspect_sd_image()
        if not inspected:
            return False
        archive_path, image_info = inspected
        image_size = image_info.file_size
        if self.checksum_skipped:
            self.log(
                "WARNING: Writing an unauthenticated archive; only ZIP CRC and "
                "post-write readback will be checked",
                "WARNING",
            )

        self._emit_flash_progress(
            progress_callback,
            "Validating target",
            0,
            1,
            "Revalidating SD card",
        )
        safe_devices = {item["path"]: item for item in self.list_safe_devices()}
        selected = safe_devices.get(device)
        if not selected:
            self.log("Refusing target: it is not a detected removable SD disk", "ERROR")
            return False
        initial_size = selected["size"]
        initial_identity = selected.get("identity", "")
        if not initial_size or image_size > initial_size:
            self.log(
                f"Refusing target: SD card is smaller than gpt.img "
                f"({self._format_bytes(image_size)})",
                "ERROR",
            )
            return False
        self.log(
            f"Target validated: {device} ({self._format_bytes(initial_size)}), "
            f"gpt.img {self._format_bytes(image_size)}"
        )

        self._emit_flash_progress(
            progress_callback,
            "Unmounting volumes",
            0,
            1,
            "Preparing target",
        )
        windows_volume_locks = []
        if IS_WINDOWS:
            windows_volume_locks = self._lock_windows_volumes(device)
            if windows_volume_locks is None:
                return False
        elif not self._unmount_partitions(device):
            return False

        try:
            refreshed = {item["path"]: item for item in self.list_safe_devices()}
            selected_after = refreshed.get(device)
            if (
                not selected_after
                or selected_after["size"] != initial_size
                or selected_after.get("identity", "") != initial_identity
            ):
                self.log("Refusing target: device identity or size changed", "ERROR")
                return False

            self.log(
                f"Streaming {Path(image_info.filename).name} from "
                f"{archive_path.name} to {device}"
            )
            self.log("WARNING: This erases the entire selected SD card", "WARNING")
            if IS_WINDOWS or os.geteuid() == 0:
                expected_hash = self._stream_gpt_direct(
                    archive_path, image_info, device, progress_callback
                )
            else:
                expected_hash = self._stream_gpt_with_dd(
                    archive_path, image_info, device, progress_callback
                )
            self.log("Write and ZIP CRC validation complete; verifying readback")
            if IS_LINUX:
                subprocess.run(["sync"], check=False)
            actual_hash = self._hash_device_prefix(
                device, image_size, progress_callback
            )
            if actual_hash != expected_hash:
                self.last_error = (
                    "Post-write SHA-256 mismatch: the SD card did not read back "
                    "the same data that was written"
                )
                self.log(
                    f"Error: {self.last_error} "
                    f"(source {expected_hash}, readback {actual_hash})",
                    "ERROR",
                )
                return False
            self._emit_flash_progress(
                progress_callback,
                "Complete",
                1,
                1,
                "GPT image verified successfully",
            )
            self.log(f"Verified SHA-256: {actual_hash}")
            self.log("SD-card write and readback verification completed successfully!")
            return True
        except (OSError, RuntimeError, zipfile.BadZipFile) as error:
            self.last_error = f"{type(error).__name__}: {error}"
            self.log(f"Error: {self.last_error}", "ERROR")
            return False
        finally:
            if windows_volume_locks:
                self._release_windows_volume_locks(windows_volume_locks)
                self.log("Released Windows volume locks")
    
    
    def run(self):
        """Run the complete CLI workflow."""
        self.log(f"RADXOID Installer {VERSION}")
        self.log(f"Platform: {PLATFORM}")
        if self.log_path:
            self.log(f"Session log: {self.log_path}")
        if not self.select_volumes_dir() or not self.verify_checksums():
            return False
        device = self.select_sd_card()
        if not device:
            return False
        expected = f"ERASE {device}"
        typed = input(
            f"This permanently erases {device}. Type exactly '{expected}': "
        )
        if typed != expected:
            self.log("SD-card write cancelled: confirmation did not match", "WARNING")
            return False
        return self.flash_to_sd_card(device)


class RADXOIDGUI:
    """Three-step GUI for verification and destructive SD-card writing."""

    def __init__(self, root):
        self.root = root
        self.root.title(f"RADXOID Installer {VERSION}")
        self.root.geometry("900x680")
        self.root.resizable(True, True)
        self.root.protocol("WM_DELETE_WINDOW", self.close_app)
        try:
            self.root.iconbitmap(default="radxoid.ico")
        except (tk.TclError, OSError):
            pass

        self.installer = RADXOIDInstaller()
        self.operation_percent = 0.0
        self.progress_queue = queue.Queue()
        self.flash_progress_queue = queue.Queue()
        self.worker_result_queue = queue.Queue()
        self.running = True

        self.checksum_started = False
        self.checksum_result = None
        self.checksum_error = None
        self.checksum_skipped = False
        self.checksum_cancel = threading.Event()
        self.flash_started = False
        self.flash_result = None
        self.flash_error = None
        self.sd_card_device = ""
        self.device_options = {}
        self._last_progress = -1.0

        self.create_ui()
        self.installer.log(f"RADXOID Installer {VERSION}")
        self.installer.log(f"Platform: {PLATFORM}")
        if self.installer.log_path:
            self.installer.log(f"Session log: {self.installer.log_path}")
        self.root.after(100, self.process_queues)

    def create_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            main_frame,
            text=f"RADXOID {VERSION} Installer",
            font=("Helvetica", 16, "bold"),
        ).pack(pady=8)
        ttk.Label(
            main_frame,
            text="Lean Android 11 for Radxa ROCK 3A (RK3568)",
            font=("Helvetica", 10),
        ).pack(pady=4)

        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=8)
        self.steps = ["Select Assets", "Verify Checksums", "Write SD Card"]
        self.current_step = 0
        self.step_labels = []
        for index, step in enumerate(self.steps):
            progress_frame.columnconfigure(index, weight=1)
            label = ttk.Label(
                progress_frame,
                text=step,
                padding=5,
                anchor=tk.CENTER,
            )
            label.grid(row=0, column=index, sticky="ew", padx=5)
            self.step_labels.append(label)

        self.content_frame = ttk.Frame(main_frame)
        self.content_frame.pack(fill=tk.X, pady=8)

        self.log_frame = ttk.LabelFrame(main_frame, text="Operation log")
        self.log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.log_text = scrolledtext.ScrolledText(
            self.log_frame,
            wrap=tk.WORD,
            height=13,
            state="disabled",
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=8)
        self.prev_button = ttk.Button(
            button_frame,
            text="Back",
            command=self.prev_step,
            state="disabled",
        )
        self.prev_button.pack(side=tk.LEFT, padx=5)
        self.next_button = ttk.Button(
            button_frame,
            text="Next",
            command=self.next_step,
        )
        self.next_button.pack(side=tk.RIGHT, padx=5)

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(
            main_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
        ).pack(fill=tk.X, pady=(0, 8))
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            maximum=100,
            mode="determinate",
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))

        self.update_step_indicator()
        self.update_content_frame()

    def checksum_busy(self):
        return self.checksum_started and self.checksum_result is None

    def flash_busy(self):
        return self.flash_started and self.flash_result is None

    def update_step_indicator(self):
        for index, label in enumerate(self.step_labels):
            if index == self.current_step:
                label.config(
                    foreground="blue",
                    font=("Helvetica", 10, "bold"),
                )
            elif index < self.current_step:
                label.config(foreground="green", font=("Helvetica", 10))
            else:
                label.config(foreground="gray", font=("Helvetica", 10))

    def update_content_frame(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self.step_message_var = tk.StringVar()

        if self.current_step == 0:
            self.step_message_var.set(
                "Select the folder containing the RADXOID GPT ZIP and "
                "SHA-256 manifest."
            )
            ttk.Label(
                self.content_frame,
                textvariable=self.step_message_var,
                padding=5,
                wraplength=760,
            ).pack(pady=5)
            ttk.Button(
                self.content_frame,
                text="Browse release assets...",
                command=self.browse_volumes,
            ).pack(pady=5)
            if self.installer.volumes_dir:
                ttk.Label(
                    self.content_frame,
                    text=f"Selected: {self.installer.volumes_dir}",
                    foreground="green",
                    wraplength=760,
                ).pack(pady=5)

        elif self.current_step == 1:
            if self.checksum_result is None and self.checksum_skipped:
                text = "Stopping SHA-256 verification safely..."
                color = "darkorange"
            elif self.checksum_result is None:
                text = (
                    f"Verifying release assets: {self.operation_percent:.1f}%. "
                    "Do not close the installer."
                )
                color = "blue"
            elif self.checksum_skipped:
                text = "SHA-256 verification was skipped. Click Next to continue."
                color = "darkorange"
            elif self.checksum_result:
                text = "Release assets passed SHA-256 verification. Click Next."
                color = "green"
            else:
                text = (
                    "SHA-256 verification failed. "
                    f"{self.checksum_error or 'See the operation log.'}"
                )
                color = "red"
            self.step_message_var.set(text)
            ttk.Label(
                self.content_frame,
                textvariable=self.step_message_var,
                foreground=color,
                padding=5,
                wraplength=760,
            ).pack(pady=5)
            if not self.checksum_started:
                self.checksum_started = True
                threading.Thread(
                    target=self.run_checksums,
                    name="radxoid-checksum",
                    daemon=True,
                ).start()
            if self.checksum_result is None and not self.checksum_skipped:
                ttk.Button(
                    self.content_frame,
                    text="Skip SHA-256 verification (unsafe)",
                    command=self.skip_checksums,
                ).pack(pady=5)

        else:
            if not self.flash_started:
                text = (
                    "Select a removable SD card. The installer streams gpt.img "
                    "from the verified GPT ZIP, then reads it back and verifies SHA-256."
                )
                color = "blue"
            elif self.flash_result is None:
                text = (
                    "Writing and verifying gpt.img. Do not remove the SD card, "
                    "close the installer, or power off the computer."
                )
                color = "blue"
            elif self.flash_result:
                text = "SD-card write and readback verification completed successfully."
                color = "green"
            else:
                text = (
                    "SD-card write failed. "
                    f"{self.flash_error or 'See the operation log.'}"
                )
                color = "red"
            self.step_message_var.set(text)
            ttk.Label(
                self.content_frame,
                textvariable=self.step_message_var,
                foreground=color,
                padding=5,
                wraplength=760,
            ).pack(pady=5)
            ttk.Button(
                self.content_frame,
                text="Refresh SD-card list",
                command=self.refresh_devices,
                state="disabled" if self.flash_busy() else "normal",
            ).pack(pady=5)

            if IS_WINDOWS and not self.installer._windows_is_admin():
                ttk.Label(
                    self.content_frame,
                    text=(
                        "Administrator privileges are required. Use the packaged "
                        "installer, which requests them when it starts."
                    ),
                    foreground="red",
                    padding=5,
                    wraplength=760,
                ).pack(pady=5)

            devices = self.installer.list_safe_devices()
            self.device_options = {
                item["label"]: item["path"] for item in devices
            }
            if self.sd_card_device not in self.device_options.values():
                self.sd_card_device = ""
            if not devices:
                ttk.Label(
                    self.content_frame,
                    text=(
                        "No writable removable SD card detected. Insert the card "
                        "and click Refresh SD-card list."
                    ),
                    foreground="red",
                    padding=5,
                    wraplength=760,
                ).pack(pady=5)
            else:
                ttk.Label(
                    self.content_frame,
                    text=(
                        "Only removable SD-card whole disks are listed. "
                        "System and boot disks are excluded."
                    ),
                    foreground="green",
                    padding=5,
                    wraplength=760,
                ).pack(pady=5)
                self.device_var = tk.StringVar()
                self.device_combo = ttk.Combobox(
                    self.content_frame,
                    textvariable=self.device_var,
                    values=list(self.device_options),
                    state="disabled" if self.flash_busy() else "readonly",
                    width=88,
                )
                self.device_combo.pack(pady=5)
                ttk.Button(
                    self.content_frame,
                    text="Select target",
                    command=self.select_gui_device,
                    state="disabled" if self.flash_busy() else "normal",
                ).pack(pady=5)
                if self.sd_card_device:
                    ttk.Label(
                        self.content_frame,
                        text=f"Selected whole disk: {self.sd_card_device}",
                        foreground="red",
                    ).pack(pady=5)
                    ttk.Button(
                        self.content_frame,
                        text="Write and verify gpt.img",
                        command=self.run_flash,
                        state="disabled" if self.flash_busy() else "normal",
                    ).pack(pady=5)

        busy = self.checksum_busy() or self.flash_busy()
        self.prev_button.config(
            state=(
                "disabled"
                if self.current_step == 0 or busy
                else "normal"
            )
        )
        if self.current_step == 0:
            next_enabled = bool(self.installer.volumes_dir)
        elif self.current_step == 1:
            next_enabled = self.checksum_result is True
        else:
            next_enabled = self.flash_result is True
        self.next_button.config(
            text="Close" if self.current_step == len(self.steps) - 1 else "Next",
            state="normal" if next_enabled else "disabled",
        )
        self.progress_var.set(
            self.operation_percent if self.current_step in (1, 2) else 0.0
        )

    def _report_progress(self, label, value):
        percent = max(0.0, min(100.0, float(value)))
        if percent - self._last_progress < 0.1 and percent < 100.0:
            return
        self._last_progress = percent
        self.progress_queue.put((label, percent))

    def _report_flash_progress(self, phase, percent, detail):
        self.flash_progress_queue.put((phase, percent, detail))

    def _apply_progress(self, label, percent):
        self.operation_percent = percent
        self.progress_var.set(percent)
        self.status_var.set(f"{label}: {percent:.1f}%")
        if (
            self.current_step == 1
            and self.checksum_result is None
            and not self.checksum_skipped
        ):
            self.step_message_var.set(
                f"Verifying release assets: {percent:.1f}%. "
                "Do not close the installer."
            )

    def _apply_flash_progress(self, phase, percent, detail):
        self.operation_percent = percent
        self.progress_var.set(percent)
        self.status_var.set(f"{phase}: {detail} ({percent:.1f}%)")
        if self.current_step == 2 and self.flash_result is None:
            self.step_message_var.set(
                f"{phase}: {detail} ({percent:.1f}%). "
                "Do not remove the SD card."
            )

    def _append_log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def _apply_worker_result(self, kind, result, error, skipped=False):
        if kind == "checksum":
            self.checksum_skipped = self.checksum_skipped or skipped
            self.checksum_result = True if self.checksum_skipped else result
            self.checksum_error = error
        elif kind == "flash":
            self.flash_result = result
            self.flash_error = error
            if result:
                messagebox.showinfo(
                    "RADXOID SD card ready",
                    "gpt.img was written and verified successfully. "
                    "Safely eject the SD card before removing it.",
                )
            else:
                messagebox.showerror(
                    "SD-card write failed",
                    error or "See the operation log for details.",
                )
        self.update_content_frame()

    def process_queues(self):
        try:
            while True:
                label, percent = self.progress_queue.get_nowait()
                self._apply_progress(label, percent)
        except queue.Empty:
            pass
        try:
            while True:
                phase, percent, detail = self.flash_progress_queue.get_nowait()
                self._apply_flash_progress(phase, percent, detail)
        except queue.Empty:
            pass
        try:
            while True:
                message = self.installer.log_queue.get_nowait()
                self._append_log(message)
        except queue.Empty:
            pass
        try:
            while True:
                self._apply_worker_result(*self.worker_result_queue.get_nowait())
        except queue.Empty:
            pass
        if self.running:
            self.root.after(100, self.process_queues)

    def browse_volumes(self):
        if self.installer.select_volumes_dir():
            self.update_content_frame()

    def refresh_devices(self):
        if not self.flash_busy():
            self.sd_card_device = ""
            self.update_content_frame()

    def skip_checksums(self):
        confirmed = messagebox.askyesno(
            "Skip SHA-256 verification?",
            "Integrity verification protects against corrupted or modified images. "
            "Continue only if the files came directly from the official release.",
        )
        if not confirmed:
            return
        self.checksum_skipped = True
        self.checksum_cancel.set()
        self.installer.checksum_skipped = True
        self.installer.log(
            "WARNING: SHA-256 verification skipped by user",
            "WARNING",
        )
        self.update_content_frame()

    def run_checksums(self):
        self.installer.log("Starting SHA-256 verification")
        result = False
        error = None
        try:
            result = self.installer.verify_checksums(
                progress_callback=lambda value: self._report_progress(
                    "SHA-256",
                    value,
                ),
                cancel_event=self.checksum_cancel,
            )
        except Exception as exception:  # noqa: BLE001 - worker boundary
            error = str(exception)
            self.installer.log(
                f"SHA-256 verification failed: {exception}",
                "ERROR",
            )
        self.worker_result_queue.put(
            (
                "checksum",
                result,
                error,
                self.installer.checksum_skipped,
            )
        )

    def select_gui_device(self):
        device = self.device_options.get(self.device_var.get())
        if device:
            self.sd_card_device = device
            self.update_content_frame()

    def run_flash(self):
        if self.flash_busy():
            return
        device = self.sd_card_device
        if not device:
            messagebox.showerror("No target", "Select an SD-card target first.")
            return
        inspected = self.installer.inspect_sd_image()
        if not inspected:
            messagebox.showerror(
                "Invalid release assets",
                "No usable verified GPT image was found. See the operation log.",
            )
            return
        image_size = inspected[1].file_size
        expected = f"ERASE {device}"
        typed = simpledialog.askstring(
            "Final destructive-write confirmation",
            f"The whole disk {device} will be erased.\n"
            f"Image size: {self.installer._format_bytes(image_size)}\n\n"
            f"Type exactly:\n{expected}",
        )
        if typed != expected:
            messagebox.showwarning(
                "Write cancelled",
                "The exact confirmation did not match. Nothing was written.",
            )
            return
        self.flash_started = True
        self.flash_result = None
        self.flash_error = None
        self.operation_percent = 0.0
        self.flash_progress_queue = queue.Queue()
        self.installer.log(f"Starting SD-card write to {device}")
        self.update_content_frame()
        threading.Thread(
            target=self.run_flash_worker,
            args=(device,),
            name="radxoid-sd-writer",
            daemon=False,
        ).start()

    def run_flash_worker(self, device):
        result = False
        error = None
        try:
            result = self.installer.flash_to_sd_card(
                device,
                progress_callback=self._report_flash_progress,
            )
            if not result:
                error = (
                    self.installer.last_error
                    or "The write or readback verification failed. See the operation log."
                )
        except Exception as exception:  # noqa: BLE001 - worker boundary
            error = str(exception)
            self.installer.log(f"SD-card write failed: {exception}", "ERROR")
        self.worker_result_queue.put(("flash", result, error))

    def next_step(self):
        if self.current_step == len(self.steps) - 1:
            if self.flash_result is True:
                self.close_app()
            return
        if self.current_step == 0:
            if not self.installer.volumes_dir:
                messagebox.showerror(
                    "Release assets required",
                    "Select the release-assets folder first.",
                )
                return
            self.checksum_started = False
            self.checksum_result = None
            self.checksum_error = None
            self.checksum_skipped = False
            self.checksum_cancel = threading.Event()
            self.operation_percent = 0.0
            self._last_progress = -1.0
        elif self.current_step == 1:
            if self.checksum_result is not True:
                return
            self.flash_started = False
            self.flash_result = None
            self.flash_error = None
            self.operation_percent = 0.0
            self.sd_card_device = ""
        self.current_step += 1
        self.update_step_indicator()
        self.update_content_frame()

    def prev_step(self):
        if self.current_step == 0 or self.checksum_busy() or self.flash_busy():
            return
        self.current_step -= 1
        self.update_step_indicator()
        self.update_content_frame()

    def close_app(self):
        if self.flash_busy():
            messagebox.showwarning(
                "Write in progress",
                "The SD-card write is still running. Closing now could corrupt "
                "the card, so the installer will remain open.",
            )
            return
        self.running = False
        self.root.destroy()

    def run_app(self):
        self.root.mainloop()


def main():
    if IS_WINDOWS:
        try:
            if not _ensure_windows_elevation():
                return
        except OSError as error:
            ctypes.windll.user32.MessageBoxW(
                None,
                str(error),
                f"RADXOID Installer {VERSION}",
                0x10,
            )
            return
        if not GUI_AVAILABLE:
            ctypes.windll.user32.MessageBoxW(
                None,
                "Tkinter is unavailable. Install Python from python.org with "
                "the Tcl/Tk option enabled.",
                f"RADXOID Installer {VERSION}",
                0x10,
            )
            return
    if GUI_AVAILABLE:
        root = tk.Tk()
        RADXOIDGUI(root).run_app()
    else:
        print("RADXOID Installer - CLI Mode")
        print(f"Version: {VERSION}")
        print(f"Platform: {PLATFORM}")
        RADXOIDInstaller().run()


if __name__ == "__main__":
    main()
