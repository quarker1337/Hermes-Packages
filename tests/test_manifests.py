from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_index import build_index, load_manifest  # noqa: E402


def test_all_manifests_load_and_match_paths():
    manifests = sorted(ROOT.glob("packages/*/*/package.toml"))
    assert manifests, "expected package manifests"
    for manifest in manifests:
        data = load_manifest(manifest)
        assert data["name"] == manifest.parent.name
        assert data["channel"] == manifest.parts[-3]


def test_expected_bootstrap_packages_exist():
    index = build_index(ROOT)
    expected = {
        "web-search", "browser", "dashboard", "tts", "voice", "image-gen",
        "gateway", "cron", "kanban", "discord", "discord-admin", "yuanbao",
        "feishu", "spotify", "homeassistant",
    }
    assert expected <= set(index["packages"])


def test_optional_skill_category_packages_ship_skill_pack_assets():
    index = build_index(ROOT)
    expected = {"skills-creative", "skills-mlops", "skills-productivity", "skills-research"}

    assert expected <= set(index["packages"])
    for package_name in expected:
        package = index["packages"][package_name]
        assets = package["install"]["optional_assets"]
        assert package["type"] == "skill"
        assert package["channel"] == "skills"
        assert len(assets) == 1
        asset = assets[0]
        assert asset["type"] == "skill_pack"
        assert asset["format"] == "tar.gz"
        assert asset["destination"] == "skills"
        assert asset["source"].startswith("assets/skills/")
        assert len(asset["sha256"]) == 64


def test_official_packages_do_not_enable_post_install_scripts():
    index = build_index(ROOT)
    for package in index["packages"].values():
        if package["channel"] == "official":
            assert package["security"]["post_install_scripts"] is False
