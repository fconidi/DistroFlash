from contextlib import contextmanager
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch

from distroflash.engine import PreparedImage, copy_files, run_tool, verify_files, _write_windows
from distroflash.streams import Cancelled


class MountedDirectory:
    def __init__(self, root):
        self.root = root
        self.active = False

    @contextmanager
    def mounted_iso(self, fd):
        self.active = True
        try:
            yield self.root
        finally:
            self.active = False


@unittest.skipUnless(shutil.which("wimlib-imagex"), "Installare wimtools")
class WindowsIntegrationTests(unittest.TestCase):
    def test_real_wim_is_copied_without_split_or_staging(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = root/"payload"
            payload.mkdir()
            # Exercise a real archive containing several independent resources.
            for i in range(4):
                (payload/f"data{i}").write_bytes(os.urandom(700 * 1024))
            iso_root = root/"iso"
            (iso_root/"sources").mkdir(parents=True)
            (iso_root/"efi/boot").mkdir(parents=True)
            (iso_root/"efi/boot/bootx64.efi").write_bytes(b"synthetic EFI fixture")
            (iso_root/"setup.exe").write_bytes(b"fixture")
            wim = iso_root/"sources/install.wim"
            subprocess.run(["wimlib-imagex", "capture", str(payload), str(wim),
                            "--compress=none", "--check", "--no-acls"], check=True,
                           stdout=subprocess.DEVNULL)
            shutil.copyfile(wim, iso_root/"sources/boot.wim")
            image_file = root/"windows.iso"
            image_file.write_bytes(b"synthetic image container")
            storage = MountedDirectory(iso_root)
            def fast_tool(arguments, cancel=None):
                self.assertEqual(arguments[1], "info", "Default preparation must only inspect WIM metadata")
                return run_tool(arguments, cancel)

            with patch("distroflash.engine.run_tool", side_effect=fast_tool):
                image = PreparedImage(image_file, storage)
            try:
                self.assertEqual(image.kind, "windows")
                self.assertTrue(any(name == "sources/install.wim" for _, name, _ in image.entries))
                self.assertFalse(any(name.endswith(".swm") for _, name, _ in image.entries))
                dest = root/"usb"
                dest.mkdir()
                manifest = copy_files(image.entries, dest)
                verify_files(dest, manifest)
                run_tool(["wimlib-imagex", "verify", str(dest/"sources/install.wim")])
                self.assertEqual((dest/"sources/install.wim").read_bytes(), wim.read_bytes())
            finally:
                image.close()
            self.assertFalse(storage.active)

    def test_large_wim_preparation_never_runs_split(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/"sources").mkdir()
            (root/"efi/boot").mkdir(parents=True)
            for name in ("sources/boot.wim", "sources/install.wim", "efi/boot/bootx64.efi"):
                (root/name).write_bytes(b"fixture")
            source = root/"image.iso"
            source.write_bytes(b"container")
            entries = {"sources/boot.wim": 7, "sources/install.wim": 8 * 1024**3,
                       "efi/boot/bootx64.efi": 7}
            def metadata_only(arguments, cancel=None):
                self.assertEqual(arguments[1], "info")
            with patch("distroflash.engine.scan_tree", return_value=entries), \
                    patch("distroflash.engine.run_tool", side_effect=metadata_only):
                image = PreparedImage(source, MountedDirectory(root))
            try:
                self.assertIn((root/"sources/install.wim", "sources/install.wim", 8 * 1024**3), image.entries)
            finally:
                image.close()

    def test_deep_check_detects_corrupt_payload_that_metadata_check_does_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = root/"payload"
            payload.mkdir()
            marker = b"unique uncompressed WIM payload" * 100
            (payload/"data").write_bytes(marker)
            iso = root/"iso"
            (iso/"sources").mkdir(parents=True)
            (iso/"efi/boot").mkdir(parents=True)
            (iso/"efi/boot/bootx64.efi").write_bytes(b"fixture")
            wim = iso/"sources/install.wim"
            subprocess.run(["wimlib-imagex", "capture", str(payload), str(wim),
                            "--compress=none", "--no-acls"], check=True, stdout=subprocess.DEVNULL)
            shutil.copyfile(wim, iso/"sources/boot.wim")
            data = bytearray(wim.read_bytes())
            offset = data.index(marker)
            data[offset] ^= 1
            wim.write_bytes(data)
            source = root/"image.iso"
            source.write_bytes(b"container")
            storage = MountedDirectory(iso)
            image = PreparedImage(source, storage)
            image.close()
            with self.assertRaises(ValueError):
                PreparedImage(source, storage, deep_check=True)
            self.assertFalse(storage.active)

    def test_invalid_wim_fails_before_any_device_operation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/"sources").mkdir()
            (root/"efi/boot").mkdir(parents=True)
            for name in ("sources/boot.wim", "sources/install.wim", "efi/boot/bootx64.efi"):
                (root/name).write_bytes(b"invalid data")
            source = root/"image.iso"
            source.write_bytes(b"container")
            storage = MountedDirectory(root)
            with self.assertRaises(ValueError):
                PreparedImage(source, storage)
            self.assertFalse(storage.active)


class WindowsWriteTests(unittest.TestCase):
    def test_readback_remains_required_without_another_wim_decompression(self):
        from types import SimpleNamespace
        for corrupt in (False, True):
            with self.subTest(corrupt=corrupt), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                source, target, boot = root/"source", root/"usb", root/"boot"
                source.write_bytes(b"original archive bytes")
                target.mkdir()
                boot.mkdir()
                image = SimpleNamespace(entries=[(source, "install.wim", source.stat().st_size)],
                                        kind="windows")
                mounts = []

                class Storage:
                    def format_windows(self, *args):
                        return "data", "boot"

                    def mount(self, part, readonly=False):
                        mounts.append((part, readonly))
                        if part == "data" and readonly and corrupt:
                            data = bytearray((target/"install.wim").read_bytes())
                            data[0] ^= 1
                            (target/"install.wim").write_bytes(data)
                        return target if part == "data" else boot

                    def properties(self, *args):
                        return {"DeviceNumber": target.stat().st_dev}

                    def unmount(self, part):
                        pass

                with patch("distroflash.engine.run_tool", side_effect=AssertionError("Redundant WIM pass")):
                    if corrupt:
                        with self.assertRaises(OSError):
                            _write_windows(image, "device", Storage(), lambda: None, None, lambda *a: None)
                    else:
                        _write_windows(image, "device", Storage(), lambda: None, None, lambda *a: None)
                        self.assertEqual((target/"install.wim").read_bytes(), source.read_bytes())
                self.assertEqual(mounts, [("boot", False), ("boot", True), ("data", False), ("data", True)])



class PreparationTests(unittest.TestCase):
    def test_raw_source_change_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)/"image.img"
            source.write_bytes(b"source")
            image = PreparedImage(source, None)
            try:
                source.write_bytes(b"changed")
                with self.assertRaises(ValueError):
                    image.check_source()
            finally:
                image.close()

    def test_preparation_cancel_releases_loop(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)/"image.iso"
            source.write_bytes(b"image")
            storage = MountedDirectory(Path(tmp))
            cancel = threading.Event()
            cancel.set()
            with self.assertRaises(Cancelled):
                PreparedImage(source, storage, cancel)
            self.assertFalse(storage.active)
