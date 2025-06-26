#!/bin/bash

# 🧠 Claude Code モデル切り替えシステム
# タスクの複雑度に応じて自動的にSonnet/Opus/Haikuを使い分け

set -e

# プロジェクト名取得
PROJECT_NAME="$1"
TASK_TYPE="$2"  # simple, complex, critical
TARGET_AGENT="$3"  # president, boss1, worker1-5
CUSTOM_MODEL="$4"  # 任意のモデル指定

if [ -z "$PROJECT_NAME" ] || [ -z "$TASK_TYPE" ] || [ -z "$TARGET_AGENT" ]; then
    echo "使用方法: $0 [プロジェクト名] [タスク種別] [対象エージェント] [カスタムモデル(任意)]"
    echo ""
    echo "タスク種別:"
    echo "  simple   - 簡単なタスク（ドキュメント、設定等）→ Haiku"
    echo "  standard - 標準的なタスク（実装、レビュー等）→ Sonnet"
    echo "  complex  - 複雑なタスク（アーキテクチャ、最適化等）→ Opus"
    echo "  critical - 重要なタスク（セキュリティ、品質管理等）→ Opus"
    echo ""
    echo "対象エージェント: president, boss1, worker1, worker2, worker3, worker4, worker5"
    echo ""
    echo "例: $0 hotel complex worker1"
    exit 1
fi

# 環境変数読み込み
ENV_FILE=".env_${PROJECT_NAME}"
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
fi

# ログ関数
log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [MODEL-SWITCH] $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [MODEL-SWITCH] [$PROJECT_NAME] [$TARGET_AGENT] $1" >> development/development_log.txt
}

# tmuxペイン特定
get_tmux_pane() {
    local agent="$1"
    
    case "$agent" in
        "president")
            echo "${PRESIDENT_SESSION}"
            ;;
        "boss1")
            echo "${MULTIAGENT_SESSION}:0.0"
            ;;
        "worker1")
            echo "${MULTIAGENT_SESSION}:0.1"
            ;;
        "worker2")
            echo "${MULTIAGENT_SESSION}:0.2"
            ;;
        "worker3")
            echo "${MULTIAGENT_SESSION}:0.3"
            ;;
        "worker4")
            echo "${MULTIAGENT_SESSION}:0.4"
            ;;
        "worker5")
            echo "${MULTIAGENT_SESSION}:0.5"
            ;;
        *)
            echo "unknown"
            ;;
    esac
}

# モデル選択ロジック（Claude判断ベース）
select_model() {
    local task_type="$1"
    local custom_model="$2"
    local task_content="$3"
    
    # カスタムモデル指定があればそれを使用
    if [ ! -z "$custom_model" ]; then
        echo "$custom_model"
        return
    fi
    
    # Claude判断による自動選択
    if [ ! -z "$task_content" ]; then
        # タスク内容を分析して適切なモデルを選択
        if echo "$task_content" | grep -i "critical\|security\|authentication\|payment\|database" > /dev/null; then
            echo "opus"   # 重要・セキュリティ関連
        elif echo "$task_content" | grep -i "complex\|architecture\|optimization\|algorithm" > /dev/null; then
            echo "opus"   # 複雑な処理
        elif echo "$task_content" | grep -i "document\|readme\|config\|simple\|basic" > /dev/null; then
            echo "haiku"  # 簡単なタスク
        else
            echo "sonnet" # 標準的なタスク
        fi
    else
        # タスク種別による選択（従来ロジック）
        case "$task_type" in
            "simple")
                echo "haiku"  # 簡単なタスク: 高速・低コスト
                ;;
            "standard")
                echo "sonnet" # 標準的なタスク: バランス重視
                ;;
            "complex")
                echo "opus"   # 複雑なタスク: 高性能
                ;;
            "critical")
                echo "opus"   # 重要なタスク: 最高品質
                ;;
            *)
                echo "sonnet" # デフォルト
                ;;
        esac
    fi
}

# コスト見積もり
estimate_cost() {
    local model="$1"
    
    case "$model" in
        "haiku")
            echo "低コスト（高速処理）"
            ;;
        "sonnet")
            echo "中コスト（バランス）"
            ;;
        "opus")
            echo "高コスト（高品質）"
            ;;
        *)
            echo "不明"
            ;;
    esac
}

# メイン処理
TMUX_PANE=$(get_tmux_pane "$TARGET_AGENT")
SELECTED_MODEL=$(select_model "$TASK_TYPE" "$CUSTOM_MODEL")
COST_ESTIMATE=$(estimate_cost "$SELECTED_MODEL")

if [ "$TMUX_PANE" = "unknown" ]; then
    echo "❌ エラー: 不明なエージェント: $TARGET_AGENT"
    exit 1
fi

log_info "🧠 モデル切り替え開始"
log_info "対象: $TARGET_AGENT ($TMUX_PANE)"
log_info "タスク種別: $TASK_TYPE"
log_info "選択モデル: $SELECTED_MODEL"
log_info "コスト見積: $COST_ESTIMATE"

# 現在のモデルを確認（可能であれば）
log_info "📋 モデル切り替え実行中..."

# Claude Code モデル切り替えコマンド実行
if [ "$TARGET_AGENT" = "president" ]; then
    # PRESIDENTセッション
    tmux send-keys -t "$TMUX_PANE" "claude --model $SELECTED_MODEL --dangerously-skip-permissions" C-m
else
    # MULTIAGENTセッション
    tmux send-keys -t "$TMUX_PANE" "claude --model $SELECTED_MODEL --dangerously-skip-permissions" C-m
fi

# 切り替え確認待機
sleep 3

log_info "✅ モデル切り替え完了"
log_info "新モデル: $SELECTED_MODEL ($COST_ESTIMATE)"

# 成功通知
echo "🧠 モデル切り替え完了"
echo "  対象: $TARGET_AGENT"
echo "  モデル: $SELECTED_MODEL"
echo "  コスト: $COST_ESTIMATE"
echo ""

# 使用状況を記録
echo "[$(date '+%Y-%m-%d %H:%M:%S')] $TARGET_AGENT: $TASK_TYPE → $SELECTED_MODEL" >> ./tmp/model_usage_log.txt

# PRESIDENTに報告（workerの場合のみ）
if [[ "$TARGET_AGENT" =~ ^worker[1-5]$ ]]; then
    ./agent-send.sh "$PROJECT_NAME" "president" "モデル切り替え完了: $TARGET_AGENT → $SELECTED_MODEL ($TASK_TYPE タスク用)"
fi