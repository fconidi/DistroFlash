"""Image preparation and USB workflows; no custom privileged helper."""
from contextlib import ExitStack
from pathlib import Path
import fcntl
import os
import shutil
import stat
import subprocess
import tempfile
import time

from .devices import DeviceError, snapshot, validate_device
from .files import copy_files, verify_files
from .images import (FAT32_MAX, ImageError, is_windows, looks_like_iso,
                     scan_tree, validate_hybrid, windows_plan)
from .streams import Cancelled, checkpoint, copy_stream, verify_stream
from .i18n import tr

WIM_PART_MIB = 3800


def cache_directory():
    base = (Path.home()/".cache/distroflash").resolve()
    base.mkdir(parents=True, exist_ok=True, mode=0o700)
    return base


def run_tool(arguments, cancel=None):
    checkpoint(cancel)
    with tempfile.TemporaryFile(dir=cache_directory()) as log:
        with subprocess.Popen(arguments, stdout=log, stderr=subprocess.STDOUT) as process:
            while process.poll() is None:
                if cancel is not None and cancel.wait(0.1):
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    raise Cancelled(tr('Preparation cancelled.'))
                if cancel is None:
                    time.sleep(0.1)
            if process.returncode:
                log.seek(max(0, log.tell() - 2000))
                raise ImageError(tr('Command failed: ') + arguments[0] + "\n" + log.read().decode(errors="replace"))
    checkpoint(cancel)


def fingerprint(fd):
    value = os.fstat(fd)
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)


class PreparedImage:
    def __init__(self, path, storage, cancel=None, status=lambda message: None, *, deep_check=False):
        self.path = Path(path).expanduser().resolve(strict=True)
        self.storage = storage
        self.stack = ExitStack()
        self.closed = False
        try:
            self.source = self.stack.enter_context(self.path.open("rb", buffering=0))
            self.original = fingerprint(self.source.fileno())
            if not stat.S_ISREG(os.fstat(self.source.fileno()).st_mode) or self.original[2] == 0:
                raise ImageError(tr('Select a non-empty regular image file.'))
            self.kind, self.plan, self.root = "raw", None, None
            self.entries = []
            self.required_bytes = self.original[2]
            pinned = Path("/proc/self/fd")/str(self.source.fileno())
            # Check extension as well as the contents of the pinned descriptor.
            if self.path.suffix.lower() == ".iso" or looks_like_iso(pinned):
                status(tr('Inspecting ISO contents…'))
                self.root = self.stack.enter_context(storage.mounted_iso(self.source.fileno()))
                checkpoint(cancel)
                if is_windows(self.root):
                    self.kind = "windows"
                    self.plan = windows_plan(scan_tree(self.root))
                    self.required_bytes = self.plan.required_bytes
                    self._prepare_windows(cancel, status, deep_check)
                else:
                    validate_hybrid(pinned)
            elif self.path.suffix.lower() not in {".img", ".raw", ".bin"}:
                raise ImageError(tr('Supported formats: uncompressed ISO, IMG, RAW and BIN.'))
            checkpoint(cancel)
            self.check_source()
        except BaseException:
            self.close()
            raise

    def _prepare_windows(self, cancel, status, deep_check):
        if not shutil.which("wimlib-imagex"):
            raise ImageError(tr('Windows support requires wimtools (wimlib-imagex).'))
        lookup = {name.casefold(): name for name, _ in self.plan.files}
        status(tr('Checking Windows file integrity…') if deep_check else tr('Checking Windows image metadata…'))
        for key in ("sources/boot.wim", "sources/install.wim", "sources/install.esd"):
            if key in lookup:
                run_tool(["wimlib-imagex", "verify" if deep_check else "info",
                          str(self.root/lookup[key])], cancel)
        self.entries = [(self.root/name, name, size) for name, size in self.plan.files
                        if name != self.plan.split_wim]
        if self.plan.split_wim:
            status(tr('Splitting install.wim for FAT32…'))
            original = self.root/self.plan.split_wim
            required = original.stat().st_size + 64 * 1024**2
            if shutil.disk_usage(cache_directory()).free < required:
                raise ImageError(tr('Not enough local cache space to split install.wim.'))
            staging = Path(self.stack.enter_context(tempfile.TemporaryDirectory(
                prefix="windows-", dir=cache_directory())))
            run_tool(["wimlib-imagex", "split", str(original), str(staging/"install.swm"),
                      str(WIM_PART_MIB)], cancel)
            parts = sorted(staging.glob("install*.swm"))
            if not parts or any(p.stat().st_size > FAT32_MAX for p in parts):
                raise ImageError(tr('The WIM cannot be split into FAT32-compatible files.'))
            parent = Path(self.plan.split_wim).parent
            self.entries += [(part, (parent/part.name).as_posix(), part.stat().st_size) for part in parts]
            total = sum(size for _, _, size in self.entries)
            self.required_bytes = max(1024**3, total + total // 50 + 64 * 1024**2)

    def check_source(self):
        if self.closed or fingerprint(self.source.fileno()) != self.original:
            raise ImageError(tr('The source image changed. Select it again.'))

    def close(self):
        if not self.closed:
            self.closed = True
            self.stack.close()


def write_image(image, device, storage, cancel, report):
    image.check_source()
    required = image.required_bytes
    validate_device(device, snapshot(), image.original[0], required)
    path = storage.block_path(device.number)
    block = storage.properties(path, "Block")
    drive = block["Drive"]
    props = storage.properties(drive, "Drive")
    identity = tuple(props.get(k) for k in ("Id", "Serial", "TimeDetected", "TimeMediaDetected"))

    def guard():
        image.check_source()
        validate_device(device, snapshot(), image.original[0], required)
        current = storage.properties(path, "Block")
        now = storage.properties(drive, "Drive")
        if (current["DeviceNumber"] != device.number or current["Size"] != device.size
                or current["ReadOnly"] or current["Drive"] != drive
                or tuple(now.get(k) for k in ("Id", "Serial", "TimeDetected", "TimeMediaDetected")) != identity):
            raise DeviceError(tr('The device identity changed.'))

    # Prevent simultaneous operations by this user's DistroFlash processes.
    lock = cache_directory()/f"device-{device.number}.lock"
    with lock.open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        guard()
        checkpoint(cancel)
        if image.kind == "windows":
            _write_windows(image, path, storage, guard, cancel, report)
        else:
            fd = storage.open_device(path)
            with os.fdopen(fd, "r+b", buffering=0) as target:
                info = os.fstat(fd)
                if not stat.S_ISBLK(info.st_mode) or info.st_rdev != device.number:
                    raise DeviceError(tr('Invalid device descriptor.'))
                guard()
                image.source.seek(0)
                digest = copy_stream(image.source, target, image.original[2], cancel,
                                     lambda n, total: report(tr('Writing'), n, total))
                os.fsync(fd)
                if hasattr(os, "posix_fadvise"):
                    os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
                target.seek(0)
                verify_stream(target, image.original[2], digest, cancel,
                              lambda n, total: report(tr('Verifying'), n, total))
            storage.call(path, "Block", "Rescan", "(a{sv})", ({},))
        image.check_source()
        checkpoint(cancel)


def _write_windows(image, path, storage, guard, cancel, report):
    report(tr('Preparing Windows UEFI'), 0, 0)
    part = storage.format_windows(path, guard, lambda: checkpoint(cancel))
    mounted = False
    try:
        checkpoint(cancel)
        root = storage.mount(part)
        mounted = True
        expected = storage.properties(part, "Block")["DeviceNumber"]
        if root.stat().st_dev != expected:
            raise DeviceError(tr('The mounted filesystem does not match the created partition.'))
        if shutil.disk_usage(root).free < sum(size for _, _, size in image.entries):
            raise DeviceError(tr('Not enough FAT32 space after formatting.'))
        manifest = copy_files(image.entries, root, cancel,
                              lambda n, total: report(tr('Copying Windows'), n, total))
        # Read back every copied file, including split archives, using its SHA256.
        storage.unmount(part)
        mounted = False
        checkpoint(cancel)
        root = storage.mount(part, readonly=True)
        mounted = True
        if root.stat().st_dev != expected:
            raise DeviceError(tr('The partition changed during verification.'))
        verify_files(root, manifest, cancel, lambda n, total: report(tr('Verifying Windows'), n, total))
    finally:
        if mounted:
            storage.unmount(part)
