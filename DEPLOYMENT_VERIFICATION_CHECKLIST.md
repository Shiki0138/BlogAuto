# 🚀 BlogAuto デプロイ検証チェックリスト

**作成日時**: 2025年6月30日  
**検証担当**: worker3 (worker5サポート)  
**プロジェクト**: BlogAuto - 美容師特化自動ブログシステム

## 📋 デプロイ前準備チェックリスト

### 1. 環境確認
- [ ] GitHub アカウントが有効である
- [ ] リポジトリへのアクセス権限がある
- [ ] GitHub Actions が有効化されている
- [ ] ローカル開発環境でテスト済みである

### 2. 必須APIキー取得状況
#### 必須項目
- [ ] **GEMINI_API_KEY**: [Google AI Studio](https://makersuite.google.com/app/apikey) から取得
  - 無料枠: 60 RPM (リクエスト/分)
  - 美容師向け画像生成に対応

- [ ] **WordPress認証情報**:
  - [ ] WP_USER: WordPress管理者ユーザー名
  - [ ] WP_APP_PASS: [アプリケーションパスワード生成](https://wordpress.org/support/article/application-passwords/)
  - [ ] WP_SITE_URL: https://your-site.com 形式

#### オプション項目（推奨）
- [ ] **UNSPLASH_ACCESS_KEY**: 無料の高品質画像
- [ ] **PEXELS_API_KEY**: 無料の画像バックアップ
- [ ] **OPENAI_API_KEY**: 高品質記事生成の代替

## 🔧 GitHub Secrets 設定手順

### Step 1: Secretsページへアクセス
```
1. GitHubリポジトリを開く
2. Settings タブをクリック
3. 左メニューから「Secrets and variables」→「Actions」を選択
```

### Step 2: 必須Secretsの追加
以下を「New repository secret」で追加:

```yaml
# 必須設定
GEMINI_API_KEY: AIzaSy...（あなたのAPIキー）
WP_USER: your_wordpress_username
WP_APP_PASS: xxxx xxxx xxxx xxxx
WP_SITE_URL: https://your-wordpress-site.com

# オプション（画像取得優先度順）
UNSPLASH_ACCESS_KEY: your_unsplash_key
PEXELS_API_KEY: your_pexels_key
OPENAI_API_KEY: sk-...
```

### Step 3: 動作モード設定
```yaml
# 投稿ステータス（draft推奨で開始）
WP_STATUS: draft
```

## 🧪 ローカルテスト実行手順

### 1. 依存関係インストール
```bash
pip install -r requirements.txt
```

### 2. 環境変数設定（.envファイル作成）
```bash
cp .env.example .env
# .envファイルを編集してAPIキーを設定
```

### 3. 単体テスト実行
```bash
# 記事生成テスト
python scripts/generate_article.py

# 画像取得テスト（美容師特化）
python scripts/fetch_image.py

# WordPress投稿テスト（モック）
python scripts/post_to_wp.py
```

### 4. 統合テスト実行
```bash
# パイプライン全体テスト
python scripts/pipeline_orchestrator.py daily

# 外部API有効化テスト
ENABLE_EXTERNAL_API=true python scripts/pipeline_orchestrator.py daily --enable-api
```

## 🎯 初回デプロイ実行手順

### Step 1: GitHub Actions手動実行
1. リポジトリの「Actions」タブを開く
2. 「Daily Blog Automation」ワークフローを選択
3. 「Run workflow」ボタンをクリック
4. ブランチを選択して「Run workflow」を実行

### Step 2: 実行状況確認
- [ ] ワークフローが開始された
- [ ] 各ステップが順番に実行されている
- [ ] エラーなく完了した

### Step 3: 結果確認
- [ ] WordPress管理画面で下書き記事を確認
- [ ] 記事内容が美容師向けに最適化されている
- [ ] アイキャッチ画像が設定されている
- [ ] タグ・カテゴリーが適切に設定されている

## 🔍 検証項目チェックリスト

### 記事品質
- [ ] 文字数: 1800〜2200文字
- [ ] 見出し構造: H2が5本、H3が含まれる
- [ ] 美容師特化内容: 心理学アプローチ、Instagram集客等
- [ ] SEO最適化: キーワード配置が自然

### 画像品質
- [ ] 美容サロンに適した画像コンセプト
- [ ] プロフェッショナルな印象
- [ ] ブログヘッダーに適したアスペクト比

### システム動作
- [ ] 実行時間: 3分以内で完了
- [ ] エラーハンドリング: 適切なフォールバック
- [ ] ログ出力: 詳細な実行ログ

## 🚨 トラブルシューティング

### よくある問題と解決方法

#### 1. APIキーエラー
```
エラー: "Gemini API key not found"
解決: GitHub Secretsに GEMINI_API_KEY が正しく設定されているか確認
```

#### 2. WordPress接続エラー
```
エラー: "WordPress authentication failed"
解決: 
- WP_USER が正しいか確認
- WP_APP_PASS がアプリケーションパスワードか確認
- WP_SITE_URL に https:// が含まれているか確認
```

#### 3. 画像取得エラー
```
エラー: "All image APIs failed"
解決: 
- 最低限 GEMINI_API_KEY が設定されているか確認
- APIの利用制限に達していないか確認
```

#### 4. 記事生成エラー
```
エラー: "Article generation failed"
解決:
- ENABLE_EXTERNAL_API が true に設定されているか確認
- APIキーが有効か確認
```

## 📊 パフォーマンス基準

### 期待される実行時間
- 記事生成: 10〜30秒
- 画像取得: 5〜20秒
- WordPress投稿: 5〜10秒
- **合計**: 20〜60秒

### リソース使用量
- メモリ: 512MB以下
- CPU: 最小限
- ネットワーク: API通信のみ

## ✅ 最終確認チェックリスト

### デプロイ準備完了確認
- [ ] すべての必須APIキーが設定済み
- [ ] ローカルテストがすべて成功
- [ ] GitHub Actionsが有効
- [ ] WordPress側の準備完了
- [ ] 初回は draft モードで実行

### 本番運用開始条件
- [ ] 3日間の試験運用で問題なし
- [ ] 生成記事の品質が基準を満たす
- [ ] 自動実行スケジュールが正常動作
- [ ] エラー通知システムが機能

## 🎉 デプロイ成功基準

1. **初回実行**: 手動実行で正常完了
2. **品質確認**: 美容師向け高品質記事の生成確認
3. **安定性**: 3日間連続で正常実行
4. **本番移行**: WP_STATUS を publish に変更

---

**デプロイ支援完了**: このチェックリストに従って、worker5は確実にBlogAutoをデプロイできます。

**サポート**: worker3  
**最終更新**: 2025年6月30日 08:00