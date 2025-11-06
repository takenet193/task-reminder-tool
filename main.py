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
    # 本通知はウィンドウを登録し、警告時は既存ウィンドウを警告モードへ切替
    task_manager.set_notification_callback('pre_notification', 
        lambda task: ReminderWindow(task_manager).show_pre_notification(task))
    def _show_main(task):
        win = ReminderWindow(task_manager)
        task_manager.register_window(task['id'], win)
        win.show_main_notification(task)
    def _show_warning(task):
        win = task_manager.get_window(task['id'])
        if win and win.window_exists():
            win.switch_to_warning_mode()
        else:
            ReminderWindow(task_manager).show_warning_notification(task)
    task_manager.set_notification_callback('main_notification', _show_main)
    task_manager.set_notification_callback('warning_notification', _show_warning)
    
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
