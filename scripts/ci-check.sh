#!/bin/bash
# CI品質チェックをローカルで実行するスクリプト

set -e

echo "Running tests with coverage..."
pytest --cov=. --cov-report=term-missing
coverage report --fail-under=60

echo "Running ruff linter..."
ruff check .

echo "Checking black formatting..."
black --check .

echo "Running mypy type check..."
mypy . --config-file pyproject.toml

echo "All checks passed!"

