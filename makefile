.PHONY: \
	install run test coverage lint format check all coverage-html commit-clean \
	precommit-install precommit-run apply-ruleset-main apply-ruleset-develop \
	clean help package

.DEFAULT_GOAL := help

POETRY = poetry
PYTHON = $(POETRY) run python

help:  ## Show this help message
	@awk 'BEGIN {FS = ":.*?## "}; /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install:  ## Install dependencies using Poetry
	$(POETRY) install

run:  ## Run the main application
	$(PYTHON) -m skaven.main

test:  ## Run all tests
	$(POETRY) run pytest


coverage:  ## Run tests with coverage and show report
	PYTHONPATH=src $(POETRY) run pytest --cov=skaven --cov-report=term-missing


coverage-html:  ## Generate and open HTML coverage report
	PYTHONPATH=src $(POETRY) run pytest --cov=skaven --cov-report=html
	@if command -v open > /dev/null; then open htmlcov/index.html; \
	elif command -v xdg-open > /dev/null; then xdg-open htmlcov/index.html; fi

lint:  ## Run ruff, mypy, and black --check
	$(POETRY) run ruff check .
	$(POETRY) run mypy src
	$(POETRY) run black --check .

format:  ## Auto-format code with black and ruff
	$(POETRY) run black .
	$(POETRY) run ruff check . --fix

check:  ## Run tests, coverage, and lint
	$(MAKE) test
	$(MAKE) coverage
	$(MAKE) lint

commit-clean: format lint test  ## Format, lint, test, and commit
	git add .
	git commit -m "chore: format, lint, and test passed"

all:  ## Install dependencies and run all checks
	$(MAKE) install
	$(MAKE) check

precommit-install:  ## Install pre-commit hooks
	$(POETRY) run pre-commit install

precommit-run:  ## Run all pre-commit hooks
	$(POETRY) run pre-commit run --all-files

clean:  ## Remove build, test, and coverage artifacts
	rm -rf .pytest_cache .mypy_cache htmlcov dist build *.egg-info
	find . -name '*.pyc' -delete

# === Ruleset automation ===

GITHUB_TOKEN ?= $(shell grep GITHUB_TOKEN .secrets.env | cut -d '=' -f2)
REPO_NAME ?= skaven-soundscape
REPO_OWNER ?= kpeacocke

apply-ruleset-main:  ## Apply main ruleset to GitHub repo
	@if [ -z "$(GITHUB_TOKEN)" ]; then \
		echo "GITHUB_TOKEN not set!"; exit 1; \
	fi
	@echo "Applying ruleset-main.json to $(REPO_OWNER)/$(REPO_NAME)"
	curl -X POST \
		-H "Authorization: Bearer $(GITHUB_TOKEN)" \
		-H "Accept: application/vnd.github+json" \
		https://api.github.com/repos/$(REPO_OWNER)/$(REPO_NAME)/rulesets \
		-d @rulesets/ruleset-main.json

apply-ruleset-develop:  ## Apply develop ruleset to GitHub repo
	@if [ -z "$(GITHUB_TOKEN)" ]; then \
		echo "GITHUB_TOKEN not set!"; exit 1; \
	fi
	@echo "Applying ruleset-develop.json to $(REPO_OWNER)/$(REPO_NAME)"
	curl -X POST \
		-H "Authorization: Bearer $(GITHUB_TOKEN)" \
		-H "Accept: application/vnd.github+json" \
		https://api.github.com/repos/$(REPO_OWNER)/$(REPO_NAME)/rulesets \
		-d @rulesets/ruleset-develop.json

package:  ## Build the package with Poetry
	$(POETRY) build
