#!/bin/bash

# 📋 仕様書変換スクリプト
# テキスト仕様書をMarkdown形式に変換

set -e

PROJECT_NAME="${PROJECT_NAME:-default}"

# 色付きログ関数
log_info() {
    echo -e "\033[1;32m[INFO]\033[0m $1"
}

log_success() {
    echo -e "\033[1;34m[SUCCESS]\033[0m $1"
}

log_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
}

echo "📋 仕様書変換システム"
echo "====================="
echo ""

# 仕様書ファイル確認
SPEC_FILE="specifications/project_spec.txt"
if [ ! -f "$SPEC_FILE" ]; then
    log_error "仕様書ファイルが見つかりません: $SPEC_FILE"
    echo "specifications/project_spec.txt を作成してください。"
    exit 1
fi

log_info "仕様書ファイル確認: $SPEC_FILE"

# 出力ファイル設定
OUTPUT_DIR="specifications"
OUTPUT_FILE="$OUTPUT_DIR/project_spec.md"

log_info "Markdown変換開始..."

# 基本的なMarkdown変換
{
    echo "# 📋 プロジェクト仕様書"
    echo ""
    echo "**変換日時**: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "**プロジェクト**: $PROJECT_NAME"
    echo ""
    echo "---"
    echo ""
    
    # テキストファイルの内容を処理
    while IFS= read -r line || [[ -n "$line" ]]; do
        # 空行はそのまま
        if [[ -z "$line" ]]; then
            echo ""
            continue
        fi
        
        # #で始まる行はヘッダーとして処理
        if [[ "$line" =~ ^#+ ]]; then
            echo "$line"
            continue
        fi
        
        # -で始まる行はリストとして処理
        if [[ "$line" =~ ^[[:space:]]*- ]]; then
            echo "$line"
            continue
        fi
        
        # 数字で始まる行はリストとして処理
        if [[ "$line" =~ ^[[:space:]]*[0-9]+\. ]]; then
            echo "$line"
            continue
        fi
        
        # その他の行は段落として処理
        echo "$line"
        
    done < "$SPEC_FILE"
    
    echo ""
    echo "---"
    echo ""
    echo "**注意**: この仕様書は全エージェントが参照します。変更時は必ずPRESIDENTの承認を得てください。"
    
} > "$OUTPUT_FILE"

log_success "Markdown変換完了: $OUTPUT_FILE"

# 開発ログに記録
mkdir -p development
echo "[$(date '+%Y-%m-%d %H:%M:%S')] [CONVERT] [$PROJECT_NAME] [PRESIDENT] 仕様書をMarkdown変換: $OUTPUT_FILE" >> development/development_log.txt

# 変換後ファイルの確認
if [ -f "$OUTPUT_FILE" ]; then
    log_info "変換後ファイルサイズ: $(wc -l < "$OUTPUT_FILE") 行"
    log_success "✅ 仕様書変換完了"
    echo ""
    echo "📋 次のステップ:"
    echo "  1. 変換された仕様書確認: cat $OUTPUT_FILE"
    echo "  2. 全エージェントに通知: ./agent-send.sh [PROJECT_NAME] [AGENT] \"仕様書が更新されました\""
else
    log_error "変換ファイルの作成に失敗しました"
    exit 1
fi