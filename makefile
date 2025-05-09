.PHONY: install run test coverage lint format check all coverage-html commit-clean \
		precommit-install precommit-run apply-ruleset-main apply-ruleset-develop

install:
	poetry install

run:
	poetry run python -m skaven.main

test:
	poetry run pytest

coverage:
	poetry run coverage run -m pytest
	poetry run coverage report -m

coverage-html:
	poetry run coverage run -m pytest
	poetry run coverage html
	open htmlcov/index.html  # macOS; use xdg-open on Linux

lint:
	poetry run ruff check .
	poetry run mypy src
	poetry run black --check .

format:
	poetry run black .
	poetry run ruff check . --fix

check: test coverage lint

commit-clean: format lint test
	git add .
	git commit -m "chore: format, lint, and test passed"

all: install check

precommit-install:
	poetry run pre-commit install

precommit-run:
	poetry run pre-commit run --all-files

# === Ruleset automation ===

GITHUB_TOKEN ?= $(shell grep GITHUB_TOKEN .secrets.env | cut -d '=' -f2)
REPO_NAME ?= skaven-soundscape
REPO_OWNER ?= kpeacocke

apply-ruleset-main:
	@echo "Applying ruleset-main.json to $(REPO_OWNER)/$(REPO_NAME)"
	curl -X POST \
	  -H "Authorization: Bearer $(GITHUB_TOKEN)" \
	  -H "Accept: application/vnd.github+json" \
	  https://api.github.com/repos/$(REPO_OWNER)/$(REPO_NAME)/rulesets \
	  -d @rulesets/ruleset-main.json

apply-ruleset-develop:
	@echo "Applying ruleset-develop.json to $(REPO_OWNER)/$(REPO_NAME)"
	curl -X POST \
	  -H "Authorization: Bearer $(GITHUB_TOKEN)" \
	  -H "Accept: application/vnd.github+json" \
	  https://api.github.com/repos/$(REPO_OWNER)/$(REPO_NAME)/rulesets \
	  -d @rulesets/ruleset-develop.json

package:
	poetry build
