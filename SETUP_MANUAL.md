# 📋 BlogAuto セットアップマニュアル

## 📝 はじめに

BlogAutoは、AI駆動型の自動ブログ投稿システムです。本マニュアルでは、ゼロから本番運用開始までの手順を詳しく説明します。

## 🎯 前提条件

### 必須要件
- **OS**: macOS, Linux, Windows (WSL2)
- **Python**: 3.8以上
- **Git**: 最新版
- **GitHub アカウント**: Actions実行用
- **WordPress サイト**: REST API有効

### 必要なAPIキー
- **Gemini API キー** (推奨・無料): [Google AI Studio](https://makersuite.google.com/app/apikey)から取得
- **OpenAI API キー** (代替・クレジット制): [OpenAI Platform](https://platform.openai.com/api-keys)から取得
- **WordPress Application Password** (必須): WordPressダッシュボードから生成

### オプションAPIキー（画像取得用）
- **Unsplash API**: [Unsplash Developers](https://unsplash.com/developers)
- **Pexels API**: [Pexels API](https://www.pexels.com/api/)
- **Google Gemini API**: [Google AI Studio](https://makersuite.google.com/app/apikey)
- **OpenAI API**: [OpenAI Platform](https://platform.openai.com/api-keys)

## 🚀 クイックスタート（5分で完了）

### 1. リポジトリのクローン
```bash
git clone https://github.com/yourusername/BlogAuto.git
cd BlogAuto
```

### 2. 自動セットアップ実行
```bash
# 実行権限付与
chmod +x setup.sh

# セットアップ実行
./setup.sh
```

### 3. 環境変数設定
```bash
# .envファイルを作成
cp .env.example .env

# .envファイルを編集
nano .env  # またはお好みのエディタで編集
```

### 4. 必須設定項目
```bash
# 必須項目
ENABLE_EXTERNAL_API=true
GEMINI_API_KEY=  # 推奨（無料枠大）
# OPENAI_API_KEY=your_openai_api_key_here  # 代替案
WP_SITE_URL=https://invest-master.net/
WP_USER=invast51@
WP_APP_PASS=
```

### 5. テスト実行
```bash
make test-run
```

## 🔧 詳細セットアップガイド

### ステップ1: Python環境構築

#### macOSの場合
```bash
# Homebrewでpython3インストール
brew install python@3.12

# pipアップグレード
python3 -m pip install --upgrade pip
```

#### Ubuntuの場合
```bash
# Python3とpipインストール
sudo apt update
sudo apt install python3 python3-pip python3-venv

# バージョン確認
python3 --version
```

#### Windowsの場合
```bash
# WSL2でUbuntu環境を使用推奨
wsl --install
# その後、Ubuntu手順に従う
```

### ステップ2: プロジェクトセットアップ

```bash
# 1. プロジェクトディレクトリ作成
mkdir -p ~/projects/BlogAuto
cd ~/projects/BlogAuto

# 2. リポジトリクローン
git clone https://github.com/yourusername/BlogAuto.git .

# 3. 仮想環境作成
python3 -m venv venv

# 4. 仮想環境有効化
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows

# 5. 依存関係インストール
pip install -r requirements.txt
```

### ステップ3: APIキー取得ガイド

#### Claude API キー取得
1. [Anthropic Console](https://console.anthropic.com/)にアクセス
2. サインアップ/ログイン
3. 「API Keys」セクションへ移動
4. 「Create Key」をクリック
5. キーをコピーして安全に保管

#### WordPress Application Password生成
1. WordPressダッシュボードにログイン
2. ユーザー → プロフィール
3. 「アプリケーションパスワード」セクションまでスクロール
4. 新しいアプリケーション名を入力（例：BlogAuto）
5. 「新しいアプリケーションパスワードを追加」をクリック
6. 生成されたパスワードをコピー（スペース含む）

#### Unsplash API キー取得（オプション）
1. [Unsplash Developers](https://unsplash.com/developers)にアクセス
2. 「Your apps」→「New Application」
3. ガイドラインに同意してアプリ作成
4. Access Keyをコピー

### ステップ4: 環境変数詳細設定

```bash
# .envファイルの完全な例
# ========== 必須設定 ==========
# 外部API接続を有効化（本番環境では必須）
ENABLE_EXTERNAL_API=true

# Claude API認証
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# WordPress設定
WP_SITE_URL=https://your-wordpress-site.com
WP_USER=your_wordpress_username
WP_APP_PASS=xxxx xxxx xxxx xxxx xxxx xxxx

# ========== オプション設定（画像取得） ==========
# 優先度1: Unsplash（高品質写真）
UNSPLASH_ACCESS_KEY=your_unsplash_access_key

# 優先度2: Pexels（無料写真）
PEXELS_API_KEY=your_pexels_api_key

# 優先度3: Google Gemini（AI生成）
GEMINI_API_KEY=your_gemini_api_key

# 優先度4: OpenAI（DALL-E）
OPENAI_API_KEY=sk-your-openai-key

# ========== 高度な設定 ==========
# ログレベル（DEBUG, INFO, WARNING, ERROR）
LOG_LEVEL=INFO

# タイムゾーン
TZ=Asia/Tokyo

# WordPress投稿ステータス（draft, publish, private）
WP_POST_STATUS=draft

# 記事の文字数範囲
MIN_CONTENT_LENGTH=1600
MAX_CONTENT_LENGTH=1800

# API リトライ設定
MAX_RETRIES=3
RETRY_DELAY=2
```

### ステップ5: 動作確認

#### 基本動作テスト
```bash
# 1. ヘルスチェック
make check

# 2. 開発モードでテスト（モックデータ使用）
make dev

# 3. 個別機能テスト
python3 scripts/generate_article.py --test
python3 scripts/fetch_image.py --test
python3 scripts/post_to_wp.py --test

# 4. 統合テスト
make integration-test
```

#### API接続テスト
```bash
# Claude API接続確認
python3 -c "
import os
from anthropic import Anthropic
client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
print('Claude API: 接続OK')
"

# WordPress API接続確認
curl -u "$WP_USER:$WP_APP_PASS" \
  "$WP_SITE_URL/wp-json/wp/v2/users/me"
```

## 🌐 GitHub Actions設定

### ステップ1: リポジトリ作成
```bash
# 1. GitHubで新規リポジトリ作成
# 2. ローカルリポジトリと連携
git remote add origin https://github.com/yourusername/BlogAuto.git
git branch -M main
git push -u origin main
```

### ステップ2: Secrets設定

1. GitHubリポジトリページへアクセス
2. Settings → Secrets and variables → Actions
3. 「New repository secret」をクリック
4. 以下のSecretsを追加：

```yaml
# 必須Secrets
ANTHROPIC_API_KEY: sk-ant-api03-xxxxx
WP_SITE_URL: https://your-site.com
WP_USER: your_username
WP_APP_PASS: xxxx xxxx xxxx xxxx

# オプションSecrets
UNSPLASH_ACCESS_KEY: your_key
PEXELS_API_KEY: your_key
GEMINI_API_KEY: your_key
OPENAI_API_KEY: sk-xxxxx
```

### ステップ3: ワークフロー有効化

1. Actions タブへ移動
2. 「I understand my workflows, go ahead and enable them」をクリック
3. 「Daily Blog」ワークフローを選択
4. 「Enable workflow」をクリック

### ステップ4: 手動実行テスト

1. Actions → Daily Blog
2. 「Run workflow」をクリック
3. 「Run workflow」ボタンを再度クリック
4. 実行状況を確認

## 🛠️ トラブルシューティング

### よくある問題と解決方法

#### 1. ModuleNotFoundError
```bash
# 解決方法
pip install -r requirements.txt --force-reinstall
```

#### 2. Claude API エラー
```bash
# APIキー確認
echo $ANTHROPIC_API_KEY

# 残高確認
# Anthropic Consoleで利用状況確認
```

#### 3. WordPress 認証エラー
```bash
# パスワード形式確認（スペース含む）
echo $WP_APP_PASS | wc -c  # 24文字+スペース5個

# 認証テスト
curl -I -u "$WP_USER:$WP_APP_PASS" \
  "$WP_SITE_URL/wp-json/wp/v2/posts"
```

#### 4. 画像取得エラー
```bash
# API優先順位確認
# Unsplash → Pexels → Gemini → OpenAI
# 少なくとも1つのAPIキーが必要
```

### ログ確認方法
```bash
# 実行ログ
tail -f logs/daily_blog.log

# エラーログのみ
grep ERROR logs/daily_blog.log

# 詳細デバッグ
LOG_LEVEL=DEBUG python3 scripts/pipeline_orchestrator.py
```

## 🔒 セキュリティ設定

### 本番環境のベストプラクティス

1. **環境変数の保護**
```bash
# .envファイルの権限設定
chmod 600 .env

# .gitignoreに追加確認
grep -q "^\.env$" .gitignore || echo ".env" >> .gitignore
```

2. **APIキーのローテーション**
- 3ヶ月ごとにAPIキーを更新
- 古いキーは即座に無効化

3. **アクセス制限**
```bash
# WordPress REST APIの制限
# wp-config.phpに追加
define('REST_API_AUTHENTICATION', true);
```

## 📊 パフォーマンス最適化

### 推奨設定
```bash
# 高速化設定
export ENABLE_CACHE=true
export CACHE_TTL=3600
export PARALLEL_REQUESTS=true
```

### リソース使用量
- **メモリ**: 最大512MB
- **CPU**: 通常0.5-1.0コア
- **実行時間**: 30-60秒

## 🎯 運用開始チェックリスト

### 本番運用前の最終確認

- [ ] Python 3.8以上インストール済み
- [ ] すべての必須APIキー設定済み
- [ ] WordPress認証テスト成功
- [ ] 統合テスト全項目合格
- [ ] GitHub Secrets設定完了
- [ ] Actions手動実行成功
- [ ] ログ出力確認
- [ ] エラー通知設定
- [ ] セキュリティ設定完了
- [ ] バックアップ設定

## 📞 サポート

### 問題が解決しない場合

1. **詳細ログ取得**
```bash
LOG_LEVEL=DEBUG make run > debug.log 2>&1
```

2. **システム情報収集**
```bash
python3 --version
pip list
cat /etc/os-release  # Linux
sw_vers  # macOS
```

3. **Issue報告**
- [GitHub Issues](https://github.com/yourusername/BlogAuto/issues)
- ログファイル添付
- 環境情報記載

## 🎉 セットアップ完了！

セットアップが完了したら、以下のコマンドで動作確認：

```bash
# 最終動作確認
make run

# 成功メッセージ確認
# ✅ Pipeline completed successfully!
```

**これでBlogAutoの準備は完了です！毎日09:00 JSTに自動的に高品質な記事が投稿されます。**

---

*最終更新: 2025年6月28日*