# 🚀 エージェント間通信ガイド

## 重要な修正点
**agent-send.sh には3つのパラメータが必要です**：
1. プロジェクト名 (例: `hotel`)
2. エージェント名 (例: `boss1`)
3. メッセージ

## セットアップ手順

### 1. 環境変数の読み込み（各セッションで必要）
```bash
source .env_hotel
```

### 2. 正しい送信コマンドの形式
```bash
# 形式: ./agent-send.sh [プロジェクト名] [エージェント名] "[メッセージ]"

# 直接指定
./agent-send.sh hotel boss1 "あなたはboss1です。Hello World プロジェクト開始指示"

# 環境変数を使用
./agent-send.sh $PROJECT_NAME boss1 "あなたはboss1です。Hello World プロジェクト開始指示"
```

## 各エージェントの送信例

### PRESIDENT → boss1
```bash
./agent-send.sh hotel boss1 "あなたはboss1です。Hello World プロジェクト開始指示"
```

### boss1 → workers
```bash
./agent-send.sh hotel worker1 "あなたはworker1です。Hello World 作業開始"
./agent-send.sh hotel worker2 "あなたはworker2です。Hello World 作業開始"
./agent-send.sh hotel worker3 "あなたはworker3です。Hello World 作業開始"
```

### worker → boss1
```bash
./agent-send.sh hotel boss1 "全員作業完了しました"
```

### boss1 → PRESIDENT
```bash
./agent-send.sh hotel president "全員完了しました"
```

## tmuxセッション構成
- `hotel_president` - PRESIDENTセッション
- `hotel_multiagent:0.0` - boss1
- `hotel_multiagent:0.1` - worker1
- `hotel_multiagent:0.2` - worker2
- `hotel_multiagent:0.3` - worker3

## トラブルシューティング

### エラー: "プロジェクト名は英数字とアンダースコアのみ使用可能です"
→ agent-send.sh の第1引数にプロジェクト名が必要です

### エラー: "セッションが見つかりません"
→ tmuxセッションが起動していることを確認してください:
```bash
tmux ls | grep hotel
```

### 完了ファイルの確認
```bash
ls -la ./tmp/
```