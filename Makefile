.PHONY: help setup install test lint format clean data train deploy monitor docker-up docker-down

# Default target
help:
	@echo "Available commands:"
	@echo "  setup          - Initialize project environment"
	@echo "  install        - Install dependencies"
	@echo "  install-dev    - Install development dependencies"
	@echo "  test           - Run tests"
	@echo "  lint           - Run linting"
	@echo "  format         - Format code"
	@echo "  clean          - Clean temporary files"
	@echo "  data           - Download and process data"
	@echo "  train          - Train ML model"
	@echo "  deploy         - Deploy model"
	@echo "  monitor        - Start monitoring dashboard"
	@echo "  docker-up      - Start Docker services"
	@echo "  docker-down    - Stop Docker services"
	@echo "  dagster        - Start Dagster webserver"
	@echo "  mlflow         - Start MLflow server"
	@echo "  api            - Start FastAPI server"

# Environment setup
setup: install pre-commit-install
	@echo "Creating .env file from template..."
	@cp .env.template .env
	@echo "Creating data directories..."
	@mkdir -p data/raw data/processed models logs
	@echo "Setup complete! Edit .env file with your configuration."

install:
	uv sync

install-dev:
	uv sync --extra dev

# Code quality
test:
	uv run pytest tests/ -v --cov=src --cov-report=html

lint:
	uv run ruff check src tests
	uv run mypy src

format:
	uv run ruff format src tests
	uv run ruff check --fix src tests

pre-commit-install:
	uv run pre-commit install

pre-commit:
	uv run pre-commit run --all-files

# Data pipeline
data:
	uv run python scripts/download_data.py
	uv run python scripts/process_data.py

data-sample:
	uv run python scripts/download_data.py --sample

validate-data:
	uv run python scripts/validate_data.py

# ML pipeline
train:
	uv run python src/train.py

train-baseline:
	uv run python src/train.py --model baseline

evaluate:
	uv run python src/evaluate.py

# Services
dagster:
	uv run dagster dev -m src.dagster_app

mlflow:
	uv run mlflow ui --host 0.0.0.0 --port 5000

api:
	uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

monitor:
	uv run python src/monitoring/dashboard.py

# Docker
docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-build:
	docker-compose build

docker-logs:
	docker-compose logs -f

# Deployment
deploy-local: docker-up
	@echo "Local deployment started"
	@echo "MLflow UI: http://localhost:5000"
	@echo "Dagster UI: http://localhost:3001"
	@echo "API: http://localhost:8000"

deploy-cloud:
	@echo "Cloud deployment not yet implemented"

# Utilities
clean:
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/

clean-data:
	rm -rf data/raw/*
	rm -rf data/processed/*
	@echo "Data directories cleaned"

clean-models:
	rm -rf models/*
	rm -rf mlruns/*
	@echo "Models and experiments cleaned"

# Development workflow
dev-setup: setup install-dev
	@echo "Development environment ready!"

dev-test: format lint test
	@echo "Development checks complete"

dev-run: docker-up
	@echo "Starting development services..."
	@echo "Run 'make dagster' in another terminal to start Dagster"
	@echo "Run 'make mlflow' in another terminal to start MLflow"

# Production workflow
prod-test: test lint
	@echo "Production tests complete"

prod-deploy: prod-test deploy-cloud
	@echo "Production deployment complete"

# Quick commands
quick-train: data-sample train-baseline
	@echo "Quick training complete"

full-pipeline: data train evaluate deploy-local
	@echo "Full pipeline executed"