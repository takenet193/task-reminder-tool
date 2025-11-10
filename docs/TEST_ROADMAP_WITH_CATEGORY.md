# テストロードマップ（カテゴリ対応）

- [x] テストタスク1（完了済み、Core） （実績: 2025-11-10）
- [ ] テストタスク2（計画済み、Core） （予定: 2025-11-15〜2025-11-16） （実績: 2025-11-14〜2025-11-15）
- [ ] テストタスク3（依存あり、Core） 依存: task-2 （予定: 2025-11-17〜2025-11-18）

- [ ] テストタスク4（Stretch、日付なし）
- [ ] テストタスク5（Stretch、日付あり） （予定: 2025-11-20〜2025-11-21） （実績: 2025-11-19〜2025-11-20）
- [ ] テストタスク6（Stretch、日付あり2） （予定: 2025-11-22〜2025-11-23）

## ガントチャート（コア完了 〜 2025-11-23）

```mermaid
gantt
  dateFormat  YYYY-MM-DD
  title Roadmap to 2025-11-23 (Core) + Stretch
  %% ===== Core Plan =====
  section Core Plan
  テストタスク2（計画済み、Core）  :2025-11-15, 2.0d
  テストタスク3（依存あり、Core）  :2025-11-17, 2.0d
  %% ===== Core Actual =====
  section Core Actual
  テストタスク1（完了済み、Core）  :crit, 2025-11-10, 1.0d
  テストタスク2（計画済み、Core）  :crit, 2025-11-14, 2.0d
  %% ===== Stretch Plan =====
  section Stretch Plan
  テストタスク5（Stretch、日付あり）  :2025-11-20, 2.0d
  テストタスク6（Stretch、日付あり2）  :2025-11-22, 2.0d
  %% ===== Stretch Actual =====
  section Stretch Actual
  テストタスク5（Stretch、日付あり）  :crit, 2025-11-19, 2.0d
```
