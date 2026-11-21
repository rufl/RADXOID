import hashlib
import importlib.util
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

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
            patch.object(
                self.installer,
                "list_safe_devices",
                side_effect=[[device], [device]],
            ),
            patch.object(self.installer, "_unmount_partitions", return_value=True),
            patch.object(installer_module.os, "geteuid", return_value=0),
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
