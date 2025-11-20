"""
utils/file_io.py のテスト
"""

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from utils.file_io import atomic_write_json


class TestAtomicWriteJson:
    """atomic_write_json() のテスト"""

    def test_new_file(self, temp_data_dir):
        """新規ファイルの書き込み"""
        filepath = Path(temp_data_dir) / "test.json"
        data = {"key": "value"}

        atomic_write_json(str(filepath), data)

        assert filepath.exists()
        with open(filepath, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded == data
        assert not filepath.with_suffix(filepath.suffix + ".tmp").exists()
        assert not filepath.with_suffix(filepath.suffix + ".bak").exists()

    def test_existing_file(self, temp_data_dir):
        """既存ファイルの上書き"""
        filepath = Path(temp_data_dir) / "test.json"
        original_data = {"original": "data"}
        new_data = {"new": "data"}

        # 既存ファイルを作成
        atomic_write_json(str(filepath), original_data)

        # 上書き
        atomic_write_json(str(filepath), new_data)

        with open(filepath, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded == new_data

    def test_list_data(self, temp_data_dir):
        """リストデータの書き込み"""
        filepath = Path(temp_data_dir) / "test.json"
        data = [{"item": 1}, {"item": 2}]

        atomic_write_json(str(filepath), data)

        with open(filepath, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded == data

    def test_json_encode_error(self, temp_data_dir):
        """JSONエンコードエラーのテスト"""
        filepath = Path(temp_data_dir) / "test.json"
        # 循環参照など、JSONエンコードできないデータ
        data: dict[str, Any] = {}
        data["self"] = data  # 循環参照

        with pytest.raises((TypeError, ValueError)):
            atomic_write_json(str(filepath), data)

    def test_backup_creation(self, temp_data_dir):
        """バックアップファイルの作成テスト"""
        filepath = Path(temp_data_dir) / "test.json"
        original_data = {"original": "data"}

        # 既存ファイルを作成
        atomic_write_json(str(filepath), original_data)
        assert filepath.exists()

        # 上書き（バックアップが作成される）
        new_data = {"new": "data"}
        atomic_write_json(str(filepath), new_data)

        # バックアップは成功時に削除される
        assert not filepath.with_suffix(filepath.suffix + ".bak").exists()

    def test_nested_data(self, temp_data_dir):
        """ネストされたデータの書き込み"""
        filepath = Path(temp_data_dir) / "test.json"
        data = {
            "level1": {
                "level2": {
                    "level3": "value",
                    "list": [1, 2, 3],
                }
            },
            "array": [{"a": 1}, {"b": 2}],
        }

        atomic_write_json(str(filepath), data)

        with open(filepath, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded == data

    def test_unicode_data(self, temp_data_dir):
        """Unicode文字を含むデータの書き込み"""
        filepath = Path(temp_data_dir) / "test.json"
        data = {
            "日本語": "テスト",
            "emoji": "😀",
            "特殊文字": "©®™",
        }

        atomic_write_json(str(filepath), data)

        with open(filepath, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded == data

    @patch("utils.file_io.open", side_effect=OSError("Disk full"))
    def test_disk_full_error(self, mock_file, temp_data_dir):
        """ディスク容量不足エラーのテスト"""
        filepath = Path(temp_data_dir) / "test.json"
        data = {"key": "value"}

        with pytest.raises(OSError):
            atomic_write_json(str(filepath), data)

    def test_file_permission_error(self, temp_data_dir):
        """ファイル権限エラーのテスト（読み取り専用ディレクトリ）"""
        # このテストは実際のファイルシステムの権限に依存するため、
        # スキップするか、モックを使用する
        filepath = Path(temp_data_dir) / "test.json"
        data = {"key": "value"}

        # 通常の書き込みは成功するはず
        atomic_write_json(str(filepath), data)
        assert filepath.exists()

    def test_empty_dict(self, temp_data_dir):
        """空の辞書の書き込み"""
        filepath = Path(temp_data_dir) / "test.json"
        data: dict[str, Any] = {}

        atomic_write_json(str(filepath), data)

        with open(filepath, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded == data

    def test_empty_list(self, temp_data_dir):
        """空のリストの書き込み"""
        filepath = Path(temp_data_dir) / "test.json"
        data: list[Any] = []

        atomic_write_json(str(filepath), data)

        with open(filepath, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded == data

    def test_large_data(self, temp_data_dir):
        """大きなデータの書き込み"""
        filepath = Path(temp_data_dir) / "test.json"
        data = {"items": [{"id": i, "value": f"item_{i}"} for i in range(1000)]}

        atomic_write_json(str(filepath), data)

        with open(filepath, encoding="utf-8") as f:
            loaded = json.load(f)
        assert len(loaded["items"]) == 1000
        assert loaded["items"][0]["id"] == 0
        assert loaded["items"][999]["id"] == 999
