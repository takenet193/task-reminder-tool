"""
設定管理クラス
JSONファイルの読み書きとタスク・ログデータの管理を行う
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Any


class Config:
    def __init__(self):
        self.data_dir = "data"
        self.tasks_file = os.path.join(self.data_dir, "tasks.json")
        self.logs_file = os.path.join(self.data_dir, "logs.json")
        
        # データディレクトリが存在しない場合は作成
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        # ファイルが存在しない場合は初期化
        self._init_files()
    
    def _init_files(self):
        """ファイルが存在しない場合は初期化"""
        if not os.path.exists(self.tasks_file):
            self._save_tasks([])
        
        if not os.path.exists(self.logs_file):
            self._save_logs([])
    
    def _save_tasks(self, tasks: List[Dict[str, Any]]):
        """タスクデータをJSONファイルに保存"""
        data = {"tasks": tasks}
        with open(self.tasks_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _save_logs(self, logs: List[Dict[str, Any]]):
        """ログデータをJSONファイルに保存"""
        data = {"logs": logs}
        with open(self.logs_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_tasks(self) -> List[Dict[str, Any]]:
        """タスクデータをJSONファイルから読み込み"""
        try:
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("tasks", [])
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_tasks(self, tasks: List[Dict[str, Any]]):
        """タスクデータを保存"""
        self._save_tasks(tasks)
    
    def load_logs(self) -> List[Dict[str, Any]]:
        """ログデータをJSONファイルから読み込み"""
        try:
            with open(self.logs_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("logs", [])
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_logs(self, logs: List[Dict[str, Any]]):
        """ログデータを保存"""
        self._save_logs(logs)
    
    def add_task(self, time: str, task_names: List[str], enabled: bool = True) -> str:
        """新しいタスクを追加"""
        tasks = self.load_tasks()
        task_id = f"task_{len(tasks) + 1:03d}"
        
        new_task = {
            "id": task_id,
            "time": time,
            "task_names": task_names,
            "enabled": enabled
        }
        
        tasks.append(new_task)
        self.save_tasks(tasks)
        return task_id
    
    def update_task(self, task_id: str, time: str = None, task_names: List[str] = None, enabled: bool = None):
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
    
    def delete_task(self, task_id: str):
        """タスクを削除"""
        tasks = self.load_tasks()
        tasks = [task for task in tasks if task["id"] != task_id]
        self.save_tasks(tasks)
    
    def add_log(self, task_id: str, task_name: str, completed: bool = True):
        """ログエントリを追加"""
        logs = self.load_logs()
        
        now = datetime.now()
        log_entry = {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M"),
            "task_id": task_id,
            "task_name": task_name,
            "completed": completed
        }
        
        logs.append(log_entry)
        self.save_logs(logs)
    
    def get_logs_by_date(self, date: str) -> List[Dict[str, Any]]:
        """指定した日付のログを取得"""
        logs = self.load_logs()
        return [log for log in logs if log["date"] == date]
    
    def get_logs_by_month(self, year: int, month: int) -> List[Dict[str, Any]]:
        """指定した月のログを取得"""
        logs = self.load_logs()
        target_date = f"{year:04d}-{month:02d}"
        return [log for log in logs if log["date"].startswith(target_date)]
