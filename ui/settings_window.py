"""
タスク設定画面
タスクの追加・編集・削除を行うUI
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from task_manager import TaskManager


class SettingsWindow:
    def __init__(self, task_manager: "TaskManager"):
        self.task_manager = task_manager
        self.root = None
        self.task_tree = None
        self.task_list = []

    def create_window(self):
        """設定画面を作成"""
        self.root = tk.Toplevel()
        self.root.title("タスク設定")
        self.root.geometry("600x400")
        self.root.resizable(True, True)

        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        self._create_widgets()
        self._load_tasks()

    def _create_widgets(self):
        """ウィジェットを作成"""
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # タイトル
        title_label = ttk.Label(
            main_frame, text="タスク設定", font=("Arial", 14, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))

        # タスク一覧
        ttk.Label(main_frame, text="登録済みタスク:").grid(
            row=1, column=0, sticky=tk.W, pady=(0, 5)
        )

        # ツリービュー
        columns = ("時間", "タスク名", "状態")
        self.task_tree = ttk.Treeview(
            main_frame, columns=columns, show="headings", height=10
        )

        # 列の設定
        self.task_tree.heading("時間", text="時間")
        self.task_tree.heading("タスク名", text="タスク名")
        self.task_tree.heading("状態", text="状態")

        self.task_tree.column("時間", width=80)
        self.task_tree.column("タスク名", width=400)
        self.task_tree.column("状態", width=80)

        self.task_tree.grid(
            row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10)
        )

        # スクロールバー
        scrollbar = ttk.Scrollbar(
            main_frame, orient=tk.VERTICAL, command=self.task_tree.yview
        )
        scrollbar.grid(row=2, column=3, sticky=(tk.N, tk.S))
        self.task_tree.configure(yscrollcommand=scrollbar.set)

        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=(10, 0))

        add_button = ttk.Button(button_frame, text="追加", command=self._add_task)
        add_button.grid(row=0, column=0, padx=(0, 5))

        edit_button = ttk.Button(button_frame, text="編集", command=self._edit_task)
        edit_button.grid(row=0, column=1, padx=5)

        delete_button = ttk.Button(button_frame, text="削除", command=self._delete_task)
        delete_button.grid(row=0, column=2, padx=5)

        refresh_button = ttk.Button(button_frame, text="更新", command=self._load_tasks)
        refresh_button.grid(row=0, column=3, padx=(5, 0))

        # グリッドの重み設定
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        main_frame.columnconfigure(0, weight=1)

    def _load_tasks(self):
        """タスク一覧を読み込み"""
        # ツリービューをクリア
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)

        # タスクを読み込み
        self.task_list = self.task_manager.config.load_tasks()

        # ツリービューに追加
        for task in self.task_list:
            task_names = ", ".join(task["task_names"])
            status = "有効" if task.get("enabled", True) else "無効"

            self.task_tree.insert("", "end", values=(task["time"], task_names, status))

    def _add_task(self):
        """新しいタスクを追加"""
        dialog = TaskDialog(self.root, "新しいタスクの追加")
        if dialog.result:
            time_str, task_names, enabled = dialog.result
            self.task_manager.config.add_task(time_str, task_names, enabled)
            self._load_tasks()
            messagebox.showinfo("完了", "タスクを追加しました。")

    def _edit_task(self):
        """選択されたタスクを編集"""
        selection = self.task_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "編集するタスクを選択してください。")
            return

        # 選択されたタスクのインデックスを取得
        item = selection[0]
        index = self.task_tree.index(item)
        task = self.task_list[index]

        dialog = TaskDialog(self.root, "タスクの編集", task)
        if dialog.result:
            time_str, task_names, enabled = dialog.result
            self.task_manager.config.update_task(
                task["id"], time_str, task_names, enabled
            )
            self._load_tasks()
            messagebox.showinfo("完了", "タスクを更新しました。")

    def _delete_task(self):
        """選択されたタスクを削除"""
        selection = self.task_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "削除するタスクを選択してください。")
            return

        # 確認ダイアログ
        if messagebox.askyesno("確認", "選択されたタスクを削除しますか？"):
            # 選択されたタスクのインデックスを取得
            item = selection[0]
            index = self.task_tree.index(item)
            task = self.task_list[index]

            self.task_manager.config.delete_task(task["id"])
            self._load_tasks()
            messagebox.showinfo("完了", "タスクを削除しました。")

    def _on_closing(self):
        """ウィンドウが閉じられる時の処理"""
        self.close_window()

    def close_window(self):
        """ウィンドウを閉じる"""
        if self.root:
            self.root.destroy()
            self.root = None

    def window_exists(self) -> bool:
        """ウィンドウが存在するかを確認"""
        return self.root is not None and self.root.winfo_exists()


class TaskDialog:
    def __init__(self, parent, title: str, task: dict = None):
        self.result = None
        self.parent = parent

        # ダイアログを作成
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # センターに配置
        self.dialog.geometry(
            "+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50)
        )

        self._create_widgets(task)

        # ダイアログの結果を待つ
        self.dialog.wait_window()

    def _create_widgets(self, task: dict = None):
        """ウィジェットを作成"""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 時刻設定
        ttk.Label(main_frame, text="時刻 (HH:MM):").grid(
            row=0, column=0, sticky=tk.W, pady=(0, 5)
        )
        self.time_var = tk.StringVar()
        time_entry = ttk.Entry(main_frame, textvariable=self.time_var, width=10)
        time_entry.grid(row=0, column=1, sticky=tk.W, pady=(0, 5))

        # タスク名設定
        ttk.Label(main_frame, text="タスク名 (複数設定可):").grid(
            row=1, column=0, sticky=(tk.W, tk.N), pady=(10, 5)
        )

        # タスク名リストボックス
        task_frame = ttk.Frame(main_frame)
        task_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 5))

        self.task_listbox = tk.Listbox(task_frame, height=8)
        self.task_listbox.grid(
            row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S)
        )

        task_scrollbar = ttk.Scrollbar(
            task_frame, orient=tk.VERTICAL, command=self.task_listbox.yview
        )
        task_scrollbar.grid(row=0, column=2, sticky=(tk.N, tk.S))
        self.task_listbox.configure(yscrollcommand=task_scrollbar.set)

        # タスク名入力
        self.task_entry = ttk.Entry(task_frame, width=30)
        self.task_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))

        add_task_button = ttk.Button(
            task_frame, text="追加", command=self._add_task_name
        )
        add_task_button.grid(row=1, column=1, padx=(5, 0), pady=(5, 0))

        remove_task_button = ttk.Button(
            task_frame, text="削除", command=self._remove_task_name
        )
        remove_task_button.grid(row=1, column=2, padx=(5, 0), pady=(5, 0))

        # 有効/無効設定
        self.enabled_var = tk.BooleanVar(value=True)
        enabled_check = ttk.Checkbutton(
            main_frame, text="タスクを有効にする", variable=self.enabled_var
        )
        enabled_check.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))

        # ボタン
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(20, 0))

        ok_button = ttk.Button(button_frame, text="OK", command=self._ok_clicked)
        ok_button.grid(row=0, column=0, padx=(0, 5))

        cancel_button = ttk.Button(
            button_frame, text="キャンセル", command=self._cancel_clicked
        )
        cancel_button.grid(row=0, column=1, padx=(5, 0))

        # グリッドの重み設定
        self.dialog.rowconfigure(0, weight=1)
        self.dialog.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        main_frame.columnconfigure(1, weight=1)
        task_frame.rowconfigure(0, weight=1)
        task_frame.columnconfigure(0, weight=1)

        # 既存タスクの場合は値を設定
        if task:
            self.time_var.set(task["time"])
            for task_name in task["task_names"]:
                self.task_listbox.insert(tk.END, task_name)
            self.enabled_var.set(task.get("enabled", True))

    def _add_task_name(self):
        """タスク名を追加"""
        task_name = self.task_entry.get().strip()
        if task_name:
            self.task_listbox.insert(tk.END, task_name)
            self.task_entry.delete(0, tk.END)

    def _remove_task_name(self):
        """選択されたタスク名を削除"""
        selection = self.task_listbox.curselection()
        if selection:
            self.task_listbox.delete(selection[0])

    def _ok_clicked(self):
        """OKボタンがクリックされた時の処理"""
        time_str = self.time_var.get().strip()
        if not time_str:
            messagebox.showerror("エラー", "時刻を入力してください。")
            return

        # 時刻フォーマットをチェック
        try:
            hour, minute = map(int, time_str.split(":"))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError
        except ValueError:
            messagebox.showerror("エラー", "時刻は HH:MM 形式で入力してください。")
            return

        task_names = [self.task_listbox.get(i) for i in range(self.task_listbox.size())]
        if not task_names:
            messagebox.showerror(
                "エラー", "少なくとも1つのタスク名を入力してください。"
            )
            return

        self.result = (time_str, task_names, self.enabled_var.get())
        self.dialog.destroy()

    def _cancel_clicked(self):
        """キャンセルボタンがクリックされた時の処理"""
        self.dialog.destroy()
