# ローカル開発環境用ビルドスクリプト（テスト用）
# 開発環境でのビルドテストに使用

$ErrorActionPreference = "Stop"

Write-Host "========================================="
Write-Host "ローカルビルドテスト"
Write-Host "========================================="
Write-Host ""

# プロジェクトルートに移動
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot

# build-windows.ps1を呼び出し
& (Join-Path $scriptDir "build-windows.ps1")
