# TaskReminder

発達障害のある方向けの定型業務サポートツールです。出勤退勤の報告や日報の提出などの定型業務を忘れがちな方のために、リマインダー機能とチェックボックス付きの作業表を提供します。

## 機能

### 1. リマインダー機能
- **予告通知**: 設定時刻の5分前に小さな通知ウィンドウを表示
- **本通知**: 設定時刻にタスク名とチェックボックスを表示
- **警告通知**: 未完了の場合、5分後に画面中央で警告表示

### 2. タスク管理
- タスクの追加・編集・削除
- 複数タスクの同時設定（例：14:30に日報、勤怠報告、勤務表）
- 毎日繰り返し設定

### 3. ログ・達成率表示
- タスク完了履歴の記録
- 月ごとの達成率表示
- 過去12ヶ月の未達成率グラフ

### 4. 常駐機能
- タスクバーに常駐
- バックグラウンドでの時刻監視
- 設定画面・ログ画面へのアクセス

### 5. 達成率計算設定
- **週末除外設定**: 土日を達成率計算から除外する設定
- **カレンダーオーバーライド**: 日単位で達成率の対象日を個別に設定可能
  - 週末除外設定を有効にしても、特定の土日を含めることが可能
  - 平日でも特定の日を除外することが可能

## インストール・使用方法

### Windows版（推奨）

Python環境が不要な、単一のexeファイル版を提供しています。

#### ダウンロード

1. [GitHub Releases](https://github.com/takenet193/task-reminder-tool/releases)から最新版をダウンロード
2. `TaskReminder.exe`をダウンロード

#### インストール手順

1. ダウンロードした`TaskReminder.exe`を任意のフォルダに配置
2. exeファイルをダブルクリックして起動
3. 初回起動時に、exeファイルと同じディレクトリに`data/`フォルダが自動作成されます

#### システム要件

- Windows 10以降
- 管理者権限不要
- Python環境不要

#### トラブルシューティング（Windows版）

- **ウイルススキャンの誤検知**: PyInstallerで生成したexeは誤検知されやすい場合があります。信頼できるソース（GitHub Releases）からのダウンロードであることを確認してください。
- **起動が遅い**: 初回起動時は一時ファイルの展開により、やや時間がかかることがあります（通常5秒以内）。
- **データファイルの場所**: データファイル（`data/`フォルダ）は、exeファイルと同じディレクトリに作成されます。

#### チェックサム検証

ダウンロードしたexeファイルの整合性を確認するには、以下のコマンドを実行してください：

```powershell
Get-FileHash -Path "TaskReminder.exe" -Algorithm SHA256
```

GitHub Releasesに記載されているSHA256ハッシュ値と一致することを確認してください。

### 開発者向けインストール（Python環境が必要）

#### 必要な環境
- Python 3.7以上
- tkinter（Python標準ライブラリ）
- matplotlib

#### インストール手順

1. リポジトリをクローンまたはダウンロード
```bash
git clone <repository-url>
cd TaskReminder
```

2. 依存パッケージをインストール
```bash
pip install -r requirements.txt
```

3. MCP設定（GitHub連携用）
```bash
# .envファイルを作成（mcp_setup/env.exampleを参考）
cp mcp_setup/env.example .env
# .envファイルを編集してGitHubトークンを設定

# MCP設定ファイルを生成（ワークスペースパスは絶対パスで指定してください）
# PowerShell（Windows）
powershell -ExecutionPolicy Bypass -File "mcp_setup\scripts\generate_mcp_config.ps1" -WorkspacePath "C:\path\to\your\workspace"

# Bash（Linux/macOS）
bash mcp_setup/scripts/generate_mcp_config.sh /path/to/your/workspace
```

4. アプリケーションを起動
```bash
python main.py
```

### 基本的な使用方法

1. **アプリケーション起動**
   - `python main.py`でアプリケーションを起動
   - タスクバーに小さなウィンドウが表示されます

2. **タスク設定**
   - メインウィンドウの「タスク設定」ボタンをクリック
   - 「追加」ボタンで新しいタスクを追加
   - 時刻（HH:MM形式）とタスク名を入力
   - 複数のタスク名を設定可能

3. **通知の確認**
   - 設定時刻の5分前に予告通知が表示
   - 設定時刻に本通知が表示
   - チェックボックスをすべてチェックして「完了」ボタンをクリック

4. **ログ・達成率の確認**
   - メインウィンドウの「ログ・達成率」ボタンをクリック
   - 月ごとの達成率とグラフを確認
   - 「対象日設定」タブで週末除外設定やカレンダーオーバーライドを設定可能

## PC起動時の自動起動設定

### Windows 10/11の場合

1. **スタートアップフォルダを使用する方法**
   ```
   1. Win + R キーを押して「ファイル名を指定して実行」を開く
   2. shell:startup と入力してEnter
   3. スタートアップフォルダが開く
   4. アプリケーションのショートカットを作成してコピー
   ```

2. **タスクスケジューラーを使用する方法**
   ```
   1. タスクスケジューラーを開く
   2. 「基本タスクの作成」を選択
   3. 名前: 「TaskReminder」
   4. トリガー: 「コンピューターの起動時」
   5. 操作: 「プログラムの開始」
   6. プログラム: python.exeのパス
   7. 引数: main.pyのフルパス
   8. 開始: プロジェクトフォルダのパス
   ```

3. **レジストリを使用する方法**
   ```
   1. Win + R キーを押してregeditを実行
   2. HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run
   3. 新しい文字列値を作成
   4. 名前: 「TaskReminder」
   5. 値: 「python.exe main.pyのフルパス」
   ```

### 推奨設定

- **タスクスケジューラー**を使用することを推奨します
- 遅延起動を設定して、システム起動後にアプリケーションが起動するようにします
- 管理者権限は不要です（現在のユーザーで実行）

## GitHub連携とMCP設定

このプロジェクトは、CursorエディタとGitHubを連携させるためのMCP（Model Context Protocol）設定を含んでいます。

### MCP設定の詳細

1. **GitHub連携**
   - GitHubリポジトリへのアクセス
   - Issue、PR、コミット履歴の参照
   - コードレビューの支援

2. **ファイルシステム連携**
   - プロジェクトファイルへの直接アクセス
   - コードの検索と編集支援

### GitHubトークンの設定

1. **Personal Access Tokenの作成**
   - GitHub.com にログイン
   - Settings > Developer settings > Personal access tokens > Tokens (classic)
   - "Generate new token (classic)" をクリック
   - 必要なスコープを選択: `repo`, `read:org`, `read:user`
   - トークンをコピー

2. **環境変数の設定**
   ```bash
   # .envファイルを作成
   cp mcp_setup/env.example .env

   # .envファイルを編集してトークンを設定
   GITHUB_PERSONAL_ACCESS_TOKEN=your_actual_token_here
   ```

3. **MCP設定ファイルの生成**
   ```bash
   # PowerShell（Windows）
   # ワークスペースパスは絶対パスで指定してください
   powershell -ExecutionPolicy Bypass -File "mcp_setup\scripts\generate_mcp_config.ps1" -WorkspacePath "C:\path\to\your\workspace"

   # Bash（Linux/macOS）
   # ワークスペースパスは絶対パスで指定してください
   bash mcp_setup/scripts/generate_mcp_config.sh /path/to/your/workspace
   ```

   **注意**: `filesystem` MCPは絶対パスが必要です。相対パスでは動作しません。

4. **Cursorでの設定**
   - Cursorの設定でMCP設定ファイル（`mcp_config.json`）を指定
   - 設定 > MCP Servers で設定ファイルのパスを指定

## ファイル構成

```
TaskReminder/
├── main.py                 # メインアプリケーション
├── config.py              # 設定管理クラス
├── task_manager.py        # タスク管理とスケジューリング
├── ui/
│   ├── main_window.py     # メインウィンドウ
│   ├── reminder_window.py # リマインダーウィンドウ
│   ├── settings_window.py # タスク設定画面
│   └── log_window.py      # ログ・達成率表示画面
├── utils/
│   └── __init__.py        # ユーティリティパッケージ初期化
├── data/
│   ├── tasks.json         # タスク設定データ
│   ├── logs.json          # タスク完了履歴
│   ├── settings.json      # アプリケーション設定（週末除外設定など）
│   └── calendar_overrides.json # カレンダーオーバーライド設定
├── mcp_setup/             # MCP設定テンプレート
│   ├── mcp_config.template.json
│   ├── env.example
│   └── scripts/
│       ├── generate_mcp_config.ps1
│       └── generate_mcp_config.sh
├── mcp_config.json        # 生成されるMCP設定ファイル
├── .env                   # 環境変数（Git管理対象外）
├── .gitignore            # Git除外設定
└── requirements.txt       # 依存パッケージ
```

## データファイル

- **tasks.json**: タスク設定データ
- **logs.json**: タスク完了履歴
- **settings.json**: アプリケーション設定（週末除外設定など）
- **calendar_overrides.json**: カレンダーオーバーライド設定（日単位での達成率対象日設定）

これらのファイルは`data/`フォルダに保存され、アプリケーションが自動的に管理します。

## トラブルシューティング

### よくある問題

1. **アプリケーションが起動しない**
   - **Windows版**: exeファイルをダブルクリックしても起動しない場合、ウイルススキャンソフトがブロックしている可能性があります。セキュリティソフトの設定を確認してください。
   - **開発版**: Pythonのバージョンを確認（3.7以上が必要）
   - **開発版**: 依存パッケージがインストールされているか確認

2. **通知が表示されない**
   - タスクが正しく設定されているか確認
   - システム時刻が正確か確認
   - アプリケーションがバックグラウンドで実行されているか確認

3. **自動起動が動作しない**
   - タスクスケジューラーの設定を確認
   - ファイルパスが正しいか確認
   - **Windows版**: exeファイルのフルパスを指定してください

4. **データファイルが見つからない**
   - **Windows版**: exeファイルと同じディレクトリに`data/`フォルダが作成されます
   - **開発版**: プロジェクトルートに`data/`フォルダが作成されます

5. **MCP連携が動作しない**（開発者向け）
   - GitHubトークンが正しく設定されているか確認
   - `.env`ファイルがプロジェクトルートに存在するか確認
   - `mcp_config.json`が正しく生成されているか確認
   - CursorのMCP設定で設定ファイルのパスが正しいか確認
   - MCP設定ファイル生成時にワークスペースパスを絶対パスで指定したか確認

### ログの確認

アプリケーションの動作ログは標準出力に表示されます。問題が発生した場合は、コンソール出力を確認してください。

### MCP設定の確認

1. **設定ファイルの検証**
   ```bash
   # mcp_config.jsonの内容を確認
   cat mcp_config.json
   ```

2. **環境変数の確認**
   ```bash
   # .envファイルの内容を確認（トークンは表示されません）
   cat .env
   ```

3. **CursorでのMCP接続確認**
   - Cursorの設定画面でMCPサーバーの状態を確認
   - エラーメッセージがある場合は、トークンやファイルパスを再確認

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 貢献

バグ報告や機能要望は、GitHubのIssueページでお知らせください。

## 更新履歴

- v1.0.0: 初回リリース
  - 基本的なリマインダー機能
  - タスク設定機能
  - ログ・達成率表示機能
