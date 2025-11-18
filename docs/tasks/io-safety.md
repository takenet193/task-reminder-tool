# io-safety: 原子的書き込み・バックアップ/復旧タスク仕様

- **目的**: 設定ファイルやタスクファイルの読み書き処理を見直し、原子的な書き込みとバックアップ/復旧機能を導入する。
- **関連ID**: `io-safety`

## 背景と問題点

### 現在の実装の問題

現在の `config.py` では、以下のような直接的なファイル書き込みを行っている：

```43:47:config.py
def _save_tasks(self, tasks: list[dict[str, Any]]) -> None:
    """タスクデータをJSONファイルに保存"""
    data = {"tasks": tasks}
    with open(self.tasks_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
```

この方法では以下の問題が発生する可能性がある：

1. **データ破損のリスク**: 書き込み中にプログラムがクラッシュしたり、ディスク容量不足になったりすると、既存のファイルが破損する可能性がある
2. **中途半端な状態**: 書き込みが途中で中断されると、ファイルが不完全な状態で残る
3. **復旧不可能**: エラー発生時に既存データを復旧する手段がない

## 原子的書き込みとは

原子的書き込み（Atomic Write）は、ファイル書き込みを「すべて成功」または「すべて失敗」のどちらかに保証する手法である。書き込み中にエラーが発生しても、既存のファイルが壊れることがない。

### 仕組み

1. **一時ファイルへの書き込み**: まず一時ファイル（例: `tasks.json.tmp`）にデータを書き込む
2. **原子的リネーム**: 書き込みが完了したら、`os.replace()` を使用して一時ファイルを元のファイル名にリネームする
3. **原子的操作**: `os.replace()` は多くのOSで原子的操作として実装されているため、既存ファイルが壊れることはない

### メリット

- **データの整合性**: 書き込み失敗時も既存ファイルが壊れない
- **バックアップ/復旧**: エラー時にバックアップから復旧可能
- **並行処理の安全性**: 複数のプロセスが同時に書き込んでも、ファイルが中途半端な状態にならない

## 実装計画

### アーキテクチャ

```
utils/file_io.py (新規作成)
  └─ atomic_write_json()  # 汎用的な原子的書き込み関数

config.py (更新)
  └─ _save_tasks()
  └─ _save_logs()
  └─ _save_settings()
  └─ _save_calendar_overrides()
      └─ atomic_write_json() を使用
```

### 実装手順

#### ステップ1: `utils/file_io.py` の作成

汎用的な原子的書き込み関数を実装する。

**ファイルパス**: `utils/file_io.py`

**実装内容**:

```python
import json
import os
import shutil
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

def atomic_write_json(filepath: str, data: dict[str, Any] | list[Any]) -> None:
    """
    JSONファイルを原子的に書き込む

    Args:
        filepath: 書き込むファイルのパス
        data: 書き込むデータ（dictまたはlist）

    Raises:
        OSError: ファイル操作に失敗した場合
        json.JSONEncodeError: JSONエンコードに失敗した場合

    処理フロー:
    1. 既存ファイルがある場合はバックアップを作成（.bak）
    2. 一時ファイル（.tmp）にデータを書き込む
    3. 書き込み成功後、os.replace()で原子的にリネーム
    4. 成功したらバックアップを削除
    5. エラー時は一時ファイルを削除し、バックアップから復旧を試みる
    """
    filepath = Path(filepath)
    backup_path = filepath.with_suffix(filepath.suffix + ".bak")
    temp_path = filepath.with_suffix(filepath.suffix + ".tmp")

    # 既存ファイルのバックアップを作成
    if filepath.exists():
        try:
            shutil.copy2(filepath, backup_path)
            logger.debug(f"バックアップを作成: {backup_path}")
        except OSError as e:
            logger.warning(f"バックアップ作成に失敗: {e}")
            # バックアップ作成失敗は続行（新規ファイルの可能性もある）

    # 一時ファイルに書き込み
    try:
        logger.debug(f"一時ファイルに書き込み開始: {temp_path}")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 原子的にリネーム（既存ファイルを置き換え）
        os.replace(temp_path, filepath)
        logger.info(f"ファイルを原子的に書き込みました: {filepath}")

        # 成功したらバックアップを削除
        if backup_path.exists():
            try:
                backup_path.unlink()
                logger.debug(f"バックアップを削除: {backup_path}")
            except OSError as e:
                logger.warning(f"バックアップ削除に失敗（無視）: {e}")

    except (OSError, json.JSONEncodeError) as e:
        # エラー時は一時ファイルを削除
        if temp_path.exists():
            try:
                temp_path.unlink()
                logger.debug(f"一時ファイルを削除: {temp_path}")
            except OSError:
                pass

        # バックアップから復旧を試みる
        if backup_path.exists():
            try:
                shutil.copy2(backup_path, filepath)
                logger.warning(f"バックアップから復旧しました: {filepath}")
            except OSError as restore_error:
                logger.error(f"バックアップからの復旧に失敗: {restore_error}")

        # 元のエラーを再発生
        logger.error(f"ファイル書き込みに失敗: {filepath}, エラー: {e}")
        raise
```

**特徴**:

- 汎用的な関数として実装し、他のモジュールからも再利用可能
- 詳細なログ出力でデバッグとトラブルシューティングを支援
- エラーハンドリングを徹底し、可能な限りデータ損失を防ぐ
- バックアップからの自動復旧機能

#### ステップ2: `config.py` の更新

各 `_save_*` メソッドを原子的書き込みに変更する。

**ファイルパス**: `config.py`

**変更箇所**:

1. **インポートの追加**:
```python
from utils.file_io import atomic_write_json
```

2. **各 `_save_*` メソッドの更新**:

```python
def _save_tasks(self, tasks: list[dict[str, Any]]) -> None:
    """タスクデータをJSONファイルに保存"""
    data = {"tasks": tasks}
    atomic_write_json(self.tasks_file, data)

def _save_logs(self, logs: list[dict[str, Any]]) -> None:
    """ログデータをJSONファイルに保存"""
    data = {"logs": logs}
    atomic_write_json(self.logs_file, data)

def _save_settings(self, settings: dict[str, Any]) -> None:
    """設定データをJSONファイルに保存"""
    atomic_write_json(self.settings_file, settings)

def _save_calendar_overrides(self, overrides: dict[str, dict[str, bool]]) -> None:
    """カレンダーオーバーライドデータをJSONファイルに保存"""
    atomic_write_json(self.calendar_overrides_file, overrides)
```

**変更内容**:

- `open()` + `json.dump()` のパターンを `atomic_write_json()` に置き換え
- 既存のインターフェースは維持（メソッド名や引数は変更なし）
- 内部実装のみを原子的書き込みに変更

#### ステップ3: logging設定の確認/追加

プロジェクト全体のlogging設定を確認し、必要に応じて設定を追加する。

**確認事項**:

- `main.py` でlogging設定が行われているか確認
- 行われていない場合は、基本的なlogging設定を追加

**推奨設定** (`main.py` に追加):

```python
import logging
import sys

# logging設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        # 必要に応じてファイルハンドラーも追加
        # logging.FileHandler('app.log', encoding='utf-8'),
    ]
)
```

**ログ出力例**:

```
2025-11-19 10:30:15 - utils.file_io - DEBUG - バックアップを作成: data/tasks.json.bak
2025-11-19 10:30:15 - utils.file_io - DEBUG - 一時ファイルに書き込み開始: data/tasks.json.tmp
2025-11-19 10:30:15 - utils.file_io - INFO - ファイルを原子的に書き込みました: data/tasks.json
2025-11-19 10:30:15 - utils.file_io - DEBUG - バックアップを削除: data/tasks.json.bak
```

## エラーハンドリング

### エラーケースと対応

1. **ディスク容量不足**
   - 一時ファイル書き込み時に `OSError` が発生
   - バックアップから復旧を試みる
   - エラーをログに記録して再発生

2. **JSONエンコードエラー**
   - `json.JSONEncodeError` が発生
   - 一時ファイルを削除
   - バックアップから復旧を試みる
   - エラーをログに記録して再発生

3. **ファイル権限エラー**
   - `PermissionError` が発生
   - バックアップからの復旧も試みるが、権限エラーの場合は失敗
   - エラーをログに記録して再発生

4. **バックアップ作成失敗**
   - 警告ログを出力するが、処理は続行
   - 新規ファイルの場合はバックアップが不要なため問題なし

## テスト方法

### 手動テスト

1. **正常系テスト**:
   ```python
   # タスクを追加して保存
   config.add_task("10:00", ["タスク1", "タスク2"])
   # data/tasks.json が正常に更新されていることを確認
   ```

2. **エラーケーステスト**:
   - ディスク容量不足をシミュレート（ディスクを満杯にする）
   - ファイル権限を変更して書き込み不可にする
   - 不正なデータを渡してJSONエンコードエラーを発生させる

3. **バックアップ/復旧テスト**:
   - 書き込み中にプロセスを強制終了
   - `.bak` ファイルが存在することを確認
   - アプリケーションを再起動して復旧が機能することを確認

### 自動テスト（将来実装）

```python
import tempfile
import shutil
from pathlib import Path
from utils.file_io import atomic_write_json

def test_atomic_write_json_success():
    """正常系テスト"""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "test.json"
        data = {"key": "value"}

        atomic_write_json(str(filepath), data)

        assert filepath.exists()
        assert not filepath.with_suffix(".tmp").exists()
        assert not filepath.with_suffix(".bak").exists()

def test_atomic_write_json_backup_restore():
    """バックアップ/復旧テスト"""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "test.json"
        original_data = {"original": "data"}

        # 既存ファイルを作成
        atomic_write_json(str(filepath), original_data)

        # ディスク容量不足をシミュレート（実際のテストではモックを使用）
        # ...
```

## ファイル構造

実装後のファイル構造：

```
定型作業支援ツール/
├── utils/
│   ├── __init__.py
│   └── file_io.py          # 新規作成: 原子的書き込み関数
├── config.py               # 更新: _save_*メソッドを原子的書き込みに変更
├── main.py                 # 更新: logging設定を追加（必要に応じて）
└── data/
    ├── tasks.json
    ├── tasks.json.bak      # バックアップファイル（エラー時のみ存在）
    ├── tasks.json.tmp      # 一時ファイル（書き込み中のみ存在）
    ├── logs.json
    ├── settings.json
    └── calendar_overrides.json
```

## 注意事項

1. **一時ファイルとバックアップファイル**:
   - `.tmp` ファイルは正常終了時には自動削除される
   - `.bak` ファイルは書き込み成功時に自動削除される
   - エラー時のみこれらのファイルが残る可能性がある

2. **ログの確認**:
   - I/O操作の失敗時はログに詳細が記録される
   - 問題発生時はログを優先的に確認すること
   - ログレベルを `DEBUG` に設定すると、より詳細な情報が得られる

3. **既存データの互換性**:
   - 既存のJSONファイルはそのまま使用可能
   - ファイル形式や構造は変更しないため、後方互換性は維持される

4. **パフォーマンス**:
   - 原子的書き込みは通常の書き込みより若干オーバーヘッドがあるが、実用的な範囲内
   - バックアップ作成は既存ファイルがある場合のみ実行される

## 実装チェックリスト

- [ ] `utils/file_io.py` を作成し、`atomic_write_json()` 関数を実装
- [ ] `config.py` に `atomic_write_json` のインポートを追加
- [ ] `config.py` の `_save_tasks()` を更新
- [ ] `config.py` の `_save_logs()` を更新
- [ ] `config.py` の `_save_settings()` を更新
- [ ] `config.py` の `_save_calendar_overrides()` を更新
- [ ] `main.py` にlogging設定を追加（必要に応じて）
- [ ] 手動テストを実施して動作確認
- [ ] エラーケースのテストを実施
- [ ] ログ出力を確認

## 参考資料

- Python公式ドキュメント: [os.replace()](https://docs.python.org/ja/3/library/os.html#os.replace)
- Python公式ドキュメント: [jsonモジュール](https://docs.python.org/ja/3/library/json.html)
- Python公式ドキュメント: [loggingモジュール](https://docs.python.org/ja/3/library/logging.html)
