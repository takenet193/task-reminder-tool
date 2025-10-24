"""
リマインダーウィンドウ
予告通知、本通知、警告通知を表示するウィンドウ
"""
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Dict, Any, List
import threading
import time

if TYPE_CHECKING:
    from task_manager import TaskManager


class ReminderWindow:
    def __init__(self, task_manager: 'TaskManager'):
        self.task_manager = task_manager
        self.root = None
        self.notification_type = None  # 'pre', 'main', 'warning'
        self.task = None
        self.checkboxes = []
        self.auto_close_timer = None
        self.can_close = False
        
    def show_pre_notification(self, task: Dict[str, Any]):
        """予告通知を表示"""
        self.notification_type = 'pre'
        self.task = task
        self._create_window()
        self._setup_pre_notification()
        
        # 1分後に自動で閉じる
        self._start_auto_close_timer(60)
        
    def show_main_notification(self, task: Dict[str, Any]):
        """本通知を表示"""
        self.notification_type = 'main'
        self.task = task
        self._create_window()
        self._setup_main_notification()
        
    def show_warning_notification(self, task: Dict[str, Any]):
        """警告通知を表示"""
        self.notification_type = 'warning'
        self.task = task
        self._create_window()
        self._setup_warning_notification()
        
    def _create_window(self):
        """ウィンドウを作成"""
        if self.root:
            self.root.destroy()
            
        self.root = tk.Toplevel()
        self.root.overrideredirect(True)  # タイトルバーを削除
        self.root.attributes('-alpha', 0.8)  # 半透明
        
        # ウィンドウサイズと位置を設定
        if self.notification_type == 'pre':
            self.root.geometry("250x80")
        elif self.notification_type == 'main':
            self.root.geometry("300x200")
        else:  # warning
            self.root.geometry("350x150")
            
        self._position_window()
        
        # ドラッグ機能を追加
        self._add_drag_functionality()
        
    def _position_window(self):
        """ウィンドウの位置を設定"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        if self.notification_type == 'warning':
            # 警告通知は画面中央に表示
            x = (screen_width - 350) // 2
            y = (screen_height - 150) // 2
        else:
            # 予告通知と本通知は左下に表示
            x = 50
            y = screen_height - 200
            
        self.root.geometry(f"+{x}+{y}")
        
    def _add_drag_functionality(self):
        """ドラッグ機能を追加"""
        def start_drag(event):
            self.root.x = event.x
            self.root.y = event.y
            
        def drag_window(event):
            deltax = event.x - self.root.x
            deltay = event.y - self.root.y
            x = self.root.winfo_x() + deltax
            y = self.root.winfo_y() + deltay
            self.root.geometry(f"+{x}+{y}")
            
        self.root.bind("<Button-1>", start_drag)
        self.root.bind("<B1-Motion>", drag_window)
        
    def _setup_pre_notification(self):
        """予告通知の設定"""
        frame = ttk.Frame(self.root, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # メッセージ
        message = f"まもなくタスクがあります\n{', '.join(self.task['task_names'])}"
        label = ttk.Label(frame, text=message, font=("Arial", 10), 
                         foreground="blue")
        label.pack(expand=True)
        
    def _setup_main_notification(self):
        """本通知の設定"""
        frame = ttk.Frame(self.root, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # タイトル
        title_label = ttk.Label(frame, text="タスクの時間です！", 
                               font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 10))
        
        # タスクリスト
        task_frame = ttk.Frame(frame)
        task_frame.pack(fill=tk.BOTH, expand=True)
        
        self.checkboxes = []
        for task_name in self.task['task_names']:
            var = tk.BooleanVar()
            checkbox = ttk.Checkbutton(task_frame, text=task_name, variable=var,
                                     command=self._check_completion)
            checkbox.pack(anchor=tk.W, pady=2)
            self.checkboxes.append((task_name, var))
            
        # 完了ボタン
        complete_button = ttk.Button(frame, text="完了", 
                                   command=self._complete_tasks)
        complete_button.pack(pady=(10, 0))
        
        # 初期状態では閉じられない
        self.can_close = False
        
    def _setup_warning_notification(self):
        """警告通知の設定"""
        frame = ttk.Frame(self.root, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 警告メッセージ
        warning_label = ttk.Label(frame, text="⚠️ タスクが未完了です！", 
                                 font=("Arial", 14, "bold"), foreground="red")
        warning_label.pack(pady=(0, 10))
        
        # タスク名
        task_label = ttk.Label(frame, text=f"未完了タスク: {', '.join(self.task['task_names'])}", 
                              font=("Arial", 10))
        task_label.pack(pady=(0, 10))
        
        # 確認ボタン
        button_frame = ttk.Frame(frame)
        button_frame.pack()
        
        complete_button = ttk.Button(button_frame, text="今すぐ実行", 
                                   command=self._complete_tasks)
        complete_button.pack(side=tk.LEFT, padx=(0, 5))
        
        close_button = ttk.Button(button_frame, text="後で実行", 
                                command=self._close_warning)
        close_button.pack(side=tk.LEFT, padx=(5, 0))
        
    def _check_completion(self):
        """チェックボックスの状態を確認"""
        if self.notification_type != 'main':
            return
            
        # すべてのチェックボックスがチェックされているか確認
        all_checked = all(var.get() for _, var in self.checkboxes)
        self.can_close = all_checked
        
    def _complete_tasks(self):
        """タスク完了処理"""
        if self.notification_type == 'main':
            # チェックされたタスクをログに記録
            for task_name, var in self.checkboxes:
                if var.get():
                    self.task_manager.mark_task_completed(self.task['id'], task_name)
        elif self.notification_type == 'warning':
            # 警告通知から実行した場合もログに記録
            for task_name in self.task['task_names']:
                self.task_manager.mark_task_completed(self.task['id'], task_name)
                
        self._close_window()
        
    def _close_warning(self):
        """警告通知を閉じる"""
        self._close_window()
        
    def _close_window(self):
        """ウィンドウを閉じる"""
        if self.auto_close_timer:
            self.auto_close_timer.cancel()
            
        if self.root:
            self.root.destroy()
            self.root = None
            
    def _start_auto_close_timer(self, seconds: int):
        """自動クローズタイマーを開始"""
        self.auto_close_timer = threading.Timer(seconds, self._close_window)
        self.auto_close_timer.start()
        
    def window_exists(self) -> bool:
        """ウィンドウが存在するかを確認"""
        return self.root is not None and self.root.winfo_exists()
