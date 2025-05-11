# Contributing to Skaven Soundscape

Thank you for squeak-squeak-interest in contributing to this chaos-ridden codebase! This document outlines how to get started and the conventions we enforce.

---

## 🧰 Project Setup

### Platform Prerequisites

- **Linux (Raspberry Pi):**
  - Install `python3-dev`, `libasound2-dev`, and any required GPIO/audio libraries.
  - For GPIO support, set `USE_GPIO=true` in your `.env` and ensure your user has the correct permissions.
- **macOS:**
  - Install Python 3.9+ (e.g., `brew install python@3.9`)
  - Set `USE_GPIO=false` in your `.env` (default)
  - Some dependencies may require Xcode command line tools: `xcode-select --install`

### Environment Variables

- Copy `.env.example` to `.env` and edit as needed for your environment.
- See `.env.example` for all available configuration options.

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

## 🌀 Branching Model (GitFlow)

We follow the **GitFlow** branching model to ensure a clean, maintainable, and release-ready codebase at all times.

### 🧱 Branch Types

| Branch Type     | Prefix      | Purpose                                    |
|-----------------|-------------|--------------------------------------------|
| `main`          | —           | Always deployable. Tagged releases only.   |
| `develop`       | —           | Integration branch. All features merge here. |
| Feature branch  | `feature/`  | New functionality and enhancements         |
| Bugfix branch   | `fix/`      | Non-hotfix bug corrections                 |
| Hotfix branch   | `hotfix/`   | Emergency fix for `main`                   |
| Release branch  | `release/`  | Final polishing before tagging             |

### 🛠 Workflow Summary

1. **New work?**

   ```bash
   git checkout develop
   git pull
   git checkout -b feature/<thing>
   ```

2. **Complete your work, commit regularly**, referencing an issue (e.g. `fixes #42`).

3. **Open a PR against `develop`**.
   - Must pass all CI checks
   - Must link a GitHub Issue via PR sidebar (enforced by workflow)

4. **Prepare a release**:

   ```bash
   git checkout develop
   git checkout -b release/v0.1.0
   # Optional: update version or docs
   git push origin release/v0.1.0
   ```

   Merge into `main`, tag it, and let GitHub Actions handle the release.

5. **Hotfixes** go directly from `main`:

   ```bash
   git checkout main
   git checkout -b hotfix/serious-bug
   ```

### 🧪 PR & Commit Rules

✅ All commits must include an issue reference: `fixes #123`
✅ PRs must target `develop`, not `main`
✅ PRs must use sidebar **Linked Issues** field (required, enforced)
✅ PRs require review and passing CI
✅ `main` and `develop` are protected branches

---

This structure ensures:

- Clean history
- Safe deployment
- Clear changelogs
- Happy contributors 🐀

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
