from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch

from distroflash.engine import PreparedImage, copy_files, run_tool, verify_files
from distroflash.images import windows_plan
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
    def test_real_wim_split_copy_and_integrity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = root/"payload"
            payload.mkdir()
            # Several resources allow a genuine multipart archive at 1 MiB.
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
            original_plan = windows_plan

            def force_split(entries):
                return replace(original_plan(entries), split_wim="sources/install.wim")

            with patch("distroflash.engine.windows_plan", force_split), patch("distroflash.engine.WIM_PART_MIB", 1):
                image = PreparedImage(image_file, storage)
            staging = image.entries[-1][0].parent
            try:
                self.assertEqual(image.kind, "windows")
                parts = [e for e in image.entries if e[1].endswith(".swm")]
                self.assertGreater(len(parts), 1)
                dest = root/"usb"
                dest.mkdir()
                manifest = copy_files(image.entries, dest)
                verify_files(dest, manifest)
                run_tool(["wimlib-imagex", "verify", str(dest/"sources/install.swm"),
                          "--ref=" + str(dest/"sources/install*.swm")])
                self.assertFalse((dest/"sources/install.wim").exists())
            finally:
                image.close()
            self.assertFalse(storage.active)
            self.assertFalse(staging.exists())

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
