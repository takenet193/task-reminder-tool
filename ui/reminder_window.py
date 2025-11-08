"""
リマインダーウィンドウ
予告通知、本通知、警告通知を表示するウィンドウ
"""

import threading
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from task_manager import TaskManager


class ReminderWindow:
    def __init__(self, task_manager: "TaskManager"):
        self.task_manager = task_manager
        self.root = None
        self.notification_type = None  # 'pre', 'main', 'warning'
        self.task = None
        self.checkboxes = []
        self.auto_close_timer = None
        self.can_close = False
        self.complete_button = None

    def _clear_contents(self):
        """ウィンドウ内の既存ウィジェットをクリア"""
        for child in list(self.root.winfo_children()):
            try:
                child.destroy()
            except Exception:
                pass

    def switch_to_warning_mode(self):
        """本通知ウィンドウを警告表示に切り替える"""
        if not self.root or not self.root.winfo_exists():
            return
        self.notification_type = "warning"
        self._clear_contents()
        # 警告用のサイズへ変更
        self.root.geometry("380x220")
        # 再構築
        self._setup_warning_notification()
        # 画面中央へ
        self._position_window()
        try:
            self.root.lift()
            self.root.focus_force()
        except Exception:
            pass

    def show_pre_notification(self, task: dict[str, Any]):
        """予告通知を表示"""
        self.notification_type = "pre"
        self.task = task
        self._create_window()
        self._setup_pre_notification()

        # 1分後に自動で閉じる
        self._start_auto_close_timer(60)

    def show_main_notification(self, task: dict[str, Any]):
        """本通知を表示"""
        self.notification_type = "main"
        self.task = task
        self._create_window()
        self._setup_main_notification()

    def show_warning_notification(self, task: dict[str, Any]):
        """警告通知を表示"""
        self.notification_type = "warning"
        self.task = task
        self._create_window()
        self._setup_warning_notification()

    def _create_window(self):
        """ウィンドウを作成"""
        if self.root:
            self.root.destroy()

        self.root = tk.Toplevel()
        self.root.overrideredirect(True)  # タイトルバーを削除
        # 常に最前面に表示（不透明）
        self.root.attributes("-topmost", True)

        # ウィンドウサイズを設定（やや大きめ）
        if self.notification_type == "pre":
            self.root.geometry("300x110")
        elif self.notification_type == "main":
            self.root.geometry("360x260")
        else:  # warning
            self.root.geometry("380x220")

        self._position_window()

        # ドラッグ機能を追加
        self._add_drag_functionality()

        # 初期表示で前面に出す
        try:
            self.root.lift()
            self.root.focus_force()
        except Exception:
            pass

    def _position_window(self):
        """ウィンドウの位置を設定"""
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # すべて中央に表示
        # 現在のウィンドウサイズを取得
        try:
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            # winfo_width が 1 になることがあるため、geometry から推定
            if width <= 1 or height <= 1:
                geo = self.root.geometry()
                size_part = geo.split("+", 1)[0]
                width, height = map(int, size_part.split("x"))
        except Exception:
            # フォールバック（通知タイプ別の既定値）
            if self.notification_type == "pre":
                width, height = 300, 110
            elif self.notification_type == "main":
                width, height = 360, 260
            else:
                width, height = 380, 220

        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
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
        label = ttk.Label(frame, text=message, font=("Arial", 10), foreground="blue")
        label.pack(expand=True)

    def _setup_main_notification(self):
        """本通知の設定"""
        frame = ttk.Frame(self.root, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # タイトル
        title_label = ttk.Label(
            frame, text="タスクの時間です！", font=("Arial", 12, "bold")
        )
        title_label.pack(pady=(0, 10))

        # タスクリスト
        task_frame = ttk.Frame(frame)
        task_frame.pack(fill=tk.BOTH, expand=True)

        self.checkboxes = []
        for task_name in self.task["task_names"]:
            var = tk.BooleanVar()
            checkbox = ttk.Checkbutton(
                task_frame, text=task_name, variable=var, command=self._check_completion
            )
            checkbox.pack(anchor=tk.W, pady=2)
            self.checkboxes.append((task_name, var))

        # 完了ボタン（全チェック完了まで無効化）
        self.complete_button = ttk.Button(
            frame, text="完了", command=self._complete_tasks
        )
        self.complete_button.pack(pady=(10, 0))
        self.complete_button.configure(state=tk.DISABLED)

        # 初期状態では閉じられない
        self.can_close = False

    def _setup_warning_notification(self):
        """警告通知の設定"""
        frame = ttk.Frame(self.root, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # 警告メッセージ
        warning_label = ttk.Label(
            frame,
            text="⚠️ タスクが未完了です！",
            font=("Arial", 14, "bold"),
            foreground="red",
        )
        warning_label.pack(pady=(0, 10))

        # 全サブタスクのチェックボックスを表示（フィルタしない）
        task_list_frame = ttk.Frame(frame)
        task_list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.checkboxes = []
        for task_name in self.task.get("task_names", []):
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(
                task_list_frame,
                text=task_name,
                variable=var,
                command=self._check_completion,
            )
            cb.pack(anchor=tk.W, pady=2)
            self.checkboxes.append((task_name, var))

        # ボタン
        button_frame = ttk.Frame(frame)
        button_frame.pack()

        self.complete_button = ttk.Button(
            button_frame, text="完了", command=self._complete_tasks
        )
        self.complete_button.pack(side=tk.LEFT, padx=(0, 5))
        # 警告では1件以上チェックで有効化
        self.complete_button.configure(
            state=(
                tk.NORMAL
                if any(var.get() for _, var in self.checkboxes)
                else tk.DISABLED
            )
        )

        close_button = ttk.Button(
            button_frame, text="後で実行", command=self._close_warning
        )
        close_button.pack(side=tk.LEFT, padx=(5, 0))

    def _check_completion(self):
        """チェックボックスの状態を確認"""
        # 本通知: すべてチェックで完了可能
        if self.notification_type == "main":
            all_checked = all(var.get() for _, var in self.checkboxes)
            self.can_close = all_checked
            if self.complete_button:
                self.complete_button.configure(
                    state=(tk.NORMAL if all_checked else tk.DISABLED)
                )
        # 警告通知: 1件以上チェックで完了可能
        elif self.notification_type == "warning":
            any_checked = any(var.get() for _, var in self.checkboxes)
            if self.complete_button:
                self.complete_button.configure(
                    state=(tk.NORMAL if any_checked else tk.DISABLED)
                )

    def _complete_tasks(self):
        """タスク完了処理"""
        if self.notification_type == "main":
            # すべてチェックされていない場合は警告
            all_checked = all(var.get() for _, var in self.checkboxes)
            if not all_checked:
                from tkinter import messagebox

                messagebox.showwarning(
                    "未完了", "すべての項目にチェックを入れてください。"
                )
                return
            # チェックされたタスクをログに記録
            for task_name, var in self.checkboxes:
                if var.get():
                    self.task_manager.mark_task_completed(self.task["id"], task_name)
        elif self.notification_type == "warning":
            # 警告通知ではチェックされたものだけ記録
            any_checked = False
            for task_name, var in self.checkboxes:
                if var.get():
                    self.task_manager.mark_task_completed(self.task["id"], task_name)
                    any_checked = True
            if not any_checked:
                from tkinter import messagebox

                messagebox.showinfo("情報", "完了にチェックされた項目がありません。")
                return

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
