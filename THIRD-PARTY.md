# Third-party boot components

DistroFlash includes the unmodified x64 UEFI:NTFS loader and NTFS driver from
the `res/uefi/uefi-ntfs.img` image distributed with **Rufus 4.15**, commit
`6d8fbf98305ff37eb531c45cbd6ff44563c53917`:

https://github.com/pbatard/rufus/tree/6d8fbf98305ff37eb531c45cbd6ff44563c53917/res/uefi

- `bootx64.efi`: UEFI:NTFS 2.8, copyright Pete Batard and contributors,
  GPL-2.0-or-later. Source:
  https://github.com/pbatard/uefi-ntfs/tree/42de94dce5a0be68aab4e410494bb9d986dbcac4
- `ntfs_x64.efi`: NTFS-3G UEFI driver 1.9, copyright its respective contributors,
  GPL-2.0-or-later. Source:
  https://github.com/pbatard/ntfs-3g/tree/a2226ecd8344a427a7ad79fbb878f3244c7af393

The binaries retain their upstream Secure Boot signatures. Firmware trust and
revocation databases determine whether a particular machine accepts them.
License texts are included in `licenses/`. DistroFlash's Python code is licensed
under GPL-3.0-or-later. These components are bundled; no runtime download is needed.
