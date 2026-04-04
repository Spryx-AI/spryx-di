.DEFAULT_GOAL := help
.PHONY: help install lint format typecheck test check pre-commit clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies and pre-commit hooks
	uv sync --extra dev
	uv run pre-commit install
	uv run pre-commit install --hook-type commit-msg

lint: ## Run ruff linter
	uv run ruff check .

format: ## Format code with ruff
	uv run ruff format .

typecheck: ## Run ty type checker
	uv run ty check spryx_di/

test: ## Run tests with coverage (fail under 90%)
	uv run pytest tests/ -v --cov --cov-report=term-missing

check: lint typecheck test ## Run lint + typecheck + tests

pre-commit: ## Run all pre-commit hooks
	uv run pre-commit run --all-files

clean: ## Remove caches and build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf .ruff_cache .coverage
