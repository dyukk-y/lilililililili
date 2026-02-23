.PHONY: help install install-dev test test-cov lint format clean run docker-build docker-run docs

help:
	@echo "AutoPost Bot - Available commands:"
	@echo ""
	@echo "Setup:"
	@echo "  make install          - Install dependencies"
	@echo "  make install-dev      - Install dev dependencies (tests, linters)"
	@echo "  make venv             - Create virtual environment"
	@echo ""
	@echo "Running:"
	@echo "  make run              - Run the bot"
	@echo "  make run-examples     - Run examples"
	@echo "  make run-tests        - Run tests (shortcut)"
	@echo "  make run-quickstart   - Run interactive quickstart"
	@echo ""
	@echo "Development:"
	@echo "  make test             - Run tests"
	@echo "  make test-cov         - Run tests with coverage"
	@echo "  make lint             - Check code style (flake8)"
	@echo "  make format           - Format code (black)"
	@echo "  make type-check       - Type checking (mypy)"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            - Remove all generated files"
	@echo "  make clean-cache      - Remove __pycache__ and .pytest_cache"
	@echo "  make clean-build      - Remove build artifacts"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build     - Build Docker image"
	@echo "  make docker-run       - Run bot in Docker"
	@echo "  make docker-stop      - Stop Docker container"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs             - Open README in browser"

venv:
	python -m venv venv
	@echo "Virtual environment created. Activate with:"
	@echo "  source venv/bin/activate  (Linux/macOS)"
	@echo "  venv\\Scripts\\activate     (Windows)"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install pytest pytest-cov flake8 black mypy

run:
	python bot.py

run-examples:
	python examples.py

run-quickstart:
	python quickstart.py

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=. --cov-report=html --cov-report=term

test-watch:
	pytest tests/ -v --tb=short --looponfail

lint:
	flake8 bot.py examples.py quickstart.py telegram_bot.py platform_integrations.py --max-line-length=100

format:
	black bot.py examples.py quickstart.py telegram_bot.py platform_integrations.py --line-length=100

type-check:
	mypy bot.py --ignore-missing-imports || true

check: lint test
	@echo "✓ All checks passed"

clean: clean-cache clean-build
	rm -rf venv
	rm -f .env
	rm -f posts.json
	rm -f *.log
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true

clean-cache:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".DS_Store" -delete

clean-build:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .eggs/

docker-build:
	docker build -t autopost-bot .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-clean:
	docker-compose down -v

# Development utilities
update-deps:
	pip install --upgrade pip setuptools wheel
	pip install --upgrade -r requirements.txt

list-deps:
	pip list

freeze-deps:
	pip freeze > requirements-freeze.txt

# Build and publish
build: clean
	python setup.py sdist bdist_wheel

publish-test:
	twine upload --repository testpypi dist/*

publish:
	twine upload dist/*

# Git helpers
sync:
	git fetch upstream
	git rebase upstream/main

commit-msg:
	@echo "Commit message format:"
	@echo "  type(scope): description"
	@echo ""
	@echo "Types: feat, fix, docs, style, refactor, perf, test, chore"
	@echo "Example: feat(publish): add batch publishing"

# Documentation
docs:
	@echo "Opening README.md..."
	@python -c "import webbrowser; webbrowser.open('file://' + open('README.md').read())" || \
	@cat README.md | head -50

# Information
info:
	@echo "AutoPost Bot - Project Info"
	@echo "=========================================="
	@echo "Version: 1.0.0"
	@echo "Python: $$(python --version)"
	@echo "Location: $$(pwd)"
	@echo "=========================================="
	@echo "Installed packages:"
	@pip list | grep -E "pytz|APScheduler|pytest"

# Summary of all targets
summary: info

.DEFAULT_GOAL := help
