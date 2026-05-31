# Hermes-Packages

Package registry for NanoHermes / Hermes Agent tools, skills, MCP servers, providers, and optional feature bundles.

This repo is intentionally boring: package manifests live under `packages/`, scripts validate them, and `registry/index.json` is the generated index consumed by `hermes pkg` / `hermes plug`.

## Goals

- Keep NanoHermes core small.
- Move optional tools into explicit packages.
- Move optional skills into explicit checksummed skill-pack assets.
- Make installed tool and skill availability honest and inspectable.
- Support apt-like flows:
  - `hermes pkg update`
  - `hermes pkg search web`
  - `hermes pkg show web-search`
  - `hermes pkg install web-search`
  - `hermes pkg remove browser`
  - `hermes pkg upgrade`

## Registry layout

```text
packages/
  official/<name>/package.toml
  skills/<name>/package.toml
  mcp/<name>/package.toml
  community/README.md
assets/
  skills/<name>.tar.gz
registry/
  index.json
  index.min.json
  checksums.txt
schemas/
  package.schema.json
  registry.schema.json
scripts/
  build_index.py
  validate_package.py
tests/
  test_manifests.py
  test_index_schema.py
```

## Skill pack assets

Packages can bundle skills by declaring archive-backed assets under `install.optional_assets`. Large first-party skill categories are shipped this way instead of being bundled into every NanoHermes wheel.

```toml
[install]
optional_assets = [
  { type = "skill_pack", source = "assets/skills/skills-creative.tar.gz", format = "tar.gz", sha256 = "...", destination = "skills", overwrite = false },
]
```

Packages that ship skills should also advertise those skill paths through `contents.skills` so clients can show and search package contents without downloading the archive:

```toml
[contents]
skills = [
  "software-development/writing-plans",
  "github/github-pr-workflow",
]
```

`hermes pkg install ...` resolves relative asset paths from this registry, verifies the checksum, rejects unsafe archive members, and extracts into `$HERMES_HOME/skills`. This lets tool packages and standalone skill packages ship matching procedural memory without bloating the NanoHermes base wheel.

## Current status

Bootstrap registry with official toolset packages plus first-party skill-pack assets. Manifests and optional skill-pack assets are schema-checked and indexed for the NanoHermes package-manager client.
