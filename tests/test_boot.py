from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from distroflash.boot import boot_files
from distroflash.images import ImageError


class BootTests(unittest.TestCase):
    def test_bundled_boot_components_have_expected_paths_and_hashes(self):
        entries = boot_files()
        self.assertEqual([name for _, name, _ in entries],
                         ["efi/boot/bootx64.efi", "efi/rufus/ntfs_x64.efi"])
        for path, _, size in entries:
            self.assertGreater(size, 1024)
            self.assertTrue(path.read_bytes().startswith(b"MZ"))

    def test_missing_or_corrupted_boot_component_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("distroflash.boot.ASSET_DIRECTORY", Path(tmp)):
                with self.assertRaises(ImageError):
                    boot_files()
                (Path(tmp)/"bootx64.efi").write_bytes(b"corrupt")
                with self.assertRaises(ImageError):
                    boot_files()
