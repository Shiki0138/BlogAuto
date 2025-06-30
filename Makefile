# Daily Blog Automation - Makefile
# 開発・テスト・デプロイ用コマンド集

.PHONY: help install test run clean setup dev prod lint format check

# デフォルトターゲット
help:
	@echo "Daily Blog Automation - 利用可能なコマンド:"
	@echo ""
	@echo "  make install    - 依存関係をインストール"
	@echo "  make setup      - 初期セットアップ"
	@echo "  make dev        - 開発環境で実行"
	@echo "  make test       - テストを実行"
	@echo "  make run        - 本番実行（統合パイプライン）"
	@echo "  make lint       - コード品質チェック"
	@echo "  make format     - コードフォーマット"
	@echo "  make clean      - 一時ファイルをクリーンアップ"
	@echo "  make check      - ヘルスチェック実行"

# 依存関係インストール
install:
	pip install -r requirements.txt

# 初期セットアップ
setup: install
	@echo "セットアップ開始..."
	@mkdir -p output logs tmp
	@touch output/.gitkeep logs/.gitkeep tmp/.gitkeep
	@if [ ! -f .env ]; then cp .env.example .env; echo ".env ファイルを作成しました。APIキーを設定してください。"; fi
	@echo "セットアップ完了！"

# 開発環境実行
dev:
	@echo "開発環境で実行中..."
	python scripts/pipeline_orchestrator.py test

# テスト実行
test:
	@echo "テスト実行中..."
	pytest tests/ -v --tb=short

# 統合テスト
integration-test:
	python scripts/pipeline_orchestrator.py integration

# 本番実行
run:
	@echo "本番パイプライン実行中..."
	python scripts/pipeline_orchestrator.py daily

# 個別スクリプト実行
generate:
	python scripts/generate_article.py

fetch:
	python scripts/fetch_image.py

post:
	python scripts/post_to_wp.py

# ヘルスチェック
check:
	python scripts/pipeline_orchestrator.py health

# コード品質チェック
lint:
	@echo "コード品質チェック中..."
	flake8 scripts/ tests/ --max-line-length=120 --exclude=__pycache__
	mypy scripts/ --ignore-missing-imports

# コードフォーマット
format:
	@echo "コードフォーマット中..."
	black scripts/ tests/ --line-length=120

# クリーンアップ
clean:
	@echo "クリーンアップ中..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache .coverage htmlcov
	rm -rf tmp/*.txt tmp/*.json
	@echo "クリーンアップ完了！"

# GitHub Actions ローカルテスト
act:
	act -W .github/workflows/daily-blog.yml --secret-file .env

# パフォーマンステスト
perf:
	@echo "パフォーマンステスト実行中..."
	time python scripts/pipeline_orchestrator.py daily

# ドキュメント生成
docs:
	@echo "ドキュメント生成中..."
	mkdocs build

# バージョン表示
version:
	@echo "Daily Blog Automation v1.0.0 (100%完成版)"
	@python --version
	@pip freeze | grep -E "(anthropic|requests|markdown|jinja2|Pillow)"

# 外部API接続テスト
api-test:
	@echo "外部API接続テスト実行..."
	ENABLE_EXTERNAL_API=true python scripts/pipeline_orchestrator.py api-test

# 環境変数確認
env-check:
	@echo "環境変数設定確認:"
	@echo "ANTHROPIC_API_KEY: $$(test -n "$$ANTHROPIC_API_KEY" && echo '✅ 設定済み' || echo '❌ 未設定')"
	@echo "WP_SITE_URL: $$(test -n "$$WP_SITE_URL" && echo '✅ 設定済み' || echo '❌ 未設定')"
	@echo "WP_USER: $$(test -n "$$WP_USER" && echo '✅ 設定済み' || echo '❌ 未設定')"
	@echo "WP_APP_PASS: $$(test -n "$$WP_APP_PASS" && echo '✅ 設定済み' || echo '❌ 未設定')"

# 最終完成確認
final-check:
	@echo "🎉 最終完成確認実行..."
	make check
	make test
	make integration-test
	make perf
	@echo "✅ BlogAuto 100%完成確認完了！"