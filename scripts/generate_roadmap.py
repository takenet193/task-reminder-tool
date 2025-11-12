#!/usr/bin/env python3
"""
JSONファイルからMarkdownロードマップを自動生成するスクリプト

使い方:
    # デフォルト（plan.json → ROADMAP.md）
    python scripts/generate_roadmap.py

    # カスタム指定
    python scripts/generate_roadmap.py --input .cursor/future-tasks.json --output docs/FUTURE_TASKS.md
"""

import argparse
import json
from datetime import datetime
from pathlib import Path


def load_plan_json(plan_path: Path) -> dict:
    """plan.jsonを読み込む"""
    try:
        with open(plan_path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"plan.jsonが見つかりません: {plan_path}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"plan.jsonの形式が不正です: {e}") from e


def calculate_duration(start_date: str, end_date: str) -> float:
    """開始日と終了日から日数を計算"""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        delta = (end - start).days + 1  # 両端を含む
        return max(1.0, delta)  # 最低1日
    except ValueError:
        return 1.0


def categorize_tasks(items: list[dict]) -> dict[str, list[dict]]:
    """
    タスクをCore/Stretchに分類

    優先順位:
    1. categoryフィールドが明示的に指定されている場合はそれを使用
    2. categoryがない場合は従来のロジック:
       - Core: completed, planned（start_dateあり）, pendingだがstart_dateがある
       - Stretch: pendingでstart_dateがない
    """
    core = []
    stretch = []

    for item in items:
        # categoryフィールドが明示的に指定されている場合
        category = item.get("category")
        if category:
            if category.lower() == "core":
                core.append(item)
            elif category.lower() == "stretch":
                stretch.append(item)
            # その他の値は無視して従来ロジックにフォールバック
            continue

        # categoryがない場合は従来のロジック
        status = item.get("status", "pending")
        start_date = item.get("start_date")

        # Core判定
        if status == "completed":
            core.append(item)
        elif start_date:  # plannedまたはpendingだがstart_dateがある
            core.append(item)
        elif status == "pending":
            stretch.append(item)
        # futureは除外（FUTURE_TASKS.mdで管理）

    return {"core": core, "stretch": stretch}


def format_task_markdown(item: dict) -> str:
    """単一タスクをMarkdown形式に変換"""
    # チェックボックス
    checkbox = "[x]" if item.get("status") == "completed" else "[ ]"

    # タイトル
    title = item.get("title", "")

    # 依存関係
    deps = item.get("deps", [])
    dep_str = ""
    if deps:
        # 依存関係のIDを人間が読める形式に変換（必要に応じて）
        dep_list = ", ".join(deps)
        dep_str = f" 依存: {dep_list}"

    # 予定日
    start_date = item.get("start_date")
    end_date = item.get("end_date")
    date_str = ""
    if start_date and end_date:
        if start_date == end_date:
            date_str = f" （予定: {start_date}）"
        else:
            date_str = f" （予定: {start_date}〜{end_date}）"
    elif start_date:
        date_str = f" （予定: {start_date}）"

    # 実績日
    actual_start_date = item.get("actual_start_date")
    actual_end_date = item.get("actual_end_date")
    actual_date_str = ""
    if actual_start_date and actual_end_date:
        if actual_start_date == actual_end_date:
            actual_date_str = f" （実績: {actual_start_date}）"
        else:
            actual_date_str = f" （実績: {actual_start_date}〜{actual_end_date}）"
    elif actual_start_date:
        actual_date_str = f" （実績: {actual_start_date}）"

    # 追加情報（target_coverageなど）
    extra_info = ""
    if "target_coverage" in item:
        extra_info = f"／{item['target_coverage']}"

    return f"- {checkbox} {title}{dep_str}{date_str}{actual_date_str}{extra_info}"


def generate_gantt_chart(categorized: dict[str, list[dict]]) -> list[str]:
    """Mermaidガントチャートを生成（計画と実績の両方を表示）"""
    # 最新の終了日を計算（実績日付と計画日付の両方を考慮）
    max_end_date = None
    all_items = categorized["core"] + categorized["stretch"]
    for item in all_items:
        actual_end_date = item.get("actual_end_date")
        end_date = item.get("end_date")

        # 両方の日付をチェック
        for date_to_check in [actual_end_date, end_date]:
            if date_to_check:
                if max_end_date is None or date_to_check > max_end_date:
                    max_end_date = date_to_check

    # タイトルを動的に生成
    if max_end_date:
        gantt_title = f"Roadmap to {max_end_date} (Core) + Stretch"
        section_title = f"ガントチャート（コア完了 〜 {max_end_date}）"
    else:
        gantt_title = "Roadmap (Core) + Stretch"
        section_title = "ガントチャート"

    lines = [
        f"## {section_title}",
        "",
        "```mermaid",
        "gantt",
        "  dateFormat  YYYY-MM-DD",
        f"  title {gantt_title}",
        "  %% ===== Core Plan =====",
        "  section Core Plan",
    ]

    # Coreタスク（計画）
    for item in categorized["core"]:
        start_date = item.get("start_date")
        end_date = item.get("end_date")
        if start_date and end_date:
            title = item.get("title", "")
            duration = calculate_duration(start_date, end_date)
            lines.append(f"  {title}  :{start_date}, {duration:.1f}d")

    # Coreタスク（実績）- 実績日付があるもののみ
    # actual_start_dateがあるタスクを検出（actual_end_dateがある場合も、ない場合も含む）
    has_core_actual = any(item.get("actual_start_date") for item in categorized["core"])
    if has_core_actual:
        lines.extend(
            [
                "  %% ===== Core Actual =====",
                "  section Core Actual",
            ]
        )
        today = datetime.now().strftime("%Y-%m-%d")
        for item in categorized["core"]:
            actual_start_date = item.get("actual_start_date")
            actual_end_date = item.get("actual_end_date")
            if actual_start_date:
                title = item.get("title", "")
                # 終了日がある場合はその日まで、ない場合は今日まで
                end_date_for_calc = actual_end_date if actual_end_date else today
                duration = calculate_duration(actual_start_date, end_date_for_calc)
                # 進捗率を取得して表示
                progress_perc = item.get("progress_perc", 0) or 0
                lines.append(
                    f"  {title} ({progress_perc}%)  :crit, {actual_start_date}, {duration:.1f}d"
                )

    # Stretchタスク（計画）
    lines.extend(
        [
            "  %% ===== Stretch Plan =====",
            "  section Stretch Plan",
        ]
    )

    for item in categorized["stretch"]:
        start_date = item.get("start_date")
        end_date = item.get("end_date")
        if start_date and end_date:
            title = item.get("title", "")
            duration = calculate_duration(start_date, end_date)
            lines.append(f"  {title}  :{start_date}, {duration:.1f}d")
        elif not start_date and not end_date:
            # start_dateがないStretchタスクはコメントとして追加
            title = item.get("title", "")
            lines.append(f"  %% {title} (日付未定)")

    # Stretchタスク（実績）- 実績日付があるもののみ
    # actual_start_dateがあるタスクを検出（actual_end_dateがある場合も、ない場合も含む）
    has_stretch_actual = any(
        item.get("actual_start_date") for item in categorized["stretch"]
    )
    if has_stretch_actual:
        lines.extend(
            [
                "  %% ===== Stretch Actual =====",
                "  section Stretch Actual",
            ]
        )
        today = datetime.now().strftime("%Y-%m-%d")
        for item in categorized["stretch"]:
            actual_start_date = item.get("actual_start_date")
            actual_end_date = item.get("actual_end_date")
            if actual_start_date:
                title = item.get("title", "")
                # 終了日がある場合はその日まで、ない場合は今日まで
                end_date_for_calc = actual_end_date if actual_end_date else today
                duration = calculate_duration(actual_start_date, end_date_for_calc)
                # 進捗率を取得して表示
                progress_perc = item.get("progress_perc", 0) or 0
                lines.append(
                    f"  {title} ({progress_perc}%)  :crit, {actual_start_date}, {duration:.1f}d"
                )

    lines.extend(
        [
            "```",
            "",
        ]
    )

    return lines


def generate_roadmap_markdown(
    plan_data: dict, output_path: Path, title: str = "Roadmap"
) -> None:
    """ROADMAP.mdを生成"""
    items = plan_data.get("items", [])
    categorized = categorize_tasks(items)

    lines = [f"# {title}", ""]

    # Coreタスク
    if categorized["core"]:
        for item in categorized["core"]:
            lines.append(format_task_markdown(item))
        lines.append("")

    # Stretchタスク
    if categorized["stretch"]:
        for item in categorized["stretch"]:
            lines.append(format_task_markdown(item))
        lines.append("")

    # ガントチャート（Core/Stretchがある場合のみ）
    if categorized["core"] or categorized["stretch"]:
        lines.extend(generate_gantt_chart(categorized))

    # ファイル書き込み
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="JSONファイルからMarkdownロードマップを生成"
    )
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default=".cursor/plan.json",
        help="入力JSONファイル（デフォルト: .cursor/plan.json）",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="docs/ROADMAP.md",
        help="出力Markdownファイル（デフォルト: docs/ROADMAP.md）",
    )
    parser.add_argument(
        "--title",
        "-t",
        type=str,
        default=None,
        help="Markdownのタイトル（デフォルト: ファイル名から自動生成）",
    )

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    plan_path = project_root / args.input
    output_path = project_root / args.output

    # タイトルが指定されていない場合は出力ファイル名から生成
    if args.title is None:
        title = output_path.stem.replace("_", " ").title()
    else:
        title = args.title

    try:
        plan_data = load_plan_json(plan_path)
        generate_roadmap_markdown(plan_data, output_path, title)
        print(f"[OK] Generated {output_path.relative_to(project_root)}")
        return 0
    except Exception as e:
        print(f"[ERROR] {e}", file=__import__("sys").stderr)
        return 1


if __name__ == "__main__":
    exit(main())
