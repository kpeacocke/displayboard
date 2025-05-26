.PHONY: \
	install run run-dev test coverage lint format check all coverage-html commit-clean \
	precommit-install precommit-run clean clean-pyc distclean build help package \
	launch check-coverage release

.DEFAULT_GOAL := help

POETRY = poetry
PYTHON = $(POETRY) run python

help:  ## Show this help message
	@awk 'BEGIN {FS = ":.*?## "}; /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install:  ## Install dependencies using Poetry
	$(POETRY) install


run:  ## Run main application
	@echo "Running main application..."
	$(PYTHON) -m displayboard.main


run-dev:  ## Run the main application in development mode
	@echo "Running main application in development mode..."
	$(PYTHON) -m displayboard.main

test:  ## Run all tests
	$(POETRY) run pytest


coverage:  ## Run tests with coverage and show report
	PYTHONPATH=src $(POETRY) run pytest --cov=displayboard --cov-report=term-missing


coverage-html:  ## Generate and open HTML coverage report
	PYTHONPATH=src $(POETRY) run pytest --cov=displayboard --cov-report=html
	@if command -v open > /dev/null; then open htmlcov/index.html; \
	elif command -v xdg-open > /dev/null; then xdg-open htmlcov/index.html; fi


check-coverage:  ## Fail if coverage is below 80%
	PYTHONPATH=src $(POETRY) run pytest --cov=displayboard --cov-fail-under=80

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
	@echo "Formatting, linting, testing, and committing..."
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

clean-pyc:  ## Remove Python file artifacts
	find . -name '*.pyc' -delete
	find . -name '*.pyo' -delete
	find . -name '__pycache__' -type d -exec rm -rf {} +

distclean: clean clean-pyc  ## Remove all build, test, coverage, and venv artifacts
	rm -rf .venv venv

build:  ## Build the package (alias for package)
	$(MAKE) package

launch:  ## launch the package (alias for run)
	$(MAKE) run

package:  ## Build the package with Poetry
	$(POETRY) build

release:  ## Build and publish to PyPI
	$(POETRY) build
	$(POETRY) publish
