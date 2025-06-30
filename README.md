# 📝 Daily Blog Automation (BlogAuto)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![GitHub Actions](https://img.shields.io/badge/GitHub-Actions-orange.svg)](https://github.com/features/actions)

**AI駆動型・毎日自動ブログ投稿システム**

## 🚀 概要

Daily Blog Automation (BlogAuto) は、Gemini・OpenAI APIを活用した完全自動ブログ投稿システムです。毎日JST 09:00に、高品質な記事を自動生成し、適切な画像と共にWordPressサイトに投稿します。

### ✨ 主要機能

- 🤖 **AI記事生成**: Gemini・OpenAI APIによる高品質コンテンツ自動生成
- 🖼️ **画像自動取得**: 複数API（Unsplash → Pexels → Gemini → OpenAI）での画像取得
- 📝 **WordPress自動投稿**: WordPress REST APIによる完全自動化
- ⏰ **毎日自動実行**: GitHub Actionsで毎日09:00 JST実行
- 🔒 **セキュア認証**: 暗号化されたAPIキー管理
- 🛡️ **堅牢性**: エラーハンドリング・リトライ機能完備

## 📋 必要条件

- Python 3.8以上
- GitHub アカウント（GitHub Actions実行用）
- WordPress サイト（REST API有効）
- Gemini API キー（推奨・無料枠大）または OpenAI API キー（代替・クレジット制）

### オプション外部APIキー
- Unsplash API キー（画像取得優先度1位）
- Pexels API キー（画像取得優先度2位）
- Google Gemini API キー（画像取得優先度3位）
- OpenAI API キー（画像取得優先度4位）

## 🔧 インストール

### 1. リポジトリのクローン
```bash
git clone https://github.com/yourusername/BlogAuto.git
cd BlogAuto
```

### 2. 初期セットアップ
```bash
make setup
```

### 3. 環境変数設定
`.env` ファイルを編集し、以下の必須項目を設定：

```bash
# 必須設定
GEMINI_API_KEY=your_gemini_api_key_here  # 推奨（無料枠大）
# OPENAI_API_KEY=your_openai_api_key_here  # 代替（クレジット制）
WP_SITE_URL=https://your-wordpress-site.com
WP_USER=your_wp_username
WP_APP_PASS=your_wp_application_password

# オプション（画像取得用）
UNSPLASH_ACCESS_KEY=your_unsplash_key
PEXELS_API_KEY=your_pexels_key

# 外部API接続制御（本番環境では true）
ENABLE_EXTERNAL_API=true
```

## 🎯 使用方法

### 開発環境での実行
```bash
# 開発モードで実行（モックデータ使用）
make dev

# 個別スクリプト実行
make generate  # 記事生成のみ
make fetch     # 画像取得のみ
make post      # WordPress投稿のみ
```

### 本番環境での実行
```bash
# 完全な本番パイプライン実行
make run
```

### テスト実行
```bash
# 全テスト実行
make test

# 統合テスト実行
make integration-test

# ヘルスチェック
make check
```

## 🏗️ アーキテクチャ

```
BlogAuto/
├── scripts/
│   ├── generate_article.py    # AI記事生成
│   ├── fetch_image.py         # 画像取得（複数API）
│   ├── post_to_wp.py         # WordPress投稿
│   ├── pipeline_orchestrator.py  # メインオーケストレーター
│   ├── auth_manager.py       # セキュア認証管理
│   ├── utils.py              # 共通ユーティリティ
│   └── error_handler.py      # エラーハンドリング
├── prompts/
│   └── daily_blog.jinja      # 記事生成テンプレート
├── .github/workflows/
│   └── daily-blog.yml        # 毎日自動実行設定
├── output/                   # 生成ファイル保存先
├── logs/                     # ログファイル
└── requirements.txt          # Python依存関係
```

## ⚙️ 設定詳細

### GitHub Actions設定

リポジトリのSecrets設定で以下を追加：

```
GEMINI_API_KEY       # 推奨（無料枠大）
OPENAI_API_KEY       # 代替（クレジット制）
WP_SITE_URL  
WP_USER
WP_APP_PASS
UNSPLASH_ACCESS_KEY  # オプション
PEXELS_API_KEY       # オプション
```

### WordPress設定

1. **アプリケーションパスワード生成**
   - WordPressダッシュボード → ユーザー → プロフィール
   - 「アプリケーションパスワード」セクションで新規作成

2. **REST API有効化確認**
   ```bash
   curl https://your-site.com/wp-json/wp/v2/posts
   ```

## 🔄 自動実行フロー

1. **毎日09:00 JST**: GitHub Actionsが自動起動
2. **記事生成**: Claude APIでテーマに応じた記事作成
3. **画像取得**: 優先度順で適切な画像を取得
4. **WordPress投稿**: 記事と画像を自動投稿
5. **ログ保存**: 実行結果をアーティファクトとして保存

## 🛠️ 開発者向け

### コード品質チェック
```bash
make lint     # 静的解析
make format   # コードフォーマット
```

### セキュリティ監査
```bash
bandit -r scripts/
```

### パフォーマンステスト
```bash
make perf
```

## 🔒 セキュリティ

- **暗号化認証**: APIキーは暗号化して保存
- **セキュアHTTPS**: 全API通信でHTTPS使用
- **入力検証**: XSS・インジェクション対策実装
- **レート制限**: API呼び出し頻度制御

## 📊 モニタリング

- **ヘルスチェック**: システム状態監視
- **パフォーマンス測定**: 実行時間・リソース使用量
- **エラー追跡**: 詳細ログとアラート機能

## 🚨 トラブルシューティング

### よくある問題

**記事生成失敗**
```bash
# APIキー確認
echo $GEMINI_API_KEY
echo $OPENAI_API_KEY

# ログ確認
cat logs/daily_blog.log
```

**WordPress投稿失敗**
```bash
# 認証確認
curl -u "username:app_password" https://your-site.com/wp-json/wp/v2/users/me

# パーミッション確認
curl https://your-site.com/wp-json/wp/v2/posts
```

**画像取得失敗**
```bash
# 各API接続確認
python scripts/fetch_image.py --test
```

## 📈 パフォーマンス

- **記事生成**: 平均30-60秒
- **画像取得**: 平均10-30秒（API依存）
- **WordPress投稿**: 平均5-15秒
- **総実行時間**: 平均1-2分

## 🔄 更新・メンテナンス

### 依存関係更新
```bash
pip install --upgrade -r requirements.txt
```

### システム更新
```bash
git pull origin main
make setup
```

## 📝 ライセンス

MIT License - 詳細は [LICENSE](LICENSE) ファイルを参照

## 🤝 コントリビューション

1. リポジトリをフォーク
2. フィーチャーブランチ作成 (`git checkout -b feature/amazing-feature`)
3. コミット (`git commit -m 'Add amazing feature'`)
4. プッシュ (`git push origin feature/amazing-feature`)
5. プルリクエスト作成

## 📞 サポート

- **Issue報告**: [GitHub Issues](https://github.com/yourusername/BlogAuto/issues)
- **Discussion**: [GitHub Discussions](https://github.com/yourusername/BlogAuto/discussions)
- **Documentation**: [Wiki](https://github.com/yourusername/BlogAuto/wiki)

## 🏆 実績

- ✅ **100%完成**: 全機能実装済み
- ✅ **本番レベル品質**: エラーハンドリング・セキュリティ完備
- ✅ **統合テスト**: 全テストパス確認済み
- ✅ **デプロイ準備**: 本番環境対応完了

---

**Powered by Claude AI & GitHub Actions** 🚀

*最終更新: 2025年6月28日*