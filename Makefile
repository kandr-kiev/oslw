# OSLW Makefile
.PHONY: help install dev test lint format clean run docs

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies (production)
	uv pip install -e .

dev: ## Install dependencies (with dev tools)
	uv pip install -e ".[dev]"
	pre-commit install

clean: ## Clean build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name dist -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name build -exec rm -rf {} + 2>/dev/null || true
	rm -rf coverage.xml .coverage htmlcov/
	rm -rf data/oslw.db logs/

test: ## Run tests
	pytest tests/ -v --cov=src/oslw --cov-report=term-missing --cov-report=xml

test-fast: ## Run tests (no coverage, quick)
	pytest tests/ -v --tb=short

lint: ## Run linter
	ruff check src/ tests/

lint-fix: ## Run linter and auto-fix
	ruff check --fix src/ tests/

format: ## Format code
	ruff format src/ tests/

docs: ## Build documentation
	mkdocs build -d site/

run: ## Run the API server
	uvicorn oslw.main:app --reload --host 0.0.0.0 --port 8000

run-dev: ## Run with debug and hot-reload
	DEBUG=true uvicorn oslw.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
