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
    def test_windows_layout_has_whole_ntfs_data_and_a_small_efi_partition(self):
        class Formatting(UDisks):
            def __init__(self):
                self.created = []
                self.formatted = []

            def wait_interface(self, *args):
                return {}

            def properties(self, path, interface):
                if interface == "Filesystem":
                    return {"MountPoints": []}
                if interface == "Partition":
                    return {"Table": "disk"}
                if path == "disk":
                    return {"Size": 16 * 1024**3}
                return {"IdType": dict(self.formatted)[path]}

            def call(self, path, interface, method, signature=None, values=(), fds=None):
                if method == "CreatePartition":
                    self.created.append(values)
                    return ("part" + str(len(self.created)),), None
                self.assert_format(method)
                self.formatted.append((path, values[0]))
                return (), None

            def assert_format(self, method):
                if method != "Format":
                    raise AssertionError(method)

        storage = Formatting()
        self.assertEqual(storage.format_windows("disk", lambda: None, lambda: None), ("part1", "part2"))
        self.assertEqual(storage.formatted, [("disk", "gpt"), ("part2", "vfat"), ("part1", "ntfs")])
        data, boot = storage.created
        self.assertEqual(data[0], 1024**2)
        self.assertEqual(data[0] + data[1], boot[0])
        self.assertEqual(boot[1], 4 * 1024**2)
        self.assertLess(boot[0] + boot[1], 16 * 1024**3)

        class ForeignPartition(Formatting):
            def properties(self, path, interface):
                if interface == "Partition":
                    return {"Table": "another-disk"}
                return super().properties(path, interface)

        storage = ForeignPartition()
        with self.assertRaises(RuntimeError):
            storage.format_windows("disk", lambda: None, lambda: None)
        self.assertEqual(storage.formatted, [("disk", "gpt")])

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
