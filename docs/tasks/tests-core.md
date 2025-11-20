# tests-core: コアテスト・カバレッジタスク仕様

- **目的**: コアロジックの自動テストを整備し、一定以上のコードカバレッジを確保する。
- **関連ID**: `tests-core`

## 背景と問題点

### 現在の実装の問題

現在のプロジェクトには、コアロジックに対する自動テストが存在しない：

1. **テストファイルが存在しない**: `test_*.py` や `tests/` ディレクトリが存在しない
2. **カバレッジが0%**: テストが実行されていないため、コードカバレッジが測定できない
3. **リファクタリングのリスク**: 既存機能を変更する際に、既存機能が壊れていないか確認する手段がない
4. **バグの早期発見が困難**: ロジックのバグが本番環境で発見される可能性がある
5. **CIパイプラインでの品質保証ができない**: 次の `ci-quality` タスクでテストをCIに組み込む予定だが、テストが存在しない

### コアロジックの重要性

以下のモジュールは、アプリケーションの動作に直接影響するクリティカルパスである：

- **`utils/schedule.py`**: スケジュール計算（通知タイミングの計算）
- **`utils/file_io.py`**: 原子的書き込み（データの安全な保存）
- **`config.py`**: 設定管理（タスク・ログ・設定の読み書き）
- **`task_manager.py`**: タスク監視（通知の発火制御）

これらのモジュールにバグがあると、アプリケーション全体が正常に動作しなくなる可能性がある。

## 要件概要

- クリティカルパス（スケジュール計算・通知・永続化など）のテストを優先する
- 目標カバレッジは plan.json の `target_coverage` を参照する
  - 短期目標（2025-11-14まで）: **>= 60%**
  - 長期目標: **>= 80%**
- テストはローカルとCIの両方で安定して動作すること
- テストコードは読みやすく、保守しやすいこと
- 重要な分岐やエラー処理パスをテストでカバーすること

## 実装計画

### アーキテクチャ

```
tests/ (新規作成)
├── conftest.py              # 共通フィクスチャ（一時ディレクトリなど）
├── test_schedule.py         # utils/schedule.py のテスト
├── test_file_io.py          # utils/file_io.py のテスト
├── test_config.py           # config.py のテスト
└── test_task_manager.py     # task_manager.py のテスト

pyproject.toml (更新)
└── [tool.pytest.ini_options]  # pytest設定を追加

requirements.txt (更新)
└── pytest, pytest-cov を追加
```

### テスト対象モジュール（優先順位順）

#### 1. `utils/schedule.py`（最優先）

**理由**: 純粋関数でテストしやすく、重要なロジック

**テスト対象関数**:
- `get_schedule_config()`: スケジュール設定の取得（デフォルト値処理）
- `get_task_base_time()`: タスクの基準時刻計算（エラーハンドリング）
- `calculate_notification_times()`: 通知タイミング計算（メインロジック）

**テストケース**:
- 正常系: 有効な時刻・設定での計算
- エッジケース: 無効な時刻、欠損フィールド、境界値
- デフォルト値: `schedule` フィールドがない場合
- 後方互換性: 既存タスクデータとの互換性

#### 2. `utils/file_io.py`（高優先度）

**理由**: データの安全な保存に関わる重要な機能

**テスト対象関数**:
- `atomic_write_json()`: 原子的書き込み、バックアップ/復旧

**テストケース**:
- 正常系: 新規ファイル・既存ファイルの書き込み
- エラー系: ディスク容量不足、権限エラー、JSONエンコードエラー
- バックアップ/復旧: エラー時のバックアップからの復旧
- 一時ファイルのクリーンアップ: 成功時・失敗時のクリーンアップ

#### 3. `config.py`（高優先度）

**理由**: データ永続化の中核機能

**テスト対象メソッド**:
- `load_tasks()`, `save_tasks()`, `add_task()`, `update_task()`, `delete_task()`
- `load_logs()`, `save_logs()`, `add_log()`, `get_logs_by_date()`
- `load_settings()`, `save_settings()`, `get_exclude_weekends()`
- `load_calendar_overrides()`, `is_date_included()`

**テストケース**:
- CRUD操作: タスク・ログ・設定の追加・更新・削除・読み込み
- ファイル不存在時の初期化: ファイルが存在しない場合の動作
- JSON破損時のエラーハンドリング: 不正なJSONファイルの処理
- 週末除外・カレンダーオーバーライド: 日付判定ロジック

#### 4. `task_manager.py`（中優先度）

**理由**: スレッドとコールバックを含む複雑なロジック

**テスト対象メソッド**:
- `start_monitoring()`, `stop_monitoring()`: 監視の開始・停止
- `_should_trigger_notification()`: 通知判定（±1分の範囲）
- `mark_task_completed()`, `_is_task_completed()`: タスク完了判定
- `clear_notification_history()`: 通知履歴のクリア

**テストケース**:
- 監視の開始・停止: スレッドの起動・停止
- 通知タイミングの判定: 時刻の範囲内判定
- 通知の重複防止: 同じ通知が複数回発火しないこと
- タスク完了判定: サブタスクの完了判定ロジック

### 実装手順

#### ステップ1: テスト環境のセットアップ

**ファイルパス**: `requirements.txt`

**追加内容**:
```txt
pytest>=7.4.0
pytest-cov>=4.1.0
```

**ファイルパス**: `pyproject.toml`

**追加内容**:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--cov=.",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-exclude=ui/*",
    "--cov-exclude=main.py",
    "--cov-exclude=scripts/*",
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
]
```

**ファイルパス**: `tests/conftest.py`（新規作成）

**実装内容**:
```python
"""
テスト共通フィクスチャ
"""
import tempfile
import shutil
from pathlib import Path
import pytest


@pytest.fixture
def temp_data_dir():
    """一時データディレクトリを作成"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_task():
    """サンプルタスクデータ"""
    return {
        "id": "task_001",
        "time": "14:30",
        "task_names": ["日報", "勤怠報告"],
        "enabled": True,
        "created_date": "2025-11-18",
    }


@pytest.fixture
def sample_task_with_schedule():
    """スケジュール設定付きサンプルタスクデータ"""
    return {
        "id": "task_002",
        "time": "15:00",
        "task_names": ["タスク1"],
        "enabled": True,
        "created_date": "2025-11-18",
        "schedule": {
            "pre_notification_minutes": 10,
            "warning_minutes": 15,
            "snooze_minutes": 5,
        },
    }
```

#### ステップ2: `tests/test_schedule.py` の作成

**ファイルパス**: `tests/test_schedule.py`

**実装内容**（主要なテストケース）:

```python
"""
utils/schedule.py のテスト
"""
from datetime import datetime
import pytest
from utils.schedule import (
    get_schedule_config,
    get_task_base_time,
    calculate_notification_times,
    DEFAULT_PRE_NOTIFICATION_MINUTES,
    DEFAULT_WARNING_MINUTES,
)


class TestGetScheduleConfig:
    """get_schedule_config() のテスト"""

    def test_default_values(self, sample_task):
        """デフォルト値のテスト"""
        config = get_schedule_config(sample_task)
        assert config["pre_notification_minutes"] == DEFAULT_PRE_NOTIFICATION_MINUTES
        assert config["warning_minutes"] == DEFAULT_WARNING_MINUTES

    def test_custom_values(self, sample_task_with_schedule):
        """カスタム値のテスト"""
        config = get_schedule_config(sample_task_with_schedule)
        assert config["pre_notification_minutes"] == 10
        assert config["warning_minutes"] == 15

    def test_partial_schedule(self):
        """一部のフィールドのみ設定されている場合"""
        task = {
            "id": "task_003",
            "time": "16:00",
            "schedule": {"pre_notification_minutes": 20},
        }
        config = get_schedule_config(task)
        assert config["pre_notification_minutes"] == 20
        assert config["warning_minutes"] == DEFAULT_WARNING_MINUTES


class TestGetTaskBaseTime:
    """get_task_base_time() のテスト"""

    def test_valid_time(self, sample_task):
        """有効な時刻のテスト"""
        current_time = datetime(2025, 11, 18, 12, 0)
        base_time = get_task_base_time(sample_task, current_time)
        assert base_time == datetime(2025, 11, 18, 14, 30)

    def test_invalid_time_format(self):
        """無効な時刻形式のテスト"""
        task = {"id": "task_004", "time": "invalid"}
        current_time = datetime(2025, 11, 18, 12, 0)
        base_time = get_task_base_time(task, current_time)
        assert base_time is None

    def test_missing_time(self):
        """時刻フィールドがない場合"""
        task = {"id": "task_005"}
        current_time = datetime(2025, 11, 18, 12, 0)
        base_time = get_task_base_time(task, current_time)
        assert base_time is None

    def test_out_of_range_hour(self):
        """時刻が範囲外の場合（時）"""
        task = {"id": "task_006", "time": "25:00"}
        current_time = datetime(2025, 11, 18, 12, 0)
        base_time = get_task_base_time(task, current_time)
        assert base_time is None

    def test_out_of_range_minute(self):
        """時刻が範囲外の場合（分）"""
        task = {"id": "task_007", "time": "12:60"}
        current_time = datetime(2025, 11, 18, 12, 0)
        base_time = get_task_base_time(task, current_time)
        assert base_time is None


class TestCalculateNotificationTimes:
    """calculate_notification_times() のテスト"""

    def test_normal_case(self, sample_task):
        """正常系のテスト"""
        current_time = datetime(2025, 11, 18, 12, 0)
        base_time = datetime(2025, 11, 18, 14, 30)

        times = calculate_notification_times(sample_task, current_time, base_time)

        assert times["pre"] == datetime(2025, 11, 18, 14, 25)  # 5分前
        assert times["main"] == datetime(2025, 11, 18, 14, 30)  # 本通知
        assert times["warning"] == datetime(2025, 11, 18, 14, 35)  # 5分後

    def test_custom_schedule(self, sample_task_with_schedule):
        """カスタムスケジュールのテスト"""
        current_time = datetime(2025, 11, 18, 12, 0)
        base_time = datetime(2025, 11, 18, 15, 0)

        times = calculate_notification_times(
            sample_task_with_schedule, current_time, base_time
        )

        assert times["pre"] == datetime(2025, 11, 18, 14, 50)  # 10分前
        assert times["main"] == datetime(2025, 11, 18, 15, 0)  # 本通知
        assert times["warning"] == datetime(2025, 11, 18, 15, 15)  # 15分後

    def test_invalid_base_time(self, sample_task):
        """無効な基準時刻の場合"""
        current_time = datetime(2025, 11, 18, 12, 0)

        times = calculate_notification_times(sample_task, current_time, None)

        assert times["pre"] is None
        assert times["main"] is None
        assert times["warning"] is None

    def test_auto_calculate_base_time(self, sample_task):
        """base_timeがNoneの場合の自動計算"""
        current_time = datetime(2025, 11, 18, 12, 0)

        times = calculate_notification_times(sample_task, current_time)

        assert times["pre"] == datetime(2025, 11, 18, 14, 25)
        assert times["main"] == datetime(2025, 11, 18, 14, 30)
        assert times["warning"] == datetime(2025, 11, 18, 14, 35)
```

#### ステップ3: `tests/test_file_io.py` の作成

**ファイルパス**: `tests/test_file_io.py`

**実装内容**（主要なテストケース）:

```python
"""
utils/file_io.py のテスト
"""
import json
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, mock_open
from utils.file_io import atomic_write_json


class TestAtomicWriteJson:
    """atomic_write_json() のテスト"""

    def test_new_file(self, temp_data_dir):
        """新規ファイルの書き込み"""
        filepath = Path(temp_data_dir) / "test.json"
        data = {"key": "value"}

        atomic_write_json(str(filepath), data)

        assert filepath.exists()
        with open(filepath, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded == data
        assert not filepath.with_suffix(".tmp").exists()
        assert not filepath.with_suffix(".bak").exists()

    def test_existing_file(self, temp_data_dir):
        """既存ファイルの上書き"""
        filepath = Path(temp_data_dir) / "test.json"
        original_data = {"original": "data"}
        new_data = {"new": "data"}

        # 既存ファイルを作成
        atomic_write_json(str(filepath), original_data)

        # 上書き
        atomic_write_json(str(filepath), new_data)

        with open(filepath, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded == new_data

    def test_list_data(self, temp_data_dir):
        """リストデータの書き込み"""
        filepath = Path(temp_data_dir) / "test.json"
        data = [{"item": 1}, {"item": 2}]

        atomic_write_json(str(filepath), data)

        with open(filepath, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded == data

    def test_json_encode_error(self, temp_data_dir):
        """JSONエンコードエラーのテスト"""
        filepath = Path(temp_data_dir) / "test.json"
        # 循環参照など、JSONエンコードできないデータ
        data = {}
        data["self"] = data  # 循環参照

        with pytest.raises((TypeError, ValueError)):
            atomic_write_json(str(filepath), data)

    @patch("builtins.open", side_effect=OSError("Disk full"))
    def test_disk_full_error(self, mock_file, temp_data_dir):
        """ディスク容量不足エラーのテスト"""
        filepath = Path(temp_data_dir) / "test.json"
        data = {"key": "value"}

        with pytest.raises(OSError):
            atomic_write_json(str(filepath), data)
```

#### ステップ4: `tests/test_config.py` の作成

**ファイルパス**: `tests/test_config.py`

**実装内容**（主要なテストケース）:

```python
"""
config.py のテスト
"""
import json
import pytest
from config import Config


class TestConfigTasks:
    """タスク関連のテスト"""

    def test_add_task(self, temp_data_dir, monkeypatch):
        """タスクの追加"""
        monkeypatch.setattr(Config, "__init__", lambda self: None)
        config = Config()
        config.data_dir = temp_data_dir
        config.tasks_file = str(Path(temp_data_dir) / "tasks.json")
        config.logs_file = str(Path(temp_data_dir) / "logs.json")
        config.settings_file = str(Path(temp_data_dir) / "settings.json")
        config.calendar_overrides_file = str(
            Path(temp_data_dir) / "calendar_overrides.json"
        )
        config._init_files()

        task_id = config.add_task("14:30", ["日報", "勤怠報告"])

        assert task_id.startswith("task_")
        tasks = config.load_tasks()
        assert len(tasks) == 1
        assert tasks[0]["time"] == "14:30"
        assert tasks[0]["task_names"] == ["日報", "勤怠報告"]

    def test_update_task(self, temp_data_dir, monkeypatch):
        """タスクの更新"""
        # セットアップ（上記と同様）
        # ...

    def test_delete_task(self, temp_data_dir, monkeypatch):
        """タスクの削除"""
        # セットアップ（上記と同様）
        # ...

    def test_load_tasks_file_not_found(self, temp_data_dir, monkeypatch):
        """ファイルが存在しない場合"""
        # セットアップ（上記と同様）
        # ...


class TestConfigLogs:
    """ログ関連のテスト"""

    def test_add_log(self, temp_data_dir, monkeypatch):
        """ログの追加"""
        # セットアップ（上記と同様）
        # ...

    def test_get_logs_by_date(self, temp_data_dir, monkeypatch):
        """日付でログを取得"""
        # セットアップ（上記と同様）
        # ...


class TestConfigSettings:
    """設定関連のテスト"""

    def test_exclude_weekends(self, temp_data_dir, monkeypatch):
        """週末除外設定"""
        # セットアップ（上記と同様）
        # ...


class TestConfigCalendarOverrides:
    """カレンダーオーバーライド関連のテスト"""

    def test_is_date_included(self, temp_data_dir, monkeypatch):
        """日付の対象判定"""
        # セットアップ（上記と同様）
        # ...
```

#### ステップ5: `tests/test_task_manager.py` の作成

**ファイルパス**: `tests/test_task_manager.py`

**実装内容**（主要なテストケース）:

```python
"""
task_manager.py のテスト
"""
from datetime import datetime
import pytest
from unittest.mock import Mock, patch
from task_manager import TaskManager


class TestTaskManagerNotification:
    """通知関連のテスト"""

    def test_should_trigger_notification(self):
        """通知判定のテスト"""
        manager = TaskManager()
        current_time = datetime(2025, 11, 18, 14, 30, 0)
        target_time = datetime(2025, 11, 18, 14, 30, 30)  # 30秒後
        task_id = "task_001"
        notification_type = "main"

        # ±1分以内なのでTrue
        result = manager._should_trigger_notification(
            current_time, target_time, task_id, notification_type
        )
        assert result is True

    def test_should_not_trigger_duplicate(self):
        """重複通知の防止"""
        manager = TaskManager()
        current_time = datetime(2025, 11, 18, 14, 30, 0)
        target_time = datetime(2025, 11, 18, 14, 30, 0)
        task_id = "task_001"
        notification_type = "main"

        # 1回目はTrue
        result1 = manager._should_trigger_notification(
            current_time, target_time, task_id, notification_type
        )
        assert result1 is True

        # 2回目はFalse（重複）
        result2 = manager._should_trigger_notification(
            current_time, target_time, task_id, notification_type
        )
        assert result2 is False

    def test_is_task_completed(self, temp_data_dir, monkeypatch):
        """タスク完了判定"""
        # セットアップ（上記と同様）
        # ...
```

## テスト設計の原則

### 1. 独立性

各テストは独立して実行可能で、他のテストに依存しない。

- 各テストは独自のデータを使用
- テスト間で状態を共有しない
- テストの実行順序に依存しない

### 2. 再現性

同じ入力に対して常に同じ結果を返す。

- ランダムな値を使用しない（必要に応じて固定値を使用）
- 時刻依存のテストは固定時刻を使用
- ファイルI/Oは一時ディレクトリを使用

### 3. 隔離

テストは実際のファイルシステムや外部リソースに影響を与えない。

- ファイルI/Oは一時ディレクトリを使用
- モックを使用して外部依存を排除
- テスト後にクリーンアップを行う

### 4. カバレッジ

重要な分岐やエラー処理パスをテストでカバーする。

- 正常系だけでなく、エッジケースもテスト
- エラーハンドリングのパスもテスト
- 境界値テストを実施

### 5. 可読性

テストコードは読みやすく、保守しやすい。

- テスト名は何をテストしているか明確に
- アサーションは明確で理解しやすい
- コメントは必要最小限に

## カバレッジ測定

### カバレッジの目標

- **短期目標（2025-11-14まで）**: >= 60%
- **長期目標**: >= 80%

### カバレッジの測定方法

```bash
# カバレッジを測定
pytest --cov=. --cov-report=term-missing

# HTMLレポートを生成
pytest --cov=. --cov-report=html
# htmlcov/index.html を開く
```

### カバレッジの対象外

以下のモジュールはカバレッジの対象外とする：

- `ui/`: UIモジュール（tkinter依存、テストが困難）
- `main.py`: エントリーポイント（統合テストでカバー）
- `scripts/`: スクリプト（開発用ツール）

## エラーハンドリング

### テスト実行時のエラー

テスト実行時にエラーが発生した場合：

1. **テストが失敗する**: アサーションが失敗した場合、テストは失敗として記録される
2. **エラーメッセージを確認**: 失敗したテストのエラーメッセージを確認し、原因を特定する
3. **ログを確認**: 必要に応じてログを確認し、詳細な情報を取得する

### カバレッジが目標に達しない場合

カバレッジが目標に達しない場合：

1. **カバレッジレポートを確認**: どのモジュール・関数がカバーされていないか確認
2. **優先度の高いモジュールから追加**: クリティカルパスから優先的にテストを追加
3. **エッジケースを追加**: 境界値やエラーケースのテストを追加

## テスト方法

### ローカルでの実行

```bash
# すべてのテストを実行
pytest

# 特定のテストファイルを実行
pytest tests/test_schedule.py

# 特定のテストクラスを実行
pytest tests/test_schedule.py::TestGetScheduleConfig

# カバレッジ付きで実行
pytest --cov=. --cov-report=term-missing

# 詳細な出力で実行
pytest -v

# 失敗したテストのみ再実行
pytest --lf
```

### CIでの実行（将来）

`ci-quality` タスクで、以下のようなCIパイプラインが構築される予定：

```yaml
# .github/workflows/ci.yml（将来作成される）
name: CI Quality Gate

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - run: pip install -r requirements.txt
      - run: pytest --cov=. --cov-report=xml
      - run: # カバレッジが60%以上かチェック
```

## ファイル構造

実装後のファイル構造：

```
TaskReminder/
├── tests/                    # 新規作成: テストディレクトリ
│   ├── __init__.py
│   ├── conftest.py           # 共通フィクスチャ
│   ├── test_schedule.py      # utils/schedule.py のテスト
│   ├── test_file_io.py       # utils/file_io.py のテスト
│   ├── test_config.py        # config.py のテスト
│   └── test_task_manager.py  # task_manager.py のテスト
├── pyproject.toml            # 更新: pytest設定を追加
├── requirements.txt          # 更新: pytest, pytest-cov を追加
├── utils/
│   ├── schedule.py          # テスト対象
│   └── file_io.py           # テスト対象
├── config.py                # テスト対象
└── task_manager.py          # テスト対象
```

## 注意事項

1. **UIモジュールの除外**:
   - `ui/` モジュールはテスト対象外（tkinter依存、型チェックで無視済み）
   - UIのテストは統合テストやE2Eテストでカバーする（将来のタスク）

2. **スレッド関連のテスト**:
   - `task_manager.py` のスレッド関連のテストは時間依存のため、モックや固定時刻を使用
   - スレッドの起動・停止は慎重にテストする

3. **ファイルI/Oのテスト**:
   - 実際のファイルシステムを使用せず、一時ディレクトリを使用
   - テスト後にクリーンアップを行う

4. **既存の動作を壊さない**:
   - テストを追加する際は、既存の動作を壊さないように注意
   - リファクタリング時は、テストが既存の動作を保証することを確認

5. **テストの実行時間**:
   - テストの実行時間が長くなりすぎないように注意
   - 必要に応じて `@pytest.mark.slow` マーカーを使用

## 実装チェックリスト

- [ ] `requirements.txt` に `pytest`, `pytest-cov` を追加
- [ ] `pyproject.toml` に pytest設定を追加
- [ ] `tests/` ディレクトリを作成
- [ ] `tests/conftest.py` を作成（共通フィクスチャ）
- [ ] `tests/test_schedule.py` を作成（utils/schedule.py のテスト）
- [ ] `tests/test_file_io.py` を作成（utils/file_io.py のテスト）
- [ ] `tests/test_config.py` を作成（config.py のテスト）
- [ ] `tests/test_task_manager.py` を作成（task_manager.py のテスト）
- [ ] すべてのテストがローカルで通過することを確認
- [ ] カバレッジが60%以上であることを確認
- [ ] テストコードが読みやすく、保守しやすいことを確認

## 参考資料

- pytest公式ドキュメント: https://docs.pytest.org/
- pytest-cov公式ドキュメント: https://pytest-cov.readthedocs.io/
- Python公式ドキュメント: [unittest.mock](https://docs.python.org/ja/3/library/unittest.mock.html)
- テスト駆動開発（TDD）: https://ja.wikipedia.org/wiki/テスト駆動開発
