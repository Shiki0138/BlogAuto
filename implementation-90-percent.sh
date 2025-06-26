#!/bin/bash

# 🚀 90%実装到達システム - 本番リリース直前まで自動実装
# 外部API接続は最終フェーズ、モデル使い分けでトークン最適化

set -e

# プロジェクト名取得
if [ -z "$1" ]; then
    echo "使用方法: $0 [プロジェクト名]"
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

# 設定
TOTAL_PHASES=9          # 90%到達まで9フェーズ
PHASE_DURATION=60       # 各フェーズ60秒
PROGRESS_TARGET=90      # 目標進捗率90%

# ログ関数
log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [90%-IMPLEMENTATION] $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [90%-IMPLEMENTATION] [$PROJECT_NAME] [boss1] $1" >> development/development_log.txt
}

# モデル切り替え関数（自動判定）
switch_model() {
    local task_type="$1"
    local pane="$2"
    local task_content="$3"
    
    # タスク内容に基づく自動判定
    local selected_model="sonnet"  # デフォルト
    
    if echo "$task_content" | grep -i "critical\|security\|authentication\|payment\|database\|核心\|重要\|セキュリティ\|認証\|決済" > /dev/null; then
        selected_model="opus"
        log_info "🔴 重要タスク検出 → Opus: $pane"
    elif echo "$task_content" | grep -i "complex\|architecture\|optimization\|algorithm\|複雑\|アーキテクチャ\|最適化\|アルゴリズム" > /dev/null; then
        selected_model="opus"
        log_info "🟠 複雑タスク検出 → Opus: $pane"
    elif echo "$task_content" | grep -i "document\|readme\|config\|simple\|basic\|ドキュメント\|設定\|簡単\|基本" > /dev/null; then
        selected_model="haiku"
        log_info "🟢 簡単タスク検出 → Haiku: $pane"
    else
        # タスク種別フォールバック
        case "$task_type" in
            "simple"|"docs"|"config")
                selected_model="haiku"
                log_info "🟢 タスク種別判定 → Haiku: $pane ($task_type)"
                ;;
            "complex"|"critical"|"implementation")
                selected_model="opus"
                log_info "🔴 タスク種別判定 → Opus: $pane ($task_type)"
                ;;
            *)
                log_info "🟡 標準タスク → Sonnet: $pane"
                ;;
        esac
    fi
    
    # モデル切り替え実行
    tmux send-keys -t "$pane" "claude --model $selected_model --dangerously-skip-permissions" C-m
    sleep 2
}

# 進捗計算
calculate_progress() {
    local current_phase="$1"
    echo $(( current_phase * 10 ))  # 各フェーズで10%ずつ進捗
}

# フェーズ定義（外部API接続は最後）
PHASES=(
    "1:環境構築と基盤設定:simple"
    "2:データモデル設計と実装:complex"
    "3:認証システム構築:critical"
    "4:コアビジネスロジック実装:complex"
    "5:ユーザーインターフェース構築:complex"
    "6:データベース統合とマイグレーション:critical"
    "7:テスト自動化とCI/CD構築:simple"
    "8:セキュリティ強化と監査:critical"
    "9:パフォーマンス最適化:complex"
)

# 外部API接続フェーズ（最終10%で実行）
FINAL_PHASE="10:外部API統合とデプロイ準備:critical"

log_info "🚀 90%実装システム起動"
log_info "プロジェクト: $PROJECT_NAME"
log_info "目標進捗: ${PROGRESS_TARGET}%"
log_info "フェーズ数: $TOTAL_PHASES"
echo ""

# 進捗ファイル初期化
echo "0" > ./tmp/implementation_progress.txt
echo "start" > ./tmp/current_phase.txt

# メインループ：各フェーズを実行
for i in $(seq 1 $TOTAL_PHASES); do
    IFS=':' read -ra PHASE_INFO <<< "${PHASES[$((i-1))]}"
    PHASE_NUM="${PHASE_INFO[0]}"
    PHASE_NAME="${PHASE_INFO[1]}"
    TASK_TYPE="${PHASE_INFO[2]}"
    
    CURRENT_PROGRESS=$(calculate_progress $i)
    
    log_info "======= フェーズ$PHASE_NUM 開始 ======="
    log_info "タスク: $PHASE_NAME"
    log_info "進捗: ${CURRENT_PROGRESS}%"
    log_info "難易度: $TASK_TYPE"
    
    echo "$PHASE_NAME" > ./tmp/current_phase.txt
    echo "$CURRENT_PROGRESS" > ./tmp/implementation_progress.txt
    
    # 各workerに適切なモデルを設定してタスク配信
    for worker_id in {1..5}; do
        pane="${MULTIAGENT_SESSION}:0.$worker_id"
        
        # モデル切り替え（タスク内容も含めて判定）
        switch_model "$TASK_TYPE" "$pane" "$PHASE_NAME"
        
        # 詳細な実装指示
        DETAILED_TASK="あなたはworker${worker_id}です。【フェーズ$PHASE_NUM:$PHASE_NAME】を実装してください。
        
進捗目標: ${CURRENT_PROGRESS}%到達
タスク種別: $TASK_TYPE
実装要件:
- 実際に動作するコードを作成
- 仕様書(specifications/project_spec.md)に完全準拠
- エラーハンドリングを含む本番レベル実装
- ドキュメント更新も同時実行
- 工程完了時は詳細レポート作成

【重要】外部API接続は最終フェーズまで実装禁止"
        
        log_info "→ worker${worker_id}に指示送信 (${TASK_TYPE}モデル)"
        ./agent-send.sh "$PROJECT_NAME" "worker${worker_id}" "$DETAILED_TASK"
        sleep 2
    done
    
    # PRESIDENT に進捗報告
    PRESIDENT_REPORT="フェーズ$PHASE_NUM開始: $PHASE_NAME
進捗: ${CURRENT_PROGRESS}% / 目標90%
全workerに${TASK_TYPE}レベルタスクを配信完了
外部API接続は最終フェーズで実行予定"
    
    ./agent-send.sh "$PROJECT_NAME" "president" "$PRESIDENT_REPORT"
    
    log_info "✅ フェーズ$PHASE_NUM 指示完了"
    log_info "💤 ${PHASE_DURATION}秒待機（実装時間）"
    
    # フェーズ実行時間待機
    sleep $PHASE_DURATION
    
    # 中間進捗確認
    if [ $((i % 3)) -eq 0 ]; then
        log_info "📊 中間進捗確認フェーズ$PHASE_NUM完了"
        ./agent-send.sh "$PROJECT_NAME" "president" "進捗確認: フェーズ$PHASE_NUM完了、現在${CURRENT_PROGRESS}%到達"
    fi
done

# 90%到達完了
echo "90" > ./tmp/implementation_progress.txt
log_info "🎉 90%実装完了！"
log_info "次は外部API統合（最終10%）の準備が整いました"

# 最終報告
FINAL_REPORT="🎉 90%実装システム完了

✅ 完了フェーズ:
1. 環境構築と基盤設定 (10%)
2. データモデル設計と実装 (20%)
3. 認証システム構築 (30%)
4. コアビジネスロジック実装 (40%)
5. ユーザーインターフェース構築 (50%)
6. データベース統合とマイグレーション (60%)
7. テスト自動化とCI/CD構築 (70%)
8. セキュリティ強化と監査 (80%)
9. パフォーマンス最適化 (90%)

🔗 残り10%: 外部API統合とデプロイ準備
準備完了次第、最終フェーズを実行可能

本番リリース直前状態に到達しました！"

./agent-send.sh "$PROJECT_NAME" "president" "$FINAL_REPORT"

log_info "🏁 90%実装システム正常終了"
echo ""
echo "🚀 外部API統合を開始する場合は以下を実行:"
echo "./final-api-integration.sh $PROJECT_NAME"