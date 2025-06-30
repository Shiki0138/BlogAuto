# 初回実行テストシナリオ

## 1. テスト前準備チェックリスト

### 環境準備
- [ ] Python 3.8以上がインストールされている
- [ ] 必要なパッケージがインストール済み（`pip install -r requirements.txt`）
- [ ] .env.exampleから.envファイルを作成済み
- [ ] GitHub Secretsがすべて設定済み

### API確認
- [ ] Gemini APIキーが有効（[Google AI Studio](https://makersuite.google.com/app/apikey)で確認）
- [ ] WordPress REST APIが有効（`https://your-site.com/wp-json/wp/v2/posts`でアクセス可能）
- [ ] WordPressアプリケーションパスワードが生成済み

## 2. ローカル環境でのテストシナリオ

### シナリオ1: 基本動作確認
```bash
# 1. 環境変数の読み込み確認
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('GEMINI_API_KEY:', 'Set' if os.getenv('GEMINI_API_KEY') else 'Not set')"

# 2. モジュールインポート確認
python -c "import scripts.generate_article; import scripts.fetch_image; import scripts.post_to_wp; print('All modules imported successfully')"

# 3. パイプライン実行（ドライラン）
python scripts/pipeline_orchestrator.py --dry-run
```

### シナリオ2: 記事生成テスト
```bash
# 単独で記事生成をテスト
python scripts/generate_article.py

# 生成された記事を確認
cat output/article.md | head -50
```

### シナリオ3: 画像取得テスト
```bash
# 画像取得をテスト（美容関連のキーワード）
python -c "
from scripts.fetch_image import ImageFetcher
fetcher = ImageFetcher()
result = fetcher.fetch_and_save('美容室 インテリア')
print(f'画像取得結果: {result}')
"

# 取得した画像を確認
ls -la output/cover.jpg
```

### シナリオ4: WordPress投稿テスト（モックモード）
```bash
# モックモードで投稿テスト
python scripts/post_to_wp.py --mock

# 結果を確認
cat output/wp_result.json | jq .
```

## 3. GitHub Actions実行テストシナリオ

### シナリオ5: 手動ワークフロー実行
1. GitHubリポジトリの「Actions」タブを開く
2. 「Daily Blog Post」ワークフローを選択
3. 「Run workflow」ボタンをクリック
4. ブランチを選択（通常はmain）
5. 「Run workflow」を実行

### 期待される結果
- ワークフローが緑色のチェックマークで完了
- 実行時間: 約2-3分
- 生成物:
  - 記事ファイル (output/article.md)
  - 画像ファイル (output/cover.jpg)
  - メタデータ (output/meta.json)
  - 投稿結果 (output/wp_result.json)

## 4. 実行結果の検証ポイント

### 記事品質チェック
```bash
# 記事の文字数確認（1800-2200文字が理想）
wc -m output/article.md

# H2セクション数の確認（5つ必要）
grep -c "^## " output/article.md

# 美容関連キーワードの出現回数
grep -o "美容\|サロン\|ヘア\|スタイル" output/article.md | wc -l
```

### 画像品質チェック
```bash
# 画像サイズ確認
file output/cover.jpg

# 画像情報確認
cat output/image_info.json | jq .
```

### WordPress投稿確認
```bash
# 投稿結果の確認
cat output/wp_result.json | jq '{
  post_id: .post_id,
  status: .status,
  word_count: .word_count,
  featured_image_id: .featured_image_id
}'
```

## 5. トラブルシューティングシナリオ

### エラー1: Gemini API認証エラー
```
Error: INVALID_ARGUMENT: API key not valid
```
**対処法**: 
- APIキーが正しくコピーされているか確認
- APIキーに余分なスペースが含まれていないか確認
- Google AI Studioで新しいAPIキーを生成

### エラー2: WordPress接続エラー
```
Error: 401 Unauthorized
```
**対処法**:
- WP_URLが正しい形式か確認（https://を含む）
- アプリケーションパスワードのスペースを除去
- REST APIが有効になっているか確認

### エラー3: 画像生成エラー
```
Error: Image generation failed after all attempts
```
**対処法**:
- インターネット接続を確認
- 代替APIキー（OPENAI_API_KEY）を設定
- フォールバック画像の設定を確認

## 6. パフォーマンステスト

### 実行時間の計測
```bash
# 全体のパイプライン実行時間
time python scripts/pipeline_orchestrator.py

# 各ステップの実行時間
python -c "
import time
from scripts.pipeline_orchestrator import PipelineOrchestrator

orchestrator = PipelineOrchestrator()
start = time.time()
orchestrator.run()
end = time.time()
print(f'Total execution time: {end - start:.2f} seconds')
"
```

### 期待されるパフォーマンス
- 記事生成: 30-60秒
- 画像取得: 5-15秒
- WordPress投稿: 5-10秒
- 合計: 40-85秒

## 7. 本番環境移行前の最終チェック

### システム全体の確認
- [ ] すべてのテストシナリオが成功
- [ ] エラーログが出力されていない
- [ ] 生成された記事の品質が基準を満たしている
- [ ] 画像が適切に生成/取得されている
- [ ] WordPress投稿が正常に動作している

### 運用準備
- [ ] 日次実行時間（09:00 JST）が適切か確認
- [ ] エラー通知の設定（オプション）
- [ ] バックアップ戦略の確認
- [ ] モニタリング方法の確立

## 8. 初回本番実行

### 実行手順
1. GitHub Actionsで手動実行（本番モード）
2. 実行ログをリアルタイムで監視
3. WordPress管理画面で下書き記事を確認
4. 必要に応じて記事を編集し公開

### 成功基準
- エラーなく完了
- 記事品質スコア60点以上
- 適切な画像が設定されている
- WordPress下書きとして保存されている

これらのテストシナリオをすべて実行し、問題がないことを確認してから本番運用を開始してください。