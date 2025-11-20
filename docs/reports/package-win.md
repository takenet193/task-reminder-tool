# レポート: Windows配布 (`package-win`)

## 実施概要

- Windows向けの配布パッケージを作成し、Python環境なしで動作する単一exeファイルを生成した。
- PyInstallerを使用して、依存関係をすべてバンドルした実行可能ファイルを作成した。
- GitHub Actionsでの自動ビルドとGitHub Releasesへの自動アップロードを実装した。
- exe環境で正しく動作するよう、パス処理を修正した。
- ドキュメントを更新し、ユーザー向けのインストール手順を追加した。

## 実装内容

### 1. PyInstaller環境のセットアップ

#### `requirements.txt` の更新
- `pyinstaller>=6.0.0` を追加（パッケージング用）

#### ディレクトリ構造の準備
- `assets/` ディレクトリを作成（アイコンファイル用、オプション）

### 2. PyInstaller設定ファイル（.spec）の作成

#### `main.spec` の作成

新規ファイル `main.spec` を作成し、以下の設定を実装した：

- **エントリーポイント**: `main.py`
- **ビルドモード**: onefile（単一exeファイル）
- **コンソールウィンドウ**: 非表示（GUIアプリ）
- **除外モジュール**: 開発用モジュール（pytest、ruff、black、mypy、mcp_setup、tests等）
- **アイコン**: `assets/icon.ico`（存在する場合）
- **hiddenimports**: matplotlib関連モジュール（`matplotlib.backends.backend_tkagg`等）

**除外したモジュール**:
- `pytest`、`pytest_cov`（テスト用）
- `ruff`、`black`、`mypy`（開発用）
- `mcp_setup`（開発用）
- `tests`、`test_*`、`conftest`（テスト用）

### 3. パス処理の修正（exe環境対応）

#### `config.py` の修正

- `_get_base_dir()` 関数を追加
- `sys.frozen` を使用してexe環境を検出
- exe環境では `sys.executable` のディレクトリをベースディレクトリとして使用
- 開発環境では `os.getcwd()` を使用（既存の動作を維持）

**変更内容**:
```python
def _get_base_dir() -> str:
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.getcwd()
    return base_dir
```

#### `main.py` の修正

- `_get_log_file_path()` 関数を追加
- exe環境ではexeファイルのディレクトリに `app.log` を出力
- 開発環境では既存の動作を維持

**変更内容**:
```python
def _get_log_file_path() -> str:
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.getcwd()
    return os.path.join(base_dir, "app.log")
```

### 4. ビルドスクリプトの作成

#### `scripts/build-windows.ps1` の作成

Windows用のビルドスクリプトを作成：

- PyInstallerのインストール確認
- `main.spec` ファイルの存在確認
- 既存のビルド成果物のクリーンアップ
- PyInstallerでのビルド実行
- ビルド結果の確認（ファイルサイズ、パス等）
- エラーハンドリング

#### `scripts/build-local.ps1` の作成

ローカル開発環境用のビルドスクリプト（オプション）：

- `build-windows.ps1` を呼び出すラッパースクリプト

### 5. ローカルビルドテスト

#### ビルド実行

- ローカル環境で `pyinstaller main.spec --clean --noconfirm` を実行
- ビルドが正常に完了することを確認
- exeファイルが `dist/` ディレクトリに生成されることを確認

#### ビルド結果

- **ファイル名**: `TaskReminder.exe`
- **ファイルサイズ**: 約38.1 MB（39,979,704バイト）
- **生成場所**: `dist/TaskReminder.exe`

### 6. GitHub Actionsでの自動ビルド

#### `.github/workflows/build-release.yml` の作成

GitHub Actionsワークフローを作成し、以下の機能を実装：

**トリガー設定**:
- `push` イベント: タグが `v*` で始まる場合
- `workflow_dispatch`: 手動実行（バージョン指定可能）

**実装したジョブ**:

1. **build ジョブ**（Build Windows Executable）
   - Windows環境（`windows-latest`）のセットアップ
   - Python 3.13環境のセットアップ
   - 依存関係のインストール
   - PyInstallerでのビルド実行
   - ファイルサイズの取得
   - SHA256チェックサムの生成
   - 成果物のアップロード（Artifacts）
   - GitHub Releasesへの自動アップロード（タグの場合）

**リリースノートの自動生成**:
- ファイルサイズ
- SHA256チェックサム
- インストール手順
- システム要件
- トラブルシューティング
- チェックサム検証方法

### 7. ドキュメント更新

#### `README.md` の更新

以下のセクションを追加/更新：

1. **Windows版（推奨）セクション**
   - ダウンロード方法（GitHub Releasesへのリンク）
   - インストール手順
   - システム要件
   - トラブルシューティング（Windows版）
   - チェックサム検証方法

2. **開発者向けインストールセクション**
   - 既存のインストール手順を「開発者向け」として明確化

3. **トラブルシューティングセクションの更新**
   - Windows版と開発版を区別
   - データファイルの場所について説明を追加

#### `CHANGELOG.md` の作成

- バージョン履歴を記録するファイルを作成
- Keep a Changelog形式に準拠
- Semantic Versioningに準拠
- 未リリース版とv1.0.0の変更履歴を記載

## 実装の詳細

### ビルドプロセス

1. **PyInstallerの実行**
   - `main.spec` ファイルを読み込み
   - 依存関係の分析
   - 一時ファイルの生成（`build/` ディレクトリ）
   - exeファイルの生成（`dist/` ディレクトリ）

2. **ファイルサイズの最適化**
   - 開発用モジュールを除外
   - UPX圧縮を有効化（`upx=True`）

3. **起動速度の考慮**
   - onefileモードを使用（起動時に一時ファイルを展開）
   - 初回起動時はやや時間がかかる（通常5秒以内）

### exe環境での動作

1. **データディレクトリ**
   - exeファイルと同じディレクトリに `data/` フォルダが自動作成
   - タスク設定、ログ、設定ファイルが保存される

2. **ログファイル**
   - exeファイルと同じディレクトリに `app.log` が出力される

3. **パス処理**
   - `sys.frozen` でexe環境を検出
   - `sys.executable` でexeファイルのディレクトリを取得

### 配布プロセス

1. **ローカルビルド**
   - 開発者が `scripts/build-windows.ps1` を実行
   - または `pyinstaller main.spec --clean --noconfirm` を直接実行

2. **CI/CD自動ビルド**
   - タグ `v*` をプッシュすると自動的にビルドが実行される
   - ビルド成功後、GitHub Releasesに自動アップロードされる

3. **リリースノート**
   - ファイルサイズ、チェックサム、使用方法が自動的に記載される

## 動作確認

### ローカルビルドテスト

```bash
$ pyinstaller main.spec --clean --noconfirm
```

**結果**:
- ビルドが正常に完了
- `dist/TaskReminder.exe` が生成される
- ファイルサイズ: 約38.1 MB

### exeファイルの起動確認

- exeファイルをダブルクリックして起動
- メインウィンドウが表示される
- `data/` フォルダが自動作成される
- `app.log` ファイルが作成される

### 機能確認

- タスクの追加・編集・削除が正常に動作
- 通知機能が正常に動作
- ログ・達成率表示が正常に動作
- データファイルが正しい場所に保存される

## 注意事項

1. **ウイルススキャンの誤検知**
   - PyInstallerで生成したexeは誤検知されやすい
   - 信頼できるソース（GitHub Releases）からのダウンロードであることを確認
   - ユーザーへの説明をドキュメントに記載

2. **ファイルサイズ**
   - matplotlibを含むため、ファイルサイズが大きい（約38MB）
   - 必要に応じてUPX圧縮を検討（既に有効化済み）

3. **起動速度**
   - onefileモードは起動時に一時ファイルを展開するため、やや遅い
   - 初回起動時は通常5秒以内
   - 必要に応じてonedirモードを検討

4. **データディレクトリの場所**
   - exeファイルと同じディレクトリに `data/` フォルダが作成される
   - ユーザーがexeファイルを移動した場合、データファイルも一緒に移動する必要がある

5. **ログファイルの場所**
   - exeファイルと同じディレクトリに `app.log` が出力される
   - ログファイルのサイズが大きくなった場合は、手動で削除する必要がある

6. **CI/CDでのビルド**
   - GitHub Actionsでビルドする場合、Windows環境が必要
   - ビルド時間は約5-10分程度

## メモ

- PyInstaller 6.15.0を使用
- Python 3.13環境でビルド
- matplotlibのバックエンド（TkAgg）が正しく含まれることを確認
- 開発用モジュールが正しく除外されることを確認
- exe環境と開発環境の両方で正常に動作することを確認

## 次のステップ

1. **初回リリースの作成**
   - バージョンタグ（例: `v1.0.0`）を作成
   - GitHub Releasesでリリースを作成
   - GitHub Actionsが自動的にexeファイルをアップロード

2. **アイコンファイルの追加**（オプション）
   - `assets/icon.ico` を作成
   - `main.spec` でアイコンを設定

3. **バージョン情報の埋め込み**（オプション）
   - exeファイルにバージョン情報を埋め込み
   - Windowsのプロパティで確認可能にする

4. **クリーン環境でのテスト**
   - Python未インストールのWindows環境でテスト
   - すべての機能が正常に動作することを確認

5. **インストーラの作成**（将来的な拡張）
   - Inno SetupやNSISを使用してインストーラを作成
   - スタートメニューへのショートカット作成
   - アンインストーラの提供
