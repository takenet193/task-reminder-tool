# schedule-model: スケジュール拡張タスク仕様

- **目的**: タスクとスケジュールのモデルを拡張し、柔軟な通知・スヌーズや将来の拡張（繰り返し予定など）に対応できるようにする。
- **関連ID**: `schedule-model`

## 背景と問題点

### 現在の実装の問題

現在の `task_manager.py` では、通知タイミングの計算が監視ループ内に直接ハードコードされている：

```82:96:task_manager.py
                    # 予告通知(5分前)
                    pre_notification_time = today_task_time - timedelta(minutes=5)
                    if self._should_trigger_notification(
                        current_time, pre_notification_time, task["id"], "pre"
                    ):
                        self._trigger_pre_notification(task)

                    # 本通知(設定時刻)
                    if self._should_trigger_notification(
                        current_time, today_task_time, task["id"], "main"
                    ):
                        self._trigger_main_notification(task)

                    # 警告通知(5分後、未完了の場合)
                    warning_time = today_task_time + timedelta(minutes=5)
```

この方法では以下の問題が発生する：

1. **柔軟性の欠如**: 通知タイミング（5分前、5分後）がハードコードされており、カスタマイズできない
2. **テストの困難さ**: 計算ロジックが監視ループと密結合しており、単体テストが難しい
3. **再利用性の低さ**: 他のモジュール（UI表示など）で通知時刻を計算できない
4. **拡張性の欠如**: 将来的な機能（スヌーズ、繰り返しタスク、一時停止など）を追加しにくい
5. **モデルとロジックの分離不足**: タスクデータにスケジュール情報が含まれておらず、計算ロジックが分散している

## 要件概要

- 既存のタスクデータ構造に、スケジュール関連のフィールドを追加できるようにする（後方互換性を保つ）
- 通知タイミング（事前通知、本通知、警告）の計算がモデルから一貫して行えること
- スケジュール計算ロジックを純粋関数として分離し、テストしやすくする
- 将来的に繰り返しタスクや一時停止などを追加できる余地を残す
- 既存のタスクデータはそのまま動作すること（デフォルト値で動作）

## データモデル設計

### タスクデータ構造の拡張

既存のタスクデータに `schedule` フィールドを追加する（オプショナル）。

**既存のタスク構造**:
```json
{
  "id": "task_001",
  "time": "14:30",
  "task_names": ["日報", "勤怠報告"],
  "enabled": true,
  "created_date": "2025-11-18"
}
```

**拡張後のタスク構造**:
```json
{
  "id": "task_001",
  "time": "14:30",
  "task_names": ["日報", "勤怠報告"],
  "enabled": true,
  "created_date": "2025-11-18",
  "schedule": {
    "pre_notification_minutes": 5,
    "warning_minutes": 5,
    "snooze_minutes": 5
  }
}
```

### スケジュールフィールドの詳細

- **`schedule`** (オプショナル): スケジュール設定の辞書
  - **`pre_notification_minutes`** (int, デフォルト: 5): 予告通知を発火する分数（タスク時刻の何分前か）
  - **`warning_minutes`** (int, デフォルト: 5): 警告通知を発火する分数（タスク時刻の何分後か）
  - **`snooze_minutes`** (int, デフォルト: 5): スヌーズ機能で使用する分数（将来の拡張用）

**注意**:
- `schedule` フィールドが存在しない既存タスクは、デフォルト値（5分前、5分後）で動作する
- 将来的な拡張（`repeat`, `paused_until` など）のために、辞書構造を採用

## 実装計画

### アーキテクチャ

```
utils/schedule.py (新規作成)
  └─ calculate_notification_times()  # 純粋関数: 通知時刻を計算
  └─ get_task_base_time()            # 純粋関数: タスクの基準時刻を計算
  └─ get_schedule_config()           # 純粋関数: スケジュール設定を取得（デフォルト値含む）

task_manager.py (更新)
  └─ _monitor_tasks()
      └─ calculate_notification_times() を使用
  └─ _parse_time()                    # 既存メソッド（維持）
```

### 実装手順

#### ステップ1: `utils/schedule.py` の作成

スケジュール計算の純粋関数を実装する。

**ファイルパス**: `utils/schedule.py`

**実装内容**:

```python
"""
スケジュール計算ユーティリティ
通知タイミングの計算を純粋関数として提供
"""

from datetime import datetime, timedelta
from typing import Any

# デフォルト値
DEFAULT_PRE_NOTIFICATION_MINUTES = 5
DEFAULT_WARNING_MINUTES = 5
DEFAULT_SNOOZE_MINUTES = 5


def get_schedule_config(task: dict[str, Any]) -> dict[str, int]:
    """
    タスクからスケジュール設定を取得（デフォルト値付き）

    Args:
        task: タスクデータ

    Returns:
        スケジュール設定の辞書
        {
            "pre_notification_minutes": int,
            "warning_minutes": int,
            "snooze_minutes": int
        }
    """
    schedule = task.get("schedule", {})
    return {
        "pre_notification_minutes": schedule.get(
            "pre_notification_minutes", DEFAULT_PRE_NOTIFICATION_MINUTES
        ),
        "warning_minutes": schedule.get(
            "warning_minutes", DEFAULT_WARNING_MINUTES
        ),
        "snooze_minutes": schedule.get(
            "snooze_minutes", DEFAULT_SNOOZE_MINUTES
        ),
    }


def get_task_base_time(task: dict[str, Any], current_time: datetime) -> datetime | None:
    """
    タスクの基準時刻（今日のタスク時刻）を計算する

    Args:
        task: タスクデータ
        current_time: 現在時刻

    Returns:
        今日のタスク時刻（datetime）。時刻が無効な場合はNone
    """
    time_str = task.get("time")
    if not time_str:
        return None

    try:
        hour, minute = map(int, time_str.split(":"))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            return None

        return current_time.replace(
            hour=hour, minute=minute, second=0, microsecond=0
        )
    except (ValueError, AttributeError):
        return None


def calculate_notification_times(
    task: dict[str, Any],
    current_time: datetime,
    base_time: datetime | None = None,
) -> dict[str, datetime | None]:
    """
    タスクの通知タイミングを計算する（純粋関数）

    Args:
        task: タスクデータ
        current_time: 現在時刻
        base_time: タスクの基準時刻（Noneの場合は自動計算）

    Returns:
        通知タイプと時刻の辞書
        {
            "pre": datetime | None,      # 予告通知時刻
            "main": datetime | None,    # 本通知時刻
            "warning": datetime | None  # 警告通知時刻
        }
    """
    # 基準時刻を取得
    if base_time is None:
        base_time = get_task_base_time(task, current_time)

    if base_time is None:
        return {"pre": None, "main": None, "warning": None}

    # スケジュール設定を取得
    schedule_config = get_schedule_config(task)

    return {
        "pre": base_time - timedelta(
            minutes=schedule_config["pre_notification_minutes"]
        ),
        "main": base_time,
        "warning": base_time + timedelta(
            minutes=schedule_config["warning_minutes"]
        ),
    }
```

**特徴**:

- すべての関数が純粋関数（副作用なし、同じ入力に対して同じ出力）
- デフォルト値の処理を一箇所に集約
- エラーハンドリングを適切に行う（無効な時刻はNoneを返す）
- 型ヒントを適切に使用

#### ステップ2: `task_manager.py` の更新

監視ループで純粋関数を使用するように変更する。

**ファイルパス**: `task_manager.py`

**変更箇所**:

1. **インポートの追加**:
```python
from utils.schedule import calculate_notification_times, get_task_base_time
```

2. **`_monitor_tasks()` メソッドの更新**:

```python
def _monitor_tasks(self) -> None:
    """タスク監視のメインループ"""
    while self.running:
        try:
            current_time = datetime.now()
            tasks = self.config.load_tasks()

            for task in tasks:
                if not task.get("enabled", True):
                    continue

                # 純粋関数で通知時刻を計算
                base_time = get_task_base_time(task, current_time)
                if base_time is None:
                    continue

                notification_times = calculate_notification_times(
                    task, current_time, base_time
                )

                # 予告通知
                if self._should_trigger_notification(
                    current_time,
                    notification_times["pre"],
                    task["id"],
                    "pre",
                ):
                    self._trigger_pre_notification(task)

                # 本通知
                if self._should_trigger_notification(
                    current_time,
                    notification_times["main"],
                    task["id"],
                    "main",
                ):
                    self._trigger_main_notification(task)

                # 警告通知（未完了の場合のみ）
                if self._should_trigger_notification(
                    current_time,
                    notification_times["warning"],
                    task["id"],
                    "warning",
                ):
                    if not self._is_task_completed(
                        task["id"], current_time.strftime("%Y-%m-%d")
                    ):
                        self._trigger_warning_notification(task)

            time.sleep(10)  # 10秒間隔でチェック

        except Exception as e:
            logger.error(f"タスク監視中にエラーが発生しました: {e}", exc_info=True)
            time.sleep(10)
```

**変更内容**:

- ハードコードされた `timedelta(minutes=5)` を削除
- `calculate_notification_times()` を使用して通知時刻を取得
- `_parse_time()` メソッドは `get_task_base_time()` に置き換え可能だが、後方互換性のため残すことも可能

#### ステップ3: 後方互換性の確認

既存のタスクデータがそのまま動作することを確認する。

**確認事項**:

- `schedule` フィールドがない既存タスクは、デフォルト値（5分前、5分後）で動作する
- `schedule` フィールドがあっても、一部のフィールドが欠けている場合はデフォルト値を使用する
- 無効な値（負の数、文字列など）が設定されている場合もデフォルト値を使用する

## 純粋関数の設計

### 純粋関数とは

純粋関数（Pure Function）は以下の特徴を持つ：

1. **同じ入力に対して常に同じ出力を返す**
2. **副作用がない**（外部状態を変更しない、ファイルI/Oやログ出力をしない）

### メリット

- **テストしやすい**: モック不要で直接テスト可能
- **再利用しやすい**: 他のモジュール（UI、ログ表示など）からも使用可能
- **理解しやすい**: 入力と出力が明確で、ロジックが追いやすい
- **並行処理に安全**: 副作用がないため、並行実行しても問題ない

### 実装例

```python
# 純粋関数の例
def calculate_notification_times(task, current_time, base_time):
    # 入力: task, current_time, base_time
    # 出力: 通知時刻の辞書
    # 副作用: なし（ファイル読み込み、状態変更など一切なし）
    ...
```

## エラーハンドリング

### エラーケースと対応

1. **無効な時刻文字列**
   - `time` フィールドが "HH:MM" 形式でない場合
   - `get_task_base_time()` が `None` を返す
   - 監視ループで `continue` してスキップ

2. **無効なスケジュール設定**
   - `pre_notification_minutes` が負の数や文字列の場合
   - `get_schedule_config()` がデフォルト値を使用

3. **`schedule` フィールドが存在しない**
   - 既存タスクとの互換性のため、デフォルト値を使用

4. **`base_time` が None**
   - `calculate_notification_times()` がすべて `None` を返す
   - 監視ループで通知をスキップ

## テスト方法

### 手動テスト

1. **正常系テスト**:
   ```python
   # タスクを追加して監視
   config.add_task("14:30", ["日報"])
   # 13:25に予告通知、14:30に本通知、14:35に警告通知が発火することを確認
   ```

2. **カスタムスケジュールテスト**:
   ```python
   # カスタムスケジュールでタスクを追加
   task = {
       "id": "task_001",
       "time": "14:30",
       "task_names": ["日報"],
       "schedule": {
           "pre_notification_minutes": 10,
           "warning_minutes": 15
       }
   }
   # 14:20に予告通知、14:30に本通知、14:45に警告通知が発火することを確認
   ```

3. **既存タスクの互換性テスト**:
   ```python
   # scheduleフィールドがない既存タスクが正常に動作することを確認
   # デフォルト値（5分前、5分後）で動作する
   ```

### 自動テスト（将来実装）

```python
from datetime import datetime
from utils.schedule import (
    calculate_notification_times,
    get_task_base_time,
    get_schedule_config,
)

def test_get_schedule_config_default():
    """デフォルト値のテスト"""
    task = {"id": "task_001", "time": "14:30"}
    config = get_schedule_config(task)
    assert config["pre_notification_minutes"] == 5
    assert config["warning_minutes"] == 5

def test_get_schedule_config_custom():
    """カスタム値のテスト"""
    task = {
        "id": "task_001",
        "time": "14:30",
        "schedule": {"pre_notification_minutes": 10},
    }
    config = get_schedule_config(task)
    assert config["pre_notification_minutes"] == 10
    assert config["warning_minutes"] == 5  # デフォルト値

def test_get_task_base_time():
    """基準時刻計算のテスト"""
    task = {"id": "task_001", "time": "14:30"}
    current_time = datetime(2025, 11, 18, 12, 0)
    base_time = get_task_base_time(task, current_time)
    assert base_time == datetime(2025, 11, 18, 14, 30)

def test_calculate_notification_times():
    """通知時刻計算のテスト"""
    task = {
        "id": "task_001",
        "time": "14:30",
        "schedule": {"pre_notification_minutes": 10},
    }
    current_time = datetime(2025, 11, 18, 12, 0)
    base_time = datetime(2025, 11, 18, 14, 30)

    times = calculate_notification_times(task, current_time, base_time)
    assert times["pre"] == datetime(2025, 11, 18, 14, 20)  # 10分前
    assert times["main"] == datetime(2025, 11, 18, 14, 30)  # 本通知
    assert times["warning"] == datetime(2025, 11, 18, 14, 35)  # 5分後（デフォルト）
```

## ファイル構造

実装後のファイル構造：

```
TaskReminder/
├── utils/
│   ├── __init__.py
│   ├── file_io.py          # 既存: 原子的書き込み関数
│   └── schedule.py         # 新規作成: スケジュール計算関数
├── task_manager.py         # 更新: 純粋関数を使用
├── config.py               # 変更なし（タスクデータ構造は自然に拡張）
└── data/
    └── tasks.json          # 既存タスクはそのまま動作、新規タスクはscheduleフィールドを追加可能
```

## 注意事項

1. **後方互換性**:
   - 既存のタスクデータは `schedule` フィールドがなくても動作する
   - デフォルト値（5分前、5分後）を使用する

2. **データ移行**:
   - 既存タスクに `schedule` フィールドを追加する必要はない
   - 必要に応じて、将来的にデータ移行スクリプトを作成可能

3. **将来の拡張**:
   - `schedule` 辞書に新しいフィールド（`repeat`, `paused_until` など）を追加可能
   - 純粋関数を拡張して、新しい機能に対応

4. **パフォーマンス**:
   - 純粋関数は副作用がないため、キャッシュや最適化が容易
   - 現在の実装では、毎回計算するが、必要に応じて最適化可能

5. **テストの重要性**:
   - 純粋関数はテストしやすいため、十分なテストを追加する
   - エッジケース（無効な時刻、負の数など）もテストする

## 将来の拡張案

### スヌーズ機能

```python
# scheduleフィールドに追加
"schedule": {
    "snooze_minutes": 5,  # スヌーズ時の再通知分数
    "max_snooze_count": 3  # 最大スヌーズ回数
}
```

### 繰り返しタスク

```python
# scheduleフィールドに追加
"schedule": {
    "repeat": {
        "type": "daily",  # daily, weekly, monthly
        "days": [0, 1, 2, 3, 4]  # 月曜日〜金曜日（0=月曜日）
    }
}
```

### 一時停止機能

```python
# scheduleフィールドに追加
"schedule": {
    "paused_until": "2025-12-01"  # この日まで一時停止
}
```

## 実装チェックリスト

- [ ] `utils/schedule.py` を作成し、純粋関数を実装
- [ ] `get_schedule_config()` 関数を実装（デフォルト値処理）
- [ ] `get_task_base_time()` 関数を実装（エラーハンドリング含む）
- [ ] `calculate_notification_times()` 関数を実装
- [ ] `task_manager.py` にインポートを追加
- [ ] `task_manager.py` の `_monitor_tasks()` を更新
- [ ] 既存タスクの後方互換性を確認
- [ ] カスタムスケジュールの動作確認
- [ ] エラーハンドリングのテスト
- [ ] ログ出力を確認（必要に応じて）

## 参考資料

- Python公式ドキュメント: [datetimeモジュール](https://docs.python.org/ja/3/library/datetime.html)
- Python公式ドキュメント: [typingモジュール](https://docs.python.org/ja/3/library/typing.html)
- 関数型プログラミング: [純粋関数の概念](https://en.wikipedia.org/wiki/Pure_function)
