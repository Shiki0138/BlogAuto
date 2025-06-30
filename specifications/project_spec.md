# 📋 プロジェクト仕様書

**変換日時**: 2025-06-29 23:42:30
**プロジェクト**: default

---

Daily Blog Automation – 初期プロジェクトスキャフォールド

目的: WordPress に毎日 09:00 JST で記事を自動投稿し、無料 API を優先してアイキャッチ画像を取得する完全自動パイプラインを構築する。
使い方: このリポジトリを fork / clone し、下記 Secrets を GitHub のリポジトリ設定に追加。手動実行するか、次の cron 実行を待つ。
今後の改善ポイント: プロンプト最適化、ユニットテスト追加、draft→publish 自動切替、分析フィードバックループ。

⸻

0. 目的と前提

項目	内容
ゴール	毎日 09:00 JST に WordPress へ新規記事＋画像を投稿
画像コスト	Unsplash → Pexels → Gemini → OpenAI の順に無料枠を利用
公開フロー	当面 draft 投稿→人間校閲→publish。
開発方式	すべて Claude Code CLI で生成・改修し、GitHub Actions で実行


⸻

1. リポジトリ構成

.
├─ .github/workflows/daily-blog.yml
├─ scripts/
│  ├─ generate_article.py
│  ├─ fetch_image.py
│  ├─ post_to_wp.py
│  └─ utils.py
├─ prompts/daily_blog.jinja
├─ requirements.txt
└─ README.md


⸻

2. GitHub Actions ワークフロー

ファイル: .github/workflows/daily-blog.yml

name: Daily Blog

on:
  schedule:
    - cron: '0 0 * * *'   # 09:00 JST
  workflow_dispatch:

jobs:
  publish:
    runs-on: ubuntu-latest
    env: { TZ: Asia/Tokyo }
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }

      - run: pip install -r requirements.txt

      - run: python scripts/generate_article.py
        env: { ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }} }

      - run: python scripts/fetch_image.py
        env:
          UNSPLASH_ACCESS_KEY: ${{ secrets.UNSPLASH_ACCESS_KEY }}
          PEXELS_API_KEY:      ${{ secrets.PEXELS_API_KEY }}
          GEMINI_API_KEY:      ${{ secrets.GEMINI_API_KEY }}
          OPENAI_API_KEY:      ${{ secrets.OPENAI_API_KEY }}

      - run: python scripts/post_to_wp.py
        env:
          WP_USER:     ${{ secrets.WP_USER }}
          WP_APP_PASS: ${{ secrets.WP_APP_PASS }}


⸻

3. Secrets 一覧

環境変数	用途
ANTHROPIC_API_KEY	Claude Code API
UNSPLASH_ACCESS_KEY	Unsplash API
PEXELS_API_KEY	Pexels API
GEMINI_API_KEY	Google Gemini（画像生成）
OPENAI_API_KEY	OpenAI（DALL·E fallback）
WP_USER / WP_APP_PASS	WordPress Application Password
YT_API_KEY	YouTube Data API（動画→記事機能用、任意）


⸻

4. スクリプト仕様

4.1 generate_article.py
	•	get_today_theme() でテーマ決定（固定リスト、Google Sheet など）
	•	Claude にプロンプト送信し Markdown 記事生成
	•	output/article.md と output/meta.json（タイトル・タグ・カテゴリー）を出力

4.2 fetch_image.py
	•	フロー: Unsplash → Pexels → Gemini → OpenAI の順に画像取得
	•	成功すると { "filepath": "output/cover.jpg", "credit": "Photo by … on Unsplash" } を返却
	•	NSFW フィルタ適用 (content_filter=high)
	•	すべて失敗時は画像なしで続行

4.3 post_to_wp.py
	1.	/media へ画像アップロード（base64）→ ID 取得
	2.	Markdown → HTML 変換（Python‑Markdown）
	3.	画像クレジットを <figcaption> として本文末尾へ挿入
	4.	/posts へ status=draft で投稿（環境変数で publish に変更可）

⸻

5. Claude プロンプト雛形 (prompts/daily_blog.jinja)

あなたは SEO に精通した日本語ライターです。
本日のテーマ: {{ theme }}
投稿日: {{ date_ja }}
## 生成ルール
- 1600〜1800 文字
- H2 見出しを 4 本、必要なら H3
- 箇条書きは "- " を使用
- 結論セクション必須
- 読者行動 CTA を最後に 1 文


⸻

6. requirements.txt

anthropic>=0.24.0
python-dotenv
requests
markdown
jinja2
Pillow
# ↓任意（YouTube 拡張用）
youtube-transcript-api
whisperx


⸻

7. 品質・運用ポリシー
	•	生成後にキーワード重複チェックを実施
	•	画像ライセンス表記を必ず挿入
	•	<script> タグ除去で XSS 防止
	•	logging で INFO 出力 → GitHub Actions ログ確認
	•	pytest で API モックを使ったユニットテストを推奨

⸻

8. 実装手順サマリ
	1.	git init → claude code で各ファイルを生成（コマンド例は README に記載）
	2.	GitHub Secrets を追加
	3.	GitHub Actions を手動実行し WordPress の下書きを確認
	4.	品質が安定したら status を publish に変更

⸻

9. YouTube 動画 → ブログ記事拡張（オプション）

項目	内容
新規スクリプト	scripts/fetch_transcript.py
役割	動画 URL → 字幕取得 → output/transcript.txt 保存字幕が無い場合は Whisper で文字起こし
generate_article.py	--transcript-file オプションに対応し、本文生成プロンプトへ挿入
追加 Secret	YT_API_KEY


⸻

---

**注意**: この仕様書は全エージェントが参照します。変更時は必ずPRESIDENTの承認を得てください。
