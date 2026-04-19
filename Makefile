# ===================================================================
# BuddyAI RAG — Makefile
# Short commands for common tasks.
#
# Prerequisites:
#   - podman        installed
#   - podman-compose installed (pip install podman-compose)
#   - Python 3.11+  with venv
#
# First-time setup:
#   1. cp .env.example .env  → fill in your API keys
#   2. make venv             → create Python virtual env
#   3. make install           → install dependencies
#   4. make infra-up         → start Neo4j
#   5. make index-seed       → seed academic data into LightRAG
# ===================================================================

.PHONY: help \
        infra-up infra-down infra-restart infra-logs infra-status \
        venv install dev test \
        index-seed index-clean \
        run debug clean

# ── Colours ────────────────────────────────────────────────────────────
BOLD  := $(shell tput bold 2>/dev/null || echo '')
RESET := $(shell tput sgr0 2>/dev/null || echo '')
CYAN  := $(BOLD)$(shell tput setaf 6 2>/dev/null || echo '')
GREEN := $(BOLD)$(shell tput setaf 2 2>/dev/null || echo '')
RED   := $(BOLD)$(shell tput setaf 1 2>/dev/null || echo '')

define print
	@printf "\n$(CYAN)▶ $(RESET)$(1)\n"
endef

# ===================================================================
# HELP
# ===================================================================

help:; @grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
    awk 'BEGIN {FS = ":.*?## "}; {printf "$(BOLD)%-18s$(RESET) %s\n", $$1, $$2}'

# ===================================================================
# INFRASTRUCTURE  (podman-compose)
# ===================================================================

infra-up:  ## Start Neo4j + supporting containers
	$(call print,Starting Neo4j...)
	podman-compose -f podman-compose.yml up -d
	@echo "$(GREEN)✓ Infrastructure up$(RESET)"
	@echo "  Neo4j Browser → http://localhost:7474"
	@echo "  Bolt         → bolt://localhost:7687"

infra-down:  ## Stop and remove all containers
	$(call print,Stopping containers...)
	podman-compose -f podman-compose.yml down
	@echo "$(GREEN)✓ Infrastructure down$(RESET)"

infra-restart: infra-down infra-up  ## Restart all containers

infra-logs:  ## Tail logs from all containers
	podman-compose -f podman-compose.yml logs -f

infra-status:  ## Show container status
	podman-compose -f podman-compose.yml ps

infra-reset:  ## Destroy all containers + volumes (irreversible)
	$(call print,Destroying all containers and volumes...)
	podman-compose -f podman-compose.yml down -v
	@echo "$(RED)✓ Everything wiped$(RESET)"

# ===================================================================
# PYTHON ENVIRONMENT
# ===================================================================

venv:  ## Create Python venv
	@[ -d ".venv" ] && echo "venv already exists" || \
		python -m venv .venv && echo "venv created"

install: venv  ## Install Python dependencies
	.venv/Scripts/pip install -r requirements.txt

dev: venv  ## Install dev dependencies (add pytest, black, ruff, etc.)
	.venv/Scripts/pip install -r requirements.txt
	@echo "$(GREEN)✓ Dev ready  (run 'source .venv/Scripts/activate' to enter)$(RESET)"

# ===================================================================
# SERVER
# ===================================================================

run:  ## Start FastAPI server (production)
	.venv/Scripts/python -m uvicorn server:app \
		--host $(SERVER_HOST) \
		--port $(SERVER_PORT) \
		--workers 4

debug:  ## Start FastAPI server (debug mode with hot-reload)
	.venv/Scripts/python -m uvicorn server:app \
		--host $(SERVER_HOST) \
		--port $(SERVER_PORT) \
		--reload

test:  ## Run tests (pytest)
	.venv/Scripts/pytest -v

# ===================================================================
# RAG — INDEXING
# ===================================================================

index-seed:  ## Seed academic documents into LightRAG (via API)
	$(call print,Seeding academic data into LightRAG...)
	@curl -s -X POST http://localhost:8000/api/rag/seed \
		-H "Content-Type: application/json" \
		| python -m json.tool || \
		echo "$(RED)✗ Server may not be running — start with 'make debug' first$(RESET)"

index-clean:  ## Clear all RAG data (keeps Neo4j schema)
	$(call print,Wiping rag_working/ directory...)
	@find rag_working -type f ! -name '.gitkeep' -delete 2>/dev/null; \
		find rag_working -type d -empty -delete 2>/dev/null; \
		echo "$(GREEN)✓ rag_working/ cleaned$(RESET)"

# ===================================================================
# UTILITIES
# ===================================================================

clean: infra-down  ## Stop infra + remove generated files
	$(call print,Removing generated files...)
	@find . -type d -name __pycache__  -exec rm -rf {} + 2>/dev/null
	@find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null
	@find . -type f -name '*.pyc' -delete 2>/dev/null
	@find . -type f -name '*.pyo' -delete 2>/dev/null
	$(call print,Clean complete. To remove venv: rm -rf .venv)

.DEFAULT_GOAL := help
