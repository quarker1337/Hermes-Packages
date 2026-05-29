# Hermes-Packages

Package registry for NanoHermes / Hermes Agent tools, skills, MCP servers, providers, and optional feature bundles.

This repo is intentionally boring: package manifests live under `packages/`, scripts validate them, and `registry/index.json` is the generated index consumed by `hermes pkg` / `hermes plug`.

## Goals

- Keep NanoHermes core small.
- Move optional tools into explicit packages.
- Make installed tool availability honest and inspectable.
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

## Build

```bash
python scripts/build_index.py
python -m pytest tests/ -q
```

## Current status

Bootstrap registry. Official package manifests are schema-checked and indexed, but the NanoHermes package-manager client will land in `nanoHermes` next.
