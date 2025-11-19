"""
config.py のテスト
"""

import os
from datetime import date, datetime


class TestConfigTasks:
    """タスク関連のテスト"""

    def test_add_task(self, config_with_temp_dir):
        """タスクの追加"""
        config = config_with_temp_dir
        task_id = config.add_task("14:30", ["日報", "勤怠報告"])

        assert task_id.startswith("task_")
        tasks = config.load_tasks()
        assert len(tasks) == 1
        assert tasks[0]["time"] == "14:30"
        assert tasks[0]["task_names"] == ["日報", "勤怠報告"]
        assert tasks[0]["enabled"] is True
        assert "created_date" in tasks[0]

    def test_add_multiple_tasks(self, config_with_temp_dir):
        """複数タスクの追加"""
        config = config_with_temp_dir
        task_id1 = config.add_task("10:00", ["タスク1"])
        task_id2 = config.add_task("11:00", ["タスク2"])

        tasks = config.load_tasks()
        assert len(tasks) == 2
        assert tasks[0]["id"] == task_id1
        assert tasks[1]["id"] == task_id2

    def test_update_task(self, config_with_temp_dir):
        """タスクの更新"""
        config = config_with_temp_dir
        task_id = config.add_task("14:30", ["日報"])

        config.update_task(task_id, time="15:00")
        tasks = config.load_tasks()
        assert tasks[0]["time"] == "15:00"
        assert tasks[0]["task_names"] == ["日報"]

        config.update_task(task_id, task_names=["日報", "勤怠報告"])
        tasks = config.load_tasks()
        assert tasks[0]["task_names"] == ["日報", "勤怠報告"]

        config.update_task(task_id, enabled=False)
        tasks = config.load_tasks()
        assert tasks[0]["enabled"] is False

    def test_delete_task(self, config_with_temp_dir):
        """タスクの削除"""
        config = config_with_temp_dir
        task_id1 = config.add_task("10:00", ["タスク1"])
        task_id2 = config.add_task("11:00", ["タスク2"])

        config.delete_task(task_id1)
        tasks = config.load_tasks()
        assert len(tasks) == 1
        assert tasks[0]["id"] == task_id2

    def test_load_tasks_file_not_found(self, config_with_temp_dir):
        """ファイルが存在しない場合"""
        config = config_with_temp_dir
        # ファイルを削除
        os.remove(config.tasks_file)

        tasks = config.load_tasks()
        assert tasks == []

    def test_save_tasks(self, config_with_temp_dir):
        """タスクの保存"""
        config = config_with_temp_dir
        tasks = [
            {"id": "task_001", "time": "10:00", "task_names": ["タスク1"]},
            {"id": "task_002", "time": "11:00", "task_names": ["タスク2"]},
        ]

        config.save_tasks(tasks)
        loaded_tasks = config.load_tasks()
        assert len(loaded_tasks) == 2
        assert loaded_tasks[0]["id"] == "task_001"


class TestConfigLogs:
    """ログ関連のテスト"""

    def test_add_log(self, config_with_temp_dir):
        """ログの追加"""
        config = config_with_temp_dir
        config.add_log("task_001", "日報", True)

        logs = config.load_logs()
        assert len(logs) == 1
        assert logs[0]["task_id"] == "task_001"
        assert logs[0]["task_name"] == "日報"
        assert logs[0]["completed"] is True
        assert "date" in logs[0]
        assert "time" in logs[0]

    def test_add_log_incomplete(self, config_with_temp_dir):
        """未完了ログの追加"""
        config = config_with_temp_dir
        config.add_log("task_001", "日報", False)

        logs = config.load_logs()
        assert logs[0]["completed"] is False

    def test_get_logs_by_date(self, config_with_temp_dir):
        """日付でログを取得"""
        config = config_with_temp_dir
        config.add_log("task_001", "日報", True)
        config.add_log("task_002", "勤怠報告", True)

        # 今日の日付でログを取得
        today = datetime.now().strftime("%Y-%m-%d")
        logs = config.get_logs_by_date(today)
        assert len(logs) >= 2

    def test_get_logs_by_month(self, config_with_temp_dir):
        """月でログを取得"""
        config = config_with_temp_dir
        config.add_log("task_001", "日報", True)

        year = datetime.now().year
        month = datetime.now().month
        logs = config.get_logs_by_month(year, month)
        assert len(logs) >= 1

    def test_load_logs_file_not_found(self, config_with_temp_dir):
        """ログファイルが存在しない場合"""
        config = config_with_temp_dir
        os.remove(config.logs_file)

        logs = config.load_logs()
        assert logs == []


class TestConfigSettings:
    """設定関連のテスト"""

    def test_exclude_weekends_default(self, config_with_temp_dir):
        """週末除外設定のデフォルト値"""
        config = config_with_temp_dir
        assert config.get_exclude_weekends() is False

    def test_set_exclude_weekends(self, config_with_temp_dir):
        """週末除外設定の変更"""
        config = config_with_temp_dir
        config.set_exclude_weekends(True)
        assert config.get_exclude_weekends() is True

        config.set_exclude_weekends(False)
        assert config.get_exclude_weekends() is False

    def test_load_settings_file_not_found(self, config_with_temp_dir):
        """設定ファイルが存在しない場合"""
        config = config_with_temp_dir
        os.remove(config.settings_file)

        settings = config.load_settings()
        assert settings == {"exclude_weekends": False}

    def test_save_settings(self, config_with_temp_dir):
        """設定の保存"""
        config = config_with_temp_dir
        settings = {"exclude_weekends": True, "custom_key": "value"}
        config.save_settings(settings)

        loaded_settings = config.load_settings()
        assert loaded_settings["exclude_weekends"] is True
        assert loaded_settings["custom_key"] == "value"


class TestConfigCalendarOverrides:
    """カレンダーオーバーライド関連のテスト"""

    def test_set_day_override(self, config_with_temp_dir):
        """特定日のオーバーライド設定"""
        config = config_with_temp_dir
        config.set_day_override(2025, 11, 18, True)

        overrides = config.get_month_overrides(2025, 11)
        assert overrides["2025-11-18"] is True

    def test_get_month_overrides(self, config_with_temp_dir):
        """月のオーバーライド設定を取得"""
        config = config_with_temp_dir
        config.set_day_override(2025, 11, 18, True)
        config.set_day_override(2025, 11, 19, False)

        overrides = config.get_month_overrides(2025, 11)
        assert overrides["2025-11-18"] is True
        assert overrides["2025-11-19"] is False

    def test_clear_month_overrides(self, config_with_temp_dir):
        """月のオーバーライド設定をクリア"""
        config = config_with_temp_dir
        config.set_day_override(2025, 11, 18, True)
        config.clear_month_overrides(2025, 11)

        overrides = config.get_month_overrides(2025, 11)
        assert overrides == {}

    def test_is_date_included_without_override(self, config_with_temp_dir):
        """オーバーライドなしの場合の日付判定"""
        config = config_with_temp_dir
        # 週末除外がOFFの場合、すべての日が含まれる
        test_date = date(2025, 11, 18)  # 火曜日
        assert config.is_date_included(test_date) is True

    def test_is_date_included_with_weekend_exclusion(self, config_with_temp_dir):
        """週末除外設定ありの場合の日付判定"""
        config = config_with_temp_dir
        config.set_exclude_weekends(True)

        # 平日は含まれる
        weekday = date(2025, 11, 18)  # 火曜日
        assert config.is_date_included(weekday) is True

        # 週末は除外される
        saturday = date(2025, 11, 22)  # 土曜日
        sunday = date(2025, 11, 23)  # 日曜日
        assert config.is_date_included(saturday) is False
        assert config.is_date_included(sunday) is False

    def test_is_date_included_with_override(self, config_with_temp_dir):
        """オーバーライドありの場合の日付判定"""
        config = config_with_temp_dir
        config.set_exclude_weekends(True)

        # 週末でもオーバーライドで含める
        saturday = date(2025, 11, 22)
        config.set_day_override(2025, 11, 22, True)
        assert config.is_date_included(saturday) is True

        # 平日でもオーバーライドで除外
        weekday = date(2025, 11, 18)
        config.set_day_override(2025, 11, 18, False)
        assert config.is_date_included(weekday) is False

    def test_get_task_created_date(self, config_with_temp_dir):
        """タスクの登録日時の取得"""
        config = config_with_temp_dir
        config.add_task("14:30", ["日報"])

        tasks = config.load_tasks()
        task = tasks[0]
        created_date = config.get_task_created_date(task)

        assert created_date == task["created_date"]

    def test_get_task_created_date_without_created_date(self, config_with_temp_dir):
        """created_dateがない場合の登録日時取得"""
        config = config_with_temp_dir
        # created_dateがないタスクを作成
        task = {"id": "task_001", "time": "14:30", "task_names": ["日報"]}
        created_date = config.get_task_created_date(task)

        # ログがない場合は今日の日付が返される
        assert created_date == datetime.now().strftime("%Y-%m-%d")

    def test_load_calendar_overrides_file_not_found(self, config_with_temp_dir):
        """カレンダーオーバーライドファイルが存在しない場合"""
        config = config_with_temp_dir
        os.remove(config.calendar_overrides_file)

        overrides = config.load_calendar_overrides()
        assert overrides == {}
