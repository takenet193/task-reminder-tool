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
        self.root.geometry("600x400")
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
        update_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 週末除外チェックボックス
        self.exclude_weekends_var = tk.BooleanVar(value=self.task_manager.config.get_exclude_weekends())
        weekend_checkbox = ttk.Checkbutton(
            month_frame, 
            text="土日を達成率から除外", 
            variable=self.exclude_weekends_var,
            command=self._on_weekend_toggle
        )
        weekend_checkbox.pack(side=tk.LEFT)
        
        # タブノートブック
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # タブ1: 月間達成率
        self.achievement_frame = ttk.Frame(notebook)
        notebook.add(self.achievement_frame, text="月間達成率")
        self._create_achievement_tab()
        
        # タブ2: 対象日設定
        self.target_days_frame = ttk.Frame(notebook)
        notebook.add(self.target_days_frame, text="対象日設定")
        self._create_target_days_tab()
        
        # タブ3: 未達成率グラフ
        self.graph_frame = ttk.Frame(notebook)
        notebook.add(self.graph_frame, text="未達成率グラフ")
        self._create_graph_tab()
        
        # タブ4: 詳細ログ
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
        
        self.calendar_text = tk.Text(calendar_frame, height=25, width=60)
        calendar_scrollbar = ttk.Scrollbar(calendar_frame, orient=tk.VERTICAL, command=self.calendar_text.yview)
        self.calendar_text.configure(yscrollcommand=calendar_scrollbar.set)
        
        self.calendar_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        calendar_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _create_target_days_tab(self):
        """対象日設定タブを作成"""
        # 設定フレーム
        settings_frame = ttk.Frame(self.target_days_frame, padding="10")
        settings_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(settings_frame, text="対象日設定", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        # プリセットボタンフレーム
        preset_frame = ttk.Frame(settings_frame)
        preset_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(preset_frame, text="平日のみ選択", command=self._select_weekdays_only).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(preset_frame, text="土日除外をリセット", command=self._reset_weekend_exclusion).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(preset_frame, text="全日選択", command=self._select_all_days).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(preset_frame, text="全日解除", command=self._unselect_all_days).pack(side=tk.LEFT)
        
        # カレンダーグリッドフレーム
        calendar_grid_frame = ttk.Frame(settings_frame)
        calendar_grid_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # カレンダーグリッド用のスクロール可能なフレーム
        canvas_frame = tk.Frame(calendar_grid_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(canvas_frame, height=400)
        scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.calendar_grid_frame = scrollable_frame
        self.calendar_day_vars = {}  # {day: tk.BooleanVar}
    
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
        
        self._update_calendar_grid(year, month)
        self._update_achievement_tab(year, month)
        self._update_graph_tab()
        self._update_detail_tab(year, month)
    
    def _on_weekend_toggle(self):
        """週末除外チェックボックスの変更時の処理"""
        exclude = self.exclude_weekends_var.get()
        self.task_manager.config.set_exclude_weekends(exclude)
        # 表示を更新
        self._update_display()
    
    def _update_calendar_grid(self, year: int, month: int):
        """カレンダーグリッドを更新"""
        # 既存のウィジェットをクリア
        for widget in self.calendar_grid_frame.winfo_children():
            widget.destroy()
        self.calendar_day_vars.clear()
        
        # 月の日数を計算
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        last_day = (next_month - timedelta(days=1)).day
        
        # 現在のオーバーライド設定を取得
        month_overrides = self.task_manager.config.get_month_overrides(year, month)
        
        # カレンダーグリッドを作成（7列で配置）
        row = 0
        col = 0
        
        # 曜日ヘッダー
        weekdays = ["月", "火", "水", "木", "金", "土", "日"]
        for i, weekday in enumerate(weekdays):
            label = ttk.Label(self.calendar_grid_frame, text=weekday, width=8)
            label.grid(row=0, column=i, padx=2, pady=2)
        
        # 月の1日の曜日を取得して、配置開始位置を決定
        first_day = datetime(year, month, 1).date()
        first_day_weekday = first_day.weekday()  # 0=月曜日, 6=日曜日
        
        row = 1
        col = first_day_weekday  # 1日の曜日の位置から開始
        
        # 各日のチェックボックスを作成
        for day in range(1, last_day + 1):
            date_str = f"{year:04d}-{month:02d}-{day:02d}"
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            # デフォルト値を計算（オーバーライドを考慮せずに計算）
            exclude_weekends = self.task_manager.config.get_exclude_weekends()
            if exclude_weekends:
                weekday = date_obj.weekday()
                default_included = weekday < 5  # 0-4が月-金
            else:
                default_included = True
            
            # オーバーライドがある場合はそれを使用、ない場合はデフォルト値
            if date_str in month_overrides:
                included = month_overrides[date_str]
            else:
                included = default_included
            
            var = tk.BooleanVar(value=included)
            self.calendar_day_vars[day] = var
            
            # チェックボックスを作成
            checkbox = ttk.Checkbutton(
                self.calendar_grid_frame,
                text=f"{day}",
                variable=var,
                command=lambda d=day: self._on_day_toggle(year, month, d)
            )
            
            # 土日の場合は色分け
            weekday = date_obj.weekday()
            if weekday == 5:  # 土曜日
                checkbox.configure(style="Sat.TCheckbutton")
            elif weekday == 6:  # 日曜日
                checkbox.configure(style="Sun.TCheckbutton")
            
            checkbox.grid(row=row, column=col, padx=2, pady=2)
            
            col += 1
            if col >= 7:
                col = 0
                row += 1
    
    def _on_day_toggle(self, year: int, month: int, day: int):
        """日付チェックボックスの変更時の処理"""
        var = self.calendar_day_vars.get(day)
        if var is None:
            return
        
        included = var.get()
        
        # デフォルト値を取得（オーバーライドを考慮せずに計算）
        date_str = f"{year:04d}-{month:02d}-{day:02d}"
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        # オーバーライドを一時的に無視してデフォルト値を計算
        exclude_weekends = self.task_manager.config.get_exclude_weekends()
        if exclude_weekends:
            weekday = date_obj.weekday()
            default_included = weekday < 5  # 0-4が月-金
        else:
            default_included = True
        
        # 現在のオーバーライドを確認
        month_overrides = self.task_manager.config.get_month_overrides(year, month)
        has_override = date_str in month_overrides
        
        # デフォルト値と同じ場合で、オーバーライドが存在する場合は削除
        if included == default_included and has_override:
            # オーバーライドを削除（月別オーバーライドから該当日を削除）
            overrides = self.task_manager.config.load_calendar_overrides()
            month_key = f"{year:04d}-{month:02d}"
            if month_key in overrides and date_str in overrides[month_key]:
                del overrides[month_key][date_str]
                # 月のオーバーライドが空になったら削除
                if not overrides[month_key]:
                    del overrides[month_key]
                self.task_manager.config.save_calendar_overrides(overrides)
        elif included != default_included:
            # オーバーライドを設定
            self.task_manager.config.set_day_override(year, month, day, included)
        
        # 達成率表示を更新
        self._update_achievement_tab(year, month)
    
    def _select_weekdays_only(self):
        """平日のみ選択"""
        year = int(self.year_var.get())
        month = int(self.month_var.get())
        
        # 月の日数を計算
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        last_day = (next_month - timedelta(days=1)).day
        
        for day in range(1, last_day + 1):
            date_str = f"{year:04d}-{month:02d}-{day:02d}"
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            weekday = date_obj.weekday()
            
            # 平日（月-金）のみ選択
            included = weekday < 5
            var = self.calendar_day_vars.get(day)
            if var:
                var.set(included)
                self.task_manager.config.set_day_override(year, month, day, included)
        
        self._update_achievement_tab(year, month)
    
    def _reset_weekend_exclusion(self):
        """土日除外をリセット（デフォルトに戻す）"""
        year = int(self.year_var.get())
        month = int(self.month_var.get())
        
        # 月のオーバーライドをクリア
        self.task_manager.config.clear_month_overrides(year, month)
        
        # グリッドを更新
        self._update_calendar_grid(year, month)
        self._update_achievement_tab(year, month)
    
    def _select_all_days(self):
        """全日選択"""
        year = int(self.year_var.get())
        month = int(self.month_var.get())
        
        # 月の日数を計算
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        last_day = (next_month - timedelta(days=1)).day
        
        for day in range(1, last_day + 1):
            var = self.calendar_day_vars.get(day)
            if var:
                var.set(True)
                self.task_manager.config.set_day_override(year, month, day, True)
        
        self._update_achievement_tab(year, month)
    
    def _unselect_all_days(self):
        """全日解除"""
        year = int(self.year_var.get())
        month = int(self.month_var.get())
        
        # 月の日数を計算
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        last_day = (next_month - timedelta(days=1)).day
        
        for day in range(1, last_day + 1):
            var = self.calendar_day_vars.get(day)
            if var:
                var.set(False)
                self.task_manager.config.set_day_override(year, month, day, False)
        
        self._update_achievement_tab(year, month)
        
    def _update_achievement_tab(self, year: int, month: int):
        """達成率タブを更新"""
        # その月のログを取得
        logs = self.task_manager.config.get_logs_by_month(year, month)
        
        # タスク設定を取得
        tasks = self.task_manager.config.load_tasks()
        enabled_tasks = [task for task in tasks if task.get("enabled", True)]
        
        # 今日の日付を取得
        today = datetime.now().date()
        
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
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            day_logs = [log for log in logs if log["date"] == date_str]
            
            # その日に設定されたタスク数を計算
            # タスクが登録された日以降、かつ今日以前の日付のみを対象とする
            # さらに、is_date_includedで対象日かどうかをチェック
            if not self.task_manager.config.is_date_included(date_obj):
                # 対象外の日はスキップ
                daily_stats[day] = {
                    "total": 0,
                    "completed": 0,
                    "rate": 0
                }
                continue
            
            daily_tasks = 0
            for task in enabled_tasks:
                # タスクの登録日を取得
                task_created_date = self.task_manager.config.get_task_created_date(task)
                task_created = datetime.strptime(task_created_date, "%Y-%m-%d").date()
                
                # タスクが登録された日以降、かつ今日以前の場合のみカウント
                if task_created <= date_obj <= today:
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
        
        # 今日の日付を取得
        today = datetime.now().date()
        
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
                date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                day_logs = [log for log in logs if log["date"] == date_str]
                
                for task in enabled_tasks:
                    # タスクの登録日を取得
                    task_created_date = self.task_manager.config.get_task_created_date(task)
                    task_created = datetime.strptime(task_created_date, "%Y-%m-%d").date()
                    
                    # タスクが登録された日以降、かつ今日以前の場合のみカウント
                    # さらに、is_date_includedで対象日かどうかをチェック
                    if task_created <= date_obj <= today and self.task_manager.config.is_date_included(date_obj):
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
