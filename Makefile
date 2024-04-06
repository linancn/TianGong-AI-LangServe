.PHONY: all help spell_check spell_fix lint format

## help: Show this help info.
help: Makefile
	@printf "\n\033[1mUsage: make <TARGETS> ...\033[0m\n\n\033[1mTargets:\033[0m\n\n"
	@sed -n 's/^##//p' $< | awk -F':' '{printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' | sort | sed -e 's/^/ /'

## all: Default target, shows help.
all: help

## spell_check: Run codespell on the project.
spell_check:
	poetry run codespell --toml pyproject.toml

## spell_fix: Run codespell on the project and fix the errors.
spell_fix:
	poetry run codespell --toml pyproject.toml -w

## lint: Run linting on the project.
lint:
	poetry run ruff check --exclude src/utilities src
	poetry run ruff format --exclude src/utilities src --diff
	poetry run ruff check --exclude src/utilities --select I src

## format: Format the project files.
format:
	poetry run ruff format --exclude src/utilities src
	poetry run ruff check --exclude src/utilities --select I --fix src