# 🚀 美容師向けブログ自動投稿システム - 本番実装ガイド

## 📋 実装前チェックリスト

### ✅ システム準備完了項目
- [x] YouTube連携機能（@shiki_138）
- [x] 美容師特化テーマ生成器
- [x] Gemini API画像生成機能
- [x] 内部リンク自動生成
- [x] WordPress投稿システム
- [x] GitHub Actions自動実行

## 🔧 あなたが実行すべき手順

### ステップ1: GitHubリポジトリ作成
```bash
# 1. GitHubでリポジトリ作成
# - リポジトリ名: BlogAuto または任意の名前
# - プライベートリポジトリ推奨

# 2. ローカルからpush
git init
git add .
git commit -m "Initial commit: 美容師向けブログ自動投稿システム"
git branch -M main
git remote add origin https://github.com/[ユーザー名]/[リポジトリ名].git
git push -u origin main
```

### ステップ2: GitHub Secrets設定（重要）
GitHubリポジトリの Settings > Secrets and variables > Actions で以下を設定：

#### 必須設定
```
WP_USER: invast51@
WP_APP_PASS: Ikyosai51
WP_SITE_URL: https://invest-master.net/
WP_STATUS: draft
```

#### API Keys（取得後設定）
```
GEMINI_API_KEY: [Google AI StudioでAPIキー取得]
OPENAI_API_KEY: [OpenAIでAPIキー取得]（オプション）
```

### ステップ3: APIキー取得方法

#### Google Gemini API（推奨・無料枠大）
1. https://makersuite.google.com/app/apikey にアクセス
2. Googleアカウントでログイン
3. 「Create API Key」をクリック
4. 生成されたキーをGitHub Secretsの `GEMINI_API_KEY` に設定

#### OpenAI API（オプション）
1. https://platform.openai.com/api-keys にアクセス
2. 「Create new secret key」をクリック
3. 生成されたキーをGitHub Secretsの `OPENAI_API_KEY` に設定

### ステップ4: 自動実行確認
```bash
# GitHub Actionsページで確認
# - Actions タブをクリック
# - "Daily Blog Automation" ワークフローを確認
# - 毎日09:00 JST に自動実行されることを確認
```

### ステップ5: 手動テスト実行
```bash
# GitHubリポジトリで手動実行
# 1. Actions タブ > Daily Blog Automation
# 2. "Run workflow" ボタンをクリック
# 3. "Run workflow" で実行
# 4. invest-master.net の下書きに記事が投稿されることを確認
```

## 🎯 実装後の運用

### 自動投稿スケジュール
- **毎日09:00 JST**: 自動記事生成・投稿
- **投稿先**: https://invest-master.net/
- **ステータス**: 下書き保存（手動で公開可能）

### コンテンツ内容
- **美容師・サロン経営者向け**心理学・マーケティング記事
- **2000-3000文字**の高品質コンテンツ
- **Instagram集客・AI活用・心理学理論**を含む実践的内容
- **YouTube動画（@shiki_138）**との連携コンテンツ

### 記事カテゴリ例
1. 美容師向け心理学・行動経済学
2. Instagram/TikTok集客戦略
3. 生成AI活用術（ChatGPT/Claude/Gemini）
4. 求人・人材育成ノウハウ
5. 地域密着マーケティング

## 🔧 カスタマイズ方法

### テーマ変更
```bash
# prompts/beauty_business_themes.txt でテーマを編集
# 新しいテーマを追加・既存テーマを修正可能
```

### 投稿スケジュール変更
```bash
# .github/workflows/daily-blog.yml の cron 設定を変更
# 例: '0 0 * * *' → '0 12 * * *' (21:00 JST)
```

### WordPress設定変更
```bash
# GitHub Secrets で以下を変更可能:
# - WP_SITE_URL: 投稿先WordPressサイト
# - WP_STATUS: draft/publish（公開状態）
```

## ⚠️ 注意事項

### セキュリティ
- **APIキーは絶対に公開しない**
- GitHub Secretsを正しく使用する
- 定期的にAPIキーをローテーションする

### コスト管理
- Gemini API: 無料枠内で使用（月50リクエスト程度）
- OpenAI API: 使用する場合は課金発生の可能性
- GitHub Actions: プライベートリポジトリは月2000分まで無料

### バックアップ
- 生成された記事は `output/` フォルダに保存
- GitHub Actionsの実行ログでトラブルシューティング可能

## 🎉 完了後の確認項目

- [ ] GitHubリポジトリ作成完了
- [ ] GitHub Secrets設定完了
- [ ] Gemini APIキー取得・設定完了
- [ ] 手動テスト実行で記事生成確認
- [ ] invest-master.net で下書き記事確認
- [ ] 毎日09:00の自動実行設定確認

## 🆘 トラブルシューティング

### よくある問題
1. **記事が生成されない**: Gemini APIキーを確認
2. **WordPress投稿失敗**: WP_USER/WP_APP_PASSを確認
3. **GitHub Actions失敗**: Secretsの設定を再確認

### サポート
- GitHub Actionsの実行ログを確認
- `output/` フォルダの生成ファイルを確認
- 必要に応じてissue作成でサポート

---

**🎯 このガイドに従って実装すれば、美容師向けの高品質ブログ記事が毎日自動投稿されます！**