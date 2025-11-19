"""
テスト共通フィクスチャ
"""

import os
import shutil
import tempfile

import pytest

from config import Config


@pytest.fixture
def temp_data_dir():
    """一時データディレクトリを作成"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def config_with_temp_dir(temp_data_dir):
    """一時ディレクトリを使用するConfigインスタンス"""
    config = Config()
    config.data_dir = temp_data_dir
    config.tasks_file = os.path.join(temp_data_dir, "tasks.json")
    config.logs_file = os.path.join(temp_data_dir, "logs.json")
    config.settings_file = os.path.join(temp_data_dir, "settings.json")
    config.calendar_overrides_file = os.path.join(
        temp_data_dir, "calendar_overrides.json"
    )
    config._init_files()
    return config


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
