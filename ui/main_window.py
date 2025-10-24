"""
メインウィンドウ
タスクバーに常駐し、設定画面やログ画面へのアクセスを提供
"""
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from task_manager import TaskManager


class MainWindow:
    def __init__(self, task_manager: 'TaskManager'):
        self.task_manager = task_manager
        self.root = None
        self.settings_window = None
        self.log_window = None
        
    def create_window(self):
        """メインウィンドウを作成"""
        self.root = tk.Tk()
        self.root.title("定型作業支援ツール")
        self.root.geometry("300x150")
        self.root.resizable(False, False)
        
        # ウィンドウをタスクバーに最小化状態で表示
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        self._create_widgets()
        
    def _create_widgets(self):
        """ウィジェットを作成"""
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # ルートウィンドウのグリッド設定
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        
        # タイトル
        title_label = ttk.Label(main_frame, text="定型作業支援ツール", 
                               font=("Arial", 12, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="")
        
        # ステータス表示
        status_label = ttk.Label(main_frame, text="監視中", 
                               foreground="green", font=("Arial", 10))
        status_label.grid(row=1, column=0, columnspan=2, pady=(0, 10), sticky="")
        
        # ボタン
        settings_button = ttk.Button(main_frame, text="タスク設定", 
                                   command=self._open_settings)
        settings_button.grid(row=2, column=0, padx=(0, 5), sticky=(tk.W, tk.E))
        
        log_button = ttk.Button(main_frame, text="ログ・達成率", 
                              command=self._open_log_window)
        log_button.grid(row=2, column=1, padx=(5, 0), sticky=(tk.W, tk.E))
        
        # 終了ボタン
        exit_button = ttk.Button(main_frame, text="終了", 
                               command=self._exit_application)
        exit_button.grid(row=3, column=0, columnspan=2, pady=(10, 0), sticky=(tk.W, tk.E))
        
        # グリッドの重み設定
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
    def _open_settings(self):
        """設定画面を開く"""
        if self.settings_window is None or not self.settings_window.window_exists():
            from ui.settings_window import SettingsWindow
            self.settings_window = SettingsWindow(self.task_manager)
            self.settings_window.create_window()
        else:
            self.settings_window.root.lift()
            self.settings_window.root.focus_force()
    
    def _open_log_window(self):
        """ログ画面を開く"""
        if self.log_window is None or not self.log_window.window_exists():
            from ui.log_window import LogWindow
            self.log_window = LogWindow(self.task_manager)
            self.log_window.create_window()
        else:
            self.log_window.root.lift()
            self.log_window.root.focus_force()
    
    def _exit_application(self):
        """アプリケーションを終了"""
        self.task_manager.stop_monitoring()
        if self.settings_window:
            self.settings_window.close_window()
        if self.log_window:
            self.log_window.close_window()
        self.root.quit()
        self.root.destroy()
    
    def _on_closing(self):
        """ウィンドウが閉じられようとした時の処理"""
        # 最小化するのではなく、実際に終了する
        self._exit_application()
    
    def run(self):
        """ウィンドウを実行"""
        if self.root:
            self.root.mainloop()
