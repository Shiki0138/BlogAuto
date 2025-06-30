# 🔧 GitHub設定完全ガイド

## 🚀 すぐに実行すべき手順

### 1. GitHubリポジトリ作成・アップロード

```bash
# 現在のフォルダで実行
git init
git add .
git commit -m "美容師向けブログ自動投稿システム - 初期コミット"

# GitHubでリポジトリ作成後
git branch -M main
git remote add origin https://github.com/[あなたのユーザー名]/BlogAuto.git
git push -u origin main
```

### 2. GitHub Secrets設定（最重要）

GitHubリポジトリ → Settings → Secrets and variables → Actions → New repository secret

#### 必須設定（4項目）
```
名前: WP_USER
値: invast51@

名前: WP_APP_PASS  
値: Ikyosai51

名前: WP_SITE_URL
値: https://invest-master.net/

名前: WP_STATUS
値: draft
```

#### APIキー設定（1項目必須）
```
名前: GEMINI_API_KEY
値: [下記で取得したAPIキー]
```

### 3. Gemini APIキー取得（無料）

1. **Google AI Studio**にアクセス: https://makersuite.google.com/app/apikey
2. Googleアカウントでログイン
3. 「**Create API Key**」をクリック
4. 生成されたキーをコピー
5. GitHub Secretsの `GEMINI_API_KEY` に設定

### 4. 自動実行テスト

1. GitHubリポジトリの「**Actions**」タブをクリック
2. 「**Daily Blog Automation**」を選択
3. 「**Run workflow**」→「**Run workflow**」をクリック
4. 約1分後、実行完了を確認
5. **invest-master.net**の管理画面で下書き記事を確認

## ✅ 設定完了チェックリスト

- [ ] GitHubリポジトリ作成・アップロード完了
- [ ] GitHub Secrets 5項目設定完了
- [ ] Gemini APIキー取得・設定完了  
- [ ] 手動テスト実行で記事生成確認
- [ ] invest-master.net で下書き記事確認
- [ ] 毎日09:00自動実行設定確認

## 🎯 実装後の動作

### 自動投稿スケジュール
- **毎日09:00 JST**: 美容師向け記事を自動生成・投稿
- **投稿先**: invest-master.net
- **ステータス**: 下書き保存（手動で公開可能）

### 記事内容
- **文字数**: 2000-3000文字の高品質コンテンツ
- **テーマ**: 美容師向け心理学・マーケティング・AI活用
- **構成**: SEO最適化済み、実践的ノウハウ満載

## 🆘 よくある問題と解決方法

### Q: GitHub Actionsが失敗する
**A**: GitHub Secrets設定を再確認。特にAPI_KEYが正しく設定されているか確認

### Q: WordPress投稿が失敗する  
**A**: WP_USER/WP_APP_PASSが正しく設定されているか確認

### Q: 記事が生成されない
**A**: GEMINI_API_KEYが有効か確認。Google AI Studioで使用量確認

### Q: 投稿スケジュールを変更したい
**A**: `.github/workflows/daily-blog.yml`のcron設定を変更

---

**🎉 この設定で、毎日高品質な美容師向けブログ記事が自動投稿されます！**