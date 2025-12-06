---
description: リポジトリ&Web調査を行い、DiscussionまたはIssueを発行する
argument-hint: [調査テーマ]
---

# リサーチタスク: $ARGUMENTS

## 調査プロセス

### 1. 事前確認
- 既存のIssue/Discussion/PRで同様のテーマがないか確認
- 関連するマイルストーン、GitHub ProjectのREADMEを確認

### 2. コードベース調査
- 関連する既存実装を検索・分析
- 影響を受けるファイル・モジュールを特定
- 既存のパターンや設計方針を把握

### 3. Web調査
- 競合サービスの実装例
- ベストプラクティス
- 関連技術・ライブラリの調査

### 4. 調査結果のまとめ
以下の形式で整理:
- **現状**: 現在のコードベースの状態
- **課題/機会**: 解決すべき問題または実現したい機能
- **選択肢**: 考えられるアプローチ（メリット・デメリット付き）
- **推奨案**: 調査に基づく推奨アプローチ
- **次のステップ**: 具体的なアクションアイテム

### 5. 成果物の発行

調査結果に基づいて適切な形式で発行:

**Discussionを作成する場合**（設計検討・意思決定が必要な場合）:

カテゴリID一覧:
- Ideas: `DIC_kwDOOnt_I84CzVON`
- General: `DIC_kwDOOnt_I84CzVOL`
- Q&A: `DIC_kwDOOnt_I84CzVOM`
- knowledge: `DIC_kwDOOnt_I84CzVOQ`

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
}' -f repositoryId="R_kgDOOnt_Iw" -f categoryId="DIC_kwDOOnt_I84CzVON" -f title="タイトル" -f body="本文"
```

**Issueを作成する場合**（具体的なタスクが明確な場合）:
```bash
gh issue create --repo kkm-horikawa/wagtail-reusable-blocks \
  --title "タイトル" \
  --body "Issue本文" \
  --label "適切なラベル"
```

## 注意事項
- 調査中に発見した関連Issueはリンクで参照する
- 不明点は明示的に「要確認」として記載
- 技術的な判断には根拠を添える
