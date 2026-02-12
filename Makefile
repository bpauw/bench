.PHONY: check setup install

check:
	uv run ruff check --show-fixes --fix src/
	uv run ruff format src/
	uv run ty check src/

setup:
	uv sync --all-groups

install:
	uv tool install --reinstall .
