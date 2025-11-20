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
        "warning_minutes": schedule.get("warning_minutes", DEFAULT_WARNING_MINUTES),
        "snooze_minutes": schedule.get("snooze_minutes", DEFAULT_SNOOZE_MINUTES),
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

        return current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
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
        "pre": base_time
        - timedelta(minutes=schedule_config["pre_notification_minutes"]),
        "main": base_time,
        "warning": base_time + timedelta(minutes=schedule_config["warning_minutes"]),
    }
