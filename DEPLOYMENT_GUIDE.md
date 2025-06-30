# 🚀 BlogAuto デプロイガイド

**本番環境へのデプロイ完全マニュアル**

## 📋 デプロイ前チェックリスト

### ✅ 必須要件確認
- [ ] Python 3.8以上インストール済み
- [ ] GitHub Actionsアクセス権限
- [ ] WordPress サイトのREST API有効化
- [ ] 必要なAPIキー取得済み
- [ ] セキュリティ設定完了

## 🏗️ クイックデプロイ

### 1. リポジトリ準備
```bash
git clone https://github.com/yourusername/BlogAuto.git
cd BlogAuto
pip install -r requirements.txt
```

### 2. 環境設定
```bash
# 推奨AI API（無料枠大）
export GEMINI_API_KEY=your_gemini_api_key

# 代替AI API（無料クレジット付き）
export OPENAI_API_KEY=your_openai_api_key

# WordPress認証（必須）
export WP_USER=your_wordpress_username  
export WP_APP_PASS=your_wordpress_app_password
export WP_SITE_URL=https://your-site.com

# 画像API（オプション）
export UNSPLASH_ACCESS_KEY=your_unsplash_key
export PEXELS_API_KEY=your_pexels_key

# 本番モード有効化
export ENABLE_EXTERNAL_API=true
```

### 3. テスト実行
```bash
# 品質チェック実行
python scripts/quality_checker.py

# パイプライン統合テスト
python scripts/pipeline_orchestrator.py test

# 日次ワークフローテスト
python scripts/pipeline_orchestrator.py daily

# ユニットテスト実行
python -m pytest tests/ -v
```

### 4. GitHub Actions設定
1. リポジトリの「Settings」→「Secrets and variables」→「Actions」
2. `DEPLOYMENT_SECRETS_CHECKLIST.md` を参照してSecrets設定
3. GitHub Actions有効化で毎日09:00 JST自動実行開始

## 🎯 SaaS化オプション

### 決済システム
```bash
# Stripe/PayPal統合
python -m integrations.payment.payment_cli auth stripe $STRIPE_KEY
python -m integrations.payment.payment_cli auth paypal $PAYPAL_ID --secret $PAYPAL_SECRET
```

### 通知システム
```bash
# プッシュ/メール通知統合
export SENDGRID_API_KEY=your_sendgrid_key
export FIREBASE_SERVICE_ACCOUNT=path/to/service-account.json
```

## 🔒 セキュリティ

- **暗号化認証**: APIキー暗号化保存
- **HTTPS強制**: 全通信暗号化
- **レート制限**: DDoS攻撃対策
- **入力検証**: XSS/インジェクション対策

## 📊 監視

- **GitHub Actions**: 実行ログ監視
- **WordPress**: 投稿状況確認
- **エラー追跡**: 詳細ログ出力

## 🚨 トラブルシューティング

### よくある問題
1. **APIキー未設定**: 環境変数確認
2. **WordPress接続失敗**: Application Password確認
3. **GitHub Actions失敗**: Secrets設定確認

## 🎉 デプロイ完了

BlogAutoが本番環境で安定稼働し、毎日高品質な記事を自動生成・投稿します。

**🚀 史上最強のブログ自動化システムが稼働開始！**

---
**最終更新**: 2025年6月28日  
**完成度**: 100%  
**デプロイ準備**: 完了