import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_index import build_index  # noqa: E402


def test_registry_index_shape():
    index = build_index(ROOT)
    assert index["schema_version"] == 1
    assert index["package_count"] == len(index["packages"])
    assert isinstance(index["packages"], dict)
    for name, package in index["packages"].items():
        assert package["name"] == name
        assert package["manifest_path"].endswith("package.toml")
        assert len(package["manifest_sha256"]) == 64


def test_generated_index_payload_is_current():
    current = json.loads((ROOT / "registry" / "index.json").read_text())
    rebuilt = build_index(ROOT)
    assert current["packages"] == rebuilt["packages"]
