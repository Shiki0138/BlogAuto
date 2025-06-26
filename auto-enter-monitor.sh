#!/bin/bash

# 🔍 自動Enter監視システム
# テキストボックスに未送信メッセージが残っている状態を検出し、自動でEnterを送信

set -e

PROJECT_NAME="$1"
CHECK_INTERVAL="${2:-15}"  # チェック間隔（秒）デフォルト15秒

if [ -z "$PROJECT_NAME" ]; then
    echo "使用方法: $0 [プロジェクト名] [チェック間隔秒数]"
    echo "例: $0 hotel 15"
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
log_monitor() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [AUTO-ENTER] $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [AUTO-ENTER] [$PROJECT_NAME] [monitor] $1" >> development/development_log.txt
}

# tmuxペイン情報取得
get_pane_info() {
    local session="$1"
    local pane="$2"
    
    # ペインの最後の行を取得（プロンプトや入力状態確認）
    tmux capture-pane -t "$session:$pane" -p | tail -3
}

# 未送信メッセージ検出
detect_unsent_message() {
    local session="$1"
    local pane="$2"
    local pane_content
    
    pane_content=$(get_pane_info "$session" "$pane")
    
    # 未送信メッセージの典型的パターンを検出
    if echo "$pane_content" | grep -E "(あなたは|worker|boss|president)" | grep -v "C-m" | tail -1 | grep -v "^\s*$" > /dev/null; then
        # メッセージがあるが改行されていない（未送信）
        echo "unsent"
    elif echo "$pane_content" | grep -E "Claude Code.*\?" > /dev/null; then
        # Claude Code プロンプト待ちではない場合
        echo "prompt_waiting"
    elif echo "$pane_content" | grep -E "❌|Error|Failed" > /dev/null; then
        # エラー状態
        echo "error"
    else
        # 正常状態
        echo "normal"
    fi
}

# 自動Enter送信
send_auto_enter() {
    local session="$1"
    local pane="$2"
    local agent_name="$3"
    
    log_monitor "🔧 自動Enter送信: $agent_name ($session:$pane)"
    tmux send-keys -t "$session:$pane" C-m
    
    # 少し待ってから確認
    sleep 2
    local after_status=$(detect_unsent_message "$session" "$pane")
    
    if [ "$after_status" = "normal" ]; then
        log_monitor "✅ Enter送信成功: $agent_name"
    else
        log_monitor "⚠️ Enter送信後も異常: $agent_name ($after_status)"
        # 2回目のEnter送信
        tmux send-keys -t "$session:$pane" C-m
        log_monitor "🔧 追加Enter送信: $agent_name"
    fi
}

# 緊急修復処理
emergency_fix() {
    local session="$1"
    local pane="$2"
    local agent_name="$3"
    
    log_monitor "🚨 緊急修復開始: $agent_name"
    
    # Ctrl+C で現在の処理をキャンセル
    tmux send-keys -t "$session:$pane" C-c
    sleep 1
    
    # Enterを送信
    tmux send-keys -t "$session:$pane" C-m
    sleep 1
    
    # Claude再起動が必要かチェック
    local content=$(get_pane_info "$session" "$pane")
    if echo "$content" | grep -E "Claude.*exit|connection.*lost" > /dev/null; then
        log_monitor "🔄 Claude再起動: $agent_name"
        tmux send-keys -t "$session:$pane" 'claude --dangerously-skip-permissions' C-m
        sleep 3
    fi
    
    log_monitor "✅ 緊急修復完了: $agent_name"
}

# エージェント情報定義
AGENTS=(
    "president:$PRESIDENT_SESSION:0"
    "boss1:$MULTIAGENT_SESSION:0.0"
    "worker1:$MULTIAGENT_SESSION:0.1"
    "worker2:$MULTIAGENT_SESSION:0.2"
    "worker3:$MULTIAGENT_SESSION:0.3"
    "worker4:$MULTIAGENT_SESSION:0.4"
    "worker5:$MULTIAGENT_SESSION:0.5"
)

log_monitor "🔍 自動Enter監視システム起動"
log_monitor "プロジェクト: $PROJECT_NAME"
log_monitor "チェック間隔: ${CHECK_INTERVAL}秒"
log_monitor "監視対象: 7エージェント"

# メイン監視ループ
while true; do
    log_monitor "📊 監視サイクル開始"
    
    ISSUES_FOUND=0
    FIXES_APPLIED=0
    
    for agent_info in "${AGENTS[@]}"; do
        IFS=':' read -ra PARTS <<< "$agent_info"
        agent_name="${PARTS[0]}"
        session="${PARTS[1]}"
        pane="${PARTS[2]}"
        
        # セッション存在確認
        if ! tmux has-session -t "$session" 2>/dev/null; then
            log_monitor "⚠️ セッション未存在: $session ($agent_name)"
            continue
        fi
        
        # ペイン状態検出
        status=$(detect_unsent_message "$session" "$pane")
        
        case "$status" in
            "unsent")
                log_monitor "🔍 未送信メッセージ検出: $agent_name"
                send_auto_enter "$session" "$pane" "$agent_name"
                ISSUES_FOUND=$((ISSUES_FOUND + 1))
                FIXES_APPLIED=$((FIXES_APPLIED + 1))
                ;;
            "error")
                log_monitor "🚨 エラー状態検出: $agent_name"
                emergency_fix "$session" "$pane" "$agent_name"
                ISSUES_FOUND=$((ISSUES_FOUND + 1))
                FIXES_APPLIED=$((FIXES_APPLIED + 1))
                ;;
            "prompt_waiting")
                log_monitor "⏳ プロンプト待ち: $agent_name"
                ;;
            "normal")
                # 正常状態は通常ログに出力しない
                ;;
        esac
        
        sleep 0.5  # エージェント間の処理間隔
    done
    
    if [ $ISSUES_FOUND -gt 0 ]; then
        log_monitor "📋 監視結果: $ISSUES_FOUND 件の問題検出、$FIXES_APPLIED 件修復"
        
        # PRESIDENTに報告
        if command -v ./agent-send.sh &> /dev/null; then
            ./agent-send.sh "$PROJECT_NAME" "president" "自動Enter監視: $ISSUES_FOUND 件の問題を検出・修復しました"
        fi
    else
        log_monitor "✅ 全エージェント正常動作中"
    fi
    
    log_monitor "💤 ${CHECK_INTERVAL}秒待機中..."
    sleep "$CHECK_INTERVAL"
done