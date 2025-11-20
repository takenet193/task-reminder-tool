"""
utils/schedule.py のテスト
"""

from datetime import datetime

from utils.schedule import (
    DEFAULT_PRE_NOTIFICATION_MINUTES,
    DEFAULT_WARNING_MINUTES,
    calculate_notification_times,
    get_schedule_config,
    get_task_base_time,
)


class TestGetScheduleConfig:
    """get_schedule_config() のテスト"""

    def test_default_values(self, sample_task):
        """デフォルト値のテスト"""
        config = get_schedule_config(sample_task)
        assert config["pre_notification_minutes"] == DEFAULT_PRE_NOTIFICATION_MINUTES
        assert config["warning_minutes"] == DEFAULT_WARNING_MINUTES
        assert config["snooze_minutes"] == 5

    def test_custom_values(self, sample_task_with_schedule):
        """カスタム値のテスト"""
        config = get_schedule_config(sample_task_with_schedule)
        assert config["pre_notification_minutes"] == 10
        assert config["warning_minutes"] == 15
        assert config["snooze_minutes"] == 5

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
        assert config["snooze_minutes"] == 5

    def test_empty_schedule(self):
        """空のscheduleフィールドの場合"""
        task = {
            "id": "task_004",
            "time": "17:00",
            "schedule": {},
        }
        config = get_schedule_config(task)
        assert config["pre_notification_minutes"] == DEFAULT_PRE_NOTIFICATION_MINUTES
        assert config["warning_minutes"] == DEFAULT_WARNING_MINUTES


class TestGetTaskBaseTime:
    """get_task_base_time() のテスト"""

    def test_valid_time(self, sample_task):
        """有効な時刻のテスト"""
        current_time = datetime(2025, 11, 18, 12, 0)
        base_time = get_task_base_time(sample_task, current_time)
        assert base_time == datetime(2025, 11, 18, 14, 30)
        assert base_time.second == 0
        assert base_time.microsecond == 0

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

    def test_negative_hour(self):
        """負の時のテスト"""
        task = {"id": "task_008", "time": "-1:00"}
        current_time = datetime(2025, 11, 18, 12, 0)
        base_time = get_task_base_time(task, current_time)
        assert base_time is None

    def test_boundary_values(self):
        """境界値のテスト"""
        current_time = datetime(2025, 11, 18, 12, 0)

        # 00:00
        task1 = {"id": "task_009", "time": "00:00"}
        base_time1 = get_task_base_time(task1, current_time)
        assert base_time1 == datetime(2025, 11, 18, 0, 0)

        # 23:59
        task2 = {"id": "task_010", "time": "23:59"}
        base_time2 = get_task_base_time(task2, current_time)
        assert base_time2 == datetime(2025, 11, 18, 23, 59)


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

    def test_invalid_base_time(self):
        """無効な基準時刻の場合（無効なタスク時刻）"""
        task = {"id": "task_013", "time": "invalid"}
        current_time = datetime(2025, 11, 18, 12, 0)

        times = calculate_notification_times(task, current_time)

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

    def test_invalid_task_time(self):
        """無効なタスク時刻の場合"""
        task = {"id": "task_011", "time": "invalid"}
        current_time = datetime(2025, 11, 18, 12, 0)

        times = calculate_notification_times(task, current_time)

        assert times["pre"] is None
        assert times["main"] is None
        assert times["warning"] is None

    def test_zero_minutes(self):
        """0分の設定の場合"""
        task = {
            "id": "task_012",
            "time": "14:30",
            "schedule": {
                "pre_notification_minutes": 0,
                "warning_minutes": 0,
            },
        }
        current_time = datetime(2025, 11, 18, 12, 0)
        base_time = datetime(2025, 11, 18, 14, 30)

        times = calculate_notification_times(task, current_time, base_time)

        assert times["pre"] == datetime(2025, 11, 18, 14, 30)  # 0分前 = 本通知と同じ
        assert times["main"] == datetime(2025, 11, 18, 14, 30)
        assert times["warning"] == datetime(
            2025, 11, 18, 14, 30
        )  # 0分後 = 本通知と同じ
