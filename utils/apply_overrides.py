import argparse
import sys
from pathlib import Path
from typing import Final

import yaml

from .yaml import load_yamls

BASE_YAML: Final = Path("golem-cluster.yaml")
LOCAL_OVERRIDE_YAML: Final = Path("golem-cluster.local.yaml")


def main():
    parser = argparse.ArgumentParser("Apply YAML overrides and output a complete YAML.")
    parser.add_argument("overrides", type=Path, nargs="*", help="Overrides to apply")
    parser.add_argument(
        "--base", "-b", type=Path, default=BASE_YAML, help="Base YAML file, default: %(default)s"
    )
    parser.add_argument(
        "--local",
        "-l",
        type=Path,
        default=LOCAL_OVERRIDE_YAML,
        help="Local override file, default: %(default)s",
    )
    parser.add_argument("--out", "-o", type=Path, help="Output file, default: stdout")
    args = parser.parse_args()

    yaml_files = [args.base]
    yaml_files.extend(args.overrides)

    if args.local.exists():
        yaml_files.append(args.local)

    data = load_yamls(*yaml_files)

    if args.out:
        with open(args.out, "w") as f:
            yaml.dump(data, f)
    else:
        yaml.dump(data, sys.stdout)


if __name__ == "__main__":
    main()
