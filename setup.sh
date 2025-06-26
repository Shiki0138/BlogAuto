#!/bin/bash

# 🚀 Multi-Agent Communication Demo 環境構築
# 参考: setup_full_environment.sh

set -e  # エラー時に停止

# コマンドラインオプション処理
AUTO_ATTACH=false
if [[ "$1" == "--attach" ]] || [[ "$2" == "--attach" ]]; then
    AUTO_ATTACH=true
fi

# プロジェクト名取得
PROJECT_NAME="$1"
if [[ "$1" == "--attach" ]]; then
    PROJECT_NAME="$2"
fi

if [ -z "$PROJECT_NAME" ]; then
    echo "🤖 Multi-Agent Communication Demo 環境構築"
    echo "==========================================="
    echo ""
    echo "📝 プロジェクト名を入力してください:"
    echo "   - 英数字とアンダースコアのみ使用可能"
    echo "   - 例: myproject, web_app, test_project"
    echo ""
    
    while true; do
        read -p "プロジェクト名: " PROJECT_NAME
        
        # 空文字チェック
        if [ -z "$PROJECT_NAME" ]; then
            echo "❌ プロジェクト名が入力されていません。再度入力してください。"
            continue
        fi
        
        # 文字種チェック
        if ! [[ "$PROJECT_NAME" =~ ^[a-zA-Z0-9_]+$ ]]; then
            echo "❌ プロジェクト名は英数字とアンダースコアのみ使用可能です。再度入力してください。"
            continue
        fi
        
        # 長さチェック
        if [ ${#PROJECT_NAME} -gt 20 ]; then
            echo "❌ プロジェクト名は20文字以内で入力してください。再度入力してください。"
            continue
        fi
        
        # 確認
        echo ""
        echo "📋 入力されたプロジェクト名: $PROJECT_NAME"
        read -p "この名前でよろしいですか？ (y/n): " confirm
        
        case "$confirm" in
            [yY]|[yY][eE][sS])
                break
                ;;
            [nN]|[nN][oO])
                echo "再度入力してください。"
                echo ""
                continue
                ;;
            *)
                echo "y または n で入力してください。"
                continue
                ;;
        esac
    done
    
    echo ""
    echo "✅ プロジェクト名が設定されました: $PROJECT_NAME"
    echo ""
fi

# コマンドライン引数での検証（プロンプト入力の場合は既に検証済み）
if [ "$1" ]; then
    if ! [[ "$PROJECT_NAME" =~ ^[a-zA-Z0-9_]+$ ]]; then
        echo "❌ エラー: プロジェクト名は英数字とアンダースコアのみ使用可能です"
        echo "使用方法: $0 [プロジェクト名]"
        echo "または引数なしでプロンプト入力: $0"
        exit 1
    fi
fi

# セッション名設定
MULTIAGENT_SESSION="${PROJECT_NAME}_multiagent"
PRESIDENT_SESSION="${PROJECT_NAME}_president"

# 色付きログ関数
log_info() {
    echo -e "\033[1;32m[INFO]\033[0m $1"
}

log_success() {
    echo -e "\033[1;34m[SUCCESS]\033[0m $1"
}

# プロンプト入力でない場合（引数指定）のタイトル表示
if [ "$1" ]; then
    echo "🤖 Multi-Agent Communication Demo 環境構築"
    echo "==========================================="
fi

echo "📋 プロジェクト名: $PROJECT_NAME"
echo "📋 multiagentセッション: $MULTIAGENT_SESSION"
echo "📋 presidentセッション: $PRESIDENT_SESSION"
echo ""

# STEP 1: 既存セッションクリーンアップ
log_info "🧹 既存セッションクリーンアップ開始..."

tmux kill-session -t "$MULTIAGENT_SESSION" 2>/dev/null && log_info "${MULTIAGENT_SESSION}セッション削除完了" || log_info "${MULTIAGENT_SESSION}セッションは存在しませんでした"
tmux kill-session -t "$PRESIDENT_SESSION" 2>/dev/null && log_info "${PRESIDENT_SESSION}セッション削除完了" || log_info "${PRESIDENT_SESSION}セッションは存在しませんでした"

# 完了ファイルクリア
mkdir -p ./tmp
rm -f ./tmp/worker*_done.txt 2>/dev/null && log_info "既存の完了ファイルをクリア" || log_info "完了ファイルは存在しませんでした"
rm -f ./tmp/cycle_*.txt 2>/dev/null && log_info "既存のサイクルファイルをクリア" || log_info "サイクルファイルは存在しませんでした"

log_success "✅ クリーンアップ完了"
echo ""

# STEP 2: multiagentセッション作成（6ペイン：boss1 + worker1,2,3,4,5）
log_info "📺 multiagentセッション作成開始 (6ペイン)..."

# 最初のペイン作成（ウィンドウ名を短縮）
tmux new-session -d -s "$MULTIAGENT_SESSION" -n "MA"

# 3x2グリッド作成（合計6ペイン）- 均等分割
# まず2行に分割
tmux split-window -v -t "${MULTIAGENT_SESSION}:0"      # 垂直分割（上下）
tmux select-layout -t "${MULTIAGENT_SESSION}:0" even-vertical

# 各行を3列に分割
tmux select-pane -t "${MULTIAGENT_SESSION}:0.0"
tmux split-window -h                                   # 上段を水平分割
tmux split-window -h                                   # 上段を3分割

tmux select-pane -t "${MULTIAGENT_SESSION}:0.3"
tmux split-window -h                                   # 下段を水平分割
tmux split-window -h                                   # 下段を3分割

# レイアウトを均等に調整
tmux select-layout -t "${MULTIAGENT_SESSION}:0" tiled

# ペインタイトル設定
log_info "ペインタイトル設定中..."
PANE_TITLES=("boss1" "worker1" "worker2" "worker3" "worker4" "worker5")

for i in {0..5}; do
    tmux select-pane -t "${MULTIAGENT_SESSION}:0.$i" -T "${PANE_TITLES[$i]}"
    
    # 作業ディレクトリ設定
    tmux send-keys -t "${MULTIAGENT_SESSION}:0.$i" "cd $(pwd)" C-m
    
    # カラープロンプト設定
    if [ $i -eq 0 ]; then
        # boss1: 赤色
        tmux send-keys -t "${MULTIAGENT_SESSION}:0.$i" "export PS1='(\[\033[1;31m\]${PANE_TITLES[$i]}\[\033[0m\]) \[\033[1;32m\]\w\[\033[0m\]\$ '" C-m
    else
        # workers: 青色
        tmux send-keys -t "${MULTIAGENT_SESSION}:0.$i" "export PS1='(\[\033[1;34m\]${PANE_TITLES[$i]}\[\033[0m\]) \[\033[1;32m\]\w\[\033[0m\]\$ '" C-m
    fi
    
    # ウェルカムメッセージ
    tmux send-keys -t "${MULTIAGENT_SESSION}:0.$i" "echo '=== ${PANE_TITLES[$i]} エージェント ===' && echo 'プロジェクト: $PROJECT_NAME'" C-m
done

log_success "✅ multiagentセッション作成完了"
echo ""

# STEP 3: presidentセッション作成（1ペイン）
log_info "👑 presidentセッション作成開始..."

tmux new-session -d -s "$PRESIDENT_SESSION" -n "PR"
tmux send-keys -t "$PRESIDENT_SESSION" "cd $(pwd)" C-m
tmux send-keys -t "$PRESIDENT_SESSION" "export PS1='(\[\033[1;35m\]PRESIDENT\[\033[0m\]) \[\033[1;32m\]\w\[\033[0m\]\$ '" C-m
tmux send-keys -t "$PRESIDENT_SESSION" "echo '=== PRESIDENT セッション ==='" C-m
tmux send-keys -t "$PRESIDENT_SESSION" "echo 'プロジェクト統括責任者'" C-m
tmux send-keys -t "$PRESIDENT_SESSION" "echo 'プロジェクト: $PROJECT_NAME'" C-m
tmux send-keys -t "$PRESIDENT_SESSION" "echo '========================'" C-m

log_success "✅ presidentセッション作成完了"
echo ""

# STEP 4: 環境確認・表示
log_info "🔍 環境確認中..."

echo ""
echo "📊 セットアップ結果:"
echo "==================="

# tmuxセッション確認
echo "📺 Tmux Sessions:"
tmux list-sessions
echo ""

# ペイン構成表示
echo "📋 ペイン構成:"
echo "  multiagentセッション（6ペイン）:"
echo "    Pane 0: boss1     (チームリーダー)"
echo "    Pane 1: worker1   (実行担当者A)"
echo "    Pane 2: worker2   (実行担当者B)"
echo "    Pane 3: worker3   (実行担当者C)"
echo "    Pane 4: worker4   (実行担当者D)"
echo "    Pane 5: worker5   (実行担当者E)"
echo ""
echo "  presidentセッション（1ペイン）:"
echo "    Pane 0: PRESIDENT (プロジェクト統括)"

echo ""
log_success "🎉 Demo環境セットアップ完了！"
echo ""
echo "📋 次のステップ:"
echo "  1. 🔗 セッションアタッチ:"
echo "     tmux attach-session -t $MULTIAGENT_SESSION   # マルチエージェント確認"
echo "     tmux attach-session -t $PRESIDENT_SESSION    # プレジデント確認"
echo ""
echo "  2. 🤖 Claude Code起動:"
echo "     # 手順1: President認証"
echo "     tmux send-keys -t $PRESIDENT_SESSION 'claude --dangerously-skip-permissions' C-m"
echo "     # 手順2: 認証後、multiagent一括起動"
echo "     for i in {0..5}; do tmux send-keys -t ${MULTIAGENT_SESSION}:0.\\\$i 'claude --dangerously-skip-permissions' C-m; done"
echo ""
echo "  3. 📜 指示書確認:"
echo "     PRESIDENT: instructions/president.md"
echo "     boss1: instructions/boss.md"
echo "     worker1,2,3,4,5: instructions/worker.md"
echo "     システム構造: CLAUDE.md"
echo "     開発ルール: development/development_rules.md"
echo ""
echo "  4. 🎯 デモ実行: PRESIDENTに「あなたはpresidentです。指示書に従って」と入力"
echo ""
echo "  5. 📧 メッセージ送信:"
echo "     ./agent-send.sh $PROJECT_NAME [エージェント名] \"[メッセージ]\""
echo "     例: ./agent-send.sh $PROJECT_NAME president \"あなたはpresidentです。指示書に従って\""
echo ""

# プロジェクト名を環境ファイルに保存
echo "export PROJECT_NAME=\"$PROJECT_NAME\"" > .env_${PROJECT_NAME}
echo "export MULTIAGENT_SESSION=\"$MULTIAGENT_SESSION\"" >> .env_${PROJECT_NAME}
echo "export PRESIDENT_SESSION=\"$PRESIDENT_SESSION\"" >> .env_${PROJECT_NAME}

echo "📋 環境変数ファイル作成: .env_${PROJECT_NAME}"
echo "   使用方法: source .env_${PROJECT_NAME}"
echo ""

# Claude自動起動オプション
read -p "🤖 Claude Codeを自動起動しますか？ (y/n): " start_claude

if [[ "$start_claude" =~ ^[yY]([eE][sS])?$ ]]; then
    log_info "Claude Code起動開始..."
    
    # 少し待機してセッションが安定するのを待つ
    sleep 2
    
    # multiagentセッション全ペインでClaude起動
    log_info "multiagentセッションでClaude起動中..."
    for i in {0..5}; do
        tmux send-keys -t "${MULTIAGENT_SESSION}:0.$i" 'claude --dangerously-skip-permissions' C-m
        sleep 0.5
    done
    
    log_success "✅ Claude Code起動完了"
    echo ""
    echo "📋 次のステップ:"
    echo "  1. PRESIDENTセッションを起動: ./presidentsetup.sh $PROJECT_NAME"
    echo "  2. PRESIDENTで「あなたはpresidentです。指示書に従って」を入力"
    echo ""
    
    # 自動アタッチオプション
    if [[ "$AUTO_ATTACH" == "true" ]]; then
        log_info "セッションアタッチ中..."
        sleep 1
        tmux attach-session -t "$MULTIAGENT_SESSION"
    else
        read -p "🔗 multiagentセッションにアタッチしますか？ (y/n): " attach_now
        if [[ "$attach_now" =~ ^[yY]([eE][sS])?$ ]]; then
            log_info "セッションアタッチ中..."
            sleep 1
            tmux attach-session -t "$MULTIAGENT_SESSION"
        fi
    fi
else
    echo ""
    echo "📋 手動でClaude Codeを起動する場合:"
    echo "  1. PRESIDENTセッション起動:"
    echo "     ./presidentsetup.sh $PROJECT_NAME"
    echo ""
    echo "  2. 全エージェント一括起動:"
    echo "     for i in {0..5}; do tmux send-keys -t ${MULTIAGENT_SESSION}:0.\$i 'claude --dangerously-skip-permissions' C-m; done"
    echo ""
    
    # 自動アタッチオプション
    if [[ "$AUTO_ATTACH" == "true" ]]; then
        log_info "セッションアタッチ中..."
        sleep 1
        tmux attach-session -t "$MULTIAGENT_SESSION"
    else
        read -p "🔗 multiagentセッションにアタッチしますか？ (y/n): " attach_now
        if [[ "$attach_now" =~ ^[yY]([eE][sS])?$ ]]; then
            log_info "セッションアタッチ中..."
            sleep 1
            tmux attach-session -t "$MULTIAGENT_SESSION"
        fi
    fi
fi 