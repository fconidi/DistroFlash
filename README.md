# DistroFlash

<img src="src/distroflash/logo.svg" alt="DistroFlash logo" width="96">

A native Linux application for creating Linux and Windows USB installation media.

DistroFlash uses a three-step GTK interface: choose an image, select the USB/SD device,
then write and verify. It runs as a normal user; UDisks2 and Polkit authorize storage
operations. No telemetry or online account is required.

## Supported images

- **Linux:** hybrid USB-bootable ISO files and uncompressed IMG, RAW or BIN images.
- **Windows:** standard Windows 10/11 x64 installation ISOs with UEFI boot files.
  The device receives a GPT partition table, a main NTFS partition containing the
  original Windows files, and a small FAT EFI System Partition with the bundled
  UEFI:NTFS loader and NTFS driver. Files above 4 GiB are copied whole; no WIM
  splitting, recompression or temporary payload staging is needed.

The initial version targets Windows **UEFI x64**. Windows legacy BIOS, ARM64,
custom ISOs and existing split-WIM source layouts are not supported. Firmware and
Secure Boot compatibility depend on the original Windows boot files and firmware
policy; universal boot compatibility is not guaranteed. There is no persistence.

## Installation

On Debian, Ubuntu or SysLinuxOS, install the downloaded Debian package:

```sh
sudo apt install ./distroflash_0.2.2_all.deb
```

Launch **DistroFlash** from the applications menu or run `distroflash`.
Do not launch the application with sudo. An active desktop Polkit authentication
agent must be available.

To run directly from the source directory:

```sh
sudo apt install python3-gi gir1.2-gtk-3.0 udisks2 dosfstools ntfs-3g wimtools util-linux
PYTHONPATH=src /usr/bin/python3 -m distroflash
```

To build the Debian package, run `/usr/bin/python3 build-deb.py`.
The package is written to `~/.cache/distroflash/packages/`.

## Using DistroFlash

1. Select an image. Windows archive metadata is checked before any destination is erased.
   Enable **Deep Windows integrity check (slower)** in the image chooser for a full
   archive check, including decompression and internal checksums.
2. Select the USB/SD device. Use **Unmount partitions** if it is mounted.
3. Select **Write and verify**, then type the displayed device path to confirm erasure.
4. Wait for verification to finish, then use **Eject**.

Every written file is read back and checked with SHA256, including Windows
archives and the UEFI:NTFS boot components. This confirms the copy matches its
source. The optional deep check also detects corruption inside the source Windows
archives; metadata checks alone do not.

**All data on the selected destination will be erased.** Cancellation leaves the
media incomplete; recreate it before use. Internal disks, devices with active
storage mappings, Btrfs filesystems, system mounts and the source-image device
are excluded. Refresh the device list after connecting or removing media.

Windows image selection performs a quick content and archive-metadata check.
Copying starts after device selection and confirmation; no multi-gigabyte
preparation files are created. UEFI:NTFS is included for offline use.
See [third-party components](THIRD-PARTY.md) for source and license information.

## Languages

The interface, progress and application error messages automatically follow the
system language: **English, Italian, French, German and Spanish**. English is the
fallback for unsupported locales. `LC_ALL`, `LC_MESSAGES`, `LANG` and the `LANGUAGE`
preference list are respected; the C/POSIX locale uses English. Messages returned
by system services and external tools follow those tools’ own locale settings.

`distroflash --version` prints the version; `distroflash --list` lists eligible
USB/SD devices without changing them.

## Italiano

DistroFlash crea chiavette USB Linux e Windows con interfaccia GTK, controlli sui
dispositivi e verifica finale. Le ISO Windows vengono preparate per **UEFI x64**;
i file originali vengono copiati interi su NTFS, senza suddivisione WIM. Una piccola
partizione FAT contiene UEFI:NTFS per l’avvio. Nessuna persistenza.
La lingua viene rilevata automaticamente, con inglese predefinito e supporto
italiano, francese, tedesco e spagnolo.
La preparazione Windows usa controlli rapidi dei metadati; il controllo approfondito
degli archivi è facoltativo nella finestra di scelta dell’immagine. La verifica
SHA256 dei file scritti sulla chiavetta resta sempre attiva.

## License

Copyright © 2026 Franco Conidi. Licensed under GPL-3.0-or-later; see [LICENSE](LICENSE).
