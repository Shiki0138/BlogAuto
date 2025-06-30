# 🔐 GitHub Secrets 設定チェックリスト

## 📋 概要
このドキュメントは、BlogAutoプロジェクトの本番デプロイに必要なGitHub Secretsの設定手順を説明します。

## ✅ 必須設定項目

### 1. AI API Key（最低1つ必須）

#### Option A: Gemini API（推奨）
- [ ] **`GEMINI_API_KEY`**
  - 取得元: [Google AI Studio](https://makersuite.google.com/app/apikey)
  - 料金: 無料枠が大きい（推奨）
  - 用途: 記事生成

#### Option B: OpenAI API
- [ ] **`OPENAI_API_KEY`**
  - 取得元: [OpenAI Platform](https://platform.openai.com/api-keys)
  - 料金: 初回無料クレジット付き
  - 用途: 記事生成（Geminiの代替）

#### Option C: Claude API（非推奨）
- [ ] **`ANTHROPIC_API_KEY`**
  - 取得元: [Anthropic Console](https://console.anthropic.com/)
  - 料金: 有料（非推奨）
  - 用途: 記事生成（高品質だが高コスト）

### 2. WordPress設定（全て必須）

- [ ] **`WP_USER`**
  - 説明: WordPressのユーザー名
  - 例: `admin` or `your-username`

- [ ] **`WP_APP_PASS`**
  - 説明: WordPressアプリケーションパスワード
  - 取得方法:
    1. WordPress管理画面にログイン
    2. ユーザー → プロフィール
    3. アプリケーションパスワード → 新しいアプリケーションパスワード
    4. 名前を入力（例: "BlogAuto"）して生成
    5. **重要**: スペースを除去して保存

- [ ] **`WP_SITE_URL`**
  - 説明: WordPressサイトのURL
  - 形式: `https://your-site.com` （末尾スラッシュなし）
  - 例: `https://example.wordpress.com`

## 📋 オプション設定項目

### 3. 画像API（推奨）

- [ ] **`UNSPLASH_ACCESS_KEY`**
  - 取得元: [Unsplash Developers](https://unsplash.com/developers)
  - 料金: 無料（リクエスト制限あり）
  - 用途: 高品質な写真取得

- [ ] **`PEXELS_API_KEY`**
  - 取得元: [Pexels API](https://www.pexels.com/api/)
  - 料金: 無料
  - 用途: Unsplashのフォールバック

### 4. YouTube連携（オプション）

- [ ] **`YT_API_KEY`**
  - 取得元: [Google Cloud Console](https://console.cloud.google.com/)
  - 料金: 無料枠あり
  - 用途: YouTube動画からブログ記事生成

## 🚀 GitHub Secrets設定手順

### Step 1: リポジトリ設定へアクセス
1. GitHubでリポジトリを開く
2. **Settings** タブをクリック
3. 左サイドバーの **Secrets and variables** → **Actions** を選択

### Step 2: Secret追加
1. **New repository secret** ボタンをクリック
2. 以下の情報を入力:
   - **Name**: 環境変数名（例: `GEMINI_API_KEY`）
   - **Secret**: 実際のAPIキー値
3. **Add secret** をクリック

### Step 3: 設定確認
設定済みのSecretsが一覧に表示されることを確認

## 🔍 設定値の検証

### 必須チェック項目
```yaml
# 最低限必要なSecrets
✅ AI API Key（以下のいずれか1つ）
  - GEMINI_API_KEY（推奨）
  - OPENAI_API_KEY
  - ANTHROPIC_API_KEY

✅ WordPress設定（全て必須）
  - WP_USER
  - WP_APP_PASS
  - WP_SITE_URL
```

### 推奨チェック項目
```yaml
⭐ 画像API（どちらか1つ以上）
  - UNSPLASH_ACCESS_KEY
  - PEXELS_API_KEY

⭐ YouTube連携
  - YT_API_KEY
```

## 🛡️ セキュリティベストプラクティス

### やってはいけないこと
- ❌ APIキーをコード内にハードコーディング
- ❌ APIキーを.envファイルでコミット
- ❌ APIキーを公開リポジトリで共有
- ❌ 本番用と開発用で同じAPIキーを使用

### 推奨事項
- ✅ 定期的なAPIキーのローテーション
- ✅ 最小権限の原則（必要な権限のみ付与）
- ✅ アクセスログの定期的な監視
- ✅ 不要になったAPIキーの即座の無効化

## 📊 動作確認方法

### 1. GitHub Actions手動実行
1. **Actions** タブを開く
2. **Daily Blog** ワークフローを選択
3. **Run workflow** → **Run workflow** をクリック
4. ログを確認して正常動作を確認

### 2. 環境変数検証スクリプト実行
```bash
# ローカルで環境変数を検証
python scripts/env_validator.py
```

### 3. 期待される結果
- ✅ 記事生成成功
- ✅ 画像取得成功（画像APIが設定されている場合）
- ✅ WordPress投稿成功（draft状態）

## 🆘 トラブルシューティング

### よくあるエラーと対処法

#### 1. "Authentication failed"
- **原因**: APIキーが正しくない
- **対処**: APIキーを再確認し、前後の空白を除去

#### 2. "WordPress connection error"
- **原因**: WP_SITE_URLの形式が正しくない
- **対処**: `https://`で始まり、末尾スラッシュがないことを確認

#### 3. "API rate limit exceeded"
- **原因**: API使用制限に達した
- **対処**: 
  - 別のAPIキーを使用
  - 次の日まで待つ
  - 有料プランへアップグレード

## 📝 最終チェックリスト

デプロイ前の最終確認:

- [ ] 必須APIキーが最低1つ設定されている
- [ ] WordPress設定が全て完了している
- [ ] GitHub Actionsでテスト実行が成功した
- [ ] エラーログがない
- [ ] 画像APIが少なくとも1つ設定されている（推奨）

## 🎉 完了！

全ての設定が完了したら、毎日09:00 JSTに自動でブログ記事が投稿されます。

**次のステップ:**
1. 最初の自動投稿を確認
2. WordPressで記事の品質を確認
3. 必要に応じて`WP_STATUS`を`publish`に変更

---

**最終更新**: 2025-06-30  
**作成者**: worker1 (BlogAuto Development Team)