"""
タスク管理とスケジューリング
設定されたタスクの時刻監視と通知制御を行う
"""
import threading
import time
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Callable
from config import Config


class TaskManager:
    def __init__(self):
        self.config = Config()
        self.running = False
        self.monitor_thread = None
        self.notification_callbacks = {
            'pre_notification': None,  # 予告通知コールバック
            'main_notification': None,  # 本通知コールバック
            'warning_notification': None  # 警告通知コールバック
        }
        self.active_notifications = {}  # アクティブな通知を追跡
        
    def set_notification_callback(self, notification_type: str, callback: Callable):
        """通知コールバックを設定"""
        if notification_type in self.notification_callbacks:
            self.notification_callbacks[notification_type] = callback
    
    def start_monitoring(self):
        """時刻監視を開始"""
        if not self.running:
            self.running = True
            self.monitor_thread = threading.Thread(target=self._monitor_tasks, daemon=True)
            self.monitor_thread.start()
    
    def stop_monitoring(self):
        """時刻監視を停止"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def _monitor_tasks(self):
        """タスク監視のメインループ"""
        while self.running:
            try:
                current_time = datetime.now()
                tasks = self.config.load_tasks()
                
                for task in tasks:
                    if not task.get("enabled", True):
                        continue
                    
                    task_time_str = task["time"]
                    task_time = self._parse_time(task_time_str)
                    
                    if task_time is None:
                        continue
                    
                    # 今日のタスク時刻を計算
                    today_task_time = current_time.replace(
                        hour=task_time.hour,
                        minute=task_time.minute,
                        second=0,
                        microsecond=0
                    )
                    
                    # 予告通知(5分前)
                    pre_notification_time = today_task_time - timedelta(minutes=5)
                    if self._should_trigger_notification(current_time, pre_notification_time, 
                                                       task["id"], "pre"):
                        self._trigger_pre_notification(task)
                    
                    # 本通知(設定時刻)
                    if self._should_trigger_notification(current_time, today_task_time, 
                                                       task["id"], "main"):
                        self._trigger_main_notification(task)
                    
                    # 警告通知(5分後、未完了の場合)
                    warning_time = today_task_time + timedelta(minutes=5)
                    if self._should_trigger_notification(current_time, warning_time, 
                                                       task["id"], "warning"):
                        # タスクが未完了の場合のみ警告通知を発火
                        if not self._is_task_completed(task["id"], current_time.strftime('%Y-%m-%d')):
                            self._trigger_warning_notification(task)
                
                time.sleep(10)  # 10秒間隔でチェック
                
            except Exception as e:
                print(f"タスク監視中にエラーが発生しました: {e}")
                time.sleep(10)
    
    def _parse_time(self, time_str: str) -> datetime:
        """時刻文字列を解析"""
        try:
            hour, minute = map(int, time_str.split(":"))
            return datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
        except ValueError:
            return None
    
    def _should_trigger_notification(self, current_time: datetime, target_time: datetime, 
                                   task_id: str, notification_type: str) -> bool:
        """通知をトリガーすべきかを判定"""
        # 通知キーを生成（タスクID + 日付_時刻 + 通知タイプ）
        notification_key = f"{task_id}_{target_time.strftime('%Y-%m-%d_%H:%M')}_{notification_type}"
        
        # 既に通知済みの場合はスキップ
        if notification_key in self.active_notifications:
            return False
        
        # 時刻の範囲内かチェック（±1分の範囲）
        time_diff = abs((current_time - target_time).total_seconds())
        if time_diff <= 60:  # 1分以内
            self.active_notifications[notification_key] = True
            return True
        
        return False
    
    def _trigger_pre_notification(self, task: Dict[str, Any]):
        """予告通知をトリガー"""
        if self.notification_callbacks['pre_notification']:
            self.notification_callbacks['pre_notification'](task)
    
    def _trigger_main_notification(self, task: Dict[str, Any]):
        """本通知をトリガー"""
        if self.notification_callbacks['main_notification']:
            self.notification_callbacks['main_notification'](task)
    
    def _trigger_warning_notification(self, task: Dict[str, Any]):
        """警告通知をトリガー"""
        if self.notification_callbacks['warning_notification']:
            self.notification_callbacks['warning_notification'](task)
    
    def mark_task_completed(self, task_id: str, task_name: str):
        """タスク完了を記録"""
        self.config.add_log(task_id, task_name, True)
    
    def mark_task_incomplete(self, task_id: str, task_name: str):
        """タスク未完了を記録"""
        self.config.add_log(task_id, task_name, False)
    
    def get_today_tasks(self) -> List[Dict[str, Any]]:
        """今日のタスク一覧を取得"""
        tasks = self.config.load_tasks()
        return [task for task in tasks if task.get("enabled", True)]
    
    def _is_task_completed(self, task_id: str, date: str) -> bool:
        """タスクが完全に完了しているかを判定
        
        Args:
            task_id: タスクID
            date: 日付文字列 (YYYY-MM-DD)
            
        Returns:
            bool: すべてのサブタスクが完了している場合True
        """
        try:
            # 指定日のログを取得
            logs = self.config.get_logs_by_date(date)
            
            # 該当タスクの完了ログを抽出
            completed_logs = [
                log for log in logs 
                if log["task_id"] == task_id and log["completed"] == True
            ]
            
            # タスクのサブタスク数を取得
            tasks = self.config.load_tasks()
            task = next((t for t in tasks if t["id"] == task_id), None)
            
            if not task:
                return False  # タスクが見つからない場合は未完了
            
            expected_count = len(task.get("task_names", []))
            actual_count = len(completed_logs)
            
            # すべてのサブタスクが完了しているかチェック
            return actual_count >= expected_count and expected_count > 0
            
        except Exception as e:
            print(f"タスク完了判定中にエラーが発生しました: {e}")
            return False  # エラー時は未完了として扱う
    
    def clear_notification_history(self):
        """通知履歴をクリア（当日以外のキーを削除）"""
        today_str = datetime.now().strftime('%Y-%m-%d')
        # パターン例: _2025-10-28_14:30_
        pattern = re.compile(rf"_{today_str}_\d{{2}}:\d{{2}}_")
        
        keys_to_remove = []
        for key in list(self.active_notifications.keys()):
            if not pattern.search(key):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.active_notifications[key]

