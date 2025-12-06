---
description: Issueのフィジビリティチェック&アトミックチェックを行い、必要に応じて子Issue発行・関係設定
argument-hint: [issue-number]
---

# Issue #$ARGUMENTS のフィジビリティ&アトミックチェック

## Phase 1: Issue情報収集

### 1.1 対象Issue確認
```bash
gh issue view $ARGUMENTS --repo kkm-horikawa/wagtail-reusable-blocks
```

### 1.2 既存の親子・依存関係確認
```bash
# 親Issueの確認
gh api graphql -H "GraphQL-Features: sub_issues" -f query='
query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) {
    issue(number: $number) {
      parentIssue { number title state }
    }
  }
}' -f owner="kkm-horikawa" -f repo="wagtail-reusable-blocks" -F number=$ARGUMENTS

# 子Issueの確認
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

### 1.3 マイルストーン・プロジェクト確認
- Issueが属するマイルストーン
- GitHub Project (JOBMORE #3) のREADMEで全体方針確認

## Phase 2: フィジビリティチェック（実現可能性調査）

### 2.1 コードベース調査
- 関連する既存実装の有無
- 影響を受けるモジュール・ファイル
- 技術的制約の確認
- 既存パターンとの整合性

### 2.2 Web調査
- 類似機能の実装例
- 使用予定ライブラリの評価
- ベストプラクティス
- 既知の落とし穴・注意点

### 2.3 フィジビリティ判定
| 判定項目 | 状態 | 備考 |
|----------|------|------|
| 技術的に実現可能か | OK/NG/要調査 | |
| 既存システムとの整合性 | OK/NG/要調査 | |
| 依存ライブラリの成熟度 | OK/NG/要調査 | |
| 工数見積もり | 小/中/大 | |
| リスク | 低/中/高 | |

## Phase 3: アトミックチェック（粒度確認）

### 3.1 アトミックIssueの条件
以下をすべて満たす場合、アトミック（分割不要）:
- [ ] 単一の責務・目的
- [ ] 1つのPRで完結できる規模
- [ ] 独立してテスト可能
- [ ] レビュー可能な変更量（目安: 500行以下）

### 3.2 分割が必要な場合の分割基準
- **機能単位**: 独立した機能ごとに分割
- **レイヤー単位**: モデル → API → UI
- **依存順序**: 先に完了すべきものを先行Issue化

## Phase 4: 子Issue発行（分割が必要な場合）

### 4.1 子Issue作成
```bash
gh issue create --repo kkm-horikawa/wagtail-reusable-blocks \
  --title "タイトル" \
  --body "$(cat <<'EOF'
## 親Issue
#$ARGUMENTS の子Issue

## 概要
（このIssueで実現すること）

## 完了条件
- [ ] 条件1
- [ ] 条件2
EOF
)" \
  --milestone "マイルストーン名"
```

### 4.2 Sub-issue関係を設定
```bash
PARENT_ID=$(gh issue view $ARGUMENTS --repo kkm-horikawa/wagtail-reusable-blocks --json id --jq ".id")
CHILD_ID=$(gh issue view [子Issue番号] --repo kkm-horikawa/wagtail-reusable-blocks --json id --jq ".id")

gh api graphql -H "GraphQL-Features: sub_issues" -f query='
mutation($parentId: ID!, $childId: ID!) {
  addSubIssue(input: { issueId: $parentId, subIssueId: $childId }) {
    issue { title number }
    subIssue { title number }
  }
}' -f parentId="$PARENT_ID" -f childId="$CHILD_ID"
```

### 4.3 依存関係（Blocked by）を設定
子Issue間に依存がある場合:
```bash
ISSUE_ID=$(gh issue view [後続Issue番号] --repo kkm-horikawa/wagtail-reusable-blocks --json id --jq ".id")
BLOCKING_ID=$(gh issue view [先行Issue番号] --repo kkm-horikawa/wagtail-reusable-blocks --json id --jq ".id")

gh api graphql -H "GraphQL-Features: issue_types" -f query='
mutation($issueId: ID!, $blockingIssueId: ID!) {
  addBlockedBy(input: { issueId: $issueId, blockingIssueId: $blockingIssueId }) {
    issue { title number }
    blockingIssue { title number }
  }
}' -f issueId="$ISSUE_ID" -f blockingIssueId="$BLOCKING_ID"
```

## Phase 5: 元Issueの更新

### 5.1 フィジビリティ結果をコメント
```bash
gh issue comment $ARGUMENTS --repo kkm-horikawa/wagtail-reusable-blocks --body "$(cat <<'EOF'
## フィジビリティチェック結果

### 技術調査
（調査結果のサマリ）

### 判定
| 項目 | 結果 |
|------|------|
| 実現可能性 | OK |
| アトミック | OK / 分割済み |

### 子Issue（分割した場合）
- #xxx: タイトル
- #xxx: タイトル

### 依存関係
- #xxx は #xxx に依存（先に完了が必要）

### 次のステップ
`/implement $ARGUMENTS` で実装開始可能
EOF
)"
```

## Phase 6: 例外処理（実現不可・要検討の場合）

技術的に困難、または大きな設計判断が必要な場合はDiscussionを発行:

```bash
gh api graphql -f query='
mutation($repositoryId: ID!, $categoryId: ID!, $title: String!, $body: String!) {
  createDiscussion(input: {
    repositoryId: $repositoryId
    categoryId: $categoryId
    title: $title
    body: $body
  }) {
    discussion {
      url
      number
    }
  }
}' -f repositoryId="R_kgDOOnt_Iw" \
   -f categoryId="DIC_kwDOOnt_I84CzVON" \
   -f title="[検討] #$ARGUMENTS の実現方式について" \
   -f body="$(cat <<'EOF'
## 関連Issue
#$ARGUMENTS

## 背景
（Issueの内容要約）

## 課題
（実現が困難な理由、または判断が必要な点）

## 選択肢
### 案A
- メリット:
- デメリット:

### 案B
- メリット:
- デメリット:

## 検討依頼事項
- どの方式で進めるべきか
- 追加調査が必要な点
EOF
)"
```

その後、元Issueにリンク:
```bash
gh issue comment $ARGUMENTS --repo kkm-horikawa/wagtail-reusable-blocks --body "フィジビリティチェックの結果、検討が必要な点があります。Discussion #XXX を参照してください。"
```

## チェックリスト

- [ ] Issue内容を理解した
- [ ] コードベース調査完了
- [ ] Web調査完了（必要な場合）
- [ ] フィジビリティ判定完了
- [ ] アトミックチェック完了
- [ ] 子Issue発行（必要な場合）
- [ ] 親子関係設定（必要な場合）
- [ ] 依存関係設定（必要な場合）
- [ ] 元Issueに結果コメント
- [ ] Discussion発行（例外の場合）
