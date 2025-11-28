# ポートフォリオ自動生成システム 仕様書 v2.0

## 概要

就労移行支援で使用するポートフォリオを、コードベース全体から直接情報を抽出してエクセルに自動入力するシステムです。

**前バージョンからの主な変更点:**
- マークダウンレポート経由方式を廃止
- コードベースを直接参照してエクセルに記入
- エクセル読み込み不要（テンプレートをコピーして書き込む方式）
- 動的パターンマッチングによる柔軟なファイル探索

## 設計思想

### 基本方針

1. **中間生成物を排除**: Markdownレポートを経由せず、コードベースから直接情報を抽出
2. **設定ファイル中心**: セルマッピング情報は設定ファイル（`.cursor/portfolio_config.json`）に固定
3. **動的ファイル探索**: プロジェクト構造に依存しない柔軟なファイル探索
4. **効率的な処理**: エクセルは読み込まず、テンプレートをコピーして書き込むだけ

### なぜこの方式か

- **品質向上**: コードベースから直接情報を抽出することで、より正確で詳細な内容を生成
- **効率化**: 中間レポート生成を省略し、処理を高速化
- **柔軟性**: プロジェクト構造が異なっても対応可能
- **保守性**: 設定ファイルで一元管理、エクセル読み込み不要で処理がシンプル

## システムアーキテクチャ

### 処理フロー

```
[1] 設定ファイル（.cursor/portfolio_config.json）を読み込む
    ↓
    - セルマッピング情報（固定）
    - 各セルの説明（descriptionフィールド）
    - データソース設定
    ↓

[2] 各セル項目について処理
    ├─ 設定ファイルの"description"を読む（エクセルの解説の代わり）
    ├─ コードベース全体を動的に探索・参照
    ├─ セマンティック検索で関連ファイルを特定
    └─ 生成した内容をメモリ上に保持
    ↓

[3] エクセルテンプレートをコピー
    shutil.copy("ポートフォリオ_Template_ver2.0.xlsx", "ポートフォリオ_出力.xlsx")
    ↓

[4] コピーしたエクセルに一括で書き込み
    - 書式は既に保持されている（テンプレートのまま）
    - 値だけを書き換える
    ↓

[5] 保存して完了
```

### データフロー

```
設定ファイル
    ↓
セルマッピング情報（各セルの説明、データソース、変換ルール）
    ↓
コードベース参照（動的ファイル探索 + セマンティック検索）
    ↓
内容生成（AIによる文脈理解と文章生成）
    ↓
エクセル書き込み（テンプレートコピー + 値の書き換え）
```

## 設定ファイル構造

### 基本構造

設定ファイル（`.cursor/portfolio_config.json`）は以下の構造を持ちます：

```json
{
  "version": "2.0",
  "description": "ポートフォリオ自動生成システムの設定ファイル（v2.0）",
  "excel_template": {
    "file": "ポートフォリオ_Template_ver2.0.xlsx",
    "sheet": "フォーマット"
  },
  "cell_mapping": {
    "項目名": {
      "cell": "セルアドレス（例: D3）",
      "merged_range": "統合範囲（例: D9:L14）",
      "row_count": 行数,
      "estimated_chars": 推定文字数,
      "description": "このセルに何を記入すべきかの説明",
      "codebase_sources": ["参照すべきデータソース"],
      "max_chars": 最大文字数,
      "transform": "変換ルール"
    }
  },
  "dynamic_file_discovery": {
    "documentation_patterns": [...],
    "source_patterns": [...]
  }
}
```

### セルマッピングの説明

#### descriptionフィールド

- **役割**: エクセルのセル解説の代わり
- **内容**: そのセルに何を記入すべきかを明確に説明
- **例**: "プロジェクトの背景・動機を説明。なぜこのテーマを選んだのか、どのような課題を解決しようとしているのかを記述。約500文字。"

この`description`をAIが読み取り、コードベースを参照して適切な内容を生成します。

#### codebase_sources

参照すべきデータソースの優先順位を指定：

- `["README.md", "ARCHITECTURE.md", "main.py"]`: 特定ファイルを優先
- `["documentation", "source_code"]`: カテゴリ指定
- `["semantic_search"]`: セマンティック検索で自動特定

## コードベース参照の効率化

### 動的パターンマッチング

プロジェクト構造が異なっても対応できるように、パターンベースでファイルを探索します。

#### 1. パターンベースのファイル探索

固定のファイル名ではなく、パターンでファイルを探索：

```python
documentation_patterns = [
    # プロジェクト概要系（最も優先）
    ("README*", "プロジェクト全体の説明"),
    ("readme*", "プロジェクト全体の説明"),
    ("README.*", "プロジェクト全体の説明"),

    # アーキテクチャ・設計系
    ("ARCHITECTURE*", "システム設計の詳細"),
    ("architecture*", "システム設計の詳細"),
    ("DESIGN*", "システム設計の詳細"),
    ("設計*", "システム設計の詳細"),

    # 変更履歴・ログ系
    ("CHANGELOG*", "変更履歴"),
    ("CHANGES*", "変更履歴"),
    ("HISTORY*", "変更履歴"),

    # 計画・目的系
    ("plan*.json", "タスク計画・目的"),
    ("*.plan.json", "タスク計画・目的"),
    ("ROADMAP*", "開発計画"),

    # 技術仕様系
    ("requirements*.txt", "使用技術"),
    ("package.json", "使用技術"),
    ("Pipfile", "使用技術"),
    ("pyproject.toml", "プロジェクト設定"),
]
```

#### 2. ディレクトリ構造の自動認識

実際に存在するディレクトリを認識して優先度を決めます：

```python
def discover_project_structure(root_dir: str) -> dict:
    """
    プロジェクトのディレクトリ構造を自動認識
    """
    structure = {
        "documentation_dirs": [],  # docs/, documentation/, doc/ など
        "source_dirs": [],         # src/, lib/, app/, など
        "config_files": [],        # 設定ファイル
        "main_entry_points": []    # main.py, index.py, app.py など
    }

    # ドキュメントディレクトリを探索
    for dir_name in os.listdir(root_dir):
        if os.path.isdir(dir_name):
            if any(keyword in dir_name.lower() for keyword in
                   ["doc", "readme", "spec", "design"]):
                structure["documentation_dirs"].append(dir_name)

    # ソースコードディレクトリを探索
    common_source_dirs = ["src", "lib", "app", "source", "main"]
    for dir_name in common_source_dirs:
        if os.path.exists(os.path.join(root_dir, dir_name)):
            structure["source_dirs"].append(dir_name)

    return structure
```

#### 3. セマンティック検索による関連ファイル特定

まずセマンティック検索で関連ファイルを特定し、その結果から優先順位を決定：

```python
def get_relevant_files_for_cell(
    cell_description: str,
    excel_instruction: str,
    project_root: str
) -> list[str]:
    """
    エクセルセルの解説に基づいて、関連ファイルを動的に特定
    """
    # 1. セマンティック検索で関連ファイルを探す
    query = f"{excel_instruction} {cell_description}"
    search_results = codebase_search(
        query=query,
        target_directories=[]  # 全体を検索
    )

    # 検索結果から関連ファイルを抽出
    relevant_files = extract_files_from_search_results(search_results)

    # 2. ファイルの重要度を自動評価
    file_scores = {}
    for file_path in relevant_files:
        score = calculate_file_importance(
            file_path,
            cell_description,
            excel_instruction
        )
        file_scores[file_path] = score

    # 3. スコア順にソート
    sorted_files = sorted(
        file_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return [file for file, score in sorted_files[:10]]  # 上位10ファイル
```

#### 4. ファイル重要度の自動評価

ファイルの重要度を複数の要素で評価：

```python
def calculate_file_importance(
    file_path: str,
    cell_description: str,
    excel_instruction: str
) -> float:
    """
    ファイルの重要度をスコアリング（0.0-1.0）
    """
    score = 0.0

    # 1. ファイル名の重要度
    filename = os.path.basename(file_path).lower()

    # ドキュメントファイルは高スコア
    if any(keyword in filename for keyword in
           ["readme", "architecture", "design", "changelog"]):
        score += 0.4

    # メインファイルは高スコア
    if any(keyword in filename for keyword in
           ["main", "index", "app"]):
        score += 0.3

    # 2. ディレクトリ位置の重要度
    if "/" not in file_path or file_path.startswith("./"):
        score += 0.2  # ルート直下は重要

    # 3. ファイルサイズ（適度なサイズが良い）
    try:
        size = os.path.getsize(file_path)
        if 1000 < size < 100000:  # 1KB-100KB
            score += 0.1
    except:
        pass

    return min(score, 1.0)
```

### 除外するファイル/ディレクトリ

以下のファイルは処理から除外します：

```python
exclude_patterns = [
    # 実行ファイル・バイナリ
    "*.exe",
    "*.pyc",
    "__pycache__/**",
    "build/**",
    "dist/**",

    # ログ・データファイル
    "*.log",
    "data/**",  # ユーザーデータは除外

    # 設定ファイル（プロジェクト理解には不要）
    ".env",
    ".git/**",

    # テストファイル（実装内容には関係ない）
    "tests/**",

    # ドキュメント生成物（旧方式のレポート）
    "docs/reports/*.md",  # 新方式では不要

    # MCP設定（ポートフォリオには関係ない）
    "mcp_setup/**",

    # スクリプト（配布用、CI用は除外）
    "scripts/build-*.ps1",
    "scripts/build-*.sh",
    "scripts/ci-check.*",
]
```

## エクセル操作

### テンプレートコピー方式

エクセルは読み込まず、テンプレートをコピーして書き込む方式を採用：

```python
# 1. テンプレートをコピー
import shutil
shutil.copy(
    "ポートフォリオ_Template_ver2.0.xlsx",
    "ポートフォリオ_出力.xlsx"
)

# 2. コピーしたエクセルに書き込む
# 書式は既に保持されているため、値だけを書き換える
```

### メリット

- **高速**: エクセルの読み込み・解析が不要
- **シンプル**: コピー→書き込みのみで処理が単純
- **書式保持**: テンプレートの書式が自動的に保持される
- **エラー回避**: エクセル読み込み時のエラーを回避

## 各セルへの記入方法

### 記入プロセス

各セルについて、以下のプロセスで内容を生成します：

1. **設定ファイルから情報を取得**
   - セルアドレス、説明、データソース、文字数制限など

2. **コードベースを探索**
   - パターンマッチングで関連ファイルを特定
   - セマンティック検索でさらに関連ファイルを発見
   - ファイル重要度で優先順位を決定

3. **関連ファイルを読み込む**
   - 優先順位の高いファイルから順に読み込み
   - 十分な情報が集まったら早期終了

4. **内容を生成**
   - AIがコードベースの内容を理解
   - セルの説明に基づいて適切な内容を生成
   - 文字数制限を考慮

5. **エクセルに書き込む**
   - 生成した内容を指定セルに書き込み

### 例: 「背景」セルの記入

```json
{
  "背景": {
    "cell": "D9",
    "merged_range": "D9:L14",
    "estimated_chars": 500,
    "description": "プロジェクトの背景・動機を説明。なぜこのテーマを選んだのか、どのような課題を解決しようとしているのかを記述。約500文字。",
    "codebase_sources": ["README.md", "ARCHITECTURE.md", "semantic_search"],
    "max_chars": 500
  }
}
```

**処理手順:**

1. `description`を読む → 「プロジェクトの背景・動機を説明...」
2. コードベースを探索:
   - パターン: `README*` を検索
   - セマンティック検索: "プロジェクトの背景 動機 テーマ選定理由" で検索
3. 関連ファイルを読み込み:
   - `README.md` → プロジェクト概要セクション
   - `ARCHITECTURE.md` → 背景セクション
   - 検索結果から関連コード
4. 内容を生成:
   - AIがコードベースを理解
   - 「背景・動機」に関する内容を約500文字で生成
5. エクセルに書き込み:
   - セル D9:L14 に書き込み

## データソース

### 主要データソース

1. **ドキュメントファイル**
   - README.md
   - ARCHITECTURE.md
   - CHANGELOG.md
   - その他のドキュメント

2. **ソースコード**
   - メインファイル（main.py, index.py など）
   - コアロジックファイル
   - UIファイル

3. **設定ファイル**
   - plan.json（タスク計画・目的）
   - requirements.txt（使用技術）
   - pyproject.toml（プロジェクト設定）

4. **Git履歴**
   - 最新コミット日
   - コミットメッセージ（必要な場合）

### セマンティック検索

コードベース全体に対してセマンティック検索を実行：

- エクセルセルの説明から検索クエリを生成
- 関連するコード・ドキュメントを自動発見
- 重要度スコアで優先順位を決定

## 実装の詳細

### 主要モジュール

#### 1. 設定ファイル読み込みモジュール

設定ファイル（`.cursor/portfolio_config.json`）を読み込み、セルマッピング情報を取得。

#### 2. 動的ファイル探索モジュール

- パターンマッチングによるファイル探索
- ディレクトリ構造の自動認識
- セマンティック検索の統合
- ファイル重要度の評価

#### 3. コードベース参照モジュール

- 関連ファイルの読み込み
- コンテキストの構築
- 情報の抽出

#### 4. 内容生成モジュール

- AIによる文脈理解
- セルの説明に基づいた内容生成
- 文字数制限の考慮

#### 5. エクセル操作モジュール

- テンプレートのコピー
- セルへの書き込み
- 書式の保持

## コマンドラインインターフェース

### 基本的な使用法

```bash
python scripts/generate_portfolio.py \
    --template "ポートフォリオ_Template_ver2.0.xlsx" \
    --output "ポートフォリオ_出力.xlsx" \
    --config ".cursor/portfolio_config.json"
```

### オプション

- `--template`: テンプレートファイルのパス（必須）
- `--output`: 出力ファイルのパス（オプション、デフォルト: プロジェクト名_ポートフォリオ.xlsx）
- `--config`: 設定ファイルのパス（オプション、デフォルト: .cursor/portfolio_config.json）
- `--project-root`: プロジェクトルートディレクトリ（オプション、デフォルト: 現在のディレクトリ）
- `--verbose`: 詳細なログを出力

## エラーハンドリング

### 想定されるエラーと対応

1. **設定ファイルが見つからない**
   - デフォルト設定を使用
   - またはエラーメッセージを表示して終了

2. **テンプレートファイルが見つからない**
   - エラーメッセージを表示して終了

3. **コードベースから情報が見つからない**
   - 該当セルを空欄にする
   - 警告メッセージをログに記録

4. **ファイル読み込みエラー**
   - そのファイルをスキップして続行
   - エラーログに記録

## 今後の改善点

1. **AI機能の拡張**
   - より高度な文脈理解
   - 文章生成の品質向上

2. **パフォーマンス最適化**
   - ファイル探索の高速化
   - 並列処理の導入

3. **設定の柔軟性向上**
   - より細かいカスタマイズオプション
   - 複数テンプレートの対応

4. **エクセル書式の動的調整**
   - 文字数に応じた行の自動調整
   - フォントサイズの調整

## まとめ

この仕様書で定義したシステムは、コードベースから直接情報を抽出してポートフォリオを生成する、効率的で柔軟なシステムです。プロジェクト構造に依存せず、動的なファイル探索により、様々なプロジェクトに対応できます。
