"""Content-based Windows planning. No device mutation in this module."""
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import os
import stat
from .i18n import tr

FAT32_MAX = 2**32 - 1
MIB = 1024**2


class ImageError(ValueError):
    pass


@dataclass(frozen=True)
class WindowsPlan:
    files: tuple[tuple[str, int], ...]
    split_wim: str | None
    required_bytes: int


def windows_plan(entries: dict[str, int]) -> WindowsPlan:
    names = {}
    components = {}
    for name, size in entries.items():
        path = PurePosixPath(name)
        if (not name or path.is_absolute() or ".." in path.parts
                or str(path) != name or size < 0):
            raise ImageError(tr('Invalid image path: {0}').format(name))
        for index, part in enumerate(path.parts):
            if (any(c in part for c in '\\:*?"<>|') or part.endswith((".", " "))
                    or any(ord(c) < 32 for c in part)
                    or len(part.encode("utf-16-le")) > 510):
                raise ImageError(tr('Name incompatible with FAT32: {0}').format(name))
            component = "/".join(path.parts[:index + 1])
            key = component.casefold()
            if key in components and components[key] != component:
                raise ImageError(tr('Conflicting names on FAT32: {0}').format(name))
            components[key] = component
        key = name.casefold()
        if key in names:
            raise ImageError(tr('Duplicate names: {0}').format(name))
        names[key] = name
    required = ("efi/boot/bootx64.efi", "sources/boot.wim")
    if any(k not in names for k in required):
        raise ImageError(tr('The Windows ISO must contain x64 UEFI boot files and sources/boot.wim.'))
    payloads = [names[k] for k in ("sources/install.wim", "sources/install.esd") if k in names]
    if len(payloads) != 1:
        raise ImageError(tr('Exactly one sources/install.wim or install.esd is required.'))
    split = None
    for name, size in entries.items():
        if size == 0 and name.casefold() in (*required, "sources/install.wim", "sources/install.esd"):
            raise ImageError(tr('Empty Windows file: {0}').format(name))
        if size > FAT32_MAX:
            if name.casefold() != "sources/install.wim":
                raise ImageError(tr('File exceeds the FAT32 limit: {0}. Only install.wim can be split.').format(name))
            split = name
    if any(k.startswith("sources/install") and k.endswith(".swm") for k in names):
        raise ImageError(tr('ISOs with existing .swm files are not supported in this version.'))
    total = sum(entries.values())
    return WindowsPlan(tuple(sorted(entries.items())), split, max(1024**3, total + total // 50 + 64 * MIB))


def scan_tree(root: Path) -> dict[str, int]:
    """Reject links/special files instead of following untrusted image entries."""
    entries = {}
    pending = [root]
    while pending:
        directory = pending.pop()
        with os.scandir(directory) as children:
            for child in children:
                info = child.stat(follow_symlinks=False)
                path = Path(child.path)
                if stat.S_ISDIR(info.st_mode):
                    pending.append(path)
                elif stat.S_ISREG(info.st_mode):
                    entries[path.relative_to(root).as_posix()] = info.st_size
                else:
                    raise ImageError(tr('Link or special file in the image: {0}').format(path.name))
    return entries


def is_windows(root: Path) -> bool:
    names = {p.name.casefold(): p for p in root.iterdir()}
    if "bootmgr" in names or "setup.exe" in names:
        return True
    sources = names.get("sources")
    return bool(sources and sources.is_dir() and any(
        p.name.casefold() in {"boot.wim", "install.wim", "install.esd", "install.swm"}
        for p in sources.iterdir()))


def looks_like_iso(path: Path) -> bool:
    with path.open("rb") as stream:
        stream.seek(16 * 2048)
        header = stream.read(48 * 2048)
    return path.suffix.lower() == ".iso" or any(
        header[i + 1:i + 6] in (b"CD001", b"BEA01", b"NSR02", b"NSR03")
        for i in range(0, len(header), 2048))


def validate_hybrid(path: Path):
    with path.open("rb") as stream:
        header = stream.read(512)
    if (len(header) != 512 or header[510:] != b"\x55\xaa"
            or not any(header[446 + 16 * i + 4] for i in range(4))):
        raise ImageError(tr('This ISO is not recognized as USB hybrid. No data was written.'))
