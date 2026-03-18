# Contributing

Thank you for your interest in retro-game-indexer! This document explains how to contribute.

## Branching Strategy

This project follows a **Git Flow** branching model adapted for a small open-source project.

```
main ─────●─────────────●─────────────●──── stable releases (tagged)
           \           /               \
develop ────●───●───●──●────●───●───●───●── integration branch
                 \     /         \     /
feature/xxx ──────●───●    feat/yyy ──●     feature branches
```

### Branch overview

| Branch | Purpose | Merges into | Protected |
|--------|---------|-------------|-----------|
| `main` | Stable releases only. Every commit is tagged (`v0.1.0`, `v0.2.0`, ...). | — | Yes |
| `develop` | Integration branch. All features are merged here first. | `main` (via release) | Yes |
| `feature/*` | New features or enhancements. | `develop` | No |
| `fix/*` | Bug fixes. | `develop` | No |
| `hotfix/*` | Urgent fixes on a released version. | `main` + `develop` | No |
| `release/*` | Release preparation (version bump, changelog, final tests). | `main` + `develop` | No |
| `docs/*` | Documentation-only changes. | `develop` | No |

### Workflow

#### New feature

```bash
git checkout develop
git pull origin develop
git checkout -b feature/visual-detection
# ... work ...
git push -u origin feature/visual-detection
# Open PR: feature/visual-detection → develop
```

#### Bug fix

```bash
git checkout develop
git checkout -b fix/alias-case-sensitivity
# ... fix ...
git push -u origin fix/alias-case-sensitivity
# Open PR: fix/alias-case-sensitivity → develop
```

#### Release

```bash
git checkout develop
git checkout -b release/v0.4.0
# Bump version in pyproject.toml, update CHANGELOG.md
git push -u origin release/v0.4.0
# Open PR: release/v0.4.0 → main
# After merge: tag main as v0.4.0, merge main back into develop
```

#### Hotfix (urgent fix on released version)

```bash
git checkout main
git checkout -b hotfix/critical-bug
# ... fix ...
git push -u origin hotfix/critical-bug
# Open PR: hotfix/critical-bug → main
# After merge: tag, merge main back into develop
```

### Commit messages

Use clear, imperative-mood messages:

```
Add visual detection pipeline with CLIP embeddings
Fix case-sensitivity bug in alias lookup
Update known_titles.json with N64 games
Refactor data lake module for better error handling
```

Prefix with scope when helpful:

```
datasets: expand known_titles with Mega Drive games
cli: add --export flag for CSV output
docs: update roadmap for v0.5.0
```

### Versioning

This project uses [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.0.0) — breaking changes to CLI interface or data formats
- **MINOR** (0.x.0) — new features, new commands, new pipelines
- **PATCH** (0.0.x) — bug fixes, dataset updates, documentation

## Development setup

```bash
git clone https://github.com/cmellojr/retro-game-indexer.git
cd retro-game-indexer
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows
pip install -e .
```

## Expanding datasets

The easiest way to contribute is by expanding the JSON datasets in `datasets/reference/`:

- **`games/known_titles.json`** — add game titles for better validation
- **`games/aliases.json`** — map common misspellings or fragments to canonical names
- **`games/stopwords.json`** — add false positives to filter out
- **`maintenance/known_terms.json`** — add tools, components, and mod names

For personal overrides that shouldn't be committed, use `datasets/community/` (gitignored).

## Code style

- **Style guide**: Google Python Style Guide
- **Docstrings**: Google format (`Args:`, `Returns:`, `Raises:`)
- **Type hints**: Python 3.12+ syntax (`list[dict]`, `str | None`)
- **Linter**: `ruff check src/`
