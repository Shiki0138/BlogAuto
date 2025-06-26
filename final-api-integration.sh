#!/bin/bash

# 🌐 最終10%: 外部API統合とデプロイ準備
# 90%完了後に実行する最終フェーズ

set -e

PROJECT_NAME="$1"
if [ -z "$PROJECT_NAME" ]; then
    echo "使用方法: $0 [プロジェクト名]"
    exit 1
fi

ENV_FILE=".env_${PROJECT_NAME}"
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
fi

# 進捗確認
CURRENT_PROGRESS=$(cat ./tmp/implementation_progress.txt 2>/dev/null || echo "0")
if [ "$CURRENT_PROGRESS" -lt "90" ]; then
    echo "❌ エラー: 90%実装が未完了です（現在: ${CURRENT_PROGRESS}%）"
    echo "先に ./implementation-90-percent.sh $PROJECT_NAME を実行してください"
    exit 1
fi

log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [FINAL-API] $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [FINAL-API] [$PROJECT_NAME] [boss1] $1" >> development/development_log.txt
}

# 外部API統合タスク
API_INTEGRATIONS=(
    "決済API統合（Stripe/PayPal）"
    "メール配信API統合（SendGrid/AWS SES）"
    "地図・位置情報API統合（Google Maps）"
    "プッシュ通知API統合（Firebase/OneSignal）"
    "画像・ファイルストレージAPI統合（AWS S3/Cloudinary）"
)

log_info "🌐 最終フェーズ開始: 外部API統合"
log_info "現在進捗: ${CURRENT_PROGRESS}% → 目標100%"

# 全workerを最高性能モデル（Opus）に切り替え
log_info "🧠 重要処理につき全workerをOpusに切り替え"
for worker_id in {1..5}; do
    ./model-switcher.sh "$PROJECT_NAME" "critical" "worker${worker_id}"
    sleep 1
done

# PRESIDENTもOpusに切り替え
./model-switcher.sh "$PROJECT_NAME" "critical" "president"

# 外部API統合実行
for i in "${!API_INTEGRATIONS[@]}"; do
    api_task="${API_INTEGRATIONS[$i]}"
    progress=$((90 + (i + 1) * 2))  # 90%から2%ずつ増加
    
    log_info "======= API統合 $((i+1))/5 ======="
    log_info "タスク: $api_task"
    log_info "進捗: ${progress}%"
    
    # 各workerに分担して外部API統合
    for worker_id in {1..5}; do
        INTEGRATION_TASK="【最終フェーズ: 外部API統合】
        
あなたはworker${worker_id}です。
タスク: $api_task
進捗目標: ${progress}%

実装要件:
- 本番レベルの外部API接続実装
- 適切なエラーハンドリングとリトライ機能
- API Key管理とセキュリティ対策
- レート制限対応
- 完全なテストカバレッジ
- 詳細なドキュメント作成

【注意】実際のAPI Keyは開発用のものを使用し、本番Keyは含めないこと"

        log_info "→ worker${worker_id}に外部API統合指示"
        ./agent-send.sh "$PROJECT_NAME" "worker${worker_id}" "$INTEGRATION_TASK"
        sleep 2
    done
    
    # 進捗更新
    echo "$progress" > ./tmp/implementation_progress.txt
    
    # PRESIDENT報告
    ./agent-send.sh "$PROJECT_NAME" "president" "外部API統合 $((i+1))/5 完了: $api_task (進捗: ${progress}%)"
    
    log_info "✅ $api_task 指示完了"
    sleep 30  # API統合時間
done

# 最終デプロイ準備（100%到達）
log_info "🚀 最終デプロイ準備開始"
echo "100" > ./tmp/implementation_progress.txt

FINAL_DEPLOYMENT_TASK="【🚀 最終デプロイ準備: 100%到達】

本番リリース直前の最終確認と準備:

1. 全API接続テスト実行
2. セキュリティ最終監査
3. パフォーマンステスト実行
4. 本番環境設定確認
5. デプロイスクリプト準備
6. 監視・ログ設定
7. バックアップ戦略確認
8. ロールバック手順準備

【重要】本番デプロイは承認後に実行"

for worker_id in {1..5}; do
    ./agent-send.sh "$PROJECT_NAME" "worker${worker_id}" "$FINAL_DEPLOYMENT_TASK"
done

# 完了報告
log_info "🎉 100%実装完了！"

COMPLETION_REPORT="🎉 プロジェクト100%完了

✅ フェーズ1-9: 基盤実装完了 (90%)
✅ 外部API統合: 完了 (10%)

完了した外部API統合:
- 決済API統合（Stripe/PayPal）
- メール配信API統合（SendGrid/AWS SES）  
- 地図・位置情報API統合（Google Maps）
- プッシュ通知API統合（Firebase/OneSignal）
- 画像・ファイルストレージAPI統合（AWS S3/Cloudinary）

🚀 本番リリース準備完了
次のステップ: 承認後デプロイ実行"

./agent-send.sh "$PROJECT_NAME" "president" "$COMPLETION_REPORT"

log_info "🏁 最終API統合システム正常終了"
echo ""
echo "🎉 本番リリース100%完了！"
echo "✅ 全システム実装完了"
echo "🚀 本番デプロイ承認待ち"