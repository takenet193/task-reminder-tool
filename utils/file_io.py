"""
ファイルI/Oユーティリティ
原子的書き込み機能を提供する
"""

import json
import logging
import os
import shutil
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def atomic_write_json(filepath: str, data: dict[str, Any] | list[Any]) -> None:
    """
    JSONファイルを原子的に書き込む

    Args:
        filepath: 書き込むファイルのパス
        data: 書き込むデータ（dictまたはlist）

    Raises:
        OSError: ファイル操作に失敗した場合
        ValueError: JSONエンコードに失敗した場合

    処理フロー:
    1. 既存ファイルがある場合はバックアップを作成（.bak）
    2. 一時ファイル（.tmp）にデータを書き込む
    3. 書き込み成功後、os.replace()で原子的にリネーム
    4. 成功したらバックアップを削除
    5. エラー時は一時ファイルを削除し、バックアップから復旧を試みる
    """
    filepath_obj = Path(filepath)
    backup_path = filepath_obj.with_suffix(filepath_obj.suffix + ".bak")
    temp_path = filepath_obj.with_suffix(filepath_obj.suffix + ".tmp")

    # 既存ファイルのバックアップを作成
    if filepath_obj.exists():
        try:
            shutil.copy2(filepath_obj, backup_path)
            logger.debug(f"バックアップを作成: {backup_path}")
        except OSError as e:
            logger.warning(f"バックアップ作成に失敗: {e}")
            # バックアップ作成失敗は続行（新規ファイルの可能性もある）

    # 一時ファイルに書き込み
    try:
        logger.debug(f"一時ファイルに書き込み開始: {temp_path}")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 原子的にリネーム（既存ファイルを置き換え）
        os.replace(temp_path, filepath_obj)
        logger.info(f"ファイルを原子的に書き込みました: {filepath_obj}")

        # 成功したらバックアップを削除
        if backup_path.exists():
            try:
                backup_path.unlink()
                logger.debug(f"バックアップを削除: {backup_path}")
            except OSError as e:
                logger.warning(f"バックアップ削除に失敗（無視）: {e}")

    except (OSError, ValueError, TypeError) as e:
        # エラー時は一時ファイルを削除
        if temp_path.exists():
            try:
                temp_path.unlink()
                logger.debug(f"一時ファイルを削除: {temp_path}")
            except OSError:
                pass

        # バックアップから復旧を試みる
        if backup_path.exists():
            try:
                shutil.copy2(backup_path, filepath_obj)
                logger.warning(f"バックアップから復旧しました: {filepath_obj}")
            except OSError as restore_error:
                logger.error(f"バックアップからの復旧に失敗: {restore_error}")

        # 元のエラーを再発生
        logger.error(f"ファイル書き込みに失敗: {filepath_obj}, エラー: {e}")
        raise
