# 🐀 Skaven Soundscape

---

## ⚡ Quick Start

1. **Clone the repo & install dependencies:**

   ```zsh
   git clone https://github.com/kpeacocke/skaven-soundscape.git
   cd skaven-soundscape
   poetry install
   cp .env.example .env  # Edit as needed
   ```

2. **Run the soundscape:**

   ```zsh
   make run
   # or
   poetry run skaven
   ```

---

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

### Environment Variables

Configuration is managed via environment variables. See `.env.example` for all options:

```env
SOUND_VOLUME=0.75
USE_GPIO=true
DEBUG_MODE=false
```

Copy `.env.example` to `.env` and adjust as needed for your setup.

### Platform Notes

- **Linux (Raspberry Pi recommended):**
  - All features supported (audio, GPIO, video, lighting, fog, etc.)
  - Install `python3-dev`, `libasound2-dev`, and other audio/GPIO dependencies as needed.
  - For GPIO: `USE_GPIO=true` in your `.env` and ensure you have the correct permissions (often requires running as root or configuring groups).

- **macOS:**
  - Audio and video playback supported (no GPIO/fog/servo integration).
  - Install Python 3.9+ (e.g., via Homebrew: `brew install python@3.9`)
  - Some dependencies may require Xcode command line tools: `xcode-select --install`
  - Set `USE_GPIO=false` in your `.env` (default)

---

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

See `CONTRIBUTING.md` for commit rules, branching, PR templates, and CI rules.
See `.env.example` for environment variable setup.
For platform-specific setup, see the Platform Notes above.

All PRs must reference a GitHub Issue (closes #123) and be linked in the PR sidebar (this is enforced).

🧙‍♂️ Glory to the Great Horned One

This project is maintained by Kristian Peacocke.
