"""
設定管理クラス
JSONファイルの読み書きとタスク・ログデータの管理を行う
"""

import json
import logging
import os
from datetime import date, datetime
from typing import Any

from utils.file_io import atomic_write_json

logger = logging.getLogger(__name__)


class Config:
    def __init__(self):
        self.data_dir = "data"
        self.tasks_file = os.path.join(self.data_dir, "tasks.json")
        self.logs_file = os.path.join(self.data_dir, "logs.json")
        self.settings_file = os.path.join(self.data_dir, "settings.json")
        self.calendar_overrides_file = os.path.join(
            self.data_dir, "calendar_overrides.json"
        )

        # データディレクトリが存在しない場合は作成
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        # ファイルが存在しない場合は初期化
        self._init_files()

    def _init_files(self) -> None:
        """ファイルが存在しない場合は初期化"""
        if not os.path.exists(self.tasks_file):
            self._save_tasks([])

        if not os.path.exists(self.logs_file):
            self._save_logs([])

        if not os.path.exists(self.settings_file):
            self._save_settings({"exclude_weekends": False})

        if not os.path.exists(self.calendar_overrides_file):
            self._save_calendar_overrides({})

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

    def load_tasks(self) -> list[dict[str, Any]]:
        """タスクデータをJSONファイルから読み込み"""
        try:
            with open(self.tasks_file, encoding="utf-8") as f:
                data = json.load(f)
                tasks = data.get("tasks", [])
                logger.debug(f"タスクデータを読み込みました: {len(tasks)}件")
                return tasks
        except FileNotFoundError:
            logger.debug("タスクファイルが見つかりません。空のリストを返します")
            return []
        except json.JSONDecodeError as e:
            logger.error(
                f"タスクファイルの読み込みに失敗（JSON形式エラー）: {e}", exc_info=True
            )
            return []

    def save_tasks(self, tasks: list[dict[str, Any]]) -> None:
        """タスクデータを保存"""
        try:
            self._save_tasks(tasks)
            logger.info(f"タスクデータを保存しました: {len(tasks)}件")
        except Exception as e:
            logger.error(f"タスクデータの保存に失敗: {e}", exc_info=True)
            raise

    def load_logs(self) -> list[dict[str, Any]]:
        """ログデータをJSONファイルから読み込み"""
        try:
            with open(self.logs_file, encoding="utf-8") as f:
                data = json.load(f)
                logs = data.get("logs", [])
                logger.debug(f"ログデータを読み込みました: {len(logs)}件")
                return logs
        except FileNotFoundError:
            logger.debug("ログファイルが見つかりません。空のリストを返します")
            return []
        except json.JSONDecodeError as e:
            logger.error(
                f"ログファイルの読み込みに失敗（JSON形式エラー）: {e}", exc_info=True
            )
            return []

    def save_logs(self, logs: list[dict[str, Any]]) -> None:
        """ログデータを保存"""
        try:
            self._save_logs(logs)
            logger.info(f"ログデータを保存しました: {len(logs)}件")
        except Exception as e:
            logger.error(f"ログデータの保存に失敗: {e}", exc_info=True)
            raise

    def add_task(self, time: str, task_names: list[str], enabled: bool = True) -> str:
        """新しいタスクを追加"""
        tasks = self.load_tasks()
        task_id = f"task_{len(tasks) + 1:03d}"

        # 登録日時を追加（YYYY-MM-DD形式）
        now = datetime.now()
        created_date = now.strftime("%Y-%m-%d")

        new_task = {
            "id": task_id,
            "time": time,
            "task_names": task_names,
            "enabled": enabled,
            "created_date": created_date,
        }

        tasks.append(new_task)
        self.save_tasks(tasks)
        return task_id

    def update_task(
        self,
        task_id: str,
        time: str | None = None,
        task_names: list[str] | None = None,
        enabled: bool | None = None,
    ) -> None:
        """タスクを更新"""
        tasks = self.load_tasks()
        for task in tasks:
            if task["id"] == task_id:
                if time is not None:
                    task["time"] = time
                if task_names is not None:
                    task["task_names"] = task_names
                if enabled is not None:
                    task["enabled"] = enabled
                break

        self.save_tasks(tasks)

    def delete_task(self, task_id: str) -> None:
        """タスクを削除"""
        tasks = self.load_tasks()
        tasks = [task for task in tasks if task["id"] != task_id]
        self.save_tasks(tasks)

    def add_log(self, task_id: str, task_name: str, completed: bool = True) -> None:
        """ログエントリを追加"""
        logs = self.load_logs()

        now = datetime.now()
        log_entry = {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M"),
            "task_id": task_id,
            "task_name": task_name,
            "completed": completed,
        }

        logs.append(log_entry)
        self.save_logs(logs)

    def get_logs_by_date(self, date: str) -> list[dict[str, Any]]:
        """指定した日付のログを取得"""
        logs = self.load_logs()
        return [log for log in logs if log["date"] == date]

    def get_logs_by_month(self, year: int, month: int) -> list[dict[str, Any]]:
        """指定した月のログを取得"""
        logs = self.load_logs()
        target_date = f"{year:04d}-{month:02d}"
        return [log for log in logs if log["date"].startswith(target_date)]

    def get_task_created_date(self, task: dict[str, Any]) -> str:
        """タスクの登録日時を取得（後方互換性を考慮）

        既存のタスクには登録日時がない可能性があるため、
        最初のログの日付を使用するか、今日の日付をデフォルトとする
        """
        # 登録日時が既に存在する場合はそれを返す
        if "created_date" in task and task["created_date"]:
            return task["created_date"]

        # 登録日時がない場合、そのタスクの最初のログの日付を取得
        logs = self.load_logs()
        task_logs = [log for log in logs if log["task_id"] == task["id"]]

        if task_logs:
            # 日付でソートして最初のログの日付を返す
            task_logs.sort(key=lambda x: x["date"])
            return task_logs[0]["date"]

        # ログもない場合は今日の日付を返す（後方互換性のため）
        return datetime.now().strftime("%Y-%m-%d")

    def load_settings(self) -> dict[str, Any]:
        """設定データをJSONファイルから読み込み"""
        try:
            with open(self.settings_file, encoding="utf-8") as f:
                settings = json.load(f)
                logger.debug("設定データを読み込みました")
                return settings
        except FileNotFoundError:
            logger.debug("設定ファイルが見つかりません。デフォルト設定を返します")
            return {"exclude_weekends": False}
        except json.JSONDecodeError as e:
            logger.error(
                f"設定ファイルの読み込みに失敗（JSON形式エラー）: {e}", exc_info=True
            )
            return {"exclude_weekends": False}

    def save_settings(self, settings: dict[str, Any]) -> None:
        """設定データを保存"""
        try:
            self._save_settings(settings)
            logger.info("設定データを保存しました")
        except Exception as e:
            logger.error(f"設定データの保存に失敗: {e}", exc_info=True)
            raise

    def get_exclude_weekends(self) -> bool:
        """週末除外設定を取得"""
        settings = self.load_settings()
        return settings.get("exclude_weekends", False)

    def set_exclude_weekends(self, exclude: bool) -> None:
        """週末除外設定を保存"""
        settings = self.load_settings()
        settings["exclude_weekends"] = exclude
        self.save_settings(settings)

    def load_calendar_overrides(self) -> dict[str, dict[str, bool]]:
        """カレンダーオーバーライドデータをJSONファイルから読み込み"""
        try:
            with open(self.calendar_overrides_file, encoding="utf-8") as f:
                overrides = json.load(f)
                logger.debug("カレンダーオーバーライドデータを読み込みました")
                return overrides
        except FileNotFoundError:
            logger.debug(
                "カレンダーオーバーライドファイルが見つかりません。空の辞書を返します"
            )
            return {}
        except json.JSONDecodeError as e:
            logger.error(
                f"カレンダーオーバーライドファイルの読み込みに失敗（JSON形式エラー）: {e}",
                exc_info=True,
            )
            return {}

    def save_calendar_overrides(self, overrides: dict[str, dict[str, bool]]) -> None:
        """カレンダーオーバーライドデータを保存"""
        try:
            self._save_calendar_overrides(overrides)
            logger.info("カレンダーオーバーライドデータを保存しました")
        except Exception as e:
            logger.error(
                f"カレンダーオーバーライドデータの保存に失敗: {e}", exc_info=True
            )
            raise

    def get_month_overrides(self, year: int, month: int) -> dict[str, bool]:
        """指定月のオーバーライド設定を取得"""
        overrides = self.load_calendar_overrides()
        month_key = f"{year:04d}-{month:02d}"
        return overrides.get(month_key, {})

    def set_day_override(self, year: int, month: int, day: int, included: bool) -> None:
        """特定日のオーバーライド設定を保存"""
        overrides = self.load_calendar_overrides()
        month_key = f"{year:04d}-{month:02d}"
        date_str = f"{year:04d}-{month:02d}-{day:02d}"

        if month_key not in overrides:
            overrides[month_key] = {}

        overrides[month_key][date_str] = included
        self.save_calendar_overrides(overrides)

    def clear_month_overrides(self, year: int, month: int) -> None:
        """指定月のオーバーライド設定をクリア"""
        overrides = self.load_calendar_overrides()
        month_key = f"{year:04d}-{month:02d}"
        if month_key in overrides:
            del overrides[month_key]
            self.save_calendar_overrides(overrides)

    def is_date_included(self, date_obj: date) -> bool:
        """日付が達成率計算の対象日かどうかを判定

        Args:
            date_obj: 判定する日付（date型）

        Returns:
            bool: 対象日の場合True
        """
        year = date_obj.year
        month = date_obj.month
        date_str = date_obj.strftime("%Y-%m-%d")

        # 月別オーバーライドを確認
        month_overrides = self.get_month_overrides(year, month)
        if date_str in month_overrides:
            # オーバーライドが設定されている場合はその値を使用
            return month_overrides[date_str]

        # オーバーライドがない場合はデフォルト規則（週末除外設定）を適用
        exclude_weekends = self.get_exclude_weekends()
        if exclude_weekends:
            # 週末（土曜日=5、日曜日=6）を除外
            weekday = date_obj.weekday()
            return weekday < 5  # 0-4が月-金

        # 週末除外がOFFの場合は全ての日を含める
        return True
