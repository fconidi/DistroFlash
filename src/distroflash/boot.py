"""Pinned, signed x64 UEFI:NTFS components distributed with DistroFlash."""
from pathlib import Path
import hashlib

from .images import ImageError
from .i18n import tr

ASSET_DIRECTORY = Path(__file__).with_name("uefi")
BOOT_PART_BYTES = 4 * 1024**2
FILES = (
    ("bootx64.efi", "efi/boot/bootx64.efi",
     "5e22e6209ea557fce49cdbab7d06be4fc99e65d45c4fba01da928e763776bb94"),
    ("ntfs_x64.efi", "efi/rufus/ntfs_x64.efi",
     "d77e7f1c317a42467d3f7ade7b3e0a20996b9bf541492fbc15d6245d8d46dcac"),
)


def boot_files():
    entries = []
    for filename, destination, expected in FILES:
        path = ASSET_DIRECTORY/filename
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ImageError(tr('The bundled UEFI:NTFS boot files are missing or damaged. Reinstall DistroFlash.'))
        entries.append((path, destination, path.stat().st_size))
    return entries
