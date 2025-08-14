.PHONY: all format lint test tests test_watch integration_tests docker_tests help extended_tests serve serve_direct serve_prod

# Default target executed when no arguments are given to make.
all: help

# Define a variable for the test file path.
TEST_FILE ?= tests/unit_tests/

test:
	python -m pytest $(TEST_FILE)

integration_tests:
	python -m pytest tests/integration_tests 

test_watch:
	python -m ptw --snapshot-update --now . -- -vv tests/unit_tests

test_profile:
	python -m pytest -vv tests/unit_tests/ --profile-svg

extended_tests:
	python -m pytest --only-extended $(TEST_FILE)


######################
# LINTING AND FORMATTING
######################

# Define a variable for Python and notebook files.
PYTHON_FILES=src/
MYPY_CACHE=.mypy_cache
lint format: PYTHON_FILES=.
lint_diff format_diff: PYTHON_FILES=$(shell git diff --name-only --diff-filter=d main | grep -E '\.py$$|\.ipynb$$')
lint_package: PYTHON_FILES=src
lint_tests: PYTHON_FILES=tests
lint_tests: MYPY_CACHE=.mypy_cache_test

lint lint_diff lint_package lint_tests:
	python -m ruff check .
	[ "$(PYTHON_FILES)" = "" ] || python -m ruff format $(PYTHON_FILES) --diff
	[ "$(PYTHON_FILES)" = "" ] || python -m ruff check --select I $(PYTHON_FILES)
	[ "$(PYTHON_FILES)" = "" ] || python -m mypy --strict $(PYTHON_FILES)
	[ "$(PYTHON_FILES)" = "" ] || mkdir -p $(MYPY_CACHE) && python -m mypy --strict $(PYTHON_FILES) --cache-dir $(MYPY_CACHE)

format format_diff:
	ruff format $(PYTHON_FILES)
	ruff check --select I --fix $(PYTHON_FILES)

spell_check:
	codespell --toml pyproject.toml

spell_fix:
	codespell --toml pyproject.toml -w

######################
# SERVER MANAGEMENT
######################

serve:
	@echo "🚀 Starting Emergency Management System with LangGraph Dev"
	@echo "🌐 Server: http://127.0.0.1:2024"
	@echo "📚 Docs: http://127.0.0.1:2024/docs"
	@echo "🎨 Studio: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024"
	langgraph dev

serve_direct:
	@echo "🚀 Starting Emergency Management System in Direct Mode"
	@echo "🌐 Server: http://127.0.0.1:2024"
	@echo "📚 Docs: http://127.0.0.1:2024/docs"
	python src/main.py

serve_prod:
	@echo "🚀 Starting Emergency Management System in Production Mode"
	@echo "🌐 Server: http://127.0.0.1:2024"
	gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 127.0.0.1:2024 --timeout 120

######################
# HELP
######################

help:
	@echo '----'
	@echo 'format                       - run code formatters'
	@echo 'lint                         - run linters'
	@echo 'test                         - run unit tests'
	@echo 'tests                        - run unit tests'
	@echo 'test TEST_FILE=<test_file>   - run all tests in file'
	@echo 'test_watch                   - run unit tests in watch mode'
	@echo '----'
	@echo 'serve                        - start server with LangGraph Dev (recommended)'
	@echo 'serve_direct                 - start server with direct FastAPI'
	@echo 'serve_prod                   - start server in production mode'

