"""
定型作業支援ツール メインアプリケーション
"""
import tkinter as tk
from task_manager import TaskManager
from ui.main_window import MainWindow
from ui.reminder_window import ReminderWindow


def main():
    """メイン関数"""
    # タスクマネージャーを初期化
    task_manager = TaskManager()
    
    # 通知コールバックを設定（通知ごとに新しいウィンドウを生成）
    task_manager.set_notification_callback('pre_notification', lambda task: ReminderWindow(task_manager).show_pre_notification(task))
    task_manager.set_notification_callback('main_notification', lambda task: ReminderWindow(task_manager).show_main_notification(task))
    task_manager.set_notification_callback('warning_notification', lambda task: ReminderWindow(task_manager).show_warning_notification(task))
    
    # メインウィンドウを初期化
    main_window = MainWindow(task_manager)
    main_window.create_window()
    
    # タスク監視を開始
    task_manager.start_monitoring()
    
    try:
        # メインループを開始
        main_window.run()
    except KeyboardInterrupt:
        print("アプリケーションが中断されました")
    finally:
        # クリーンアップ
        task_manager.stop_monitoring()


if __name__ == "__main__":
    main()
