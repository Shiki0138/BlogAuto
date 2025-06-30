# 🌍 BlogAuto 環境変数設定ガイド

## 📋 概要
このガイドでは、BlogAutoプロジェクトの環境変数設定について、ステップバイステップで説明します。

## 🚀 クイックスタート

### 1. 環境変数ファイルの作成
```bash
# .env.exampleをコピー
cp .env.example .env

# 編集
nano .env  # または好きなエディタで開く
```

### 2. 最小限の設定（必須）
```env
# AI API（以下のいずれか1つ）
GEMINI_API_KEY=your_actual_gemini_key_here

# WordPress設定
WP_USER=your_wordpress_username
WP_APP_PASS=your_app_password_without_spaces
WP_SITE_URL=https://your-site.com
```

## 📝 詳細設定ガイド

### AI API設定（優先順位順）

#### 1. Gemini API（推奨 🌟）
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

**取得方法:**
1. [Google AI Studio](https://makersuite.google.com/app/apikey) にアクセス
2. Googleアカウントでログイン
3. "Create API key" をクリック
4. APIキーをコピー

**メリット:**
- ✅ 無料枠が大きい（1分間60リクエスト）
- ✅ 高品質な日本語生成
- ✅ 安定性が高い

#### 2. OpenAI API（代替案）
```env
OPENAI_API_KEY=sk-...your_openai_key_here
```

**取得方法:**
1. [OpenAI Platform](https://platform.openai.com/) にアクセス
2. アカウント作成/ログイン
3. API keys → Create new secret key
4. APIキーをコピー

**メリット:**
- ✅ 初回$18相当の無料クレジット
- ✅ GPT-3.5は低コスト
- ✅ 実績豊富

#### 3. Claude API（非推奨）
```env
# コメントアウトのままでOK
# ANTHROPIC_API_KEY=your_anthropic_key_here
```

**理由:** 有料のみ（無料枠なし）

### WordPress設定

#### 1. ユーザー名
```env
WP_USER=admin  # または your-username
```

#### 2. アプリケーションパスワード
```env
WP_APP_PASS=abcd1234efgh5678ijkl9012
```

**取得方法:**
1. WordPress管理画面にログイン
2. ユーザー → プロフィール
3. 下部の「アプリケーションパスワード」セクション
4. 新しいアプリケーションパスワード名: `BlogAuto`
5. 「新しいアプリケーションパスワードを追加」をクリック
6. **重要**: 表示されたパスワードからスペースを削除

例:
- 表示: `abcd 1234 efgh 5678 ijkl 9012`
- 設定: `abcd1234efgh5678ijkl9012`

#### 3. サイトURL
```env
WP_SITE_URL=https://example.com
```

**注意事項:**
- `https://` で始める
- 末尾にスラッシュ(`/`)を付けない
- サブディレクトリの場合: `https://example.com/blog`

### 画像API設定（オプション）

#### Unsplash API
```env
UNSPLASH_ACCESS_KEY=your_unsplash_access_key
```

**取得方法:**
1. [Unsplash Developers](https://unsplash.com/developers) にアクセス
2. "Register as a developer" → アプリ作成
3. Access Keyをコピー

**制限:** 50リクエスト/時間（無料）

#### Pexels API
```env
PEXELS_API_KEY=your_pexels_api_key
```

**取得方法:**
1. [Pexels API](https://www.pexels.com/api/) にアクセス
2. アカウント作成 → APIキー取得
3. 即座に利用可能

**制限:** 200リクエスト/時間（無料）

### YouTube API設定（オプション）
```env
YT_API_KEY=AIza...your_youtube_api_key
```

**取得方法:**
1. [Google Cloud Console](https://console.cloud.google.com/)
2. 新規プロジェクト作成
3. YouTube Data API v3 を有効化
4. 認証情報 → APIキー作成

### システム設定

```env
# 投稿ステータス
WP_STATUS=draft  # draft/publish/private

# ログレベル
LOG_LEVEL=INFO  # DEBUG/INFO/WARNING/ERROR

# 外部API接続
ENABLE_EXTERNAL_API=false  # 本番では true に

# タイムゾーン
TZ=Asia/Tokyo
```

## 🔍 設定検証

### 環境変数検証ツール実行
```bash
python scripts/env_validator.py
```

期待される出力:
```
✅ GEMINI_API_KEY: 設定済み
✅ WP_USER: 設定済み
✅ WP_APP_PASS: 設定済み
✅ WP_SITE_URL: 設定済み
✅ 本番デプロイ可能です！
```

### トラブルシューティング

#### よくあるエラー

1. **"API key not set"**
   ```env
   # ❌ 間違い
   GEMINI_API_KEY=your_gemini_api_key_here
   
   # ✅ 正しい
   GEMINI_API_KEY=AIzaSyC...実際のキー
   ```

2. **"WordPress authentication failed"**
   ```env
   # ❌ 間違い（スペースあり）
   WP_APP_PASS=abcd 1234 efgh 5678
   
   # ✅ 正しい（スペースなし）
   WP_APP_PASS=abcd1234efgh5678
   ```

3. **"Invalid URL format"**
   ```env
   # ❌ 間違い
   WP_SITE_URL=example.com
   WP_SITE_URL=https://example.com/
   
   # ✅ 正しい
   WP_SITE_URL=https://example.com
   ```

## 🛡️ セキュリティベストプラクティス

### やってはいけないこと
- ❌ `.env`ファイルをGitにコミット
- ❌ APIキーを他人と共有
- ❌ 公開リポジトリにAPIキーを記載

### 推奨事項
- ✅ `.gitignore`に`.env`を追加（デフォルトで設定済み）
- ✅ 定期的にAPIキーを更新
- ✅ 本番と開発で異なるAPIキー使用

## 📊 優先順位まとめ

### 必須設定（これだけでも動作）
1. `GEMINI_API_KEY` または `OPENAI_API_KEY`
2. `WP_USER`
3. `WP_APP_PASS`
4. `WP_SITE_URL`

### 推奨設定（品質向上）
1. `UNSPLASH_ACCESS_KEY`（高品質画像）
2. `PEXELS_API_KEY`（バックアップ画像源）

### オプション設定
1. `YT_API_KEY`（YouTube連携）
2. システム設定各種

## 🎯 次のステップ

1. **ローカルテスト**
   ```bash
   python scripts/pipeline_orchestrator.py
   ```

2. **GitHub Secretsに設定**
   - このガイドの設定をGitHub Secretsにも追加

3. **GitHub Actions実行**
   - 手動実行でテスト
   - 毎日09:00 JSTに自動実行

## 🆘 サポート

問題が発生した場合:
1. `scripts/env_validator.py` で検証
2. `output/deployment_env_validation_report.json` を確認
3. エラーメッセージを元に上記トラブルシューティングを参照

---

**最終更新**: 2025-06-30  
**作成者**: worker1 (BlogAuto Development Team)  
**バージョン**: 1.0