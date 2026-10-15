import argparse
import json
from . import __version__
from .i18n import tr


def main():
    parser = argparse.ArgumentParser(description=tr('DistroFlash — Linux and Windows USB'))
    parser.add_argument("--version", action="version", version="DistroFlash " + __version__)
    parser.add_argument("--list", action="store_true", help=tr('list usable USB/SD devices without making changes'))
    args = parser.parse_args()
    if args.list:
        from dataclasses import asdict
        from .devices import select_devices, snapshot
        print(json.dumps([asdict(d) for d in select_devices(snapshot())], indent=2))
        return 0
    from .gui import main as gui_main
    return gui_main()


if __name__ == "__main__":
    raise SystemExit(main())
