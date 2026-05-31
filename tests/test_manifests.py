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


def test_optional_assets_are_structured_archive_descriptors():
    index = build_index(ROOT)
    for package in index["packages"].values():
        assets = package["install"].get("optional_assets", [])
        for asset in assets:
            assert isinstance(asset, dict), (
                f"{package['name']} optional_assets entries must be archive descriptors, "
                f"not legacy marker values: {asset!r}"
            )
            assert asset.get("type") in {"skill_pack", "python_module_pack"}
            assert asset.get("source")
            assert asset.get("destination")
            assert asset.get("format") in {"tar.gz", "zip"}


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
    expected = {
        "skills-agent-clis",
        "skills-apple-macos",
        "skills-creative",
        "skills-dev-core",
        "skills-devops",
        "skills-finance",
        "skills-hermes-maintainer",
        "skills-mlops",
        "skills-mlops-cloud",
        "skills-mlops-eval-curation",
        "skills-mlops-inference",
        "skills-mlops-models",
        "skills-mlops-training",
        "skills-mlops-vector-db",
        "skills-media",
        "skills-productivity",
        "skills-research",
        "skills-security-osint",
    }

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
        "skills",
    }
    for destination, asset in by_destination.items():
        if destination.startswith("python-site-packages/"):
            assert asset["type"] == "python_module_pack"
            assert asset["format"] == "tar.gz"
            assert asset["source"].startswith("assets/python/")
            assert len(asset["sha256"]) == 64

    skill_asset = next(
        asset for asset in assets
        if isinstance(asset, dict) and asset.get("source") == "assets/skills/skills-kanban.tar.gz"
    )
    assert skill_asset["type"] == "skill_pack"
    assert skill_asset["destination"] == "skills"
    assert skill_asset["format"] == "tar.gz"
    assert len(skill_asset["sha256"]) == 64


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


def test_optional_platform_and_memory_packages_ship_python_assets():
    index = build_index(ROOT)

    discord = index["packages"]["discord"]
    discord_assets = discord["install"]["optional_assets"]
    assert len(discord_assets) == 1
    assert discord_assets[0]["type"] == "python_module_pack"
    assert discord_assets[0]["destination"] == "python-site-packages/plugins/platforms"
    assert discord_assets[0]["source"] == "assets/python/discord-platform-plugin.tar.gz"
    assert len(discord_assets[0]["sha256"]) == 64

    extra_platforms = index["packages"]["extra-platform-plugins"]
    assert extra_platforms["type"] == "plugin"
    assert extra_platforms["dependencies"] == ["gateway"]
    platform_assets = extra_platforms["install"]["optional_assets"]
    assert len(platform_assets) == 1
    assert platform_assets[0]["type"] == "python_module_pack"
    assert platform_assets[0]["destination"] == "python-site-packages/plugins/platforms"
    assert platform_assets[0]["source"] == "assets/python/extra-platform-plugins.tar.gz"
    assert len(platform_assets[0]["sha256"]) == 64

    memory = index["packages"]["memory-plugins"]
    assert memory["type"] == "plugin"
    memory_assets = memory["install"]["optional_assets"]
    assert len(memory_assets) == 1
    assert memory_assets[0]["type"] == "python_module_pack"
    assert memory_assets[0]["destination"] == "python-site-packages/plugins/memory"
    assert memory_assets[0]["source"] == "assets/python/memory-plugins.tar.gz"
    assert len(memory_assets[0]["sha256"]) == 64


def test_first_tranche_skill_packages_advertise_included_skills():
    index = build_index(ROOT)
    expected = {
        "skills-dev-core": {
            "software-development/writing-plans",
            "software-development/test-driven-development",
            "github/github-pr-workflow",
        },
        "skills-hermes-maintainer": {
            "autonomous-ai-agents/hermes-agent",
            "software-development/hermes-agent-skill-authoring",
            "mcp/native-mcp",
        },
        "skills-agent-clis": {
            "autonomous-ai-agents/claude-code",
            "autonomous-ai-agents/codex",
            "autonomous-ai-agents/opencode",
        },
        "dashboard": {
            "devops/kanban-orchestrator",
            "devops/kanban-worker",
            "autonomous-ai-agents/kanban-codex-lane",
        },
    }

    for package_name, skill_names in expected.items():
        contents = index["packages"][package_name].get("contents", {})
        assert skill_names <= set(contents.get("skills", []))


def test_second_wave_skill_packages_advertise_included_skills():
    index = build_index(ROOT)
    expected = {
        "skills-apple-macos": {
            "apple/apple-notes",
            "apple/apple-reminders",
            "apple/macos-computer-use",
        },
        "skills-media": {
            "media/spotify",
            "media/youtube-content",
            "media/gif-search",
        },
        "skills-finance": {
            "finance/3-statement-model",
            "finance/dcf-model",
            "finance/stocks",
        },
        "skills-devops": {
            "devops/docker-management",
            "devops/pinggy-tunnel",
            "devops/webhook-subscriptions",
        },
        "skills-security-osint": {
            "security/1password",
            "security/oss-forensics",
            "research/osint-investigation",
        },
        "skills-mlops-training": {
            "mlops/training/axolotl",
            "mlops/training/trl-fine-tuning",
            "mlops/training/unsloth",
        },
        "skills-mlops-inference": {
            "mlops/inference/vllm",
            "mlops/inference/outlines",
            "mlops/tensorrt-llm",
        },
        "skills-mlops-vector-db": {
            "mlops/chroma",
            "mlops/faiss",
            "mlops/qdrant",
        },
        "skills-mlops-cloud": {
            "mlops/lambda-labs",
            "mlops/modal",
        },
        "skills-mlops-models": {
            "mlops/clip",
            "mlops/llava",
            "mlops/stable-diffusion",
        },
        "skills-mlops-eval-curation": {
            "mlops/evaluation/lm-evaluation-harness",
            "mlops/nemo-curator",
            "mlops/huggingface-tokenizers",
        },
    }

    for package_name, skill_names in expected.items():
        contents = index["packages"][package_name].get("contents", {})
        assert skill_names <= set(contents.get("skills", []))


def test_tool_packages_advertise_attached_integration_skills():
    index = build_index(ROOT)
    expected = {
        "spotify": {"media/spotify"},
        "homeassistant": {"smart-home/openhue"},
        "web-search": {"research/duckduckgo-search", "research/searxng-search"},
        "mcp": {"mcp/native-mcp", "mcp/fastmcp", "mcp/mcporter"},
    }

    for package_name, skill_names in expected.items():
        package = index["packages"][package_name]
        contents = package.get("contents", {})
        assert skill_names <= set(contents.get("skills", []))
        skill_assets = [
            asset for asset in package["install"]["optional_assets"]
            if isinstance(asset, dict) and asset.get("type") == "skill_pack"
        ]
        assert skill_assets, f"{package_name} should install its attached skills"


def test_profile_bundle_packages_define_install_recipes():
    index = build_index(ROOT)
    expected_dependencies = {
        "profile-developer": [
            "skills-dev-core",
            "web-search",
            "browser",
        ],
        "profile-maintainer": [
            "skills-dev-core",
            "skills-hermes-maintainer",
            "skills-agent-clis",
            "dashboard",
            "mcp",
        ],
        "profile-research": [
            "skills-research",
            "web-search",
            "browser",
            "skills-productivity",
        ],
        "profile-mlops": [
            "skills-dev-core",
            "skills-mlops-training",
            "skills-mlops-inference",
            "skills-mlops-vector-db",
            "skills-mlops-cloud",
            "skills-mlops-models",
            "skills-mlops-eval-curation",
        ],
    }

    for package_name, dependencies in expected_dependencies.items():
        package = index["packages"][package_name]
        assert package["type"] == "bundle"
        assert package["channel"] == "community"
        assert package["dependencies"] == dependencies
        assert package["install"]["optional_assets"] == []
        assert package["security"]["post_install_scripts"] is False


def test_official_packages_do_not_enable_post_install_scripts():
    index = build_index(ROOT)
    for package in index["packages"].values():
        if package["channel"] == "official":
            assert package["security"]["post_install_scripts"] is False
