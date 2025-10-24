#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "" ]; then
  echo "Usage: $0 /abs/path/to/workspace [github_token_env=GITHUB_PERSONAL_ACCESS_TOKEN] [output=mcp_config.json]" >&2
  exit 1
fi

WORKSPACE_ABS_PATH="$1"
GITHUB_TOKEN_ENV="${2:-GITHUB_PERSONAL_ACCESS_TOKEN}"
OUTPUT="${3:-mcp_config.json}"

# 実パスに解決
if command -v realpath >/dev/null 2>&1; then
  WORKSPACE_ABS_PATH="$(realpath "$WORKSPACE_ABS_PATH")"
fi

TEMPLATE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATE_FILE="$TEMPLATE_DIR/mcp_config.template.json"

if [ ! -f "$TEMPLATE_FILE" ]; then
  echo "Template not found: $TEMPLATE_FILE" >&2
  exit 1
fi

# 置換（/ をエスケープ）
ESCAPED_PATH=$(printf '%s' "$WORKSPACE_ABS_PATH" | sed -e 's/[\/&]/\\&/g')
ESCAPED_TOKEN_ENV=$(printf '%s' "$GITHUB_TOKEN_ENV" | sed -e 's/[\/&]/\\&/g')
sed -e "s/{{WORKSPACE_ABS_PATH}}/$ESCAPED_PATH/g" -e "s/{{GITHUB_TOKEN_ENV}}/$ESCAPED_TOKEN_ENV/g" "$TEMPLATE_FILE" > "$OUTPUT"

echo "Generated $OUTPUT with WORKSPACE_ABS_PATH=$WORKSPACE_ABS_PATH and GITHUB_TOKEN_ENV=$GITHUB_TOKEN_ENV"
