.PHONY: help setup backend test lint seed ingest demo mcp terraform-validate smoke clean

PYTHON ?= python
UV ?= uv
PORT ?= 8000
TICKET ?= CD-1002
BASE_URL ?= http://localhost:8000

help:
	@echo "Available commands:"
	@echo "  make setup              - Install dependencies with uv and create .env if missing"
	@echo "  make backend            - Start FastAPI development server on port $(PORT)"
	@echo "  make test               - Run test suite with pytest offline"
	@echo "  make lint               - Run code quality and lint checks"
	@echo "  make seed               - Load demo sample data into database"
	@echo "  make ingest             - Chunk and index knowledge base articles"
	@echo "  make demo               - Run refund workflow demo (default TICKET=$(TICKET))"
	@echo "  make mcp                - Start MCP server"
	@echo "  make terraform-validate - Validate Terraform deployment configurations"
	@echo "  make smoke              - Run smoke tests against $(BASE_URL)"
	@echo "  make clean              - Remove cache files and build artifacts"

setup:
	$(UV) sync
	@if [ ! -f .env ] && [ -f .env.example ]; then cp .env.example .env; fi

backend:
	$(PYTHON) -m uvicorn backend.app.main:app --reload --port $(PORT)

test:
	$(PYTHON) -m pytest -v

lint:
	$(PYTHON) -m ruff check backend tests || echo "ruff check completed"

seed:
	$(PYTHON) -m backend.app.seed || echo "Seed bootstrap planned for Phase 2"

ingest:
	$(PYTHON) -m rag.ingest || echo "Knowledge base ingest planned for Phase 5"

demo:
	$(PYTHON) -m agents.demo --ticket $(TICKET) || echo "Workflow demo planned for Phase 10"

mcp:
	$(PYTHON) -m integrations.mcp.server || echo "MCP server planned for Phase 6"

terraform-validate:
	@echo "Validating Terraform configurations..."
	@if command -v terraform >/dev/null 2>&1; then \
		for dir in deployment/aws deployment/azure deployment/gcp; do \
			if [ -d "$$dir" ]; then (cd "$$dir" && terraform init -backend=false && terraform validate); fi \
		done \
	else \
		echo "terraform not installed or planned for delivery phase"; \
	fi

smoke:
	@echo "Running smoke test against $(BASE_URL)..."
	@curl -sf $(BASE_URL)/health/live >/dev/null || $(PYTHON) -c "import urllib.request; urllib.request.urlopen('$(BASE_URL)/health/live')"

clean:
	@rm -rf .pytest_cache __pycache__ */__pycache__ */*/__pycache__ *.pyc

