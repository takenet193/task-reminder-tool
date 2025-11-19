# CI品質チェックをローカルで実行するスクリプト（Windows用）

$ErrorActionPreference = "Stop"

Write-Host "Running tests with coverage..."
pytest --cov=. --cov-report=term-missing
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

coverage report --fail-under=60
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Running ruff linter..."
ruff check .
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Checking black formatting..."
black --check .
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Running mypy type check..."
mypy . --config-file pyproject.toml
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "All checks passed!"

