.PHONY: help install check lint format-check format fix clean

help:
	@echo "Available targets:"
	@echo "  install       Sync dependencies (including dev group)"
	@echo "  check         Run all checks: ruff lint + format check"
	@echo "  lint          Run ruff lint only"
	@echo "  format-check  Check that code is properly formatted"
	@echo "  format        Format source code with ruff"
	@echo "  fix           Auto-fix lint issues and format"
	@echo "  clean         Remove build artifacts and caches"

install:
	uv sync --all-groups

check: lint format-check

lint:
	uv run ruff check .

format-check:
	uv run ruff format --check .

format:
	uv run ruff format .

fix:
	uv run ruff check --fix .
	uv run ruff format .

clean:
	rm -rf build dist *.egg-info .ruff_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
