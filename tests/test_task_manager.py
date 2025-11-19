"""
task_manager.py のテスト
"""
from datetime import datetime
import pytest
from unittest.mock import Mock, patch
from task_manager import TaskManager


@pytest.fixture
def task_manager_with_config(config_with_temp_dir):
    """一時ディレクトリを使用するTaskManagerインスタンス"""
    manager = TaskManager()
    manager.config = config_with_temp_dir
    return manager


class TestTaskManagerNotification:
    """通知関連のテスト"""

    def test_should_trigger_notification(self, task_manager_with_config):
        """通知判定のテスト（±1分以内）"""
        manager = task_manager_with_config
        current_time = datetime(2025, 11, 18, 14, 30, 0)
        target_time = datetime(2025, 11, 18, 14, 30, 30)  # 30秒後
        task_id = "task_001"
        notification_type = "main"

        # ±1分以内なのでTrue
        result = manager._should_trigger_notification(
            current_time, target_time, task_id, notification_type
        )
        assert result is True

    def test_should_not_trigger_out_of_range(self, task_manager_with_config):
        """通知判定のテスト（範囲外）"""
        manager = task_manager_with_config
        current_time = datetime(2025, 11, 18, 14, 30, 0)
        target_time = datetime(2025, 11, 18, 14, 32, 0)  # 2分後（範囲外）
        task_id = "task_001"
        notification_type = "main"

        result = manager._should_trigger_notification(
            current_time, target_time, task_id, notification_type
        )
        assert result is False

    def test_should_not_trigger_duplicate(self, task_manager_with_config):
        """重複通知の防止"""
        manager = task_manager_with_config
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

    def test_should_trigger_exactly_one_minute(self, task_manager_with_config):
        """ちょうど1分の範囲内のテスト"""
        manager = task_manager_with_config
        current_time = datetime(2025, 11, 18, 14, 30, 0)
        target_time = datetime(2025, 11, 18, 14, 31, 0)  # ちょうど1分後
        task_id = "task_001"
        notification_type = "main"

        result = manager._should_trigger_notification(
            current_time, target_time, task_id, notification_type
        )
        assert result is True

    def test_should_trigger_before_one_minute(self, task_manager_with_config):
        """1分前の範囲内のテスト"""
        manager = task_manager_with_config
        current_time = datetime(2025, 11, 18, 14, 30, 0)
        target_time = datetime(2025, 11, 18, 14, 29, 0)  # 1分前
        task_id = "task_001"
        notification_type = "main"

        result = manager._should_trigger_notification(
            current_time, target_time, task_id, notification_type
        )
        assert result is True


class TestTaskManagerCallbacks:
    """コールバック関連のテスト"""

    def test_set_notification_callback(self, task_manager_with_config):
        """通知コールバックの設定"""
        manager = task_manager_with_config
        callback = Mock()

        manager.set_notification_callback("pre_notification", callback)
        assert manager.notification_callbacks["pre_notification"] == callback

    def test_trigger_pre_notification(self, task_manager_with_config):
        """予告通知のトリガー"""
        manager = task_manager_with_config
        callback = Mock()
        manager.set_notification_callback("pre_notification", callback)

        task = {"id": "task_001", "time": "14:30", "task_names": ["日報"]}
        manager._trigger_pre_notification(task)

        callback.assert_called_once_with(task)

    def test_trigger_main_notification(self, task_manager_with_config):
        """本通知のトリガー"""
        manager = task_manager_with_config
        callback = Mock()
        manager.set_notification_callback("main_notification", callback)

        task = {"id": "task_001", "time": "14:30", "task_names": ["日報"]}
        manager._trigger_main_notification(task)

        callback.assert_called_once_with(task)

    def test_trigger_warning_notification(self, task_manager_with_config):
        """警告通知のトリガー"""
        manager = task_manager_with_config
        callback = Mock()
        manager.set_notification_callback("warning_notification", callback)

        task = {"id": "task_001", "time": "14:30", "task_names": ["日報"]}
        manager._trigger_warning_notification(task)

        callback.assert_called_once_with(task)

    def test_trigger_without_callback(self, task_manager_with_config):
        """コールバックがない場合のトリガー"""
        manager = task_manager_with_config
        # コールバックを設定しない

        task = {"id": "task_001", "time": "14:30", "task_names": ["日報"]}
        # エラーが発生しないことを確認
        manager._trigger_pre_notification(task)
        manager._trigger_main_notification(task)
        manager._trigger_warning_notification(task)


class TestTaskManagerTaskCompletion:
    """タスク完了関連のテスト"""

    def test_mark_task_completed(self, task_manager_with_config):
        """タスク完了の記録"""
        manager = task_manager_with_config
        manager.mark_task_completed("task_001", "日報")

        logs = manager.config.load_logs()
        assert len(logs) == 1
        assert logs[0]["task_id"] == "task_001"
        assert logs[0]["task_name"] == "日報"
        assert logs[0]["completed"] is True

    def test_mark_task_incomplete(self, task_manager_with_config):
        """タスク未完了の記録"""
        manager = task_manager_with_config
        manager.mark_task_incomplete("task_001", "日報")

        logs = manager.config.load_logs()
        assert len(logs) == 1
        assert logs[0]["completed"] is False

    def test_is_task_completed_all_completed(self, task_manager_with_config):
        """すべてのサブタスクが完了している場合"""
        manager = task_manager_with_config
        # タスクを追加
        task_id = manager.config.add_task("14:30", ["日報", "勤怠報告"])

        # すべてのサブタスクを完了
        manager.mark_task_completed(task_id, "日報")
        manager.mark_task_completed(task_id, "勤怠報告")

        today = datetime.now().strftime("%Y-%m-%d")
        assert manager._is_task_completed(task_id, today) is True

    def test_is_task_completed_partial(self, task_manager_with_config):
        """一部のサブタスクのみ完了している場合"""
        manager = task_manager_with_config
        # タスクを追加
        task_id = manager.config.add_task("14:30", ["日報", "勤怠報告"])

        # 1つだけ完了
        manager.mark_task_completed(task_id, "日報")

        today = datetime.now().strftime("%Y-%m-%d")
        assert manager._is_task_completed(task_id, today) is False

    def test_is_task_completed_no_task(self, task_manager_with_config):
        """タスクが存在しない場合"""
        manager = task_manager_with_config
        today = datetime.now().strftime("%Y-%m-%d")
        assert manager._is_task_completed("nonexistent_task", today) is False

    def test_is_task_completed_no_subtasks(self, task_manager_with_config):
        """サブタスクがないタスクの場合"""
        manager = task_manager_with_config
        # タスクを追加（task_namesが空）
        task_id = manager.config.add_task("14:30", [])

        today = datetime.now().strftime("%Y-%m-%d")
        assert manager._is_task_completed(task_id, today) is False


class TestTaskManagerWindowManagement:
    """ウィンドウ管理関連のテスト"""

    def test_register_window(self, task_manager_with_config):
        """ウィンドウの登録"""
        manager = task_manager_with_config
        mock_window = Mock()

        manager.register_window("task_001", mock_window)
        assert manager.open_windows["task_001"] == mock_window

    def test_get_window(self, task_manager_with_config):
        """ウィンドウの取得"""
        manager = task_manager_with_config
        mock_window = Mock()
        mock_window.window_exists.return_value = True

        manager.register_window("task_001", mock_window)
        retrieved_window = manager.get_window("task_001")

        assert retrieved_window == mock_window

    def test_get_window_not_exists(self, task_manager_with_config):
        """存在しないウィンドウの取得"""
        manager = task_manager_with_config
        retrieved_window = manager.get_window("nonexistent_task")
        assert retrieved_window is None

    def test_get_window_dead_window(self, task_manager_with_config):
        """死んでいるウィンドウの取得"""
        manager = task_manager_with_config
        mock_window = Mock()
        mock_window.window_exists.return_value = False

        manager.register_window("task_001", mock_window)
        retrieved_window = manager.get_window("task_001")

        assert retrieved_window is None
        assert "task_001" not in manager.open_windows


class TestTaskManagerTodayTasks:
    """今日のタスク関連のテスト"""

    def test_get_today_tasks(self, task_manager_with_config):
        """今日のタスク一覧の取得"""
        manager = task_manager_with_config
        manager.config.add_task("10:00", ["タスク1"])
        manager.config.add_task("11:00", ["タスク2"])

        tasks = manager.get_today_tasks()
        assert len(tasks) == 2

    def test_get_today_tasks_with_disabled(self, task_manager_with_config):
        """無効化されたタスクを含む場合"""
        manager = task_manager_with_config
        manager.config.add_task("10:00", ["タスク1"], enabled=True)
        manager.config.add_task("11:00", ["タスク2"], enabled=False)

        tasks = manager.get_today_tasks()
        assert len(tasks) == 1
        assert tasks[0]["time"] == "10:00"


class TestTaskManagerClearNotificationHistory:
    """通知履歴クリア関連のテスト"""

    def test_clear_notification_history(self, task_manager_with_config):
        """通知履歴のクリア"""
        manager = task_manager_with_config
        # 今日の通知を追加
        today = datetime.now().strftime("%Y-%m-%d")
        today_key = f"task_001_{today}_14:30_main"
        manager.active_notifications[today_key] = True

        # 昨日の通知を追加
        yesterday_key = "task_001_2025-11-17_14:30_main"
        manager.active_notifications[yesterday_key] = True

        manager.clear_notification_history()

        # 今日の通知は残る
        assert today_key in manager.active_notifications
        # 昨日の通知は削除される
        assert yesterday_key not in manager.active_notifications

