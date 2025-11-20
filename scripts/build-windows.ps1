# Windows用ビルドスクリプト
# PyInstallerを使用してexeファイルを生成

$ErrorActionPreference = "Stop"

Write-Host "========================================="
Write-Host "Windows配布パッケージのビルド"
Write-Host "========================================="
Write-Host ""

# プロジェクトルートに移動
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot

# PyInstallerがインストールされているか確認
Write-Host "PyInstallerの確認..."
try {
    $pyinstallerVersion = pyinstaller --version
    Write-Host "PyInstaller version: $pyinstallerVersion"
} catch {
    Write-Host "エラー: PyInstallerがインストールされていません" -ForegroundColor Red
    Write-Host "以下のコマンドでインストールしてください: pip install pyinstaller" -ForegroundColor Yellow
    exit 1
}

# main.specファイルが存在するか確認
if (-not (Test-Path "main.spec")) {
    Write-Host "エラー: main.specファイルが見つかりません" -ForegroundColor Red
    exit 1
}

# 既存のビルド成果物をクリーンアップ
Write-Host ""
Write-Host "既存のビルド成果物をクリーンアップ..."
if (Test-Path "build") {
    Remove-Item -Path "build" -Recurse -Force
    Write-Host "buildディレクトリを削除しました"
}
if (Test-Path "dist") {
    Remove-Item -Path "dist" -Recurse -Force
    Write-Host "distディレクトリを削除しました"
}

# PyInstallerでビルド実行
Write-Host ""
Write-Host "PyInstallerでビルドを開始..."
Write-Host ""

try {
    pyinstaller main.spec --clean --noconfirm

    if ($LASTEXITCODE -ne 0) {
        Write-Host "エラー: ビルドに失敗しました" -ForegroundColor Red
        exit $LASTEXITCODE
    }

    Write-Host ""
    Write-Host "ビルドが完了しました！" -ForegroundColor Green
    Write-Host ""

    # ビルド結果の確認
    $exePath = Join-Path $projectRoot "dist" "TaskReminder.exe"
    if (Test-Path $exePath) {
        $fileInfo = Get-Item $exePath
        $fileSizeMB = [math]::Round($fileInfo.Length / 1MB, 2)
        Write-Host "成果物: $exePath" -ForegroundColor Green
        Write-Host "ファイルサイズ: $fileSizeMB MB" -ForegroundColor Green
        Write-Host ""
        Write-Host "次のステップ:" -ForegroundColor Yellow
        Write-Host "  1. dist/TaskReminder.exe をテストしてください"
        Write-Host "  2. 動作確認後、GitHub Releasesにアップロードしてください"
    } else {
        Write-Host "警告: exeファイルが見つかりません" -ForegroundColor Yellow
        Write-Host "distディレクトリの内容を確認してください"
    }

} catch {
    Write-Host "エラー: ビルド中にエラーが発生しました" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================="
Write-Host "ビルド完了"
Write-Host "========================================="
