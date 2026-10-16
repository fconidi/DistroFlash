# Changelog

## 0.2.0

- Create Windows media with a main NTFS partition and a small UEFI:NTFS boot partition.
- Copy large Windows WIM/ESD files whole, eliminating split preparation and temporary payload storage.
- Bundle signed x64 UEFI:NTFS components for offline use and verify their integrity before writing.
- Verify both Windows files and UEFI boot files after copying.

## 0.1.1

- Speed up Windows preparation with metadata checks and optional deep archive verification.
- Remove repeated WIM verification passes while retaining SHA256 verification of all written files.
- Add a DistroFlash logo to the application and desktop launcher.

## 0.1.0

- Create USB/SD media from hybrid Linux ISO and raw images.
- Prepare Windows x64 UEFI installation media, including split WIM archives.
- Verify written data and protect system and source devices.
- Add native GTK interface with progress, cancellation, unmounting and ejection.
- Detect the desktop language automatically: English, Italian, French, German and Spanish.
