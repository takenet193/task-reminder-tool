"""
ログ閲覧・月間達成率表示画面
タスク履歴と達成率グラフを表示するUI
"""
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Dict, Any, List
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from collections import defaultdict
import matplotlib.font_manager as fm

# 日本語フォントの設定
plt.rcParams['font.family'] = ['DejaVu Sans', 'Hiragino Sans', 'Yu Gothic', 'Meiryo', 'Takao', 'IPAexGothic', 'IPAPGothic', 'VL PGothic', 'Noto Sans CJK JP']

if TYPE_CHECKING:
    from task_manager import TaskManager


class LogWindow:
    def __init__(self, task_manager: 'TaskManager'):
        self.task_manager = task_manager
        self.root = None
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month
        
    def create_window(self):
        """ログ画面を作成"""
        self.root = tk.Toplevel()
        self.root.title("ログ・達成率")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        self._create_widgets()
        self._update_display()
        
    def _create_widgets(self):
        """ウィジェットを作成"""
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # タイトル
        title_label = ttk.Label(main_frame, text="ログ・達成率", 
                               font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # 月選択フレーム
        month_frame = ttk.Frame(main_frame)
        month_frame.grid(row=1, column=0, columnspan=2, pady=(0, 10), sticky=(tk.W, tk.E))
        
        ttk.Label(month_frame, text="表示月:").pack(side=tk.LEFT, padx=(0, 5))
        
        # 年選択
        self.year_var = tk.StringVar(value=str(self.current_year))
        year_combo = ttk.Combobox(month_frame, textvariable=self.year_var, width=8, state="readonly")
        year_combo['values'] = [str(year) for year in range(self.current_year - 1, self.current_year + 2)]
        year_combo.pack(side=tk.LEFT, padx=(0, 5))
        
        # 月選択
        self.month_var = tk.StringVar(value=str(self.current_month))
        month_combo = ttk.Combobox(month_frame, textvariable=self.month_var, width=8, state="readonly")
        month_combo['values'] = [str(month) for month in range(1, 13)]
        month_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # 更新ボタン
        update_button = ttk.Button(month_frame, text="更新", command=self._update_display)
        update_button.pack(side=tk.LEFT)
        
        # タブノートブック
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # タブ1: 月間達成率
        self.achievement_frame = ttk.Frame(notebook)
        notebook.add(self.achievement_frame, text="月間達成率")
        self._create_achievement_tab()
        
        # タブ2: 未達成率グラフ
        self.graph_frame = ttk.Frame(notebook)
        notebook.add(self.graph_frame, text="未達成率グラフ")
        self._create_graph_tab()
        
        # タブ3: 詳細ログ
        self.detail_frame = ttk.Frame(notebook)
        notebook.add(self.detail_frame, text="詳細ログ")
        self._create_detail_tab()
        
        # グリッドの重み設定
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
    def _create_achievement_tab(self):
        """月間達成率タブを作成"""
        # 達成率表示フレーム
        stats_frame = ttk.Frame(self.achievement_frame, padding="10")
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.achievement_label = ttk.Label(stats_frame, text="", font=("Arial", 16, "bold"))
        self.achievement_label.pack()
        
        # カレンダー表示フレーム
        calendar_frame = ttk.Frame(self.achievement_frame, padding="10")
        calendar_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(calendar_frame, text="カレンダー表示", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        self.calendar_text = tk.Text(calendar_frame, height=15, width=50)
        calendar_scrollbar = ttk.Scrollbar(calendar_frame, orient=tk.VERTICAL, command=self.calendar_text.yview)
        self.calendar_text.configure(yscrollcommand=calendar_scrollbar.set)
        
        self.calendar_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        calendar_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def _create_graph_tab(self):
        """未達成率グラフタブを作成"""
        # matplotlib の設定
        plt.style.use('default')
        
        # 日本語フォントの設定（Windows用）
        try:
            # フォントキャッシュをクリア
            fm._rebuild()
            
            # Windowsで利用可能な日本語フォントを試行
            available_fonts = [f.name for f in fm.fontManager.ttflist]
            japanese_fonts = ['Yu Gothic', 'Meiryo', 'MS Gothic', 'MS PGothic', 'Hiragino Sans']
            
            for font in japanese_fonts:
                if font in available_fonts:
                    plt.rcParams['font.family'] = font
                    plt.rcParams['font.sans-serif'] = [font]
                    break
            else:
                # フォールバック: システムデフォルトフォント
                plt.rcParams['font.family'] = 'DejaVu Sans'
        except:
            plt.rcParams['font.family'] = 'DejaVu Sans'
        
        # 図を作成
        self.fig = Figure(figsize=(8, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        
        # キャンバスを作成
        self.canvas = FigureCanvasTkAgg(self.fig, self.graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def _create_detail_tab(self):
        """詳細ログタブを作成"""
        # ログ表示フレーム
        log_frame = ttk.Frame(self.detail_frame, padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # ログリスト
        columns = ("日付", "時刻", "タスク名", "完了")
        self.log_tree = ttk.Treeview(log_frame, columns=columns, show="headings", height=15)
        
        # 列の設定
        self.log_tree.heading("日付", text="日付")
        self.log_tree.heading("時刻", text="時刻")
        self.log_tree.heading("タスク名", text="タスク名")
        self.log_tree.heading("完了", text="完了")
        
        self.log_tree.column("日付", width=100)
        self.log_tree.column("時刻", width=80)
        self.log_tree.column("タスク名", width=200)
        self.log_tree.column("完了", width=80)
        
        self.log_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # スクロールバー
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_tree.yview)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_tree.configure(yscrollcommand=log_scrollbar.set)
        
    def _update_display(self):
        """表示を更新"""
        year = int(self.year_var.get())
        month = int(self.month_var.get())
        
        self._update_achievement_tab(year, month)
        self._update_graph_tab()
        self._update_detail_tab(year, month)
        
    def _update_achievement_tab(self, year: int, month: int):
        """達成率タブを更新"""
        # その月のログを取得
        logs = self.task_manager.config.get_logs_by_month(year, month)
        
        # タスク設定を取得
        tasks = self.task_manager.config.load_tasks()
        enabled_tasks = [task for task in tasks if task.get("enabled", True)]
        
        # 月の日数を計算
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        last_day = (next_month - timedelta(days=1)).day
        
        # 各日の達成状況を計算
        daily_stats = {}
        for day in range(1, last_day + 1):
            date_str = f"{year:04d}-{month:02d}-{day:02d}"
            day_logs = [log for log in logs if log["date"] == date_str]
            
            # その日に設定されたタスク数を計算
            daily_tasks = 0
            for task in enabled_tasks:
                daily_tasks += len(task["task_names"])
            
            # 完了したタスク数を計算
            completed_tasks = len([log for log in day_logs if log["completed"]])
            
            daily_stats[day] = {
                "total": daily_tasks,
                "completed": completed_tasks,
                "rate": (completed_tasks / daily_tasks * 100) if daily_tasks > 0 else 0
            }
        
        # 月間達成率を計算
        total_tasks = sum(stats["total"] for stats in daily_stats.values())
        completed_tasks = sum(stats["completed"] for stats in daily_stats.values())
        achievement_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # 達成率表示を更新
        achievement_text = f"{year}年{month}月の達成率: {achievement_rate:.1f}% ({completed_tasks}/{total_tasks})"
        self.achievement_label.config(text=achievement_text)
        
        # カレンダー表示を更新
        self.calendar_text.delete(1.0, tk.END)
        calendar_text = f"{year}年{month}月のカレンダー\n\n"
        
        for day in range(1, last_day + 1):
            stats = daily_stats[day]
            if stats["total"] > 0:
                if stats["rate"] == 100:
                    status = "✓"
                    color = "green"
                elif stats["rate"] >= 50:
                    status = "△"
                    color = "orange"
                else:
                    status = "✗"
                    color = "red"
            else:
                status = "-"
                color = "gray"
            
            calendar_text += f"{day:2d}日: {status} ({stats['completed']}/{stats['total']})\n"
        
        self.calendar_text.insert(1.0, calendar_text)
        
    def _update_graph_tab(self):
        """グラフタブを更新"""
        # 過去12ヶ月のデータを取得
        months = []
        failure_rates = []
        
        for i in range(12):
            date = datetime.now() - timedelta(days=30 * i)
            year = date.year
            month = date.month
            
            logs = self.task_manager.config.get_logs_by_month(year, month)
            tasks = self.task_manager.config.load_tasks()
            enabled_tasks = [task for task in tasks if task.get("enabled", True)]
            
            # その月の日数を計算
            if month == 12:
                next_month = datetime(year + 1, 1, 1)
            else:
                next_month = datetime(year, month + 1, 1)
            last_day = (next_month - timedelta(days=1)).day
            
            # 未達成率を計算
            total_tasks = 0
            failed_tasks = 0
            
            for day in range(1, last_day + 1):
                date_str = f"{year:04d}-{month:02d}-{day:02d}"
                day_logs = [log for log in logs if log["date"] == date_str]
                
                for task in enabled_tasks:
                    total_tasks += len(task["task_names"])
                    completed_count = len([log for log in day_logs 
                                         if log["task_id"] == task["id"] and log["completed"]])
                    failed_tasks += len(task["task_names"]) - completed_count
            
            failure_rate = (failed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            months.insert(0, f"{year}-{month:02d}")
            failure_rates.insert(0, failure_rate)
        
        # グラフを描画
        self.ax.clear()
        self.ax.plot(months, failure_rates, marker='o', linewidth=2, markersize=6)
        
        # 日本語フォントを確実に適用
        try:
            self.ax.set_title('過去12ヶ月の未達成率', fontsize=14, fontweight='bold', fontfamily='Yu Gothic')
            self.ax.set_xlabel('月', fontsize=12, fontfamily='Yu Gothic')
            self.ax.set_ylabel('未達成率 (%)', fontsize=12, fontfamily='Yu Gothic')
        except:
            self.ax.set_title('過去12ヶ月の未達成率', fontsize=14, fontweight='bold')
            self.ax.set_xlabel('月', fontsize=12)
            self.ax.set_ylabel('未達成率 (%)', fontsize=12)
        self.ax.grid(True, alpha=0.3)
        self.ax.set_ylim(0, 100)
        
        # X軸のラベルを回転
        plt.setp(self.ax.get_xticklabels(), rotation=45, ha='right')
        
        # レイアウトを調整
        self.fig.tight_layout()
        self.canvas.draw()
        
    def _update_detail_tab(self, year: int, month: int):
        """詳細ログタブを更新"""
        # ツリービューをクリア
        for item in self.log_tree.get_children():
            self.log_tree.delete(item)
        
        # その月のログを取得
        logs = self.task_manager.config.get_logs_by_month(year, month)
        
        # 日付でソート
        logs.sort(key=lambda x: (x["date"], x["time"]))
        
        # ツリービューに追加
        for log in logs:
            status = "完了" if log["completed"] else "未完了"
            self.log_tree.insert("", "end", values=(
                log["date"],
                log["time"],
                log["task_name"],
                status
            ))
            
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
