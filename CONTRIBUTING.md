# Contributing to Skaven Soundscape

Thank you for squeak-squeak-interest in contributing to this chaos-ridden codebase! This document outlines how to get started and the conventions we enforce.

---

## 🧰 Project Setup

- Python 3.9+
- [Poetry](https://python-poetry.org/docs/)
- VSCode with Python extension (recommended)

### Clone & Install

```bash
git clone git@github.com:kpeacocke/skaven-soundscape.git
cd skaven-soundscape
poetry install
```

### First-time Setup

```bash
make precommit-install
```

This installs pre-commit hooks for formatting, linting, typing, and commit message enforcement.

### Running the Project

```bash
make run  # Start the soundscape
```

### Building a Package

```bash
make package  # Build a distributable package
```

---

## ✅ Contributing Guidelines

### Branching & PRs

- Use `main` as your base branch.
- Create a new branch for each issue/feature:

  ```bash
  git checkout -b feature/fog-integration
  ```

- Every **pull request must be linked to a GitHub Issue** using the PR sidebar.
- All PRs are subject to CI validation and will be blocked if not compliant.

### Commit Messages

All commits must **reference a GitHub Issue** using one of:

- `fixes #<issue>`
- `closes #<issue>`
- `refs #<issue>`

**Examples:**

```bash
fixes #42 — rat eyes now blink with fog burst
closes #18 — sound loop uses ambient + scream tracks
refs #55 — added experimental warpstone effect trigger
```

These references are **enforced by pre-commit hooks**.

---

## 🧪 Quality Standards

Before you commit:

```bash
make format check
```

This will:

- Format with `black`
- Lint with `ruff`
- Type-check with `mypy`
- Run tests with `pytest`

---

## 🔁 Testing

Tests live in `tests/` and use `pytest`:

```bash
make test
```

To generate coverage:

```bash
make coverage
```

---

## 🚀 Releasing (for maintainers)

A CI workflow handles:

- Lint + Type + Test + Coverage
- Version bump + Tag + Release
- Auto-generated release notes from commits/issues

To manually bump version and create a release:

```bash
make all
git push
```

If everything passes on `main`, a new release will be tagged.

---

## 📦 Project Structure

```bash
skaven-soundscape/
├── skaven_soundscape/     # Main app code
├── tests/                 # Pytest tests
├── sounds/                # Audio assets
├── .vscode/               # Editor config
├── .github/workflows/     # CI/CD and release workflows
│   ├── check.yml          # Runs lint, test, typecheck, coverage
│   └── release.yml        # Tags and releases clean builds on main
├── .pre-commit-config.yaml
├── Makefile               # Local automation
├── deploy.sh              # Local version/deploy workflow
├── coverage_summary.txt   # Coverage summary for releases
└── pyproject.toml         # Poetry config
```

---

## 👥 Code Ownership

To request review, tag contributors listed in `.github/CODEOWNERS`.

---

## 🐀 The Horned Rat Blesses Your Contributions
