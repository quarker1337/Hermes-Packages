#!/usr/bin/env python3
"""Validate one or more Hermes package manifests."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_index import load_manifest  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", nargs="+", help="package.toml file(s)")
    args = parser.parse_args(argv)
    for item in args.manifest:
        data = load_manifest(Path(item).resolve())
        print(f"ok {data['name']} {data['version']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
