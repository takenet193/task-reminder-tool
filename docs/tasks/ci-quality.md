# ci-quality: CI品質ゲートタスク仕様

- **目的**: CI上でテストと品質ゲートを実行し、一定品質を満たさない変更をブロックする。
- **関連ID**: `ci-quality`

## 背景と問題点

### 現在の実装の問題

現在のプロジェクトには、CI（Continuous Integration）パイプラインが存在しない：

1. **品質保証の自動化がない**: プルリクエストやコミット時に自動的に品質チェックが行われない
2. **テストの実行が手動**: 開発者がローカルでテストを実行する必要があり、見落としのリスクがある
3. **カバレッジの監視がない**: コードカバレッジが低下しても検知できない
4. **リント/フォーマットの統一性が保証されない**: コードスタイルの一貫性が手動チェックに依存している
5. **型チェックの自動化がない**: 型エラーが本番環境に混入する可能性がある
6. **品質ゲートがない**: 一定品質を満たさない変更がマージされる可能性がある

### CI品質ゲートの重要性

CI品質ゲートを導入することで、以下のメリットが得られる：

- **早期バグ発見**: プルリクエスト時点でバグや品質問題を検出
- **品質の維持**: コードカバレッジやリントエラーを監視し、品質を維持
- **開発効率の向上**: 手動チェックを自動化し、開発者の負担を軽減
- **一貫性の保証**: すべての変更が同じ品質基準を満たすことを保証

## 要件概要

- GitHub Actionsを使用してCIパイプラインを構築する
- プッシュとプルリクエスト時に自動的に品質チェックを実行する
- 以下の品質ゲートを実装する：
  - **テスト実行**: すべてのテストが通過すること
  - **カバレッジチェック**: コードカバレッジが60%以上であること（短期目標）
  - **リントチェック**: ruffによるリントエラーが0件であること
  - **フォーマットチェック**: blackによるフォーマットチェックが通過すること
  - **型チェック**: mypyによる型チェックが通過すること（UIモジュールは除外）
- 品質ゲートを通過しない変更はマージをブロックする
- ローカル環境でもCIと同じチェックを実行できるようにする

## 実装計画

### アーキテクチャ

```
.github/workflows/ci.yml (新規作成)
  └─ CI Quality Gate ワークフロー
     ├─ テスト実行ジョブ
     │  ├─ Python環境セットアップ
     │  ├─ 依存関係インストール
     │  ├─ pytest実行
     │  └─ カバレッジチェック（60%以上）
     ├─ リントジョブ
     │  ├─ ruffリントチェック
     │  └─ blackフォーマットチェック
     └─ 型チェックジョブ
        └─ mypy型チェック

requirements.txt (更新)
  └─ ruff, black, mypy を追加（開発依存関係として）
```

### 実装手順

#### ステップ1: 依存関係の追加

**ファイルパス**: `requirements.txt`

**追加内容**:
```txt
# 開発依存関係（CI用）
ruff>=0.1.0
black>=23.0.0
mypy>=1.5.0
```

**注意**: これらのツールは開発時とCIでのみ使用するため、本番環境には不要です。必要に応じて `requirements-dev.txt` を分離することも検討できますが、シンプルさを優先して `requirements.txt` に追加します。

#### ステップ2: GitHub Actionsワークフローの作成

**ファイルパス**: `.github/workflows/ci.yml`（新規作成）

**実装内容**:

```yaml
name: CI Quality Gate

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    name: Test and Coverage
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.13"]

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run tests with coverage
        run: |
          pytest --cov=. --cov-report=xml --cov-report=term-missing

      - name: Check coverage threshold
        run: |
          coverage report --fail-under=60

      - name: Upload coverage to Codecov (optional)
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: unittests
          name: codecov-umbrella
          fail_ci_if_error: false

  lint:
    name: Lint and Format Check
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run ruff linter
        run: |
          ruff check .

      - name: Check black formatting
        run: |
          black --check .

  type-check:
    name: Type Check
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run mypy
        run: |
          mypy . --config-file pyproject.toml
```

**ワークフローの説明**:

1. **トリガー**: `push` と `pull_request` イベントで実行
2. **テストジョブ**: pytestを実行し、カバレッジを測定。60%以上の閾値をチェック
3. **リントジョブ**: ruffでリントチェック、blackでフォーマットチェック
4. **型チェックジョブ**: mypyで型チェックを実行

#### ステップ3: ローカル検証スクリプトの作成（オプション）

CIと同じチェックをローカルで実行できるスクリプトを作成する。

**ファイルパス**: `scripts/ci-check.sh`（新規作成、オプション）

**実装内容**:

```bash
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
```

**Windows用**: `scripts/ci-check.ps1` も作成可能

## 品質ゲートの詳細

### 1. テスト実行とカバレッジチェック

**目的**: すべてのテストが通過し、コードカバレッジが一定水準以上であることを確認

**実行コマンド**:
```bash
pytest --cov=. --cov-report=xml --cov-report=term-missing
coverage report --fail-under=60
```

**閾値**: カバレッジ60%以上（短期目標）

**除外対象**:
- `ui/`: UIモジュール（tkinter依存）
- `main.py`: エントリーポイント
- `scripts/`: 開発用スクリプト
- `tests/`: テストコード自体

**失敗条件**:
- テストが1つでも失敗する
- カバレッジが60%未満

### 2. リントチェック（ruff）

**目的**: コードスタイルと潜在的なバグを検出

**実行コマンド**:
```bash
ruff check .
```

**設定**: `pyproject.toml` の `[tool.ruff]` セクションを参照

**有効化ルール**:
- E: pycodestyle
- F: Pyflakes
- I: isort
- B: flake8-bugbear
- W: warnings
- UP: pyupgrade

**失敗条件**: リントエラーが1つでも存在する

### 3. フォーマットチェック（black）

**目的**: コードフォーマットの一貫性を保証

**実行コマンド**:
```bash
black --check .
```

**設定**: `pyproject.toml` の `[tool.black]` セクションを参照

**失敗条件**: フォーマットがblackの標準に準拠していない

**注意**: `--check` オプションを使用するため、ファイルは変更されない。自動フォーマットが必要な場合は `black .` を実行。

### 4. 型チェック（mypy）

**目的**: 型エラーを検出し、型安全性を保証

**実行コマンド**:
```bash
mypy . --config-file pyproject.toml
```

**設定**: `pyproject.toml` の `[tool.mypy]` セクションを参照

**除外対象**:
- `tkinter.*`: tkinterモジュール（型スタブが不完全）
- `ui.*`: UIモジュール（tkinter依存）

**失敗条件**: 型エラーが1つでも存在する

## エラーハンドリング

### CI失敗時の対応

#### 1. テスト失敗

**原因**:
- テストコードのバグ
- 実装コードのバグ
- テスト環境の違い

**対応**:
1. ローカルで同じテストを実行して再現する
2. エラーメッセージを確認し、原因を特定する
3. 修正後に再度コミット・プッシュする

#### 2. カバレッジ不足

**原因**:
- 新しいコードがテストでカバーされていない
- 既存のテストが削除された

**対応**:
1. カバレッジレポートを確認し、カバーされていないコードを特定する
2. 不足しているテストを追加する
3. 必要に応じて、カバレッジ対象外に設定する（`pyproject.toml` の `[tool.coverage.run]` セクション）

#### 3. リントエラー

**原因**:
- コードスタイルの違反
- 潜在的なバグ

**対応**:
1. エラーメッセージを確認する
2. 自動修正可能な場合は `ruff check --fix .` を実行
3. 手動で修正が必要な場合は、エラーメッセージに従って修正する

#### 4. フォーマットエラー

**原因**:
- コードがblackのフォーマット標準に準拠していない

**対応**:
1. `black .` を実行して自動フォーマット
2. フォーマットされたファイルをコミット

#### 5. 型チェックエラー

**原因**:
- 型アノテーションの不整合
- 型推論の失敗

**対応**:
1. エラーメッセージを確認し、型エラーの原因を特定する
2. 型アノテーションを修正する
3. 必要に応じて `# type: ignore` コメントを追加（最終手段）

### CI環境の違いによる問題

**問題**: ローカルでは通過するが、CIで失敗する

**原因**:
- Pythonバージョンの違い
- 依存関係のバージョンの違い
- 環境変数の違い

**対応**:
1. CI環境と同じPythonバージョンを使用する
2. `requirements.txt` の依存関係バージョンを固定する
3. 環境変数の設定を確認する

## テスト方法

### ローカルでのCIチェック実行

#### 方法1: 個別コマンドを実行

```bash
# テストとカバレッジ
pytest --cov=. --cov-report=term-missing
coverage report --fail-under=60

# リントチェック
ruff check .

# フォーマットチェック
black --check .

# 型チェック
mypy . --config-file pyproject.toml
```

#### 方法2: スクリプトを使用（作成した場合）

```bash
# Linux/macOS
bash scripts/ci-check.sh

# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -File scripts/ci-check.ps1
```

#### 方法3: actを使用（GitHub Actionsをローカルで実行）

```bash
# actをインストール（https://github.com/nektos/act）
# GitHub Actionsワークフローをローカルで実行
act -j test
act -j lint
act -j type-check
```

### プルリクエスト前のチェック

プルリクエストを作成する前に、必ず以下のチェックを実行する：

1. **テスト実行**: `pytest`
2. **カバレッジ確認**: `coverage report`
3. **リントチェック**: `ruff check .`
4. **フォーマットチェック**: `black --check .`
5. **型チェック**: `mypy .`

### CIでの実行確認

1. プルリクエストを作成する
2. GitHubのActionsタブでCIの実行状況を確認する
3. すべてのジョブが成功することを確認する
4. 失敗した場合は、エラーログを確認して修正する

## ファイル構造

実装後のファイル構造：

```
TaskReminder/
├── .github/
│   └── workflows/
│       └── ci.yml              # 新規作成: CI品質ゲートワークフロー
├── scripts/
│   ├── ci-check.sh             # 新規作成（オプション）: ローカルCIチェックスクリプト
│   └── ci-check.ps1            # 新規作成（オプション）: Windows用スクリプト
├── requirements.txt            # 更新: ruff, black, mypy を追加
├── pyproject.toml               # 既存: ruff, black, mypy設定は既に存在
└── docs/tasks/
    └── ci-quality.md           # 新規作成: 本仕様書
```

## 注意事項

1. **依存関係の管理**:
   - `ruff`、`black`、`mypy` は開発依存関係として追加
   - 本番環境では不要だが、CIで使用するため `requirements.txt` に含める

2. **カバレッジ閾値**:
   - 短期目標: 60%以上
   - 長期目標: 80%以上（将来的に引き上げ可能）
   - 閾値は `coverage report --fail-under=60` で設定

3. **型チェックの除外**:
   - `ui/` モジュールは型チェックから除外（tkinter依存）
   - `pyproject.toml` の `[[tool.mypy.overrides]]` で設定済み

4. **CI実行時間**:
   - 3つのジョブ（test、lint、type-check）は並列実行される
   - 各ジョブの実行時間を監視し、必要に応じて最適化する

5. **セキュリティ**:
   - GitHub Actionsのシークレットを使用する場合は、適切に管理する
   - コードカバレッジのアップロード（Codecovなど）はオプション

6. **ブランチ保護ルール**:
   - GitHubのブランチ保護ルールで、CI通過を必須条件に設定することを推奨
   - 設定方法: リポジトリ設定 > Branches > Branch protection rules

7. **ローカル環境との整合性**:
   - CI環境と同じPythonバージョン（3.13）を使用する
   - 依存関係のバージョンを固定することを推奨

## 実装チェックリスト

- [ ] `requirements.txt` に `ruff`、`black`、`mypy` を追加
- [ ] `.github/workflows/` ディレクトリを作成
- [ ] `.github/workflows/ci.yml` を作成し、CIワークフローを実装
- [ ] テストジョブが正常に動作することを確認
- [ ] リントジョブが正常に動作することを確認
- [ ] 型チェックジョブが正常に動作することを確認
- [ ] カバレッジチェックが正常に動作することを確認
- [ ] ローカルでCIチェックを実行できることを確認（オプション: スクリプト作成）
- [ ] プルリクエストでCIが実行されることを確認
- [ ] 品質ゲートが正常に機能することを確認（意図的に失敗する変更でテスト）
- [ ] ブランチ保護ルールを設定（推奨）

## 参考資料

- GitHub Actions公式ドキュメント: https://docs.github.com/ja/actions
- pytest公式ドキュメント: https://docs.pytest.org/
- coverage.py公式ドキュメント: https://coverage.readthedocs.io/
- ruff公式ドキュメント: https://docs.astral.sh/ruff/
- black公式ドキュメント: https://black.readthedocs.io/
- mypy公式ドキュメント: https://mypy.readthedocs.io/
- act（GitHub Actionsローカル実行）: https://github.com/nektos/act
