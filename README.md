# 🐀 Skaven Soundscape

An immersive, randomized soundscape system for Skaven-themed Warhammer Age of Sigmar display boards.

🎵 Loops ambient sewer sounds
🐁 Plays randomized rat noises, chain rattles, and occasional screams
💡 Optional LED/servo/fog integration via Raspberry Pi GPIO
🔬 Fully CI/CD enforced with linting, typing, testing, and coverage
🧠 All commits & PRs must reference GitHub Issues (enforced)

---

## 📦 Requirements

- Python 3.9+
- Poetry (for development/build)
- Pygame for audio
- Optional: Raspberry Pi + GPIO hardware for effects

---

## 🛠️ Installation & Usage

You can install and run the Skaven Soundscape as a proper Python package:

```bash
# Install dependencies (dev)
poetry install

# Or install as a package (pip, editable mode)
pip install -e .

# Run the main soundscape system (CLI entry point)
skaven --help
skaven           # Starts the soundscape (sound, video, lighting)
play-video       # Play only the video loop
```

---

### 📝 Package Metadata

This project is bundled as a modern Python package using [PEP 517/518] and Poetry. Entry points are declared in `pyproject.toml`:

```toml
[tool.poetry.scripts]
skaven = "skaven.main:main"
play-video = "skaven.video_loop:main"
```

---

## 🧪 Testing, Linting, Type Checking

Run all checks:

```bash
make check
```

Run individually:

```bash
make lint      # ruff + black
make format    # autoformat code
make test      # pytest
make coverage  # text summary
make coverage-html
make type      # mypy
make package   # Build a distributable package
```

---

### 🧼 Pre-commit Hook Setup

```bash
make precommit-install
```

Will auto-run:

- black
- ruff
- mypy
- commit message format (fixes #123)

---

### 🧾 Commit Message Guidelines

All commits must reference a GitHub Issue:

- fixes #42 – sync bell servo with scream
- refs #88 – play scream when fog triggered

---

### 🔁 GitHub Workflows

| Workflow                | Triggers           | What It Does                                 |
|-------------------------|--------------------|----------------------------------------------|
| check.yml               | push/PR to main    | Lint, type check, test, coverage + PR comment|
| release.yml             | push to main after CI | Auto-tags + releases with changelog      |
| require-linked-issue.yml| all PRs            | Enforces sidebar-linked GitHub Issue         |
| consumer-typecheck.yml  | push/PR to main    | Verifies type exposure for consumers         |
| pre-commit              | local Git          | Blocks bad commits, auto-fixes code style    |

---

### 🚀 Releasing

Push to main with all checks passing.

`release.yml` tags the next patch version (e.g. v0.1.2).

Release notes are generated from commits + issue refs.

You’ll see a new GitHub Release on the repo.

---

### 🧱 Folder Structure

skaven_soundscape/
│   main.py
tests/
sounds/
├── ambient/
├── rats/
├── chains/
└── screams/
coverage.txt
coverage_summary.txt
Makefile

---

### 📚 Contributing

See CONTRIBUTING.md for commit rules, branching, PR templates, and CI rules.

All PRs must reference a GitHub Issue (closes #123) and be linked in the PR sidebar (this is enforced).

🧙‍♂️ Glory to the Great Horned One

This project is maintained by Kristian Peacocke.
