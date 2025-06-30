# 📖 BlogAuto 使い方マニュアル

## 🎯 このマニュアルについて

BlogAutoの日常的な使い方、運用方法、カスタマイズ方法を詳しく解説します。セットアップが完了している前提で説明を進めます。

## 📋 目次

1. [基本的な使い方](#基本的な使い方)
2. [日常運用ガイド](#日常運用ガイド)
3. [カスタマイズ方法](#カスタマイズ方法)
4. [高度な使い方](#高度な使い方)
5. [運用管理](#運用管理)
6. [トラブル対応](#トラブル対応)

## 🚀 基本的な使い方

### 1. 手動で記事を生成・投稿する

#### 完全自動実行（推奨）
```bash
# すべての処理を一括実行
make run

# または詳細ログ付き
python3 scripts/pipeline_orchestrator.py daily --enable-api
```

#### 個別実行
```bash
# 1. 記事生成のみ
make generate
# → output/article.md が生成される

# 2. 画像取得のみ  
make fetch
# → output/cover.jpg が取得される

# 3. WordPress投稿のみ
make post
# → WordPressに投稿される
```

### 2. テストモードでの確認

```bash
# 開発モード（モックデータ使用）
make dev

# 結果確認
cat output/article.md
cat output/meta.json
```

### 3. 生成された内容の確認

```bash
# 記事内容確認
cat output/article.md

# メタデータ確認（タイトル、タグなど）
cat output/meta.json | jq '.'

# 画像情報確認
cat output/image_meta.json | jq '.'

# 投稿結果確認
cat output/wp_result.json | jq '.'
```

## 📅 日常運用ガイド

### 1. 自動投稿の監視

#### GitHub Actionsでの自動実行状況確認
1. GitHubリポジトリ → Actions タブ
2. 「Daily Blog」ワークフローの実行履歴確認
3. 緑のチェック = 成功、赤の×= 失敗

#### ログ確認
```bash
# 最新のログを確認
tail -n 50 logs/daily_blog.log

# 今日のログのみ
grep "$(date +%Y-%m-%d)" logs/daily_blog.log

# エラーのみ確認
grep ERROR logs/daily_blog.log

# リアルタイム監視
tail -f logs/daily_blog.log
```

### 2. 投稿内容の管理

#### 投稿履歴の確認
```bash
# 過去の投稿記録
ls -la output/archive/

# 特定日の記事確認
cat output/archive/2025-06-28_article.md
```

#### WordPress側での確認
```bash
# 最新の投稿を取得
curl "$WP_SITE_URL/wp-json/wp/v2/posts?per_page=5" | jq '.'

# 下書き状態の投稿確認
curl -u "$WP_USER:$WP_APP_PASS" \
  "$WP_SITE_URL/wp-json/wp/v2/posts?status=draft" | jq '.'
```

### 3. 定期メンテナンス

#### 週次タスク
```bash
# ログファイルのローテーション
mv logs/daily_blog.log logs/daily_blog_$(date +%Y%m%d).log
touch logs/daily_blog.log

# 古いアーカイブの削除（30日以上前）
find output/archive -name "*.md" -mtime +30 -delete
```

#### 月次タスク
```bash
# パフォーマンスレポート生成
python3 scripts/generate_monthly_report.py

# APIキー使用量確認
python3 scripts/check_api_usage.py
```

## 🎨 カスタマイズ方法

### 1. 記事テーマのカスタマイズ

#### テーマリストの変更
```python
# scripts/utils.py を編集
def get_today_theme():
    """本日のテーマを取得（カスタマイズ可能）"""
    themes = [
        "健康的な生活習慣",
        "仕事の生産性向上",
        "人間関係の改善",
        "お金の管理術",
        "学習効率の向上",
        "ストレス解消法",
        "時間管理のコツ"
    ]
    # 日付ベースでローテーション
    day_of_year = datetime.now().timetuple().tm_yday
    return themes[day_of_year % len(themes)]
```

#### 特定テーマでの生成
```bash
# 環境変数で指定
BLOG_THEME="AIと未来の仕事" python3 scripts/generate_article.py
```

### 2. 記事フォーマットのカスタマイズ

#### プロンプトテンプレートの編集
```jinja2
# prompts/daily_blog.jinja を編集
あなたはSEOに精通した日本語ライターです。

本日のテーマ: {{ theme }}
投稿日: {{ date_ja }}

## 生成ルール
- 文字数: {{ min_length }}〜{{ max_length }}文字
- 見出し: H2を{{ h2_count }}本、H3を適宜使用
- トーン: {{ tone }} # 追加可能
- ターゲット: {{ target_audience }} # 追加可能

## 記事構成
1. 導入（読者の関心を引く）
2. 問題提起（なぜ重要か）
3. 解決策（具体的な方法）
4. 実例（成功事例）
5. まとめ（行動促進）
```

### 3. 投稿設定のカスタマイズ

#### WordPress投稿オプション
```bash
# .env で設定
# 投稿ステータス（draft, publish, private）
WP_POST_STATUS=publish

# カテゴリID（WordPress管理画面で確認）
WP_DEFAULT_CATEGORY=5

# 投稿者ID
WP_AUTHOR_ID=1

# カスタムフィールド対応
WP_CUSTOM_FIELDS=true
```

#### 投稿時刻の調整
```bash
# 予約投稿として設定
WP_SCHEDULE_OFFSET="+2 hours" python3 scripts/post_to_wp.py
```

### 4. 画像設定のカスタマイズ

#### 画像検索キーワードの調整
```python
# scripts/fetch_image.py を編集
def get_image_keywords(theme):
    """テーマから画像検索キーワードを生成"""
    # カスタムマッピング
    keyword_map = {
        "健康": ["wellness", "healthy lifestyle", "fitness"],
        "仕事": ["productivity", "office", "business"],
        "お金": ["finance", "investment", "savings"],
    }
    # マッピングを使用
    for key, keywords in keyword_map.items():
        if key in theme:
            return keywords
    # デフォルト
    return [theme, "japan", "lifestyle"]
```

#### 画像サイズの指定
```bash
# 環境変数で設定
IMAGE_WIDTH=1200
IMAGE_HEIGHT=630
IMAGE_QUALITY=85
```

## 🔧 高度な使い方

### 1. 複数サイト運用

#### サイト別設定ファイル
```bash
# サイト1用設定
cp .env .env.site1
# サイト2用設定
cp .env .env.site2

# サイト別実行
env $(cat .env.site1 | xargs) make run
env $(cat .env.site2 | xargs) make run
```

#### 並列実行スクリプト
```bash
#!/bin/bash
# run_multiple_sites.sh

sites=("site1" "site2" "site3")

for site in "${sites[@]}"; do
    echo "Processing $site..."
    env $(cat .env.$site | xargs) python3 scripts/pipeline_orchestrator.py &
done

wait
echo "All sites processed!"
```

### 2. A/Bテスト機能

```python
# カスタムA/Bテスト実装
import random

def generate_article_with_ab_test():
    """A/Bテストを含む記事生成"""
    
    # バリエーション選択
    variation = random.choice(['A', 'B'])
    
    if variation == 'A':
        # バージョンA: 短めのタイトル
        title_style = "concise"
        cta_position = "top"
    else:
        # バージョンB: 長めのタイトル
        title_style = "detailed"
        cta_position = "bottom"
    
    # メタデータに記録
    metadata = {
        "ab_test": {
            "variation": variation,
            "title_style": title_style,
            "cta_position": cta_position,
            "test_id": str(uuid.uuid4())
        }
    }
    
    return generate_article(metadata=metadata)
```

### 3. パフォーマンス分析

#### 実行時間の測定
```bash
# 詳細なパフォーマンスログ
PERFORMANCE_TRACKING=true python3 scripts/pipeline_orchestrator.py

# レポート確認
cat output/performance_report.json | jq '.'
```

#### メトリクス収集
```python
# カスタムメトリクス
def track_metrics():
    metrics = {
        "generation_time": 0,
        "api_calls": {
            "claude": 0,
            "unsplash": 0,
            "wordpress": 0
        },
        "token_usage": 0,
        "cost_estimate": 0
    }
    return metrics
```

### 4. カスタムワークフロー

#### 条件付き投稿
```python
# 特定条件での投稿制御
def should_post_today():
    """投稿すべきかどうかを判定"""
    
    # 休日チェック
    if is_holiday():
        return False
    
    # 既存記事チェック
    if has_recent_post_on_topic(theme):
        return False
    
    # トラフィック分析
    if get_site_traffic() < threshold:
        return False
    
    return True
```

## 📊 運用管理

### 1. コスト管理

#### API使用量の監視
```bash
# Claude API使用量確認
python3 scripts/check_claude_usage.py

# 画像API使用量
python3 scripts/check_image_api_usage.py

# 月次コストレポート
python3 scripts/generate_cost_report.py --month 2025-06
```

#### コスト最適化設定
```bash
# 低コストモード
CLAUDE_MODEL=claude-3-haiku-20240307  # 最も安価
IMAGE_API_PRIORITY=pexels,unsplash    # 無料優先
MAX_RETRIES=1                          # リトライ削減
```

### 2. 品質管理

#### 自動品質チェック
```python
# scripts/quality_check.py
def check_article_quality(content):
    """記事品質の自動チェック"""
    
    checks = {
        "length": len(content) >= 1600,
        "headings": content.count("##") >= 4,
        "keywords": check_keyword_density(content),
        "readability": calculate_readability_score(content),
        "originality": check_duplicate_content(content)
    }
    
    return all(checks.values()), checks
```

#### 品質レポート生成
```bash
# 週次品質レポート
python3 scripts/generate_quality_report.py --period week

# 結果確認
cat reports/quality_report_$(date +%Y%m%d).html
```

### 3. バックアップとリストア

#### 自動バックアップ設定
```bash
# 日次バックアップスクリプト
#!/bin/bash
# backup_daily.sh

BACKUP_DIR="/backup/blogauto/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# 設定ファイル
cp .env "$BACKUP_DIR/"
cp -r prompts/ "$BACKUP_DIR/"

# 生成データ
cp -r output/ "$BACKUP_DIR/"
cp -r logs/ "$BACKUP_DIR/"

# 圧縮
tar -czf "$BACKUP_DIR.tar.gz" "$BACKUP_DIR"
rm -rf "$BACKUP_DIR"
```

#### リストア手順
```bash
# バックアップからのリストア
tar -xzf /backup/blogauto/20250628.tar.gz
cp -r 20250628/* ./
```

## 🔧 トラブル対応

### 1. よくあるエラーと対処法

#### 記事生成エラー
```bash
# エラー: "Rate limit exceeded"
# 対処法:
sleep 60  # 1分待機
make run  # 再実行

# エラー: "Invalid API key"
# 対処法:
echo $ANTHROPIC_API_KEY  # キー確認
# Anthropic Consoleで有効性確認
```

#### WordPress投稿エラー
```bash
# エラー: "401 Unauthorized"
# 対処法:
# 1. Application Password再生成
# 2. .envファイル更新
# 3. スペースが含まれているか確認

# エラー: "413 Request Entity Too Large"
# 対処法:
# php.iniで以下を調整
# upload_max_filesize = 64M
# post_max_size = 64M
```

### 2. デバッグ方法

#### 詳細ログの有効化
```bash
# 最大詳細度でデバッグ
LOG_LEVEL=DEBUG python3 scripts/pipeline_orchestrator.py

# 特定モジュールのみ
DEBUG_MODULE=fetch_image python3 scripts/pipeline_orchestrator.py
```

#### ステップ実行
```python
# iPythonでのデバッグ
ipython
>>> from scripts.generate_article import ArticleGenerator
>>> gen = ArticleGenerator()
>>> gen.debug = True
>>> content = gen.generate_article_content("テスト", "2025年6月28日")
```

### 3. 緊急時の対応

#### 自動投稿の一時停止
```bash
# GitHub Actionsの無効化
# 1. GitHub → Settings → Actions
# 2. "Disable Actions" を選択

# または環境変数で制御
ENABLE_AUTO_POST=false
```

#### 手動でのロールバック
```bash
# 最後の投稿を下書きに戻す
python3 scripts/rollback_last_post.py

# 特定の投稿を削除
python3 scripts/delete_post.py --post-id 123
```

## 📈 パフォーマンスチューニング

### 1. 高速化設定

```bash
# 並列処理の有効化
ENABLE_PARALLEL=true
PARALLEL_WORKERS=3

# キャッシュの活用
ENABLE_CACHE=true
CACHE_TTL=3600  # 1時間

# 画像最適化
IMAGE_OPTIMIZE=true
IMAGE_MAX_SIZE=500KB
```

### 2. リソース制限

```bash
# メモリ制限
MEMORY_LIMIT=512M

# タイムアウト設定
GLOBAL_TIMEOUT=300  # 5分
API_TIMEOUT=30      # 30秒
```

## 🎯 ベストプラクティス

### 1. 日常運用のコツ

- **定期的なログ確認**: 週1回はエラーログを確認
- **APIキー管理**: 3ヶ月ごとにローテーション
- **バックアップ**: 週次で自動バックアップ
- **品質チェック**: 月1回は手動で記事品質確認

### 2. トラブル予防

- **API制限監視**: 使用量の80%でアラート
- **エラー通知**: Slack/Email連携で即座に把握
- **フォールバック**: 常に代替手段を準備
- **ドキュメント**: 変更内容は必ず記録

### 3. 拡張時の注意点

- **段階的導入**: 新機能は必ずテスト環境で検証
- **互換性維持**: 既存機能への影響を最小限に
- **パフォーマンス**: 追加機能による遅延を監視
- **セキュリティ**: 新しいAPIキーは適切に管理

## 📞 サポートとヘルプ

### トラブル時の確認手順

1. **ログ確認**: `logs/daily_blog.log`
2. **環境変数確認**: `env | grep -E "(API|WP)"`
3. **接続テスト**: `make test-connections`
4. **Issue検索**: GitHub Issuesで類似問題確認

### コミュニティサポート

- **GitHub Discussions**: 使い方の相談
- **Issues**: バグ報告・機能要望
- **Wiki**: 詳細なドキュメント

## 🎉 Happy Blogging!

BlogAutoを使って、高品質なコンテンツを自動生成し、読者に価値を提供し続けましょう！

---

*最終更新: 2025年6月28日*
*バージョン: 1.0.0*