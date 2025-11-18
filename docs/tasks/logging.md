# logging: ロギング導入タスク仕様

- **目的**: アプリ全体にロギング基盤を導入し、主要なイベント・エラーが記録されるようにする。
- **関連ID**: `logging`

## 要件概要

- アプリケーション全体で統一されたロギング機能を提供する
- 主要なイベント（タスク実行、エラー発生、設定変更など）を記録する
- ログレベルや出力先の設定を柔軟に変更できる
- トラブルシューティング時に有用な情報を提供する

## 実装計画

### アーキテクチャ

```
main.py (更新)
  └─ logging設定の初期化

各モジュール
  └─ logger = logging.getLogger(__name__)
  └─ 適切なログレベルでログ出力
```

### 実装手順

#### ステップ1: `main.py` にlogging設定を追加

アプリケーション起動時にロギング設定を初期化する。

**ファイルパス**: `main.py`

**実装内容**:

```python
import logging
import sys

# logging設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        # 必要に応じてファイルハンドラーも追加
        # logging.FileHandler('app.log', encoding='utf-8'),
    ]
)

logger = logging.getLogger(__name__)
```

**設定内容**:

- **ログレベル**: `INFO`（デフォルト）。必要に応じて `DEBUG` に変更可能
- **フォーマット**: タイムスタンプ、モジュール名、レベル、メッセージを含む
- **出力先**: 標準出力（コンソール）。必要に応じてファイルにも出力可能

#### ステップ2: 各モジュールでロガーを使用

主要なモジュールでログ出力を追加する。

**対象モジュール**:

1. **`config.py`**: ファイル読み書きの成功/失敗を記録
2. **`task_manager.py`**: タスク監視の開始/停止、通知の発火を記録
3. **`utils/file_io.py`**: 原子的書き込みの各ステップを記録（io-safetyタスクで実装）
4. **UIモジュール**: エラー発生時や重要な操作を記録

**実装例** (`config.py`):

```python
import logging

logger = logging.getLogger(__name__)

class Config:
    def save_tasks(self, tasks: list[dict[str, Any]]) -> None:
        """タスクデータを保存"""
        try:
            self._save_tasks(tasks)
            logger.info(f"タスクデータを保存しました: {len(tasks)}件")
        except Exception as e:
            logger.error(f"タスクデータの保存に失敗: {e}", exc_info=True)
            raise
```

**実装例** (`task_manager.py`):

```python
import logging

logger = logging.getLogger(__name__)

class TaskManager:
    def start_monitoring(self) -> None:
        """時刻監視を開始"""
        if not self.running:
            self.running = True
            logger.info("タスク監視を開始しました")
            # ...

    def _trigger_main_notification(self, task: dict[str, Any]) -> None:
        """本通知をトリガー"""
        logger.debug(f"本通知を発火: タスクID={task['id']}")
        # ...
```

#### ステップ3: エラーハンドリングでのログ出力

エラー発生時に詳細な情報を記録する。

**推奨パターン**:

```python
try:
    # 処理
    pass
except Exception as e:
    logger.error(f"エラーが発生しました: {e}", exc_info=True)
    # exc_info=True でスタックトレースも記録
    raise
```

## ログレベル

以下のログレベルを使用する：

- **DEBUG**: 詳細なデバッグ情報（開発時のみ）
- **INFO**: 一般的な情報（タスク実行、設定変更など）
- **WARNING**: 警告（バックアップ作成失敗など、処理は続行可能）
- **ERROR**: エラー（処理失敗、復旧を試みる）
- **CRITICAL**: 致命的なエラー（アプリケーションの継続が困難）

## ログ出力例

```
2025-11-19 10:30:15 - task_manager - INFO - タスク監視を開始しました
2025-11-19 10:30:25 - task_manager - DEBUG - 本通知を発火: タスクID=task_001
2025-11-19 10:30:30 - config - INFO - タスクデータを保存しました: 5件
2025-11-19 10:30:35 - utils.file_io - WARNING - バックアップ作成に失敗: Permission denied
2025-11-19 10:30:40 - config - ERROR - タスクデータの保存に失敗: Disk full
```

## 設定のカスタマイズ

将来的に、設定ファイルや環境変数からログレベルや出力先を変更できるようにする。

**将来の拡張案**:

```python
# config.py からログ設定を読み込む
log_level = settings.get("log_level", "INFO")
log_file = settings.get("log_file", None)

# logging設定を動的に変更
logging.getLogger().setLevel(getattr(logging, log_level))
if log_file:
    handler = logging.FileHandler(log_file, encoding='utf-8')
    logging.getLogger().addHandler(handler)
```

## 注意事項

1. **パフォーマンス**: ログ出力はパフォーマンスに影響を与える可能性があるため、過度なログ出力は避ける
2. **機密情報**: パスワードやトークンなどの機密情報はログに出力しない
3. **ログファイルの管理**: ファイルに出力する場合は、ログローテーションを検討する
4. **デバッグモード**: 開発時は `DEBUG` レベルで詳細な情報を取得できるようにする

## 実装チェックリスト

- [x] `main.py` にlogging設定を追加
- [x] `config.py` でログ出力を追加
- [x] `task_manager.py` でログ出力を追加
- [x] UIモジュールでエラーログを追加
- [x] 各モジュールで適切なログレベルを使用
- [x] エラー発生時にスタックトレースを記録
- [x] ログ出力の動作確認

## 参考資料

- Python公式ドキュメント: [loggingモジュール](https://docs.python.org/ja/3/library/logging.html)
- Python公式ドキュメント: [loggingのチュートリアル](https://docs.python.org/ja/3/howto/logging.html)
