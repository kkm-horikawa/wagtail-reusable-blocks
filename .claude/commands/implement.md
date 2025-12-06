---
description: Issue番号から実装計画を立て、DraftPR作成→実装→テスト→PRオープンまで行う
argument-hint: [issue-number]
---

# Issue #$ARGUMENTS の実装

## Phase 1: 情報収集

### 1.1 Issue内容の確認
```bash
gh issue view $ARGUMENTS --repo kkm-horikawa/wagtail-reusable-blocks
```

### 1.2 親子関係・依存関係の確認
Sub-issues（子Issue）を確認:
```bash
gh api graphql -H "GraphQL-Features: sub_issues" -f query='
query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) {
    issue(number: $number) {
      subIssues(first: 20) {
        nodes { number title state }
      }
    }
  }
}' -f owner="kkm-horikawa" -f repo="wagtail-reusable-blocks" -F number=$ARGUMENTS
```

親Issue（このIssueが子の場合）を確認:
```bash
gh api graphql -H "GraphQL-Features: sub_issues" -f query='
query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) {
    issue(number: $number) {
      parentIssue { number title }
    }
  }
}' -f owner="kkm-horikawa" -f repo="wagtail-reusable-blocks" -F number=$ARGUMENTS
```

### 1.3 マイルストーン・プロジェクトREADME確認
- Issueが属するマイルストーンを確認
- GitHub Project (JOBMORE #3) のREADMEで全体方針を確認

### 1.4 関連ファイル・既存実装の調査
- 影響を受けるファイルを特定
- 既存のパターン・設計方針を把握
- CLAUDE.mdの開発ガイドラインを確認

## Phase 2: 実装計画

### 2.1 計画作成
以下を含む実装計画を作成:
- **目的**: 何を実現するか
- **変更ファイル一覧**: 新規/修正するファイル
- **実装ステップ**: 順序立てた作業項目
- **テスト方針**: 何をどうテストするか
- **リスク・注意点**: 既存機能への影響など

## Phase 3: Draft PR作成

### 3.1 ブランチ作成
```bash
git checkout -b issue-$ARGUMENTS-$(date +%Y%m%d)-<説明>
```

### 3.2 Draft PR作成
```bash
gh pr create --draft --title "WIP: #$ARGUMENTS タイトル" --body "$(cat <<'EOF'
## 関連Issue
Closes #$ARGUMENTS

## 概要
実装計画に基づく変更

## 変更内容
- [ ] 作業項目1
- [ ] 作業項目2

## テスト
- [ ] 単体テスト
- [ ] 統合テスト

---
Draft PR - 実装中
EOF
)"
```

## Phase 4: 実装

### 4.1 コーディング
- CONTRIBUTING.mdのガイドラインに従う

### 4.2 こまめなコミット
```bash
git add <files>
git commit --trailer "Github-Issue:#$ARGUMENTS" -m "feat/fix: 変更内容"
```

## Phase 5: PRオープン

### 5.1 Draft解除
テストがすべて通ったらDraftを解除:
```bash
gh pr ready
```

### 5.2 PR本文更新
```bash
gh pr edit --body "$(cat <<'EOF'
## 関連Issue
Closes #$ARGUMENTS

## 概要
（実装内容の説明）

## 変更内容
- 変更点1
- 変更点2

## テスト
- [x] 単体テスト通過
- [x] 型チェック通過
- [x] Lint通過
- [x] ビルド成功
EOF
)"
```

## 注意事項
- 依存先Issueが未完了の場合は先にそちらを実装
- 大きな変更は段階的にコミット
- 不明点があればIssueにコメントして確認
