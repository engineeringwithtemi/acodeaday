.PHONY: help \
	lint lint-backend lint-frontend \
	format format-backend format-frontend \
	typecheck typecheck-backend typecheck-frontend \
	test test-backend test-frontend \
	check check-backend check-frontend

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-24s\033[0m %s\n", $$1, $$2}'

# =============================================================================
# Combined targets
# =============================================================================

lint: lint-backend lint-frontend ## Run all linters
format: format-backend format-frontend ## Format all code
typecheck: typecheck-backend typecheck-frontend ## Type-check all code
test: test-backend test-frontend ## Run all tests
check: lint typecheck test ## Run lint + typecheck + test

# =============================================================================
# Backend (Python — ruff, ty, pytest)
# =============================================================================

lint-backend: ## Lint backend with ruff
	cd backend && uv run ruff check .

format-backend: ## Format backend with ruff
	cd backend && uv run ruff format .

typecheck-backend: ## Type-check backend with ty
	cd backend && uv run ty check

test-backend: ## Run backend tests (non-DB)
	cd backend && uv run pytest tests/test_comparison.py -v

test-backend-all: ## Run all backend tests including DB-dependent
	cd backend && TEST_DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/acodeaday_test" \
		DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/acodeaday_test" \
		uv run pytest tests/ -v --ignore=tests/test_routes_problems.py \
		--ignore=tests/test_routes_execution.py \
		--ignore=tests/test_routes_progress.py \
		--ignore=tests/test_routes_submissions.py

check-backend: lint-backend typecheck-backend test-backend ## Lint + typecheck + test backend

# =============================================================================
# Frontend (TypeScript — eslint, prettier, tsc, vitest)
# =============================================================================

lint-frontend: ## Lint frontend with eslint
	cd frontend && npx eslint src/

format-frontend: ## Format frontend with prettier
	cd frontend && npx prettier --write "src/**/*.{ts,tsx,css}"

format-frontend-check: ## Check frontend formatting (no write)
	cd frontend && npx prettier --check "src/**/*.{ts,tsx,css}"

typecheck-frontend: ## Type-check frontend with tsc
	cd frontend && npx tsc --noEmit

test-frontend: ## Run frontend tests with vitest
	cd frontend && npx vitest run

check-frontend: lint-frontend typecheck-frontend test-frontend ## Lint + typecheck + test frontend

# =============================================================================
# Fix targets (auto-fix where possible)
# =============================================================================

fix: fix-backend fix-frontend ## Auto-fix all code

fix-backend: ## Auto-fix backend (ruff check --fix + format)
	cd backend && uv run ruff check --fix . && uv run ruff format .

fix-frontend: ## Auto-fix frontend (eslint --fix + prettier --write)
	cd frontend && npx eslint --fix src/ && npx prettier --write "src/**/*.{ts,tsx,css}"
