#!/bin/bash

# 🚀 Agent間メッセージ送信スクリプト

# エージェント→tmuxターゲット マッピング
get_agent_target() {
    local project_name="$1"
    local agent="$2"
    
    case "$agent" in
        "president") echo "${project_name}_president" ;;
        "boss1") echo "${project_name}_multiagent:0.0" ;;
        "worker1") echo "${project_name}_multiagent:0.1" ;;
        "worker2") echo "${project_name}_multiagent:0.2" ;;
        "worker3") echo "${project_name}_multiagent:0.3" ;;
        "worker4") echo "${project_name}_multiagent:0.4" ;;
        "worker5") echo "${project_name}_multiagent:0.5" ;;
        *) echo "" ;;
    esac
}

show_usage() {
    cat << EOF
🤖 Agent間メッセージ送信

使用方法:
  $0 [プロジェクト名] [エージェント名] [メッセージ]
  $0 [プロジェクト名] --list

利用可能エージェント:
  president - プロジェクト統括責任者
  boss1     - チームリーダー  
  worker1   - 実行担当者A
  worker2   - 実行担当者B
  worker3   - 実行担当者C
  worker4   - 実行担当者D
  worker5   - 実行担当者E

使用例:
  $0 myproject president "指示書に従って"
  $0 myproject boss1 "Hello World プロジェクト開始指示"
  $0 myproject worker1 "作業完了しました"
EOF
}

# エージェント一覧表示
show_agents() {
    local project_name="$1"
    echo "📋 利用可能なエージェント (プロジェクト: $project_name):"
    echo "==========================================="
    echo "  president → ${project_name}_president:0     (プロジェクト統括責任者)"
    echo "  boss1     → ${project_name}_multiagent:0.0  (チームリーダー)"
    echo "  worker1   → ${project_name}_multiagent:0.1  (実行担当者A)"
    echo "  worker2   → ${project_name}_multiagent:0.2  (実行担当者B)" 
    echo "  worker3   → ${project_name}_multiagent:0.3  (実行担当者C)"
    echo "  worker4   → ${project_name}_multiagent:0.4  (実行担当者D)"
    echo "  worker5   → ${project_name}_multiagent:0.5  (実行担当者E)"
}

# ログ記録
log_send() {
    local project_name="$1"
    local agent="$2"
    local message="$3"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    mkdir -p logs
    echo "[$timestamp] [$project_name] $agent: SENT - \"$message\"" >> logs/send_log.txt
    
    # 開発ログにも記録
    mkdir -p development
    echo "[$timestamp] [COMMUNICATION] [$project_name] $agent: \"$message\"" >> development/development_log.txt
}

# メッセージ送信
send_message() {
    local target="$1"
    local message="$2"
    
    echo "📤 送信中: $target ← '$message'"
    
    # Claude Codeのプロンプトを一度クリア
    tmux send-keys -t "$target" C-c
    sleep 0.3
    
    # メッセージ送信
    tmux send-keys -t "$target" "$message"
    sleep 0.1
    
    # エンター押下
    tmux send-keys -t "$target" C-m
    sleep 0.5
}

# ターゲット存在確認
check_target() {
    local target="$1"
    local session_name="${target%%:*}"
    
    if ! tmux has-session -t "$session_name" 2>/dev/null; then
        echo "❌ セッション '$session_name' が見つかりません"
        return 1
    fi
    
    return 0
}

# メイン処理
main() {
    if [[ $# -eq 0 ]]; then
        show_usage
        exit 1
    fi
    
    local project_name="$1"
    
    # プロジェクト名検証
    if ! [[ "$project_name" =~ ^[a-zA-Z0-9_]+$ ]]; then
        echo "❌ エラー: プロジェクト名は英数字とアンダースコアのみ使用可能です"
        exit 1
    fi
    
    # --listオプション
    if [[ "$2" == "--list" ]]; then
        show_agents "$project_name"
        exit 0
    fi
    
    if [[ $# -lt 3 ]]; then
        show_usage
        exit 1
    fi
    
    local agent_name="$2"
    local message="$3"
    
    # エージェントターゲット取得
    local target
    target=$(get_agent_target "$project_name" "$agent_name")
    
    if [[ -z "$target" ]]; then
        echo "❌ エラー: 不明なエージェント '$agent_name'"
        echo "利用可能エージェント: $0 $project_name --list"
        exit 1
    fi
    
    # ターゲット確認
    if ! check_target "$target"; then
        exit 1
    fi
    
    # メッセージ送信
    send_message "$target" "$message"
    
    # ログ記録
    log_send "$project_name" "$agent_name" "$message"
    
    echo "✅ 送信完了: [$project_name] $agent_name に '$message'"
    
    return 0
}

main "$@" 