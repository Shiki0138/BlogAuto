#!/bin/bash

# 🚀 Smart Agent間メッセージ送信スクリプト (エラー監視・自動リトライ機能付き)

# 設定
MAX_RETRIES=3
RETRY_DELAY=2
LOG_DIR="logs"
RETRY_LOG="$LOG_DIR/retry_log.txt"
ERROR_LOG="$LOG_DIR/error_log.txt"
ANALYTICS_LOG="$LOG_DIR/analytics_log.txt"

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
🤖 Smart Agent間メッセージ送信 (エラー監視・自動リトライ機能付き)

使用方法:
  $0 [プロジェクト名] [エージェント名] [メッセージ] [オプション]
  $0 [プロジェクト名] --list
  $0 --monitor                       # リアルタイム監視モード
  $0 --analyze [期間]                # エラー分析レポート
  $0 --health                        # システムヘルスチェック

オプション:
  --priority [high|normal|low]       # メッセージ優先度
  --timeout [秒]                     # タイムアウト設定
  --no-retry                         # 自動リトライ無効化
  --silent                           # サイレントモード

利用可能エージェント:
  president - プロジェクト統括責任者
  boss1     - チームリーダー  
  worker1   - 実行担当者A
  worker2   - 実行担当者B
  worker3   - 実行担当者C
  worker4   - 実行担当者D
  worker5   - 実行担当者E

使用例:
  $0 myproject president "指示書に従って" --priority high
  $0 myproject boss1 "Hello World プロジェクト開始指示"
  $0 myproject worker1 "作業完了しました" --timeout 30
  $0 --monitor
  $0 --analyze today
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

# ログディレクトリ作成
init_logs() {
    mkdir -p "$LOG_DIR"
    touch "$RETRY_LOG" "$ERROR_LOG" "$ANALYTICS_LOG"
}

# ログ記録（詳細版）
log_send() {
    local project_name="$1"
    local agent="$2"
    local message="$3"
    local status="$4"
    local retry_count="${5:-0}"
    local error_message="${6:-}"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local milliseconds=$(date '+%N' | cut -c1-3)
    
    # 基本ログ
    echo "[$timestamp.$milliseconds] [$project_name] $agent: $status - \"$message\"" >> logs/send_log.txt
    
    # 開発ログ
    echo "[$timestamp] [COMMUNICATION] [$project_name] $agent: \"$message\"" >> development/development_log.txt
    
    # リトライログ
    if [[ $retry_count -gt 0 ]]; then
        echo "[$timestamp.$milliseconds] [$project_name] $agent: RETRY #$retry_count - \"$message\"" >> "$RETRY_LOG"
    fi
    
    # エラーログ
    if [[ "$status" == "ERROR" ]] && [[ -n "$error_message" ]]; then
        echo "[$timestamp.$milliseconds] [$project_name] $agent: ERROR - \"$message\" - Error: $error_message" >> "$ERROR_LOG"
    fi
    
    # 分析用ログ（JSON形式）
    cat >> "$ANALYTICS_LOG" << EOF
{"timestamp":"$timestamp.$milliseconds","project":"$project_name","agent":"$agent","status":"$status","retry_count":$retry_count,"message":"$message","error":"$error_message"}
EOF
}

# メッセージ送信（エラーハンドリング付き）
send_message_with_retry() {
    local target="$1"
    local message="$2"
    local priority="${3:-normal}"
    local timeout="${4:-10}"
    local project_name="$5"
    local agent_name="$6"
    local retry_count=0
    local success=false
    
    while [[ $retry_count -lt $MAX_RETRIES ]]; do
        echo "📤 送信中 (試行 $((retry_count + 1))/$MAX_RETRIES): $target ← '$message'"
        
        # tmuxセッション確認
        if ! tmux has-session -t "${target%%:*}" 2>/dev/null; then
            log_send "$project_name" "$agent_name" "$message" "ERROR" "$retry_count" "Session not found"
            retry_count=$((retry_count + 1))
            sleep $RETRY_DELAY
            continue
        fi
        
        # Claude Codeのプロンプトを一度クリア
        if tmux send-keys -t "$target" C-c 2>/dev/null; then
            sleep 0.3
            
            # メッセージ送信
            if tmux send-keys -t "$target" "$message" 2>/dev/null; then
                sleep 0.1
                
                # エンター押下
                if tmux send-keys -t "$target" C-m 2>/dev/null; then
                    sleep 0.5
                    
                    # 送信確認（ウィンドウの存在チェック）
                    if tmux list-windows -t "${target%%:*}" 2>/dev/null | grep -q "${target##*:}"; then
                        log_send "$project_name" "$agent_name" "$message" "SUCCESS" "$retry_count"
                        success=true
                        break
                    fi
                fi
            fi
        fi
        
        # エラーの場合
        log_send "$project_name" "$agent_name" "$message" "RETRY" "$retry_count" "Send failed"
        retry_count=$((retry_count + 1))
        
        if [[ $retry_count -lt $MAX_RETRIES ]]; then
            echo "⚠️  送信失敗。${RETRY_DELAY}秒後にリトライします..."
            sleep $RETRY_DELAY
        fi
    done
    
    if [[ "$success" == false ]]; then
        log_send "$project_name" "$agent_name" "$message" "ERROR" "$retry_count" "Max retries exceeded"
        echo "❌ 送信失敗: 最大リトライ回数を超えました"
        return 1
    fi
    
    return 0
}

# リアルタイム監視
monitor_mode() {
    echo "👁️  通信監視モード開始 (Ctrl+C で終了)"
    echo "=================================="
    
    # 監視ダッシュボード表示
    while true; do
        clear
        echo "📊 Agent通信監視ダッシュボード - $(date '+%Y-%m-%d %H:%M:%S')"
        echo "=================================="
        
        # 最近の送信状況
        echo -e "\n📤 最近の送信 (直近10件):"
        tail -10 logs/send_log.txt 2>/dev/null || echo "  (データなし)"
        
        # エラー状況
        echo -e "\n❌ 最近のエラー (直近5件):"
        tail -5 "$ERROR_LOG" 2>/dev/null || echo "  (エラーなし)"
        
        # リトライ状況
        echo -e "\n🔄 最近のリトライ (直近5件):"
        tail -5 "$RETRY_LOG" 2>/dev/null || echo "  (リトライなし)"
        
        # 統計情報
        if [[ -f "$ANALYTICS_LOG" ]]; then
            echo -e "\n📈 統計情報:"
            local total=$(wc -l < "$ANALYTICS_LOG")
            local success=$(grep -c '"status":"SUCCESS"' "$ANALYTICS_LOG" 2>/dev/null || echo 0)
            local errors=$(grep -c '"status":"ERROR"' "$ANALYTICS_LOG" 2>/dev/null || echo 0)
            local retries=$(grep -c '"status":"RETRY"' "$ANALYTICS_LOG" 2>/dev/null || echo 0)
            
            echo "  総送信数: $total"
            echo "  成功: $success ($(awk "BEGIN {printf \"%.1f\", ($success/$total)*100}")%)"
            echo "  エラー: $errors ($(awk "BEGIN {printf \"%.1f\", ($errors/$total)*100}")%)"
            echo "  リトライ: $retries"
        fi
        
        sleep 2
    done
}

# エラー分析
analyze_errors() {
    local period="${1:-today}"
    local start_date
    local end_date=$(date '+%Y-%m-%d')
    
    case "$period" in
        "today")
            start_date=$(date '+%Y-%m-%d')
            ;;
        "week")
            start_date=$(date -d '7 days ago' '+%Y-%m-%d' 2>/dev/null || date -v-7d '+%Y-%m-%d')
            ;;
        "month")
            start_date=$(date -d '30 days ago' '+%Y-%m-%d' 2>/dev/null || date -v-30d '+%Y-%m-%d')
            ;;
        *)
            start_date="$period"
            ;;
    esac
    
    echo "📊 エラー分析レポート ($start_date ～ $end_date)"
    echo "============================================="
    
    if [[ ! -f "$ANALYTICS_LOG" ]]; then
        echo "分析データがありません"
        return
    fi
    
    # エラー統計
    echo -e "\n📈 エラー統計:"
    local total_errors=$(grep -c '"status":"ERROR"' "$ANALYTICS_LOG" 2>/dev/null || echo 0)
    local total_retries=$(grep -c '"status":"RETRY"' "$ANALYTICS_LOG" 2>/dev/null || echo 0)
    echo "  総エラー数: $total_errors"
    echo "  総リトライ数: $total_retries"
    
    # エージェント別エラー
    echo -e "\n👥 エージェント別エラー数:"
    for agent in president boss1 worker1 worker2 worker3 worker4 worker5; do
        local count=$(grep "\"agent\":\"$agent\".*\"status\":\"ERROR\"" "$ANALYTICS_LOG" 2>/dev/null | wc -l)
        if [[ $count -gt 0 ]]; then
            echo "  $agent: $count"
        fi
    done
    
    # プロジェクト別エラー
    echo -e "\n📁 プロジェクト別エラー数:"
    grep '"status":"ERROR"' "$ANALYTICS_LOG" 2>/dev/null | \
        jq -r '.project' 2>/dev/null | sort | uniq -c | sort -rn | head -10
    
    # エラーパターン
    echo -e "\n🔍 エラーパターン:"
    grep '"status":"ERROR"' "$ANALYTICS_LOG" 2>/dev/null | \
        jq -r '.error' 2>/dev/null | sort | uniq -c | sort -rn | head -10
    
    # 時間帯別エラー
    echo -e "\n🕐 時間帯別エラー分布:"
    grep '"status":"ERROR"' "$ANALYTICS_LOG" 2>/dev/null | \
        jq -r '.timestamp' 2>/dev/null | cut -d' ' -f2 | cut -d: -f1 | \
        sort | uniq -c | sort -k2n
    
    # 推奨事項
    echo -e "\n💡 推奨事項:"
    if [[ $total_errors -gt 50 ]]; then
        echo "  ⚠️  エラー数が多いです。システムの安定性を確認してください。"
    fi
    if [[ $total_retries -gt 100 ]]; then
        echo "  ⚠️  リトライ数が多いです。ネットワークまたはtmuxセッションを確認してください。"
    fi
}

# システムヘルスチェック
health_check() {
    echo "🏥 システムヘルスチェック"
    echo "========================="
    
    # tmuxセッション確認
    echo -e "\n📺 tmuxセッション状態:"
    tmux list-sessions 2>/dev/null || echo "  ❌ tmuxセッションが見つかりません"
    
    # ログファイル確認
    echo -e "\n📝 ログファイル状態:"
    for log in "$RETRY_LOG" "$ERROR_LOG" "$ANALYTICS_LOG" "logs/send_log.txt"; do
        if [[ -f "$log" ]]; then
            local size=$(du -h "$log" | cut -f1)
            local lines=$(wc -l < "$log")
            echo "  ✅ $log: $size ($lines 行)"
        else
            echo "  ❌ $log: 存在しません"
        fi
    done
    
    # 最近のエラー率
    if [[ -f "$ANALYTICS_LOG" ]]; then
        echo -e "\n📊 直近100件のエラー率:"
        local recent=$(tail -100 "$ANALYTICS_LOG" 2>/dev/null)
        local total=$(echo "$recent" | wc -l)
        local errors=$(echo "$recent" | grep -c '"status":"ERROR"' 2>/dev/null || echo 0)
        local error_rate=$(awk "BEGIN {printf \"%.1f\", ($errors/$total)*100}")
        
        if (( $(echo "$error_rate > 10" | bc -l) )); then
            echo "  ⚠️  エラー率: ${error_rate}% (高い)"
        else
            echo "  ✅ エラー率: ${error_rate}% (正常)"
        fi
    fi
    
    # ディスク容量
    echo -e "\n💾 ディスク容量:"
    df -h . | tail -1 | awk '{print "  使用率: " $5 " (利用可能: " $4 ")"}'
}

# メイン処理
main() {
    init_logs
    
    if [[ $# -eq 0 ]]; then
        show_usage
        exit 1
    fi
    
    # 特殊コマンド処理
    case "$1" in
        "--monitor")
            monitor_mode
            exit 0
            ;;
        "--analyze")
            analyze_errors "${2:-today}"
            exit 0
            ;;
        "--health")
            health_check
            exit 0
            ;;
    esac
    
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
    local priority="normal"
    local timeout="10"
    local no_retry=false
    local silent=false
    
    # オプション解析
    shift 3
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --priority)
                priority="$2"
                shift 2
                ;;
            --timeout)
                timeout="$2"
                shift 2
                ;;
            --no-retry)
                no_retry=true
                MAX_RETRIES=1
                shift
                ;;
            --silent)
                silent=true
                shift
                ;;
            *)
                echo "❌ 不明なオプション: $1"
                exit 1
                ;;
        esac
    done
    
    # エージェントターゲット取得
    local target
    target=$(get_agent_target "$project_name" "$agent_name")
    
    if [[ -z "$target" ]]; then
        echo "❌ エラー: 不明なエージェント '$agent_name'"
        echo "利用可能エージェント: $0 $project_name --list"
        exit 1
    fi
    
    # メッセージ送信
    if [[ "$silent" != true ]]; then
        echo "🚀 Smart Agent Send - プロジェクト: $project_name"
        echo "  エージェント: $agent_name"
        echo "  優先度: $priority"
        echo "  タイムアウト: ${timeout}秒"
        echo "  リトライ: $([ "$no_retry" == true ] && echo "無効" || echo "有効 (最大${MAX_RETRIES}回)")"
    fi
    
    if send_message_with_retry "$target" "$message" "$priority" "$timeout" "$project_name" "$agent_name"; then
        [[ "$silent" != true ]] && echo "✅ 送信完了: [$project_name] $agent_name に '$message'"
        return 0
    else
        [[ "$silent" != true ]] && echo "❌ 送信失敗: [$project_name] $agent_name"
        return 1
    fi
}

# jqがインストールされていない場合の警告
if ! command -v jq &> /dev/null; then
    echo "⚠️  警告: jqがインストールされていません。分析機能が制限されます。"
    echo "  インストール: brew install jq (Mac) / apt-get install jq (Linux)"
fi

main "$@"