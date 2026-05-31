#!/usr/bin/env python3
"""Build registry/index.json from package manifests."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_TOP_LEVEL = {
    "schema_version", "name", "display_name", "version", "type",
    "channel", "description", "install", "permissions",
}
VALID_CHANNELS = {"official", "skills", "mcp", "community"}
VALID_TYPES = {"toolset", "skill", "mcp", "provider", "bundle", "plugin"}
ASSET_DESTINATION_ROOTS = {"skills", "optional-skills", "optional-mcps", "python-site-packages"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest(path: Path) -> dict:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    missing = sorted(REQUIRED_TOP_LEVEL - set(data))
    if missing:
        raise ValueError(f"{path}: missing required fields: {', '.join(missing)}")
    if data["channel"] not in VALID_CHANNELS:
        raise ValueError(f"{path}: invalid channel {data['channel']!r}")
    if data["type"] not in VALID_TYPES:
        raise ValueError(f"{path}: invalid type {data['type']!r}")
    if path.parts[-3] != data["channel"]:
        raise ValueError(f"{path}: channel {data['channel']!r} does not match directory {path.parts[-3]!r}")
    if path.parent.name != data["name"]:
        raise ValueError(f"{path}: name {data['name']!r} does not match directory {path.parent.name!r}")
    return data


def normalize_optional_assets(package: dict, manifest_path: Path, root: Path) -> dict:
    install = package.get("install")
    if not isinstance(install, dict):
        return package
    assets = install.get("optional_assets", [])
    if not assets:
        return package

    normalized_assets = []
    for asset in assets:
        if not isinstance(asset, dict):
            # Legacy symbolic assets (for example browser runtime payloads) are
            # kept as-is until those installers become first-class package
            # assets. Archive-backed skill packs use dict entries below.
            normalized_assets.append(asset)
            continue
        asset = dict(asset)
        source = str(asset.get("source", "")).strip()
        destination = str(asset.get("destination", "")).strip()
        if not source:
            raise ValueError(f"{manifest_path}: optional asset missing source")
        if not destination:
            raise ValueError(f"{manifest_path}: optional asset missing destination")
        destination_root = destination.replace("\\", "/").split("/", 1)[0]
        if destination_root not in ASSET_DESTINATION_ROOTS:
            allowed = ", ".join(sorted(ASSET_DESTINATION_ROOTS))
            raise ValueError(
                f"{manifest_path}: optional asset destination must start with one of: {allowed}"
            )
        if destination_root == "python-site-packages" and "/" not in destination.replace("\\", "/"):
            raise ValueError(
                f"{manifest_path}: python-site-packages asset destination must include a package subdirectory"
            )
        asset_path = root / source
        if not asset_path.is_file():
            raise ValueError(f"{manifest_path}: optional asset source does not exist: {source}")
        if not str(asset.get("sha256", "")).strip():
            asset["sha256"] = sha256_file(asset_path)
        normalized_assets.append(asset)

    package = dict(package)
    package["install"] = dict(install)
    package["install"]["optional_assets"] = normalized_assets
    return package


def build_index(root: Path = ROOT) -> dict:
    manifests = sorted(root.glob("packages/*/*/package.toml"))
    packages: dict[str, dict] = {}
    for manifest_path in manifests:
        data = load_manifest(manifest_path)
        name = data["name"]
        if name in packages:
            raise ValueError(f"duplicate package name: {name}")
        rel = manifest_path.relative_to(root).as_posix()
        data = dict(data)
        data = normalize_optional_assets(data, manifest_path, root)
        data["manifest_path"] = rel
        data["manifest_sha256"] = sha256_file(manifest_path)
        packages[name] = data
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "package_count": len(packages),
        "packages": packages,
    }


def write_outputs(index: dict, root: Path = ROOT) -> None:
    reg = root / "registry"
    reg.mkdir(exist_ok=True)
    (reg / "index.json").write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (reg / "index.min.json").write_text(json.dumps(index, separators=(",", ":"), sort_keys=True) + "\n", encoding="utf-8")
    lines = []
    for name, pkg in sorted(index["packages"].items()):
        lines.append(f"{pkg['manifest_sha256']}  {pkg['manifest_path']}  # {name}")
    (reg / "checksums.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if generated index differs")
    args = parser.parse_args(argv)
    index = build_index()
    if args.check:
        expected = json.dumps(index, indent=2, sort_keys=True) + "\n"
        current_path = ROOT / "registry" / "index.json"
        if not current_path.exists():
            print("registry/index.json is missing", file=sys.stderr)
            return 1
        current = current_path.read_text(encoding="utf-8")
        # generated_at changes each run; compare stable package payload instead
        cur_data = json.loads(current)
        if cur_data.get("packages") != index.get("packages"):
            print("registry/index.json package payload is stale", file=sys.stderr)
            return 1
        return 0
    write_outputs(index)
    print(f"Wrote {len(index['packages'])} packages to registry/index.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
