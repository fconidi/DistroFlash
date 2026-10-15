"""Conservative USB/SD selection, revalidated immediately before mutation."""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import os
import subprocess


class DeviceError(ValueError):
    pass


@dataclass(frozen=True)
class Device:
    path: str
    size: int
    model: str
    serial: str
    number: int
    identity: str


def descendants(node):
    yield node
    for child in node.get("children", []):
        yield from descendants(child)


def device_number(value):
    major, minor = value.split(":")
    return os.makedev(int(major), int(minor))


def allowed(node):
    if node.get("type") != "disk" or not (node.get("tran") == "usb" or node.get("rm")):
        return False
    if not node.get("size") or not node.get("maj:min"):
        return False
    for child in descendants(node):
        if child.get("ro") or child.get("busy") or child.get("type") not in {"disk", "part"}:
            return False
        if child.get("fstype", "").lower() in {"btrfs", "lvm2_member", "crypto_luks", "linux_raid_member", "zfs_member"}:
            return False
        for mount in child.get("mountpoints") or []:
            if mount and not mount.startswith(("/media/", "/run/media/")):
                return False
    return True


def describe(node):
    fields = [node.get(k) for k in ("name", "size", "serial", "wwn", "maj:min", "sysfs")]
    identity = hashlib.sha256(json.dumps(fields).encode()).hexdigest()
    return Device(node["name"], int(node["size"]), (node.get("model") or "USB/SD").strip(),
                  node.get("serial") or "", device_number(node["maj:min"]), identity)


def select_devices(nodes):
    return [describe(n) for n in nodes if allowed(n)]


def validate_device(expected, nodes, source_dev, required_bytes):
    node = next((n for n in nodes if n["name"] == expected.path), None)
    if node is None or not allowed(node) or describe(node).identity != expected.identity:
        raise DeviceError("Dispositivo rimosso, cambiato o non sicuro. Aggiorna l'elenco.")
    for child in descendants(node):
        if device_number(child["maj:min"]) == source_dev:
            raise DeviceError("Il dispositivo contiene l'immagine sorgente.")
        if any(child.get("mountpoints") or []):
            raise DeviceError("Smonta prima tutte le partizioni del dispositivo.")
    if expected.size < required_bytes:
        raise DeviceError("Dispositivo troppo piccolo per l'immagine.")
    return node


def snapshot():
    # Explicit columns: https://man7.org/linux/man-pages/man8/lsblk.8.html
    command = ["lsblk", "--json", "--bytes", "--paths", "--output",
               "NAME,TYPE,SIZE,RO,RM,TRAN,MODEL,SERIAL,WWN,MAJ:MIN,MOUNTPOINTS,FSTYPE"]
    data = json.loads(subprocess.run(command, check=True, capture_output=True, text=True,
                                     timeout=15).stdout)["blockdevices"]
    for top in data:
        for node in descendants(top):
            sys = Path("/sys/dev/block") / node["maj:min"]
            node["sysfs"] = str(sys.resolve(strict=True))
            node["busy"] = any((sys / "holders").iterdir())
            node["fstype"] = node.get("fstype") or ""
    return data
