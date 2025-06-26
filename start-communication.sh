#!/bin/bash

# 🚀 エージェント間通信スタートスクリプト

# プロジェクト環境ファイルの読み込み
if [ -f .env_hotel ]; then
    source .env_hotel
    echo "✅ プロジェクト環境を読み込みました: $PROJECT_NAME"
else
    echo "❌ エラー: .env_hotel ファイルが見つかりません"
    exit 1
fi

# 環境変数の確認
echo "📋 現在の設定:"
echo "  PROJECT_NAME: $PROJECT_NAME"
echo "  MULTIAGENT_SESSION: $MULTIAGENT_SESSION"
echo "  PRESIDENT_SESSION: $PRESIDENT_SESSION"

# tmpディレクトリの作成
mkdir -p ./tmp
echo "✅ tmpディレクトリを準備しました"

# 使用方法の表示
echo ""
echo "🎯 通信の開始方法:"
echo "1. PRESIDENTセッションで: source .env_hotel"
echo "2. 次のコマンドを実行: ./agent-send.sh hotel boss1 \"あなたはboss1です。Hello World プロジェクト開始指示\""
echo ""
echo "または、環境変数を使って:"
echo "./agent-send.sh \$PROJECT_NAME boss1 \"あなたはboss1です。Hello World プロジェクト開始指示\""