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


def test_dashboard_package_bundles_kanban_python_assets():
    index = build_index(ROOT)
    dashboard = index["packages"]["dashboard"]
    kanban = index["packages"]["kanban"]

    assert dashboard["tools"]["toolsets"] == ["kanban"]
    assert kanban["dependencies"] == ["dashboard"]
    assert kanban["tools"]["toolsets"] == []

    assets = dashboard["install"]["optional_assets"]
    by_destination = {asset["destination"]: asset for asset in assets if isinstance(asset, dict)}
    assert set(by_destination) >= {
        "python-site-packages/hermes_cli",
        "python-site-packages/tools",
        "python-site-packages/plugins/kanban",
    }
    for destination, asset in by_destination.items():
        if destination.startswith("python-site-packages/"):
            assert asset["type"] == "python_module_pack"
            assert asset["format"] == "tar.gz"
            assert asset["source"].startswith("assets/python/")
            assert len(asset["sha256"]) == 64


def test_china_provider_and_gateway_packages_ship_python_assets():
    index = build_index(ROOT)

    gateway_platforms = index["packages"]["china-gateway-platforms"]
    assert gateway_platforms["type"] == "plugin"
    assert gateway_platforms["dependencies"] == ["gateway"]
    gateway_assets = gateway_platforms["install"]["optional_assets"]
    assert len(gateway_assets) == 1
    assert gateway_assets[0]["type"] == "python_module_pack"
    assert gateway_assets[0]["destination"] == "python-site-packages/gateway/platforms"
    assert gateway_assets[0]["source"] == "assets/python/china-gateway-platforms.tar.gz"
    assert len(gateway_assets[0]["sha256"]) == 64

    model_providers = index["packages"]["china-model-providers"]
    assert model_providers["type"] == "provider"
    provider_assets = model_providers["install"]["optional_assets"]
    assert len(provider_assets) == 1
    assert provider_assets[0]["type"] == "python_module_pack"
    assert provider_assets[0]["destination"] == "python-site-packages/plugins"
    assert provider_assets[0]["source"] == "assets/python/china-model-providers.tar.gz"
    assert len(provider_assets[0]["sha256"]) == 64


def test_official_packages_do_not_enable_post_install_scripts():
    index = build_index(ROOT)
    for package in index["packages"].values():
        if package["channel"] == "official":
            assert package["security"]["post_install_scripts"] is False
