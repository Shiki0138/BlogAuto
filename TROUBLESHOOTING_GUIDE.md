# BlogAutoトラブルシューティングガイド

## 1. よくあるエラーと解決方法

### 🔴 API関連のエラー

#### Gemini APIエラー
```
google.api_core.exceptions.InvalidArgument: 400 API key not valid
```
**原因**: APIキーが無効または誤っている
**解決方法**:
1. [Google AI Studio](https://makersuite.google.com/app/apikey)でAPIキーを再確認
2. .envファイルのGEMINI_API_KEYを更新
3. APIキーの前後の空白を削除
4. 新しいAPIキーを生成して再試行

#### API使用量制限エラー
```
google.api_core.exceptions.ResourceExhausted: 429 Quota exceeded
```
**原因**: API使用量の上限に到達
**解決方法**:
1. 1分待ってから再実行
2. 代替APIキー（OPENAI_API_KEY）を設定
3. Google Cloudで使用量上限を確認・調整

### 🔴 WordPress関連のエラー

#### 認証エラー
```
requests.exceptions.HTTPError: 401 Client Error: Unauthorized
```
**原因**: WordPressの認証情報が正しくない
**解決方法**:
1. WordPress管理画面にログイン
2. ユーザー → あなたのプロフィール → アプリケーションパスワード
3. 新しいパスワードを生成（名前: BlogAuto）
4. 生成されたパスワードからスペースを除去
5. .envファイルのWP_PASSWORDを更新

#### REST APIエラー
```
requests.exceptions.HTTPError: 404 Client Error: Not Found
```
**原因**: WordPress REST APIが無効またはURLが正しくない
**解決方法**:
1. ブラウザで`https://your-site.com/wp-json/wp/v2/posts`にアクセス
2. JSONが表示されることを確認
3. .envファイルのWP_URLを確認（末尾の/は不要）
4. .htaccessでREST APIがブロックされていないか確認

### 🔴 画像生成関連のエラー

#### 画像取得失敗
```
Exception: Failed to fetch image from all sources
```
**原因**: すべての画像ソースでエラーが発生
**解決方法**:
1. インターネット接続を確認
2. 各APIキーが正しく設定されているか確認
3. フォールバック画像を手動で配置:
   ```bash
   # デフォルト画像を配置
   cp assets/default_cover.jpg output/cover.jpg
   ```

#### Unsplash APIエラー
```
requests.exceptions.HTTPError: 403 Client Error: Forbidden
```
**原因**: Unsplash APIキーが無効
**解決方法**:
1. [Unsplash Developers](https://unsplash.com/developers)でアプリケーションを確認
2. Access Keyを再生成
3. .envファイルを更新

### 🔴 実行環境関連のエラー

#### モジュールインポートエラー
```
ModuleNotFoundError: No module named 'jinja2'
```
**原因**: 必要なパッケージがインストールされていない
**解決方法**:
```bash
# すべての依存関係をインストール
pip install -r requirements.txt

# 特定のパッケージのみ
pip install jinja2 markdown requests python-dotenv
```

#### 権限エラー
```
PermissionError: [Errno 13] Permission denied: 'output/article.md'
```
**原因**: outputディレクトリへの書き込み権限がない
**解決方法**:
```bash
# ディレクトリの権限を修正
chmod 755 output/
chmod 644 output/*

# 所有者を変更（必要な場合）
sudo chown -R $(whoami) output/
```

## 2. デバッグ方法

### ログレベルの設定
```python
# scripts/pipeline_orchestrator.pyの先頭に追加
import logging
logging.basicConfig(level=logging.DEBUG)
```

### ステップごとの実行
```bash
# 1. 記事生成のみテスト
python scripts/generate_article.py

# 2. 画像取得のみテスト  
python scripts/fetch_image.py

# 3. WordPress投稿のみテスト（モックモード）
python scripts/post_to_wp.py --mock
```

### 環境変数の確認
```bash
# 環境変数が正しく読み込まれているか確認
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('GEMINI_API_KEY:', 'Set' if os.getenv('GEMINI_API_KEY') else 'Not set')
print('WP_URL:', os.getenv('WP_URL', 'Not set'))
print('WP_USERNAME:', os.getenv('WP_USERNAME', 'Not set'))
"
```

## 3. パフォーマンス問題

### 実行時間が長い
**症状**: パイプライン実行に5分以上かかる
**対処法**:
1. ネットワーク接続を確認
2. APIレスポンス時間を計測:
   ```python
   import time
   start = time.time()
   # API呼び出し
   print(f"API response time: {time.time() - start}s")
   ```
3. 不要な処理をスキップ（画像生成を無効化など）

### メモリ使用量が多い
**症状**: メモリ不足エラーが発生
**対処法**:
1. 記事の最大文字数を制限
2. 画像処理を最適化
3. 不要なオブジェクトを削除:
   ```python
   import gc
   gc.collect()
   ```

## 4. GitHub Actions特有の問題

### ワークフローが開始されない
**原因**: cronスケジュールが正しくない
**解決方法**:
1. `.github/workflows/daily-blog.yml`を確認
2. cronスケジュールを修正:
   ```yaml
   schedule:
     - cron: '0 0 * * *'  # UTC時間で毎日0時（JST 9:00）
   ```

### シークレットが読み込まれない
**原因**: シークレット名が一致しない
**解決方法**:
1. GitHub → Settings → Secrets → Actions
2. シークレット名が大文字であることを確認
3. ワークフローファイルでの参照を確認:
   ```yaml
   env:
     GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
   ```

## 5. 記事品質の問題

### 生成される記事が短い
**原因**: プロンプトが適切でない
**解決方法**:
1. `prompts/daily_blog.jinja`を確認
2. 最小文字数の指定を追加:
   ```
   必ず1800文字以上2200文字以下で執筆してください。
   ```

### 美容業界に関連しない内容
**原因**: テーマ生成が適切でない
**解決方法**:
1. `scripts/generate_article.py`の`generate_theme()`を修正
2. 美容関連キーワードを追加
3. プロンプトに業界特化の指示を追加

## 6. 緊急時の対処法

### すべてが動かない場合
```bash
# 1. 基本的な動作確認
python --version  # Python 3.8以上
pip --version

# 2. 最小構成でテスト
python -c "print('Python is working')"

# 3. 手動で記事生成
python scripts/generate_article.py --theme "美容室の集客方法"

# 4. ログを確認
tail -f logs/pipeline.log
```

### データ復旧
```bash
# バックアップから復元
cp backup/article_*.md output/article.md
cp backup/cover_*.jpg output/cover.jpg

# Git履歴から復元
git checkout HEAD~1 output/
```

## 7. サポート連絡先

### 問題が解決しない場合

1. **エラーログを収集**:
   ```bash
   # ログファイルを作成
   python scripts/pipeline_orchestrator.py 2>&1 | tee error.log
   ```

2. **環境情報を収集**:
   ```bash
   python --version > env_info.txt
   pip list >> env_info.txt
   echo "OS: $(uname -a)" >> env_info.txt
   ```

3. **問題を報告**:
   - GitHubのIssuesに投稿
   - エラーログと環境情報を添付
   - 再現手順を明記

## 8. よくある質問（FAQ）

**Q: 毎日同じような記事が生成される**
A: `scripts/generate_article.py`の`generate_theme()`にランダム性を追加してください。

**Q: 画像が美容業界と関係ない**
A: `scripts/fetch_image.py`の`_optimize_beauty_prompt()`でキーワードマッピングを調整してください。

**Q: WordPress投稿が公開されない**
A: デフォルトでは下書き（draft）として保存されます。自動公開したい場合は`status: "publish"`に変更してください。

**Q: APIコストを削減したい**
A: 無料のAPIを優先的に使用し、Geminiは最後の手段として使用するよう設定されています。

このガイドで解決できない問題が発生した場合は、エラーメッセージと実行環境の詳細を含めて報告してください。