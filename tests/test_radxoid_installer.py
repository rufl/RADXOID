import hashlib
import json
import importlib.util
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from subprocess import CompletedProcess
from types import SimpleNamespace
from unittest.mock import Mock, patch

SOURCE = Path(__file__).parents[1] / "dist" / "installer" / "radxoid_installer.py"
SPEC = importlib.util.spec_from_file_location("radxoid_installer", SOURCE)
installer_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer_module)


class InstallerBackendTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.payload = (bytes(range(256)) * 24577) + b"RADXOID-GPT"
        self.archive = self.root / "test_release_gpt.zip"
        with zipfile.ZipFile(
            self.archive,
            "w",
            compression=zipfile.ZIP_DEFLATED,
        ) as archive:
            archive.writestr("images/test-release-gpt.img", self.payload)
        archive_hash = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        (self.root / f"SHA256SUMS-{installer_module.VERSION}.txt").write_text(
            f"{archive_hash}  {self.archive.name}\n",
            encoding="utf-8",
        )
        self.installer = installer_module.RADXOIDInstaller()
        self.installer.volumes_dir = self.root

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_source_launcher_requests_uac_elevation(self):
        shell32 = SimpleNamespace(
            IsUserAnAdmin=Mock(return_value=False),
            ShellExecuteW=Mock(return_value=42),
        )
        with (
            patch.object(installer_module, "IS_WINDOWS", True),
            patch.object(
                installer_module.ctypes,
                "windll",
                create=True,
                new=SimpleNamespace(shell32=shell32),
            ),
            patch.object(
                installer_module.sys,
                "executable",
                r"C:\Python\pythonw.exe",
            ),
            patch.object(
                installer_module.sys,
                "argv",
                [r"C:\Downloads\RADXOID-Installer.pyw"],
            ),
            patch.object(
                installer_module.sys,
                "frozen",
                False,
                create=True,
            ),
        ):
            self.assertFalse(installer_module._ensure_windows_elevation())

        launch = shell32.ShellExecuteW.call_args.args
        self.assertEqual(launch[1], "runas")
        self.assertEqual(launch[2], r"C:\Python\pythonw.exe")
        self.assertIn("radxoid_installer.py", launch[3])

    def test_manifest_verification_and_image_inspection(self):
        progress = []
        self.assertTrue(self.installer.verify_checksums(progress.append))
        inspected = self.installer.inspect_sd_image()
        self.assertIsNotNone(inspected)
        archive_path, image_info = inspected
        self.assertEqual(archive_path, self.archive)
        self.assertEqual(image_info.file_size, len(self.payload))
        self.assertEqual(progress[0], 0.0)
        self.assertEqual(progress[-1], 100.0)

    def test_complete_write_and_readback_pipeline(self):
        self.assertTrue(self.installer.verify_checksums())
        target = self.root / "fake-sd-card.bin"
        target.write_bytes(b"\0" * (len(self.payload) + 1024 * 1024))
        device = {
            "path": str(target),
            "label": "test removable SD",
            "size": target.stat().st_size,
            "identity": "test-card-serial",
        }
        progress = []
        with (
            patch.object(installer_module, "IS_WINDOWS", False),
            patch.object(installer_module, "IS_LINUX", True),
            patch.object(
                self.installer,
                "list_safe_devices",
                side_effect=[[device], [device]],
            ),
            patch.object(self.installer, "_unmount_partitions", return_value=True),
            patch.object(
                installer_module.os,
                "geteuid",
                return_value=0,
                create=True,
            ),
            patch.object(
                installer_module.subprocess,
                "run",
                return_value=CompletedProcess([], 0, "", ""),
            ),
        ):
            result = self.installer.flash_to_sd_card(
                str(target),
                lambda phase, percent, detail: progress.append(
                    (phase, percent, detail)
                ),
            )
        self.assertTrue(result)
        with target.open("rb") as written:
            self.assertEqual(written.read(len(self.payload)), self.payload)
        percentages = [item[1] for item in progress]
        self.assertEqual(percentages[-1], 100.0)
        self.assertEqual(percentages, sorted(percentages))
        self.assertTrue(any(phase == "Writing gpt.img" for phase, _, _ in progress))
        self.assertTrue(
            any(phase == "Verifying SD-card readback" for phase, _, _ in progress)
        )

    def test_windows_raw_device_uses_win32_io_without_crt(self):
        writes = []
        payload = b"readback"

        def write_file(_handle, raw_buffer, size, bytes_written, _overlapped):
            writes.append(installer_module.ctypes.string_at(raw_buffer, size))
            bytes_written._obj.value = size
            return True

        def read_file(_handle, raw_buffer, size, bytes_read, _overlapped):
            count = min(size, len(payload))
            installer_module.ctypes.memmove(raw_buffer, payload, count)
            bytes_read._obj.value = count
            return True

        create_file = Mock(return_value=123)
        kernel32 = SimpleNamespace(
            CreateFileW=create_file,
            ReadFile=Mock(side_effect=read_file),
            WriteFile=Mock(side_effect=write_file),
            FlushFileBuffers=Mock(return_value=True),
            CloseHandle=Mock(return_value=True),
        )
        with patch.object(
            installer_module.ctypes,
            "WinDLL",
            create=True,
            return_value=kernel32,
        ):
            target = self.installer._open_windows_device(
                r"\\.\PhysicalDrive7",
                writable=True,
            )
            write_buffer = bytearray(b"native-write")
            self.assertEqual(target.write(write_buffer), len(write_buffer))
            read_buffer = bytearray(len(payload))
            self.assertEqual(target.readinto(read_buffer), len(payload))
            target.flush()
            target.close()

        self.assertEqual(writes, [b"native-write"])
        self.assertEqual(read_buffer, payload)
        create_file.assert_called_once_with(
            r"\\.\PhysicalDrive7",
            0xC0000000,
            0x00000003,
            None,
            3,
            0x80000000,
            None,
        )
        kernel32.FlushFileBuffers.assert_called_once_with(123)
        kernel32.CloseHandle.assert_called_once_with(123)

    def test_windows_createfile_error_includes_device_and_system_error(self):
        kernel32 = SimpleNamespace(
            CreateFileW=Mock(
                return_value=installer_module.ctypes.c_void_p(-1).value
            ),
            ReadFile=Mock(),
            WriteFile=Mock(),
            FlushFileBuffers=Mock(),
            CloseHandle=Mock(return_value=True),
        )
        with (
            patch.object(
                installer_module.ctypes,
                "WinDLL",
                create=True,
                return_value=kernel32,
            ),
            patch.object(
                installer_module.ctypes,
                "get_last_error",
                create=True,
                return_value=5,
            ),
            patch.object(
                installer_module.ctypes,
                "FormatError",
                create=True,
                return_value="Access is denied.\r\n",
            ),
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                r"CreateFileW could not open \\\\\.\\PhysicalDrive7 "
                r"for raw write \(Windows error 5\): Access is denied\.",
            ):
                self.installer._open_windows_device(
                    r"\\.\PhysicalDrive7",
                    writable=True,
                )

    def test_windows_volume_is_locked_without_taking_disk_offline(self):
        volume_guid = r"\\?\Volume{test-volume}" + "\\"
        completed = CompletedProcess([], 0, json.dumps([volume_guid]), "")
        kernel32 = SimpleNamespace(
            CreateFileW=Mock(return_value=456),
            DeviceIoControl=Mock(return_value=True),
            CloseHandle=Mock(return_value=True),
        )
        with (
            patch.object(
                self.installer,
                "_powershell_executable",
                return_value="powershell.exe",
            ),
            patch.object(
                installer_module.subprocess,
                "run",
                return_value=completed,
            ) as run,
            patch.object(
                installer_module.ctypes,
                "WinDLL",
                create=True,
                return_value=kernel32,
            ),
        ):
            locks = self.installer._lock_windows_volumes(
                r"\\.\PhysicalDrive7"
            )

        self.assertEqual(locks, [(kernel32, 456, r"\\.\Volume{test-volume}")])
        script = run.call_args.args[0][-1]
        self.assertNotIn("mountvol.exe", script)
        self.assertNotIn("/p", script)
        self.assertIn("Remove-PartitionAccessPath", script)
        kernel32.CreateFileW.assert_called_once_with(
            r"\\.\Volume{test-volume}",
            0xC0000000,
            0x00000003,
            None,
            3,
            0,
            None,
        )
        controls = [
            call.args[1] for call in kernel32.DeviceIoControl.call_args_list
        ]
        self.assertEqual(controls, [0x00090018])
        self.installer._release_windows_volume_locks(locks)
        kernel32.CloseHandle.assert_called_once_with(456)

    def test_raw_write_error_is_preserved_and_volume_lock_released(self):
        self.assertTrue(self.installer.verify_checksums())
        target = r"\\.\PhysicalDrive7"
        device = {
            "path": target,
            "label": "test removable SD",
            "size": len(self.payload) + 1024,
            "identity": "permission-card",
        }
        locks = [(Mock(), 456, r"\\.\Volume{test-volume}")]
        with (
            patch.object(installer_module, "IS_WINDOWS", True),
            patch.object(installer_module, "IS_LINUX", False),
            patch.object(self.installer, "_windows_is_admin", return_value=True),
            patch.object(
                self.installer,
                "list_safe_devices",
                side_effect=[[device], [device]],
            ),
            patch.object(
                self.installer,
                "_lock_windows_volumes",
                return_value=locks,
            ),
            patch.object(
                self.installer,
                "_release_windows_volume_locks",
            ) as release,
            patch.object(
                self.installer,
                "_stream_gpt_direct",
                side_effect=PermissionError(13, "Permission denied"),
            ),
        ):
            result = self.installer.flash_to_sd_card(target)

        self.assertFalse(result)
        self.assertEqual(
            self.installer.last_error,
            "PermissionError: [Errno 13] Permission denied",
        )
        release.assert_called_once_with(locks)

    def test_refuses_target_smaller_than_uncompressed_image(self):
        self.assertTrue(self.installer.verify_checksums())
        target = self.root / "small-card.bin"
        target.write_bytes(b"unchanged")
        device = {
            "path": str(target),
            "label": "small SD",
            "size": len(self.payload) - 1,
            "identity": "small-card",
        }
        with patch.object(self.installer, "list_safe_devices", return_value=[device]):
            self.assertFalse(self.installer.flash_to_sd_card(str(target)))
        self.assertEqual(target.read_bytes(), b"unchanged")

    def test_refuses_device_identity_change_after_unmount(self):
        self.assertTrue(self.installer.verify_checksums())
        target = self.root / "changed-card.bin"
        target.write_bytes(b"\0" * (len(self.payload) + 1024))
        first = {
            "path": str(target),
            "label": "SD A",
            "size": target.stat().st_size,
            "identity": "card-a",
        }
        second = dict(first, identity="card-b")
        with (
            patch.object(installer_module, "IS_WINDOWS", False),
            patch.object(installer_module, "IS_LINUX", True),
            patch.object(
                self.installer,
                "list_safe_devices",
                side_effect=[[first], [second]],
            ),
            patch.object(self.installer, "_unmount_partitions", return_value=True),
        ):
            self.assertFalse(self.installer.flash_to_sd_card(str(target)))
        with target.open("rb") as written:
            self.assertEqual(written.read(16), b"\0" * 16)

    def test_rejects_invalid_zip_before_writing(self):
        self.archive.write_bytes(b"not a zip")
        self.installer.checksum_skipped = True
        self.assertIsNone(self.installer.inspect_sd_image())

    def test_session_log_is_durable(self):
        self.installer.log("durable-log-test")
        self.assertIsNotNone(self.installer.log_path)
        self.assertIn(
            "durable-log-test",
            self.installer.log_path.read_text(encoding="utf-8"),
        )
        self.assertIsNotNone(self.installer.latest_log_path)
        self.assertEqual(
            self.installer.latest_log_path.name,
            "installer-latest.log",
        )
        self.assertIn(
            "durable-log-test",
            self.installer.latest_log_path.read_text(encoding="utf-8"),
        )

    def test_windows_powershell_is_found_without_path_entry(self):
        windows_root = self.root / "Windows"
        powershell = (
            windows_root
            / "System32"
            / "WindowsPowerShell"
            / "v1.0"
            / "powershell.exe"
        )
        powershell.parent.mkdir(parents=True)
        powershell.write_bytes(b"test executable")
        disk_json = (
            '[{"Number":4,"Size":68719476736,"Model":"SD Reader",'
            '"BusType":"USB","UniqueId":"disk-id","SerialNumber":"card-id"}]'
        )
        completed = CompletedProcess([], 0, disk_json, "")
        with (
            patch.object(installer_module, "IS_WINDOWS", True),
            patch.dict(
                installer_module.os.environ,
                {"SystemRoot": str(windows_root), "PATH": ""},
            ),
            patch.object(installer_module.shutil, "which", return_value=None),
            patch.object(
                installer_module.subprocess,
                "run",
                return_value=completed,
            ) as run,
        ):
            devices = self.installer.list_safe_devices()
        self.assertEqual(devices[0]["path"], r"\\.\PhysicalDrive4")
        self.assertEqual(run.call_args.args[0][0], str(powershell))
        log_entries = []
        while not self.installer.log_queue.empty():
            log_entries.append(self.installer.log_queue.get_nowait())
        self.assertTrue(
            any("Windows disk scan: PhysicalDrive4" in entry for entry in log_entries)
        )


    def test_windows_sdhc_reader_is_accepted_even_when_reported_fixed(self):
        card = {
            "BusType": "USB",
            "MediaType": "External hard disk media",
            "Model": "Generic SD/MMC USB Device",
            "FriendlyName": "SDHC Card",
            "PNPDeviceID": r"USBSTOR\DISK&VEN_GENERIC&PROD_SD/MMC",
        }
        self.assertTrue(self.installer._is_windows_sd_candidate(card))

    def test_windows_scsi_removable_media_is_accepted(self):
        card = {
            "BusType": "SCSI",
            "MediaType": "Removable Media",
            "Model": "Generic STORAGE DEVICE",
        }
        self.assertTrue(self.installer._is_windows_sd_candidate(card))

    def test_windows_removable_volume_is_accepted_when_device_is_generic(self):
        card = {
            "BusType": "SCSI",
            "MediaType": "External hard disk media",
            "Model": "Generic STORAGE DEVICE",
            "HasRemovableVolume": True,
        }
        self.assertTrue(self.installer._is_windows_sd_candidate(card))

    def test_windows_fixed_usb_disk_and_system_disk_are_rejected(self):
        fixed_usb = {
            "BusType": "USB",
            "MediaType": "External hard disk media",
            "Model": "SanDisk External SSD USB Device",
            "FriendlyName": "External SSD",
            "PNPDeviceID": r"USBSTOR\DISK&VEN_SANDISK&PROD_EXTREME",
        }
        system_sd = {
            "BusType": "SD",
            "MediaType": "Removable Media",
            "Model": "SDHC Card",
            "IsSystem": True,
        }
        self.assertFalse(self.installer._is_windows_sd_candidate(fixed_usb))
        self.assertFalse(self.installer._is_windows_sd_candidate(system_sd))


@unittest.skipUnless(os.environ.get("DISPLAY"), "Tk requires a display")
class InstallerGUITests(unittest.TestCase):
    def test_log_queue_and_write_close_guard(self):
        root = installer_module.tk.Tk()
        root.withdraw()
        with patch.object(
            installer_module.RADXOIDInstaller,
            "list_safe_devices",
            return_value=[],
        ):
            gui = installer_module.RADXOIDGUI(root)
            gui.installer.log("visible-gui-log")
            gui.process_queues()
            self.assertIn("visible-gui-log", gui.log_text.get("1.0", "end"))

            gui.current_step = 2
            gui.flash_started = True
            gui.flash_result = None
            gui.update_step_indicator()
            gui.update_content_frame()
            with patch.object(installer_module.messagebox, "showwarning") as warning:
                gui.close_app()
                warning.assert_called_once()
            self.assertEqual(root.winfo_exists(), 1)

            gui.flash_result = False
            gui.close_app()

    def test_skipped_checksum_worker_cannot_revert_success(self):
        root = installer_module.tk.Tk()
        root.withdraw()
        gui = installer_module.RADXOIDGUI(root)
        gui.checksum_skipped = True
        gui._apply_worker_result("checksum", False, "late worker result", True)
        self.assertTrue(gui.checksum_result)
        gui.close_app()


if __name__ == "__main__":
    unittest.main()
