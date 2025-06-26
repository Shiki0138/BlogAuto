#!/bin/bash

# 👑 PRESIDENT専用起動スクリプト

set -e  # エラー時に停止

# コマンドラインオプション処理
FORCE_NEW=false
AUTO_ATTACH=false
AUTO_CLAUDE=false
if [[ "$1" == "--new" ]] || [[ "$2" == "--new" ]] || [[ "$3" == "--new" ]]; then
    FORCE_NEW=true
fi
if [[ "$1" == "--attach" ]] || [[ "$2" == "--attach" ]] || [[ "$3" == "--attach" ]]; then
    AUTO_ATTACH=true
fi
if [[ "$1" == "--auto-claude" ]] || [[ "$2" == "--auto-claude" ]] || [[ "$3" == "--auto-claude" ]]; then
    AUTO_CLAUDE=true
fi

# プロジェクト名取得
PROJECT_NAME="$1"
if [[ "$1" == "--new" ]] || [[ "$1" == "--attach" ]] || [[ "$1" == "--auto-claude" ]]; then
    PROJECT_NAME="$2"
fi
if [ -z "$PROJECT_NAME" ]; then
    # 環境変数ファイルを探す
    if ls .env_* 1> /dev/null 2>&1; then
        echo "📋 既存のプロジェクトが見つかりました:"
        echo ""
        for env_file in .env_*; do
            proj_name="${env_file#.env_}"
            echo "  - $proj_name"
        done
        echo ""
        read -p "プロジェクト名を入力 (または新規作成の場合は新しい名前): " PROJECT_NAME
    else
        echo "❌ エラー: プロジェクト名を指定してください"
        echo "使用方法: $0 [プロジェクト名] [オプション]"
        echo "オプション:"
        echo "  --attach      既存セッションに自動接続"
        echo "  --new         強制的に新規セッション作成"
        echo "  --auto-claude Claude Codeを自動起動"
        echo ""
        echo "先に ./setup.sh でプロジェクト環境を構築してください"
        exit 1
    fi
fi

# プロジェクト名検証
if ! [[ "$PROJECT_NAME" =~ ^[a-zA-Z0-9_]+$ ]]; then
    echo "❌ エラー: プロジェクト名は英数字とアンダースコアのみ使用可能です"
    exit 1
fi

# 環境変数ファイル確認
ENV_FILE=".env_${PROJECT_NAME}"
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
    echo "✅ 環境変数読み込み: $ENV_FILE"
else
    echo "⚠️  環境ファイルが見つかりません: $ENV_FILE"
    echo "新規にPRESIDENTセッションを作成します..."
    PRESIDENT_SESSION="${PROJECT_NAME}_president"
fi

# 色付きログ関数
log_info() {
    echo -e "\033[1;32m[INFO]\033[0m $1"
}

log_success() {
    echo -e "\033[1;34m[SUCCESS]\033[0m $1"
}

echo "👑 PRESIDENT セッション起動"
echo "=========================="
echo "📋 プロジェクト: $PROJECT_NAME"
echo "📋 セッション名: $PRESIDENT_SESSION"
echo ""

# 既存セッション確認
if tmux has-session -t "$PRESIDENT_SESSION" 2>/dev/null; then
    if [[ "$FORCE_NEW" == "true" ]]; then
        log_info "既存セッションを削除して新規作成します..."
        tmux kill-session -t "$PRESIDENT_SESSION"
    elif [[ "$AUTO_ATTACH" == "true" ]]; then
        log_info "既存セッションに接続中..."
        tmux attach-session -t "$PRESIDENT_SESSION"
        exit 0
    else
        echo "⚠️  既存のPRESIDENTセッションが見つかりました"
        read -p "既存セッションに接続しますか？ (y/n): " connect_existing
        
        if [[ "$connect_existing" =~ ^[yY]([eE][sS])?$ ]]; then
            log_info "既存セッションに接続中..."
            tmux attach-session -t "$PRESIDENT_SESSION"
            exit 0
        else
            log_info "既存セッションを削除して新規作成します..."
            tmux kill-session -t "$PRESIDENT_SESSION"
        fi
    fi
fi

# PRESIDENTセッション作成
log_info "PRESIDENTセッション作成中..."

tmux new-session -d -s "$PRESIDENT_SESSION" -n "PR"
tmux send-keys -t "$PRESIDENT_SESSION" "cd $(pwd)" C-m
tmux send-keys -t "$PRESIDENT_SESSION" "export PS1='(\[\033[1;35m\]PRESIDENT\[\033[0m\]) \[\033[1;32m\]\w\[\033[0m\]\$ '" C-m
tmux send-keys -t "$PRESIDENT_SESSION" "export PROJECT_NAME='$PROJECT_NAME'" C-m
tmux send-keys -t "$PRESIDENT_SESSION" "clear" C-m
tmux send-keys -t "$PRESIDENT_SESSION" "echo '=== 👑 PRESIDENT セッション ==='" C-m
tmux send-keys -t "$PRESIDENT_SESSION" "echo 'プロジェクト統括責任者'" C-m
tmux send-keys -t "$PRESIDENT_SESSION" "echo 'プロジェクト: $PROJECT_NAME'" C-m
tmux send-keys -t "$PRESIDENT_SESSION" "echo '========================'" C-m
tmux send-keys -t "$PRESIDENT_SESSION" "echo ''" C-m

log_success "✅ PRESIDENTセッション作成完了"

# Claude自動起動オプション
if [[ "$AUTO_CLAUDE" == "true" ]]; then
    start_claude="y"
else
    echo ""
    read -p "🤖 Claude Codeを自動起動しますか？ (y/n): " start_claude
fi

if [[ "$start_claude" =~ ^[yY]([eE][sS])?$ ]]; then
    log_info "Claude Code起動中..."
    tmux send-keys -t "$PRESIDENT_SESSION" 'claude --dangerously-skip-permissions' C-m
    sleep 1
    
    log_success "✅ Claude Code起動完了"
    echo ""
    echo "📋 PRESIDENTセッションで以下を実行してください:"
    echo "   「あなたはpresidentです。指示書に従って」"
    echo ""
    echo "🔗 セッションアタッチ中..."
    sleep 1
    tmux attach-session -t "$PRESIDENT_SESSION"
else
    echo ""
    echo "📋 次のステップ:"
    echo "  1. セッションアタッチ:"
    echo "     tmux attach-session -t $PRESIDENT_SESSION"
    echo ""
    echo "  2. Claude Code起動:"
    echo "     claude --dangerously-skip-permissions"
    echo ""
    echo "  3. 指示実行:"
    echo "     「あなたはpresidentです。指示書に従って」"
    echo ""
    read -p "今すぐセッションにアタッチしますか？ (y/n): " attach_now
    
    if [[ "$attach_now" =~ ^[yY]([eE][sS])?$ ]]; then
        tmux attach-session -t "$PRESIDENT_SESSION"
    fi
fi