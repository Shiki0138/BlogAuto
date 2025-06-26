#!/bin/bash

# 📊 進捗トラッキングシステム
# リアルタイム進捗監視とレポート生成

PROJECT_NAME="$1"
if [ -z "$PROJECT_NAME" ]; then
    echo "使用方法: $0 [プロジェクト名]"
    exit 1
fi

ENV_FILE=".env_${PROJECT_NAME}"
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
fi

# 進捗計算関数
calculate_real_progress() {
    local completed_tasks=0
    local total_tasks=0
    
    # 完了ファイルをカウント
    if [ -d "./tmp" ]; then
        completed_tasks=$(find ./tmp -name "*_done.txt" | wc -l)
    fi
    
    # 開発ログから総タスク数を推定
    if [ -f "development/development_log.txt" ]; then
        total_tasks=$(grep -c "\[COMMUNICATION\].*worker" development/development_log.txt || echo "1")
    fi
    
    if [ "$total_tasks" -gt 0 ]; then
        echo $(( completed_tasks * 100 / total_tasks ))
    else
        echo "0"
    fi
}

# 詳細進捗レポート生成
generate_progress_report() {
    local current_progress="$1"
    local target_progress="$2"
    
    echo "📊 進捗レポート - $(date '+%Y-%m-%d %H:%M:%S')"
    echo "=================================="
    echo "プロジェクト: $PROJECT_NAME"
    echo "現在進捗: ${current_progress}%"
    echo "目標進捗: ${target_progress}%"
    echo "残り: $((target_progress - current_progress))%"
    echo ""
    
    # フェーズ別進捗
    echo "📋 フェーズ別進捗:"
    echo "  ✅ 基盤構築: $( [ "$current_progress" -ge 10 ] && echo "完了" || echo "進行中")"
    echo "  ✅ データモデル: $( [ "$current_progress" -ge 20 ] && echo "完了" || echo "待機中")"
    echo "  ✅ 認証システム: $( [ "$current_progress" -ge 30 ] && echo "完了" || echo "待機中")"
    echo "  ✅ ビジネスロジック: $( [ "$current_progress" -ge 40 ] && echo "完了" || echo "待機中")"
    echo "  ✅ UI実装: $( [ "$current_progress" -ge 50 ] && echo "完了" || echo "待機中")"
    echo "  ✅ DB統合: $( [ "$current_progress" -ge 60 ] && echo "完了" || echo "待機中")"
    echo "  ✅ テスト自動化: $( [ "$current_progress" -ge 70 ] && echo "完了" || echo "待機中")"
    echo "  ✅ セキュリティ: $( [ "$current_progress" -ge 80 ] && echo "完了" || echo "待機中")"
    echo "  ✅ 最適化: $( [ "$current_progress" -ge 90 ] && echo "完了" || echo "待機中")"
    echo "  ✅ 外部API統合: $( [ "$current_progress" -ge 100 ] && echo "完了" || echo "待機中")"
    echo ""
    
    # ワーカー状況
    echo "👷 ワーカー状況:"
    for i in {1..5}; do
        if [ -f "./tmp/worker${i}_done.txt" ]; then
            task_info=$(cat "./tmp/worker${i}_done.txt" | head -1)
            echo "  worker${i}: ✅ $task_info"
        else
            echo "  worker${i}: 🔄 作業中"
        fi
    done
    echo ""
    
    # 進捗バー表示
    echo "進捗バー:"
    progress_bar=""
    for i in $(seq 1 10); do
        if [ $((i * 10)) -le "$current_progress" ]; then
            progress_bar="${progress_bar}█"
        else
            progress_bar="${progress_bar}░"
        fi
    done
    echo "[$progress_bar] ${current_progress}%"
    echo ""
}

# メイン処理
echo "📊 進捗トラッキング開始"

# 現在の進捗を取得
CURRENT_PROGRESS=$(cat ./tmp/implementation_progress.txt 2>/dev/null || echo "0")
REAL_PROGRESS=$(calculate_real_progress)
TARGET_PROGRESS=90

# 進捗レポート生成
generate_progress_report "$CURRENT_PROGRESS" "$TARGET_PROGRESS" > "./tmp/progress_report.txt"

# コンソールに表示
cat "./tmp/progress_report.txt"

# パフォーマンス分析
echo "⚡ パフォーマンス分析:"
if [ -f "development/development_log.txt" ]; then
    echo "  総ログ行数: $(wc -l < development/development_log.txt)"
    echo "  開始時刻: $(head -1 development/development_log.txt | cut -d']' -f1 | tr -d '[')"
    echo "  最終更新: $(tail -1 development/development_log.txt | cut -d']' -f1 | tr -d '[')"
    
    # サイクル数カウント
    cycle_count=$(grep -c "サイクル.*開始" development/development_log.txt || echo "0")
    echo "  実行サイクル数: $cycle_count"
    
    # 完了タスク数
    completed_count=$(grep -c "完了" development/development_log.txt || echo "0")
    echo "  完了タスク数: $completed_count"
fi

echo ""
echo "📈 推定完了時間:"
if [ "$CURRENT_PROGRESS" -gt 0 ]; then
    remaining=$((TARGET_PROGRESS - CURRENT_PROGRESS))
    if [ "$remaining" -gt 0 ]; then
        eta_minutes=$((remaining * 2))  # 1%あたり約2分と推定
        echo "  残り時間: 約${eta_minutes}分"
        echo "  完了予定: $(date -d "+${eta_minutes} minutes" '+%H:%M')"
    else
        echo "  🎉 目標達成済み！"
    fi
fi

# 結果をPRESIDENTに報告
if command -v ./agent-send.sh &> /dev/null; then
    REPORT_SUMMARY="📊 進捗レポート
現在: ${CURRENT_PROGRESS}%
実測: ${REAL_PROGRESS}%
残り: $((TARGET_PROGRESS - CURRENT_PROGRESS))%
詳細: ./tmp/progress_report.txt"
    
    ./agent-send.sh "$PROJECT_NAME" "president" "$REPORT_SUMMARY"
fi

echo ""
echo "📄 詳細レポート: ./tmp/progress_report.txt"