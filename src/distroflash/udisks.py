"""UDisks2 D-Bus transport. Privileged operations are authorized by Polkit.

API: https://storaged.org/doc/udisks2-api/latest/
FD passing: https://docs.gtk.org/gio/method.DBusConnection.call_with_unix_fd_list_sync.html
"""
from contextlib import contextmanager
from pathlib import Path
import os
import time
from gi.repository import Gio, GLib
from .i18n import tr

BUS = "org.freedesktop.UDisks2"
BASE = "/org/freedesktop/UDisks2"


def options(**values):
    return {k.replace("_", "-"): GLib.Variant(
        "b" if isinstance(v, bool) else "i" if isinstance(v, int) else "s", v)
        for k, v in values.items()}


class UDisks:
    def __init__(self):
        self.bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)

    def call(self, path, interface, method, signature=None, values=(), fds=None):
        parameters = GLib.Variant(signature, values) if signature else None
        # Never cancel a daemon-side mutation mid-flight: wait for the result,
        # then honor cooperative cancellation before starting the next phase.
        reply, output = self.bus.call_with_unix_fd_list_sync(
            BUS, path, BUS + "." + interface, method, parameters, None,
            Gio.DBusCallFlags.ALLOW_INTERACTIVE_AUTHORIZATION, 3600000, fds, None)
        return reply.unpack(), output

    def objects(self):
        return self.bus.call_sync(BUS, BASE, "org.freedesktop.DBus.ObjectManager",
                                 "GetManagedObjects", None, None, Gio.DBusCallFlags.NONE,
                                 15000, None).unpack()[0]

    def properties(self, path, interface):
        return self.objects()[path][BUS + "." + interface]

    def wait_interface(self, path, interface):
        for _ in range(100):
            obj = self.objects().get(path, {})
            if BUS + "." + interface in obj:
                return obj[BUS + "." + interface]
            time.sleep(0.1)
        raise RuntimeError(tr('Device not ready: ') + interface)

    def block_path(self, number):
        for path, interfaces in self.objects().items():
            if interfaces.get(BUS + ".Block", {}).get("DeviceNumber") == number:
                return path
        raise RuntimeError(tr('The device is no longer available in UDisks2.'))

    def mount(self, path, readonly=False):
        self.wait_interface(path, "Filesystem")
        opts = options(options="ro,nosuid,nodev,noexec" if readonly else "rw,nosuid,nodev,noexec")
        for attempt in range(3):
            filesystem = self.properties(path, "Filesystem")
            if filesystem.get("MountPoints"):
                if readonly and self.properties(path, "Block").get("ReadOnly"):
                    # Adopt a readonly ISO automount. Unmounting it can make
                    # the desktop detach the loop before a replacement Mount.
                    return Path(os.fsdecode(bytes(filesystem["MountPoints"][0]).rstrip(b"\0")))
                self.unmount(path)
            try:
                result, _ = self.call(path, "Filesystem", "Mount", "(a{sv})", (opts,))
                return Path(result[0])
            except GLib.Error as error:
                if (Gio.DBusError.get_remote_error(error) != BUS + ".Error.AlreadyMounted"
                        or attempt == 2):
                    raise
        raise RuntimeError(tr('Mount operation did not complete.'))

    def unmount(self, path):
        self.call(path, "Filesystem", "Unmount", "(a{sv})", ({},))

    @contextmanager
    def mounted_iso(self, fd):
        descriptors = Gio.UnixFDList.new()
        handle = descriptors.append(fd)
        result, _ = self.call(BASE + "/Manager", "Manager", "LoopSetup", "(ha{sv})",
                              (handle, options(read_only=True, no_part_scan=True)), descriptors)
        loop = result[0]
        number = self.properties(loop, "Block")["DeviceNumber"]
        backing = Path("/sys/dev/block")/f"{os.major(number)}:{os.minor(number)}"/"loop/backing_file"
        expected_backing = backing.read_text()
        try:
            yield self.mount(loop, readonly=True)
        finally:
            # Also handles automounts when our own Mount call failed. Detaching
            # a mounted loop merely requests autoclear and would leak a mount.
            interfaces = self.objects().get(loop, {})
            if interfaces.get(BUS + ".Filesystem", {}).get("MountPoints"):
                self.unmount(loop)
            # The desktop may have detached it as part of Unmount already.
            if backing.exists() and backing.read_text() == expected_backing:
                self.call(loop, "Loop", "Delete", "(a{sv})", ({},))

    def open_device(self, path):
        result, descriptors = self.call(path, "Block", "OpenDevice", "(sa{sv})",
                                        ("rw", options(flags=os.O_EXCL | os.O_CLOEXEC)))
        return descriptors.get(result[0])

    def format_windows(self, path, guard, checkpoint):
        guard()
        checkpoint()
        self.call(path, "Block", "Format", "(sa{sv})", ("gpt", {}))
        checkpoint()
        self.wait_interface(path, "PartitionTable")
        guard()
        # Native FAT32 EFI System Partition: no downloaded bootloader needed.
        result, _ = self.call(path, "PartitionTable", "CreatePartitionAndFormat",
                              "(ttssa{sv}sa{sv})",
                              (1024**2, 0, "c12a7328-f81f-11d2-ba4b-00a0c93ec93b",
                               "Windows", {}, "vfat", options(label="DISTROFLASH")))
        part = result[0]
        self.wait_interface(part, "Filesystem")
        version = self.properties(part, "Block").get("IdVersion")
        if version != "FAT32":
            raise RuntimeError(tr("The created filesystem is not FAT32. No Windows files were copied."))
        return part
