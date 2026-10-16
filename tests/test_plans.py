import unittest
from distroflash.images import FAT32_MAX, ImageError, windows_plan
from distroflash.devices import DeviceError, select_devices, validate_device


def disk(**changes):
    value = {"name": "/dev/sdz", "type": "disk", "size": 16 * 1024**3,
             "ro": False, "rm": True, "tran": "usb", "model": "USB",
             "serial": "123", "wwn": "", "maj:min": "8:240", "mountpoints": [],
             "children": [{"name": "/dev/sdz1", "type": "part", "ro": False,
                           "maj:min": "8:241", "mountpoints": []}]}
    value.update(changes)
    return value


def windows(**changes):
    entries = {"efi/boot/bootx64.efi": 100, "sources/boot.wim": 100,
               "sources/install.wim": 200, "setup.exe": 100}
    entries.update(changes)
    return entries


class ImageTests(unittest.TestCase):
    def test_large_wim_is_kept_whole_for_ntfs(self):
        plan = windows_plan(windows(**{"sources/install.wim": FAT32_MAX + 1}))
        self.assertEqual(dict(plan.files)["sources/install.wim"], FAT32_MAX + 1)
        self.assertGreater(plan.required_bytes, FAT32_MAX + 1)

    def test_small_wim_is_copied(self):
        self.assertEqual(dict(windows_plan(windows()).files), windows())

    def test_windows_paths_are_case_insensitive(self):
        self.assertIsNotNone(windows_plan({k.upper(): v for k, v in windows().items()}))

    def test_large_esd_is_supported_on_ntfs(self):
        entries = windows()
        del entries["sources/install.wim"]
        entries["sources/install.esd"] = FAT32_MAX + 1
        self.assertEqual(dict(windows_plan(entries).files), entries)

    def test_large_additional_file_is_supported_on_ntfs(self):
        entries = windows(**{"extra.bin": FAT32_MAX + 1})
        self.assertEqual(dict(windows_plan(entries).files), entries)

    def test_missing_uefi_rejected(self):
        entries = windows()
        del entries["efi/boot/bootx64.efi"]
        with self.assertRaises(ImageError):
            windows_plan(entries)

    def test_path_traversal_rejected(self):
        with self.assertRaises(ImageError):
            windows_plan(windows(**{"../escape": 1}))

    def test_fat_collisions_rejected(self):
        with self.assertRaises(ImageError):
            windows_plan(windows(**{"SETUP.EXE": 1}))

    def test_fat_invalid_name_rejected(self):
        with self.assertRaises(ImageError):
            windows_plan(windows(**{"sources/bad:name": 1}))


class DeviceTests(unittest.TestCase):
    def test_usb_is_eligible(self):
        self.assertEqual(len(select_devices([disk()])), 1)

    def test_internal_disk_rejected(self):
        self.assertEqual(select_devices([disk(tran="sata", rm=False)]), [])

    def test_root_on_usb_rejected(self):
        d = disk()
        d["children"][0]["mountpoints"] = ["/"]
        self.assertEqual(select_devices([d]), [])

    def test_swap_and_active_mapper_rejected(self):
        for mount, kind in [("[SWAP]", "part"), (None, "crypt"), (None, "lvm")]:
            d = disk()
            d["children"][0].update(mountpoints=[mount], type=kind)
            self.assertEqual(select_devices([d]), [])

    def test_mounted_media_visible_but_not_writable(self):
        d = disk()
        d["children"][0]["mountpoints"] = ["/media/user/USB"]
        target = select_devices([d])[0]
        with self.assertRaises(DeviceError):
            validate_device(target, [d], source_dev=0, required_bytes=1)

    def test_source_on_target_rejected(self):
        d = disk()
        import os
        with self.assertRaises(DeviceError):
            validate_device(select_devices([d])[0], [d], os.makedev(8, 241), 1)

    def test_replaced_device_rejected(self):
        target = select_devices([disk()])[0]
        with self.assertRaises(DeviceError):
            validate_device(target, [disk(serial="456")], 0, 1)

    def test_small_device_rejected(self):
        target = select_devices([disk()])[0]
        with self.assertRaises(DeviceError):
            validate_device(target, [disk()], 0, target.size + 1)

    def test_readonly_rejected(self):
        self.assertEqual(select_devices([disk(ro=True)]), [])


if __name__ == "__main__":
    unittest.main()
