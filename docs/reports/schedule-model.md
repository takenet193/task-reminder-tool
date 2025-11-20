# レポート: スケジュール拡張 (`schedule-model`)

## 実施概要

- タスクとスケジュールのモデルを拡張し、柔軟な通知タイミングに対応できるようにした。
- `utils/schedule.py` にスケジュール計算の純粋関数を実装した。
- `task_manager.py` の監視ループを更新し、ハードコードされた通知タイミング計算を純粋関数に置き換えた。
- 既存のタスクデータとの後方互換性を保ちながら、将来的な拡張（スヌーズ、繰り返しタスクなど）に対応できる基盤を構築した。

## 実装内容

### 1. スケジュール計算ユーティリティの実装（`utils/schedule.py`）

新規ファイル `utils/schedule.py` を作成し、以下の3つの純粋関数を実装した：

#### `get_schedule_config(task: dict[str, Any]) -> dict[str, int]`
- タスクからスケジュール設定を取得（デフォルト値付き）
- `schedule` フィールドがない場合はデフォルト値（5分前、5分後）を使用
- 後方互換性を保つため、既存タスクデータでも動作

#### `get_task_base_time(task: dict[str, Any], current_time: datetime) -> datetime | None`
- タスクの基準時刻（今日のタスク時刻）を計算
- 無効な時刻文字列の場合は `None` を返す
- エラーハンドリングを適切に実装

#### `calculate_notification_times(task, current_time, base_time) -> dict[str, datetime | None]`
- タスクの通知タイミングを計算するメイン関数
- 予告通知、本通知、警告通知の時刻を辞書で返す
- すべて純粋関数として実装（副作用なし）

**特徴**:
- すべての関数が純粋関数（副作用なし、同じ入力に対して同じ出力）
- デフォルト値の処理を一箇所に集約
- エラーハンドリングを適切に行う（無効な時刻は `None` を返す）
- 型ヒントを適切に使用

### 2. `task_manager.py` の更新

#### インポートの追加
```python
from utils.schedule import calculate_notification_times, get_task_base_time
```

#### `_monitor_tasks()` メソッドの更新
- ハードコードされた `timedelta(minutes=5)` を削除
- `_parse_time()` と `today_task_time` の計算を `get_task_base_time()` に置き換え
- `calculate_notification_times()` を使用して通知時刻を取得
- 通知トリガーの判定を `notification_times` 辞書から取得するように変更

**変更前**:
```python
pre_notification_time = today_task_time - timedelta(minutes=5)
warning_time = today_task_time + timedelta(minutes=5)
```

**変更後**:
```python
notification_times = calculate_notification_times(task, current_time, base_time)
# notification_times["pre"], notification_times["main"], notification_times["warning"] を使用
```

### 3. 後方互換性の確保

- `schedule` フィールドがない既存タスクは、デフォルト値（5分前、5分後）で動作
- `schedule` フィールドがあっても、一部のフィールドが欠けている場合はデフォルト値を使用
- 無効な値（負の数、文字列など）が設定されている場合もデフォルト値を使用
- 既存の `_parse_time()` メソッドは後方互換性のため残す（使用されなくなるが削除しない）

## 実装の詳細

### データモデル設計

既存のタスクデータに `schedule` フィールドを追加可能（オプショナル）：

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

- `schedule` フィールドが存在しない既存タスクは、デフォルト値で動作
- 将来的な拡張（`repeat`, `paused_until` など）のために、辞書構造を採用

### 純粋関数の設計

すべての関数が純粋関数として実装されている：

- **同じ入力に対して常に同じ出力を返す**
- **副作用がない**（外部状態を変更しない、ファイルI/Oやログ出力をしない）

**メリット**:
- テストしやすい（モック不要で直接テスト可能）
- 再利用しやすい（他のモジュールからも使用可能）
- 理解しやすい（入力と出力が明確）
- 並行処理に安全（副作用がないため、並行実行しても問題ない）

### エラーハンドリング

- 無効な時刻文字列: `get_task_base_time()` が `None` を返す
- 無効なスケジュール設定: `get_schedule_config()` がデフォルト値を使用
- `schedule` フィールドが存在しない: デフォルト値を使用
- `base_time` が `None`: `calculate_notification_times()` がすべて `None` を返す

## 動作確認

### 実装後の動作確認

- アプリケーションが正常に起動することを確認
- 既存タスクがデフォルト値（5分前、5分後）で正常に動作することを確認
- 通知が予定通りに発火することを確認
- エラーが発生しないことを確認

### 関数の動作確認

```python
from utils.schedule import calculate_notification_times, get_task_base_time, get_schedule_config
from datetime import datetime

task = {'id': 'test', 'time': '14:30'}
# get_schedule_config: {'pre_notification_minutes': 5, 'warning_minutes': 5, 'snooze_minutes': 5}
# get_task_base_time: 2025-11-19 14:30:00
# calculate_notification_times: 
#   {'pre': datetime(2025, 11, 19, 14, 25), 
#    'main': datetime(2025, 11, 19, 14, 30), 
#    'warning': datetime(2025, 11, 19, 14, 35)}
```

## 注意事項

- 既存のタスクデータは `schedule` フィールドがなくても動作する（デフォルト値を使用）
- データ移行は不要（既存タスクに `schedule` フィールドを追加する必要はない）
- `_parse_time()` メソッドは後方互換性のため残している（使用されなくなるが削除しない）
- UIから `schedule` フィールドを設定する機能は未実装（将来的に `schedule-ui` タスクで実装予定）
- 手動で `tasks.json` を編集すれば、カスタムスケジュール設定を追加可能

## 将来の拡張

今回の実装により、以下のような将来の拡張が容易になった：

- **スヌーズ機能**: `schedule.snooze_minutes` を使用
- **繰り返しタスク**: `schedule.repeat` フィールドを追加
- **一時停止機能**: `schedule.paused_until` フィールドを追加
- **カスタム通知タイミング**: UIから `schedule` フィールドを設定可能に（`schedule-ui` タスク）

## メモ

- 純粋関数として実装されているため、テストが容易
- 計算ロジックが一箇所に集約されているため、変更が容易
- 既存のタスクデータとの互換性を保ちながら、柔軟な拡張が可能
- 関心の分離とDRY原則を実践した設計

