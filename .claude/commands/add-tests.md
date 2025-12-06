---
description: Issue番号に紐づくDraft PRにテストを追加し、実行・修正・PR本文更新まで行う
argument-hint: [issue-number]
---

# Issue #$ARGUMENTS のテスト追加

## Phase 1: 情報収集

### 1.1 Issue内容の確認
```bash
gh issue view $ARGUMENTS --repo kkm-horikawa/wagtail-reusable-blocks
```

### 1.2 関連PRの確認
```bash
gh pr list --search "head:issue-$ARGUMENTS" --repo kkm-horikawa/wagtail-reusable-blocks
```

または:
```bash
gh pr list --search "#$ARGUMENTS" --repo kkm-horikawa/wagtail-reusable-blocks
```

### 1.3 マイルストーン・プロジェクトREADME確認
- GitHub Project (JOBMORE #3) のREADMEでビジネス要件を確認
- 関連Issueの要件を確認
- ユーザーストーリーや受け入れ条件を把握

### 1.4 既存実装の確認
PRの変更内容を確認:
```bash
gh pr diff <pr-number>
```

## Phase 2: テストケース設計

### 2.1 ハッピーパス（正常系）
- 基本的な成功シナリオ
- 主要なユースケース
- 期待される正常な入出力

### 2.2 エッジケース
- 境界値（最小値、最大値、空、null）
- 異常入力（不正な型、範囲外の値）
- 同時実行・競合状態
- 権限境界（認証なし、権限不足）
- データ依存（存在しないID、削除済みデータ）

### 2.3 テストケースマトリクス作成
| ケース | 入力 | 期待結果 | カテゴリ |
|--------|------|----------|----------|
| 正常系1 | ... | ... | ハッピーパス |
| 境界値1 | ... | ... | エッジケース |
| 異常系1 | ... | ... | エラーハンドリング |

## Phase 3: テスト実装

### 3.1 バックエンドテスト（pytest）
テストファイルの配置:
- `core/apps/<app>/tests/test_<module>.py`
- または `tests/<app>/test_<module>.py`

```python
import pytest
from django.test import TestCase

class TestFeatureName(TestCase):
    def setUp(self):
        # テストデータ準備
        pass

    def test_happy_path_description(self):
        """正常系: 説明"""
        pass

    def test_edge_case_description(self):
        """エッジケース: 説明"""
        pass
```

### 3.2 フロントエンドテスト（Vitest）
テストファイルの配置:
- `frontend/src/**/*.test.ts`
- `frontend/src/**/*.test.tsx`

```typescript
import { describe, it, expect } from 'vitest';

describe('FeatureName', () => {
  it('should handle happy path', () => {
    // テスト
  });

  it('should handle edge case', () => {
    // テスト
  });
});
```

## Phase 4: テスト実行・修正

### 4.1 バックエンドテスト実行
```bash
uv run pytest -n auto -v --tb=short
uv run pytest tests/path/to/test_file.py -v  # 特定ファイル
uv run pytest -k "test_name" -v              # 特定テスト
```

### 4.2 フロントエンドテスト実行
```bash
npm run test:fast
npm run test:run -- path/to/test.test.ts  # 特定ファイル
```

### 4.3 失敗時の修正サイクル
1. エラーメッセージを確認
2. 実装またはテストを修正
3. 再実行
4. 全テスト通過まで繰り返し

## Phase 5: PR更新

### 5.1 テストをコミット
```bash
git add <test-files>
git commit --trailer "Github-Issue:#$ARGUMENTS" -m "test: テスト追加の説明"
```

### 5.2 プッシュ
```bash
git push
```

### 5.3 PR本文にテスト状況を記載
```bash
gh pr edit <pr-number> --body "$(cat <<'EOF'
## 関連Issue
Closes #$ARGUMENTS

## 概要
（実装内容の説明）

## テスト状況

### バックエンド
- [x] pytest 全テスト通過
- [x] pyright 型チェック通過
- [x] ruff lint通過

### フロントエンド
- [x] vitest 全テスト通過
- [x] tsc 型チェック通過
- [x] biome lint通過
- [x] ビルド成功

### テストカバレッジ
| カテゴリ | ケース数 | 状態 |
|----------|----------|------|
| ハッピーパス | X | 通過 |
| エッジケース | X | 通過 |
| エラーハンドリング | X | 通過 |

### 追加したテスト
- `tests/path/to/test_file.py`
  - `test_happy_path_xxx`
  - `test_edge_case_xxx`
- `frontend/src/xxx.test.ts`
  - `should handle xxx`
EOF
)"
```

## 注意事項
- テストは実装と同じ品質基準で書く
- モックは必要最小限に
- テスト名は何をテストしているか明確に
- 既存テストを壊さないこと
