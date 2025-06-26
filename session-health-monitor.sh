#!/bin/bash

# 🏥 セッション健康監視システム
# 全エージェントの状態を総合的に監視し、問題を早期発見・自動修復

set -e

PROJECT_NAME="$1"
MONITORING_INTERVAL="${2:-20}"  # 監視間隔（秒）デフォルト20秒

if [ -z "$PROJECT_NAME" ]; then
    echo "使用方法: $0 [プロジェクト名] [監視間隔秒数]"
    echo "例: $0 hotel 20"
    exit 1
fi

ENV_FILE=".env_${PROJECT_NAME}"
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
else
    echo "❌ エラー: 環境ファイルが見つかりません: $ENV_FILE"
    exit 1
fi

# ログ関数
log_health() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [HEALTH] $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [HEALTH] [$PROJECT_NAME] [monitor] $1" >> development/development_log.txt
}

# エージェント健康チェック
check_agent_health() {
    local agent_name="$1"
    local session="$2"
    local pane="$3"
    
    # セッション存在確認
    if ! tmux has-session -t "$session" 2>/dev/null; then
        echo "session_missing"
        return
    fi
    
    # ペイン存在確認
    if ! tmux list-panes -t "$session:$pane" >/dev/null 2>&1; then
        echo "pane_missing"
        return
    fi
    
    # ペイン内容取得
    local content=$(tmux capture-pane -t "$session:$pane" -p | tail -5)
    
    # 状態判定
    if echo "$content" | grep -E "Claude Code.*>|❯|%|\$" > /dev/null; then
        echo "healthy"
    elif echo "$content" | grep -E "あなたは.*です" | grep -v "C-m" > /dev/null; then
        echo "unsent_message"
    elif echo "$content" | grep -E "Thinking|Processing|作業中|実行中" > /dev/null; then
        echo "working"
    elif echo "$content" | grep -E "❌|Error|Failed|connection.*lost|timeout" > /dev/null; then
        echo "error"
    elif echo "$content" | grep -E "loading|connecting|starting" > /dev/null; then
        echo "loading"
    elif echo "$content" | grep -E "Bypassing Permissions|Auto-update" > /dev/null; then
        echo "claude_updating"
    else
        echo "unknown"
    fi
}

# 自動修復処理
auto_repair() {
    local agent_name="$1"
    local session="$2"
    local pane="$3"
    local issue="$4"
    
    log_health "🔧 自動修復開始: $agent_name ($issue)"
    
    case "$issue" in
        "unsent_message")
            # 未送信メッセージを送信
            tmux send-keys -t "$session:$pane" C-m
            sleep 2
            log_health "✅ Enter送信: $agent_name"
            ;;
        "error")
            # エラー回復
            tmux send-keys -t "$session:$pane" C-c
            sleep 1
            tmux send-keys -t "$session:$pane" C-m
            sleep 2
            
            # Claude再起動が必要かチェック
            local content=$(tmux capture-pane -t "$session:$pane" -p | tail -3)
            if echo "$content" | grep -E "exit|lost|timeout" > /dev/null; then
                log_health "🔄 Claude再起動: $agent_name"
                tmux send-keys -t "$session:$pane" 'claude --dangerously-skip-permissions' C-m
                sleep 5
            fi
            log_health "✅ エラー修復: $agent_name"
            ;;
        "claude_updating")
            # Claude更新待ち
            log_health "⏳ Claude更新待ち: $agent_name"
            sleep 10
            # 更新後にプロンプトが表示されない場合はEnter送信
            local updated_content=$(tmux capture-pane -t "$session:$pane" -p | tail -3)
            if ! echo "$updated_content" | grep -E "Claude Code.*>" > /dev/null; then
                tmux send-keys -t "$session:$pane" C-m
                log_health "✅ 更新後Enter送信: $agent_name"
            fi
            ;;
        "session_missing")
            log_health "🚨 重大問題: セッション欠損 $agent_name ($session)"
            # セッション再作成は複雑なので警告のみ
            ;;
        "pane_missing")
            log_health "🚨 重大問題: ペイン欠損 $agent_name ($session:$pane)"
            ;;
    esac
}

# システム健康レポート生成
generate_health_report() {
    local healthy_count="$1"
    local total_count="$2"
    local issues="$3"
    
    local health_percentage=$((healthy_count * 100 / total_count))
    
    echo "🏥 システム健康レポート - $(date '+%Y-%m-%d %H:%M:%S')"
    echo "=================================="
    echo "プロジェクト: $PROJECT_NAME"
    echo "健康度: ${health_percentage}% (${healthy_count}/${total_count} エージェント)"
    echo ""
    
    if [ $health_percentage -ge 90 ]; then
        echo "✅ システム状態: 優良"
    elif [ $health_percentage -ge 70 ]; then
        echo "⚠️ システム状態: 注意"
    else
        echo "🚨 システム状態: 危険"
    fi
    
    if [ ! -z "$issues" ]; then
        echo ""
        echo "📋 検出された問題:"
        echo "$issues"
    fi
    
    echo ""
    echo "📊 推奨アクション:"
    if [ $health_percentage -lt 70 ]; then
        echo "  - 問題のあるエージェントを手動確認"
        echo "  - セッション再起動を検討"
    elif [ $health_percentage -lt 90 ]; then
        echo "  - 自動修復を継続監視"
    else
        echo "  - 現在の状態を維持"
    fi
}

# エージェント定義
AGENTS=(
    "president:$PRESIDENT_SESSION:0"
    "boss1:$MULTIAGENT_SESSION:0.0"
    "worker1:$MULTIAGENT_SESSION:0.1"
    "worker2:$MULTIAGENT_SESSION:0.2"
    "worker3:$MULTIAGENT_SESSION:0.3"
    "worker4:$MULTIAGENT_SESSION:0.4"
    "worker5:$MULTIAGENT_SESSION:0.5"
)

log_health "🏥 セッション健康監視システム起動"
log_health "プロジェクト: $PROJECT_NAME"
log_health "監視間隔: ${MONITORING_INTERVAL}秒"
log_health "監視対象: ${#AGENTS[@]} エージェント"

# メイン監視ループ
while true; do
    log_health "🔍 健康チェック開始"
    
    HEALTHY_COUNT=0
    TOTAL_COUNT=${#AGENTS[@]}
    ISSUES_DETECTED=""
    REPAIRS_MADE=0
    
    for agent_info in "${AGENTS[@]}"; do
        IFS=':' read -ra PARTS <<< "$agent_info"
        agent_name="${PARTS[0]}"
        session="${PARTS[1]}"
        pane="${PARTS[2]}"
        
        health_status=$(check_agent_health "$agent_name" "$session" "$pane")
        
        case "$health_status" in
            "healthy"|"working")
                HEALTHY_COUNT=$((HEALTHY_COUNT + 1))
                ;;
            "unsent_message"|"error"|"claude_updating")
                ISSUES_DETECTED="${ISSUES_DETECTED}  - $agent_name: $health_status\n"
                auto_repair "$agent_name" "$session" "$pane" "$health_status"
                REPAIRS_MADE=$((REPAIRS_MADE + 1))
                
                # 修復後再チェック
                sleep 3
                post_repair_status=$(check_agent_health "$agent_name" "$session" "$pane")
                if [ "$post_repair_status" = "healthy" ] || [ "$post_repair_status" = "working" ]; then
                    HEALTHY_COUNT=$((HEALTHY_COUNT + 1))
                fi
                ;;
            "session_missing"|"pane_missing")
                ISSUES_DETECTED="${ISSUES_DETECTED}  - $agent_name: $health_status (重大)\n"
                log_health "🚨 重大問題: $agent_name ($health_status)"
                ;;
            "loading"|"unknown")
                ISSUES_DETECTED="${ISSUES_DETECTED}  - $agent_name: $health_status (監視継続)\n"
                ;;
        esac
        
        sleep 0.5  # エージェント間チェック間隔
    done
    
    # 健康レポート生成
    health_report=$(generate_health_report "$HEALTHY_COUNT" "$TOTAL_COUNT" "$ISSUES_DETECTED")
    
    # ログ出力
    log_health "📊 健康チェック完了: ${HEALTHY_COUNT}/${TOTAL_COUNT} エージェント正常"
    if [ $REPAIRS_MADE -gt 0 ]; then
        log_health "🔧 自動修復実行: $REPAIRS_MADE 件"
    fi
    
    # レポートファイル保存
    echo "$health_report" > "./tmp/health_report.txt"
    
    # 重大問題時はPRESIDENTに即座に報告
    health_percentage=$((HEALTHY_COUNT * 100 / TOTAL_COUNT))
    if [ $health_percentage -lt 70 ]; then
        if command -v ./agent-send.sh &> /dev/null; then
            ./agent-send.sh "$PROJECT_NAME" "president" "🚨 システム健康度低下: ${health_percentage}% (${HEALTHY_COUNT}/${TOTAL_COUNT})" 2>/dev/null || true
        fi
    fi
    
    log_health "💤 ${MONITORING_INTERVAL}秒待機中..."
    sleep "$MONITORING_INTERVAL"
done