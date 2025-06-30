# GitHub Secrets設定検証ガイド

## 1. 必須シークレット一覧

### 基本API認証
```yaml
GEMINI_API_KEY: # Google Gemini API (必須)
OPENAI_API_KEY: # OpenAI API (オプション - フォールバック用)
```

### WordPress認証
```yaml
WP_URL: # WordPress サイトURL (例: https://yourdomain.com)
WP_USERNAME: # WordPress ユーザー名
WP_PASSWORD: # WordPress アプリケーションパスワード
```

### 画像API (オプション)
```yaml
UNSPLASH_ACCESS_KEY: # Unsplash API (無料枠あり)
PEXELS_API_KEY: # Pexels API (無料)
```

## 2. GitHub Secrets設定手順

### Step 1: リポジトリ設定にアクセス
1. GitHubでリポジトリを開く
2. Settings タブをクリック
3. 左メニューから "Secrets and variables" → "Actions" を選択

### Step 2: シークレットの追加
1. "New repository secret" ボタンをクリック
2. Name と Value を入力
3. "Add secret" をクリック

### 設定例
```
Name: GEMINI_API_KEY
Value: AIzaSy... (実際のAPIキー)
```

## 3. 設定値の検証スクリプト

### ローカル環境での検証
```bash
#!/bin/bash
# verify_secrets.sh

echo "=== GitHub Secrets設定検証 ==="

# 必須項目チェック
required_vars=(
    "GEMINI_API_KEY"
    "WP_URL"
    "WP_USERNAME"
    "WP_PASSWORD"
)

missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    else
        echo "✓ $var: 設定済み"
    fi
done

# オプション項目チェック
optional_vars=(
    "OPENAI_API_KEY"
    "UNSPLASH_ACCESS_KEY"
    "PEXELS_API_KEY"
)

for var in "${optional_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "○ $var: 未設定 (オプション)"
    else
        echo "✓ $var: 設定済み"
    fi
done

# 結果表示
if [ ${#missing_vars[@]} -gt 0 ]; then
    echo ""
    echo "❌ エラー: 以下の必須項目が未設定です:"
    for var in "${missing_vars[@]}"; do
        echo "   - $var"
    done
    exit 1
else
    echo ""
    echo "✅ すべての必須項目が設定されています"
fi
```

## 4. GitHub Actions での検証

### ワークフローでの確認方法
```yaml
name: Verify Secrets

on:
  workflow_dispatch:

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - name: Check required secrets
        run: |
          if [ -z "${{ secrets.GEMINI_API_KEY }}" ]; then
            echo "::error::GEMINI_API_KEY is not set"
            exit 1
          fi
          
          if [ -z "${{ secrets.WP_URL }}" ]; then
            echo "::error::WP_URL is not set"
            exit 1
          fi
          
          if [ -z "${{ secrets.WP_USERNAME }}" ]; then
            echo "::error::WP_USERNAME is not set"
            exit 1
          fi
          
          if [ -z "${{ secrets.WP_PASSWORD }}" ]; then
            echo "::error::WP_PASSWORD is not set"
            exit 1
          fi
          
          echo "✅ All required secrets are configured"
```

## 5. トラブルシューティング

### よくある問題と解決方法

#### 1. "secret not found" エラー
**原因**: シークレット名の大文字小文字が一致していない
**解決**: GitHub Secretsの名前は大文字小文字を区別します

#### 2. "authentication failed" エラー
**原因**: WordPress アプリケーションパスワードが正しくない
**解決**: 
- WordPress管理画面 → ユーザー → プロフィール
- アプリケーションパスワードを新規作成
- スペースを除いてGitHub Secretsに設定

#### 3. "API quota exceeded" エラー
**原因**: API使用量の上限に到達
**解決**: 
- Gemini API: 無料枠を確認（1分あたり60リクエスト）
- 代替APIキー（OPENAI_API_KEY）を設定

## 6. セキュリティベストプラクティス

### やってはいけないこと
- ❌ APIキーをコード内にハードコーディング
- ❌ .envファイルをGitにコミット
- ❌ ログにAPIキーを出力

### 推奨事項
- ✅ 最小権限の原則に従う
- ✅ 定期的にAPIキーをローテーション
- ✅ 使用していないシークレットは削除

## 7. 設定完了チェックリスト

- [ ] GEMINI_API_KEY を設定
- [ ] WP_URL を設定（https://を含む完全なURL）
- [ ] WP_USERNAME を設定
- [ ] WP_PASSWORD を設定（アプリケーションパスワード）
- [ ] verify_secrets.sh でローカル検証を実行
- [ ] GitHub Actions でテストワークフローを実行
- [ ] 初回の手動実行でエラーがないことを確認

## 8. 次のステップ

設定が完了したら、以下のコマンドで手動実行テストを行います：

```bash
# GitHub Actions の手動実行
# 1. Actions タブを開く
# 2. "Daily Blog Post" ワークフローを選択
# 3. "Run workflow" をクリック
```

問題が発生した場合は、Actions のログを確認し、このガイドのトラブルシューティングセクションを参照してください。