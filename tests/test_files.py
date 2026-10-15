from pathlib import Path
import tempfile
import unittest
from distroflash.engine import copy_files, verify_files
from distroflash.streams import TransferError
from distroflash.images import ImageError, scan_tree


class FileTests(unittest.TestCase):
    def test_copy_and_verify_windows_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, dest = root/"source", root/"dest"
            (source/"EFI/Boot").mkdir(parents=True)
            dest.mkdir()
            (source/"EFI/Boot/bootx64.efi").write_bytes(b"EFI file")
            (source/"setup.exe").write_bytes(b"setup")
            entries = [(source/name, name, size) for name, size in scan_tree(source).items()]
            manifest = copy_files(entries, dest)
            verify_files(dest, manifest)
            self.assertEqual((dest/"EFI/Boot/bootx64.efi").read_bytes(), b"EFI file")
            (dest/"setup.exe").write_bytes(b"bad!!")
            with self.assertRaises(TransferError):
                verify_files(dest, manifest)

    def test_source_symlinks_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/"link").symlink_to("/etc/passwd")
            with self.assertRaises(ImageError):
                scan_tree(root)

    def test_destination_parent_symlink_is_not_followed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest, outside = root/"dest", root/"outside"
            dest.mkdir()
            outside.mkdir()
            (dest/"sources").symlink_to(outside, target_is_directory=True)
            source = root/"source"
            source.write_bytes(b"payload")
            with self.assertRaises(OSError):
                copy_files([(source, "sources/install.wim", 7)], dest)
            self.assertEqual(list(outside.iterdir()), [])

    def test_existing_destination_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, dest = root/"source", root/"dest"
            source.write_bytes(b"new")
            dest.mkdir()
            (dest/"setup.exe").write_bytes(b"old")
            with self.assertRaises(FileExistsError):
                copy_files([(source, "setup.exe", 3)], dest)
            self.assertEqual((dest/"setup.exe").read_bytes(), b"old")

    def test_destination_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root/"source"
            source.write_bytes(b"data")
            with self.assertRaises(ValueError):
                copy_files([(source, "../escape", 4)], root)
            self.assertFalse((root.parent/"escape").exists())

    def test_open_directory_remains_pinned_after_path_is_replaced(self):
        import os
        from distroflash.files import open_beneath
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root/"usb"
            target.mkdir()
            fd = os.open(target, os.O_RDONLY | os.O_DIRECTORY)
            try:
                target.rename(root/"original-usb")
                target.mkdir()
                with open_beneath(fd, "payload", True) as stream:
                    stream.write(b"data")
                self.assertEqual((root/"original-usb/payload").read_bytes(), b"data")
                self.assertFalse((target/"payload").exists())
            finally:
                os.close(fd)
