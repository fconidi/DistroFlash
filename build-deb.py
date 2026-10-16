#!/usr/bin/python3
"""Build a Debian package entirely in the local cache."""
import argparse
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


def main():
    source = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Build the DistroFlash Debian package")
    parser.add_argument("--output-dir", type=Path, default=Path.home()/".cache/distroflash/packages")
    output = parser.parse_args().output_dir.expanduser().resolve()
    if output == source or source in output.parents:
        parser.error("Use an output directory outside the source tree")
    output.mkdir(parents=True, exist_ok=True)
    version = re.search(r'__version__ = "([^"]+)"',
                        (source/"src/distroflash/__init__.py").read_text()).group(1)
    with tempfile.TemporaryDirectory(prefix="package-", dir=output) as staging:
        root = Path(staging)
        package = root/"usr/share/distroflash/distroflash"
        package.mkdir(parents=True)
        for module in (source/"src/distroflash").glob("*.py"):
            shutil.copyfile(module, package/module.name)
        logo = source/"src/distroflash/logo.svg"
        shutil.copyfile(logo, package/"logo.svg")
        icons = root/"usr/share/icons/hicolor/scalable/apps"
        icons.mkdir(parents=True)
        shutil.copyfile(logo, icons/"org.syslinuxos.DistroFlash.svg")
        binary = root/"usr/bin/distroflash"
        binary.parent.mkdir(parents=True)
        shutil.copyfile(source/"packaging/distroflash", binary)
        binary.chmod(0o755)
        desktop = root/"usr/share/applications"
        desktop.mkdir(parents=True)
        shutil.copyfile(source/"packaging/org.syslinuxos.DistroFlash.desktop",
                        desktop/"org.syslinuxos.DistroFlash.desktop")
        docs = root/"usr/share/doc/distroflash"
        docs.mkdir(parents=True)
        shutil.copyfile(source/"LICENSE", docs/"copyright")
        shutil.copyfile(source/"README.md", docs/"README.md")
        control = root/"DEBIAN"
        control.mkdir()
        (control/"control").write_text(
            f"Package: distroflash\nVersion: {version}\nArchitecture: all\n"
            "Section: utils\nPriority: optional\n"
            "Maintainer: Franco Conidi <fconidi@gmail.com>\n"
            "Depends: python3 (>= 3.11), python3-gi, gir1.2-gtk-3.0, udisks2 (>= 2.9), util-linux, dosfstools, wimtools\n"
            "Recommends: polkit-1-auth-agent\n"
            "Homepage: https://github.com/fconidi/DistroFlash\n"
            "Description: Create Linux and Windows bootable USB media\n"
            " Native GTK image writer with readback verification and Windows UEFI support.\n")
        artifact = output/f"distroflash_{version}_all.deb"
        subprocess.run(["dpkg-deb", "--root-owner-group", "--build", str(root), str(artifact)], check=True)
        print(artifact)


if __name__ == "__main__":
    main()
