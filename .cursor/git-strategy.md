# Git戦略文書 - 定型作業支援ツール

## AI エージェント向けメタデータ

```json
{
  "project": {
    "name": "定型作業支援ツール",
    "id": "task-reminder-tool",
    "repository": "https://github.com/takenet193/task-reminder-tool"
  },
  "strategy": {
    "type": "hybrid",
    "description": "GitHub Flow + Git Flow elements",
    "approach": "Simple features → main, Complex features → develop → main"
  },
  "development": {
    "team_size": "individual",
    "purpose": "learning_and_development",
    "experience_level": "beginner_to_intermediate"
  },
  "metadata": {
    "last_updated": "2025-10-25",
    "version": "1.0",
    "status": "active"
  }
}
```

---

## ブランチ戦略

### ブランチの種類と役割

#### 1. main ブランチ
- **役割**: 本番環境用（常に安定した状態）
- **特徴**: デプロイ可能な状態を維持
- **更新頻度**: 機能完成時のみ

#### 2. develop ブランチ（オプション）
- **役割**: 統合テスト用
- **使用条件**: 複数機能を統合する時のみ使用
- **特徴**: 複数のfeatureブランチを統合してテスト

#### 3. feature/* ブランチ
- **役割**: 機能開発用（必須）
- **命名規則**: `feature/機能名` または `feature/機能名-詳細`
- **例**: `feature/mcp-integration`, `feature/ui-improvement`

#### 4. hotfix/* ブランチ
- **役割**: 緊急修正用
- **使用条件**: mainブランチの緊急バグ修正
- **特徴**: 即座にmainにマージ

## 使い分けルール

### パターン1: シンプルな機能追加
```
feature/new-feature → main
```
- **適用条件**: 単一機能、影響範囲が限定的
- **メリット**: シンプル、迅速
- **例**: UIの微調整、小さなバグ修正

### パターン2: 複数機能の統合
```
feature/feature-a → develop
feature/feature-b → develop
develop → main
```
- **適用条件**: 複数機能、相互依存、テストが必要
- **メリット**: 統合テスト、段階的リリース
- **例**: MCP統合のような大きな機能追加

### パターン3: 緊急修正
```
hotfix/critical-bug → main
```
- **適用条件**: 本番環境の緊急バグ
- **メリット**: 即座の修正
- **例**: セキュリティホール、重大なバグ

## ワークフロー

### 通常の開発フロー（GitHub Flow ベース）

#### 1. 機能開発の開始
```bash
# mainブランチから最新を取得
git checkout main
git pull origin main

# 新しいfeatureブランチを作成
git checkout -b feature/new-feature

# 開発開始
```

#### 2. 開発中の作業
```bash
# 変更をコミット
git add .
git commit -m "feat: 新しい機能を追加"

# 定期的にプッシュ
git push origin feature/new-feature
```

#### 3. 機能完成後のマージ
```bash
# プルリクエストを作成
# GitHub上でプルリクエスト: feature/new-feature → main

# マージ後、ローカルを更新
git checkout main
git pull origin main
git branch -d feature/new-feature
```

### 複雑な機能開発時のフロー（Git Flow 要素）

#### 1. developブランチの作成（初回のみ）
```bash
git checkout main
git checkout -b develop
git push origin develop
```

#### 2. 複数機能の開発
```bash
# 機能A
git checkout develop
git checkout -b feature/feature-a
# 開発・コミット・プッシュ

# 機能B
git checkout develop
git checkout -b feature/feature-b
# 開発・コミット・プッシュ
```

#### 3. developブランチへの統合
```bash
# プルリクエスト: feature/feature-a → develop
# プルリクエスト: feature/feature-b → develop

# developブランチで統合テスト
git checkout develop
git pull origin develop
```

#### 4. mainブランチへのリリース
```bash
# プルリクエスト: develop → main
# リリース後、developをmainと同期
git checkout develop
git merge main
git push origin develop
```

## コミットメッセージ規約

### Conventional Commits形式

#### 基本形式
```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

#### タイプ一覧
- **feat**: 新機能
- **fix**: バグ修正
- **docs**: ドキュメント変更
- **style**: コードスタイル変更（機能に影響なし）
- **refactor**: リファクタリング
- **test**: テスト追加・修正
- **chore**: ビルドプロセス、補助ツールの変更

#### 具体例
```bash
# 新機能
git commit -m "feat(mcp): GitHub連携機能を追加"

# バグ修正
git commit -m "fix(ui): 通知ウィンドウの表示位置を修正"

# ドキュメント
git commit -m "docs: READMEにMCP設定手順を追加"

# リファクタリング
git commit -m "refactor(config): 設定管理クラスを整理"

# テスト
git commit -m "test(task): タスク管理のテストケースを追加"

# その他
git commit -m "chore: 依存パッケージを更新"
```

## プルリクエストガイドライン

### プルリクエストテンプレート

#### タイトル
```
<type>: <簡潔な説明>
```

#### 説明テンプレート
```markdown
## 概要
このプルリクエストの目的と変更内容を簡潔に説明

## 変更内容
- [ ] 変更点1
- [ ] 変更点2
- [ ] 変更点3

## テスト
- [ ] 動作確認済み
- [ ] 既存機能に影響なし
- [ ] エラーなし

## 関連
- Issue #番号（該当する場合）
- 関連するプルリクエスト（該当する場合）
```

### レビューチェックリスト

#### コード品質
- [ ] コードが読みやすい
- [ ] 適切なコメントがある
- [ ] エラーハンドリングが適切
- [ ] パフォーマンスに問題なし

#### セキュリティ
- [ ] 機密情報が含まれていない
- [ ] セキュリティリスクがない
- [ ] 適切な権限設定

#### ドキュメント
- [ ] READMEが更新されている
- [ ] コメントが適切
- [ ] 変更履歴が記録されている

### マージ基準
1. **コードレビュー完了**
2. **テスト通過**
3. **ドキュメント更新**
4. **セキュリティチェック完了**

## 実践例：MCP統合プロジェクト

### 実際のブランチ運用
```bash
# 1. mainブランチから開始
git checkout main
git pull origin main

# 2. featureブランチを作成
git checkout -b feature/mcp-integration

# 3. 段階的なコミット
git commit -m "feat(mcp): MCP設定テンプレートを追加"
git commit -m "feat(mcp): GitHubトークン設定を追加"
git commit -m "feat(mcp): Cursor設定ファイルを作成"
git commit -m "refactor(mcp): 環境変数化でセキュリティ向上"
git commit -m "docs(mcp): Git戦略文書を追加"

# 4. プッシュ
git push origin feature/mcp-integration

# 5. プルリクエスト作成
# GitHub上で: feature/mcp-integration → main
```

### コミット履歴の良い例
```
3ad423d feat(mcp): 環境変数設定でセキュリティ向上
8870886 refactor(mcp): 個人データをGit管理から除外
8f4c53f feat(mcp): MCP設定とプロジェクトセットアップ
e687ded chore: 要件定義の後、とりあえず生成
```

## クイックリファレンス

### よく使うコマンド

#### ブランチ操作
```bash
# ブランチ一覧
git branch -a

# ブランチ作成・切り替え
git checkout -b feature/new-feature

# ブランチ切り替え
git checkout main

# ブランチ削除
git branch -d feature/old-feature
```

#### コミット・プッシュ
```bash
# 変更をステージング
git add .

# コミット
git commit -m "feat: 新機能を追加"

# プッシュ
git push origin feature/branch-name

# 強制プッシュ（注意して使用）
git push --force-with-lease origin feature/branch-name
```

#### マージ・リベース
```bash
# マージ
git merge feature/branch-name

# リベース（履歴を整理）
git rebase main

# インタラクティブリベース
git rebase -i HEAD~3
```

#### トラブルシューティング
```bash
# 変更を取り消し
git checkout -- filename

# コミットを取り消し
git reset --soft HEAD~1

# マージを取り消し
git reset --hard HEAD~1

# リモートの変更を取得
git fetch origin
git reset --hard origin/main
```

## 今後の運用方針

### 現在の状況（2025-10-25）
- `feature/mcp-integration`ブランチが完成
- プルリクエストが作成済み
- マージ待ちの状態

### 推奨する次のステップ
1. **プルリクエストをマージ**（feature/mcp-integration → main）
2. **developブランチを作成**（今後の複雑な機能開発用）
3. **この戦略文書を更新**（実践結果を反映）

### 学習ポイント
- GitHub Flowの基本をマスター
- Git Flowの概念を理解
- 状況に応じた戦略の使い分け
- コミットメッセージの重要性

---

**注意**: この文書は個人開発プロジェクト向けに最適化されています。チーム開発に移行する際は、より厳密なルールの追加を検討してください。
