#!/bin/bash

# 🔄 Boss自動サイクルスクリプト
# 一定時間ごとにワーカーの状態を確認し、次の指示を自動発行

set -e

# 設定
CYCLE_INTERVAL=30  # サイクル間隔（秒）
MAX_CYCLES=10      # 最大サイクル数

# プロジェクト名取得
if [ -z "$1" ]; then
    echo "使用方法: $0 [プロジェクト名]"
    echo "例: $0 hotel"
    exit 1
fi

PROJECT_NAME="$1"
ENV_FILE=".env_${PROJECT_NAME}"

# 環境変数読み込み
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
else
    echo "❌ エラー: 環境ファイルが見つかりません: $ENV_FILE"
    exit 1
fi

# ログ関数
log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [AUTO-CYCLE] $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [AUTO_CYCLE] [$PROJECT_NAME] [boss1] $1" >> development/development_log.txt
}

# タスクリスト
TASKS=(
    "仕様書を再確認して実装計画を作成"
    "開発環境のセットアップを実施"
    "基本機能の実装を開始"
    "テストコードの作成"
    "コードレビューとリファクタリング"
    "ドキュメント作成と更新"
    "デプロイ準備と確認"
    "パフォーマンス最適化"
    "セキュリティチェック"
    "最終品質確認"
)

# サイクルカウンター初期化
CYCLE_COUNT=0
if [ -f "./tmp/cycle_count.txt" ]; then
    CYCLE_COUNT=$(cat ./tmp/cycle_count.txt)
fi

log_info "🔄 自動サイクルシステム起動"
log_info "プロジェクト: $PROJECT_NAME"
log_info "サイクル間隔: ${CYCLE_INTERVAL}秒"
log_info "最大サイクル数: $MAX_CYCLES"
echo ""

# メインループ
while [ $CYCLE_COUNT -lt $MAX_CYCLES ]; do
    CYCLE_COUNT=$((CYCLE_COUNT + 1))
    echo $CYCLE_COUNT > ./tmp/cycle_count.txt
    
    log_info "======= サイクル $CYCLE_COUNT 開始 ======="
    
    # 完了ファイルチェック
    COMPLETED_WORKERS=0
    for i in {1..5}; do
        if [ -f "./tmp/worker${i}_done.txt" ]; then
            COMPLETED_WORKERS=$((COMPLETED_WORKERS + 1))
        fi
    done
    
    log_info "完了ワーカー数: $COMPLETED_WORKERS / 5"
    
    # 全員完了またはタイムアウトで次のタスク発行
    if [ $COMPLETED_WORKERS -eq 5 ] || [ $COMPLETED_WORKERS -gt 0 ]; then
        # 完了ファイルクリア
        rm -f ./tmp/worker*_done.txt
        
        # 次のタスク選択
        TASK_INDEX=$(( ($CYCLE_COUNT - 1) % ${#TASKS[@]} ))
        CURRENT_TASK="${TASKS[$TASK_INDEX]}"
        
        log_info "📋 次のタスク: $CURRENT_TASK"
        
        # 各ワーカーに指示
        for i in {1..5}; do
            MESSAGE="あなたはworker${i}です。タスク実行: $CURRENT_TASK"
            log_info "→ worker${i}に指示送信"
            ./agent-send.sh "$PROJECT_NAME" "worker${i}" "$MESSAGE"
            sleep 1
        done
        
        log_info "✅ サイクル $CYCLE_COUNT 指示完了"
        
        # PRESIDENTに進捗報告
        ./agent-send.sh "$PROJECT_NAME" "president" "サイクル${CYCLE_COUNT}完了: ${CURRENT_TASK}を全workerに指示しました"
    else
        log_info "⏳ ワーカー作業中... (${CYCLE_INTERVAL}秒後に再チェック)"
    fi
    
    # 次のサイクルまで待機
    echo ""
    log_info "💤 ${CYCLE_INTERVAL}秒待機中..."
    sleep $CYCLE_INTERVAL
done

log_info "🏁 最大サイクル数に到達しました"
log_info "自動サイクルシステム終了"

# 最終報告
./agent-send.sh "$PROJECT_NAME" "president" "自動サイクル完了: 全${MAX_CYCLES}サイクル実行完了"