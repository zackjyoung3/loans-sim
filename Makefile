.PHONY: install format lint fix test

install:
	uv venv
	uv pip install -r pyproject.toml

format:
	uv run ruff format .

lint:
	uv run ruff check

fix:
	uv run ruff check --fix


test:
	uv run pytest


commit-ready: format lint test