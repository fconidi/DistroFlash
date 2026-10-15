from pathlib import Path
import unittest
from distroflash.udisks import UDisks


class Automounted(UDisks):
    def __init__(self):
        self.mounted = True
        self.calls = []

    def wait_interface(self, path, interface):
        return {"MountPoints": [list(b"/media/test\0")] if self.mounted else []}

    def properties(self, path, interface):
        return self.wait_interface(path, interface)

    def call(self, path, interface, method, signature=None, values=(), fds=None):
        self.calls.append(method)
        if method == "Unmount":
            self.mounted = False
            return (), None
        if method == "Mount":
            if self.mounted:
                raise RuntimeError("Already mounted")
            self.mounted = True
            return ("/media/test",), None
        raise AssertionError(method)


class UDisksTests(unittest.TestCase):
    def test_automount_is_replaced_with_requested_mount_options(self):
        storage = Automounted()
        self.assertEqual(storage.mount("/created-loop", readonly=True), Path("/media/test"))
        self.assertEqual(storage.calls, ["Unmount", "Mount"])

    def test_readonly_iso_automount_is_adopted_without_detaching_loop(self):
        class Readonly(Automounted):
            def properties(self, path, interface):
                if interface == "Block":
                    return {"ReadOnly": True}
                return super().properties(path, interface)
        storage = Readonly()
        self.assertEqual(storage.mount("/created-loop", readonly=True), Path("/media/test"))
        self.assertEqual(storage.calls, [])
