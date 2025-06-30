# 🔐 GitHub Secrets 設定チェックリスト

**Daily Blog Automation システム**用の GitHub Secrets 設定ガイドです。

## 📋 設定手順

### 1. GitHub リポジトリの Settings へアクセス
1. GitHub リポジトリページを開く
2. 「Settings」タブをクリック
3. 左サイドバーの「Secrets and variables」→「Actions」をクリック

### 2. 必須 Secrets の設定

#### 🤖 AI API（記事生成用）- 優先度順
```bash
# ✅ 推奨: Gemini API（無料枠大）
GEMINI_API_KEY=your_gemini_api_key_here

# ✅ 代替: OpenAI API（無料クレジット付き）
OPENAI_API_KEY=your_openai_api_key_here

# ❌ 非推奨: Claude API（有料のため）
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

#### 📝 WordPress 連携（必須）
```bash
WP_USER=your_wordpress_username
WP_APP_PASS=your_wordpress_app_password
WP_SITE_URL=https://your-wordpress-site.com
WP_STATUS=draft  # または publish
```

#### 🖼️ 画像API（オプション）- 優先度順
```bash
# 優先度1: Unsplash（無料枠あり）
UNSPLASH_ACCESS_KEY=your_unsplash_access_key

# 優先度2: Pexels（無料枠あり）
PEXELS_API_KEY=your_pexels_api_key

# 優先度3: 上記のAI APIが画像生成も担当
```

### 3. WordPress Application Password の作成手順

1. WordPress 管理画面にログイン
2. 「ユーザー」→「プロフィール」
3. 「Application Passwords」セクションまでスクロール
4. 新しいアプリケーション名を入力: `BlogAuto GitHub Actions`
5. 「Add New Application Password」をクリック
6. 生成されたパスワードを `WP_APP_PASS` として設定

### 4. API キーの取得方法

#### Gemini API（推奨）
1. [Google AI Studio](https://makersuite.google.com/app/apikey) にアクセス
2. Googleアカウントでログイン
3. 「Get API key」をクリック
4. 新しいAPIキーを作成
5. キーをコピーして `GEMINI_API_KEY` として設定

#### OpenAI API（代替）
1. [OpenAI Platform](https://platform.openai.com/api-keys) にアクセス
2. アカウント作成・ログイン
3. 「Create new secret key」をクリック
4. キーをコピーして `OPENAI_API_KEY` として設定

#### Unsplash API（オプション）
1. [Unsplash Developers](https://unsplash.com/developers) にアクセス
2. アカウント作成・ログイン
3. 「New Application」を作成
4. Access Keyをコピーして `UNSPLASH_ACCESS_KEY` として設定

#### Pexels API（オプション）
1. [Pexels API](https://www.pexels.com/api/) にアクセス
2. アカウント作成・ログイン
3. APIキーを取得
4. キーをコピーして `PEXELS_API_KEY` として設定

## ✅ 設定確認チェックリスト

### 必須項目
- [ ] `GEMINI_API_KEY` または `OPENAI_API_KEY` のいずれかが設定済み
- [ ] `WP_USER` が設定済み
- [ ] `WP_APP_PASS` が設定済み
- [ ] `WP_SITE_URL` が設定済み（https://で始まる）

### オプション項目
- [ ] `WP_STATUS` が設定済み（draft または publish）
- [ ] `UNSPLASH_ACCESS_KEY` が設定済み（画像API用）
- [ ] `PEXELS_API_KEY` が設定済み（画像API用）

### 動作確認
- [ ] GitHub Actions ワークフローの手動実行テスト
- [ ] WordPress に下書き記事が正常に投稿される
- [ ] 画像が正常に取得・アップロードされる
- [ ] ログにエラーが出ていない

## 🚨 セキュリティ注意事項

1. **APIキーの取り扱い**
   - APIキーは絶対にコードにハードコーディングしない
   - GitHub Secrets 以外での共有は避ける
   - 定期的にAPIキーをローテーションする

2. **WordPress認証**
   - Application Password は通常のログインパスワードと別物
   - 不要になったら WordPress 側で無効化する
   - 権限は必要最小限に設定する

3. **トークン管理**
   - 使用していないAPIキーは削除する
   - 異常な使用量が検出されたら即座に無効化する

## 🔍 トラブルシューティング

### よくあるエラーと対処法

#### 1. WordPress 認証エラー
```
Error: 401 Unauthorized
```
- `WP_USER` と `WP_APP_PASS` の組み合わせを確認
- WordPress Application Password が有効か確認
- サイトURLが正しいか確認

#### 2. AI API エラー
```
Error: API key invalid
```
- APIキーの有効性を確認
- 使用量制限に達していないか確認
- APIキーの権限設定を確認

#### 3. 画像API エラー
```
Warning: Image fetch failed
```
- 複数の画像APIを設定して冗長化
- 無料枠の制限を確認
- ネットワーク接続を確認

## 📞 サポート

設定でお困りの場合は、以下を確認してください：
1. GitHub Actions のログを確認
2. WordPress のエラーログを確認
3. API提供者のステータスページを確認

---

**更新日**: 2025-06-29  
**対象システム**: Daily Blog Automation v2.0