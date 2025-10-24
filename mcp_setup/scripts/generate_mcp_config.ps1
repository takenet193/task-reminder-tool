param(
    [Parameter(Mandatory=$true)][string]$WorkspacePath,
    [string]$GithubTokenEnv = "GITHUB_PERSONAL_ACCESS_TOKEN",
    [string]$Output = "mcp_config.json"
)

$ErrorActionPreference = "Stop"

# 正規化（絶対パス化）
$abs = (Resolve-Path -Path $WorkspacePath).Path

$template = Get-Content -Raw -Path (Join-Path $PSScriptRoot "..\mcp_config.template.json")
$json = $template -replace "\{\{WORKSPACE_ABS_PATH\}\}", [Regex]::Escape($abs)
$json = $json -replace "\{\{GITHUB_TOKEN_ENV\}\}", $GithubTokenEnv

# 出力
Set-Content -Path (Join-Path (Get-Location) $Output) -Value $json -Encoding UTF8
Write-Host "Generated $Output with WORKSPACE_ABS_PATH=$abs and GITHUB_TOKEN_ENV=$GithubTokenEnv"
