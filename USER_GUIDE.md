# 🤖 Claude Code Multi-Agent System - 完全ユーザーガイド

## 📖 概要

このシステムは、Claude Codeを使用した革新的なマルチエージェント開発システムです。**1回の作業で90%の完成度**を達成し、**自動的にモデルを切り替え**てトークン効率を最適化します。

## 🎯 主要機能

### 1. 🔄 自動サイクルシステム
- **目的**: 作業の自動循環で停滞を防止
- **動作**: 30秒ごとに状況確認、自動的に次タスクを配信
- **利点**: 手動管理不要、継続的な進捗

### 2. 🚀 90%自動実装システム
- **目的**: 1回で本番リリース90%まで到達
- **動作**: 9フェーズ×60秒で体系的実装
- **特徴**: 外部API接続は最終フェーズ

### 3. 🧠 自動モデル切り替え
- **目的**: タスク複雑度に応じた最適化
- **動作**: Claude判断による自動切り替え
- **効果**: トークン効率化、コスト最適化

### 4. 📊 進捗トラッキング
- **目的**: リアルタイム進捗監視
- **動作**: 自動レポート生成、ETA計算
- **活用**: 計画調整、品質管理

## 🚀 クイックスタート

### ステップ1: 環境準備
```bash
# リポジトリをクローン
git clone https://github.com/Shiki0138/claude-code-template.git
cd claude-code-template

# 実行権限付与
chmod +x *.sh
```

### ステップ2: プロジェクト起動
```bash
# マルチエージェント環境起動
./setup.sh myproject

# 別ターミナルでPRESIDENT起動
./presidentsetup.sh myproject --auto-claude
```

### ステップ3: 作業開始
```bash
# PRESIDENTセッションで実行
あなたはpresidentです。指示書に従って

# または90%自動実装を直接起動
./implementation-90-percent.sh myproject
```

## 📋 機能別詳細ガイド

### 🔄 自動サイクルシステム (`boss-auto-cycle.sh`)

**何をするか**: 作業が停滞しないよう自動的に次のタスクを配信

**使い方**:
```bash
# 基本起動
./boss-auto-cycle.sh myproject

# バックグラウンド実行
./boss-auto-cycle.sh myproject &
```

**設定可能項目**:
- `CYCLE_INTERVAL=30` - サイクル間隔（秒）
- `MAX_CYCLES=10` - 最大サイクル数

**タスクリスト**:
1. 仕様書再確認と実装計画
2. 開発環境セットアップ
3. 基本機能実装
4. テストコード作成
5. コードレビューとリファクタリング
6. ドキュメント作成と更新
7. デプロイ準備と確認
8. パフォーマンス最適化
9. セキュリティチェック
10. 最終品質確認

### 🚀 90%自動実装システム (`implementation-90-percent.sh`)

**何をするか**: 本番リリース90%まで一気に実装

**使い方**:
```bash
./implementation-90-percent.sh myproject
```

**実装フェーズ**:
1. **環境構築と基盤設定** (10%) - simple → Haiku
2. **データモデル設計と実装** (20%) - complex → Opus
3. **認証システム構築** (30%) - critical → Opus
4. **コアビジネスロジック実装** (40%) - complex → Opus
5. **ユーザーインターフェース構築** (50%) - complex → Opus
6. **データベース統合とマイグレーション** (60%) - critical → Opus
7. **テスト自動化とCI/CD構築** (70%) - simple → Haiku
8. **セキュリティ強化と監査** (80%) - critical → Opus
9. **パフォーマンス最適化** (90%) - complex → Opus

**特徴**:
- 各フェーズ60秒の集中実装
- 自動的にタスク複雑度を判定
- 外部API接続は最終10%で実行

### 🧠 自動モデル切り替えシステム (`model-switcher.sh`)

**何をするか**: タスクの複雑度に応じて最適なモデルを自動選択

**判定基準**:
- **simple** → **Haiku**: ドキュメント、設定、簡単な実装
- **standard** → **Sonnet**: 通常の実装、レビュー
- **complex** → **Opus**: アーキテクチャ設計、複雑な実装
- **critical** → **Opus**: セキュリティ、品質管理、重要機能

**自動切り替え**:
- Claude が指示内容を分析
- 適切なモデルを自動選択
- コスト効率と品質を両立

**手動切り替え** (必要時のみ):
```bash
./model-switcher.sh myproject complex worker1
```

### 📊 進捗トラッキングシステム (`progress-tracker.sh`)

**何をするか**: リアルタイムで進捗を監視・レポート

**使い方**:
```bash
./progress-tracker.sh myproject
```

**レポート内容**:
- 現在進捗率
- フェーズ別完了状況
- ワーカー別作業状況
- 視覚的進捗バー
- 完了予定時刻

**自動実行**:
- 進捗変更時に自動レポート
- PRESIDENTに自動通知
- 詳細レポートファイル生成

### 🌐 最終API統合システム (`final-api-integration.sh`)

**何をするか**: 90%完了後の外部API統合（最終10%）

**使い方**:
```bash
# 90%完了後に実行
./final-api-integration.sh myproject
```

**統合API**:
1. 決済API（Stripe/PayPal）
2. メール配信API（SendGrid/AWS SES）
3. 地図・位置情報API（Google Maps）
4. プッシュ通知API（Firebase/OneSignal）
5. 画像・ファイルストレージAPI（AWS S3/Cloudinary）

## 🛠️ セットアップスクリプト

### `setup.sh` - マルチエージェント環境構築

**機能**:
- 6ペイン（boss1 + worker1-5）tmuxセッション作成
- 自動Claude起動オプション
- 環境変数設定

**オプション**:
```bash
./setup.sh myproject --attach  # 自動アタッチ
```

### `presidentsetup.sh` - PRESIDENT専用起動

**機能**:
- PRESIDENT専用セッション作成
- 自動Claude起動
- セッション管理

**オプション**:
```bash
./presidentsetup.sh myproject --attach      # 既存セッション接続
./presidentsetup.sh myproject --new         # 強制新規作成
./presidentsetup.sh myproject --auto-claude # 非対話式Claude起動
```

## 📞 エージェント間通信

### `agent-send.sh` - メッセージ送信

**使い方**:
```bash
./agent-send.sh [プロジェクト名] [エージェント] "[メッセージ]"

# 例
./agent-send.sh myproject president "指示書に従って"
./agent-send.sh myproject worker1 "仕様書確認して作業開始"
```

**対象エージェント**:
- `president` - プロジェクト統括
- `boss1` - チームリーダー
- `worker1`-`worker5` - 実行担当

## 📁 ファイル構造

```
claude-code-template/
├── setup.sh                    # 環境構築（Claude自動起動）
├── presidentsetup.sh           # PRESIDENT専用起動
├── agent-send.sh               # エージェント間通信
├── boss-auto-cycle.sh          # 自動サイクルシステム
├── implementation-90-percent.sh # 90%自動実装
├── model-switcher.sh           # モデル切り替え
├── final-api-integration.sh    # 最終API統合
├── progress-tracker.sh         # 進捗トラッキング
├── instructions/               # エージェント指示書
│   ├── president.md
│   ├── boss.md
│   └── worker.md
├── development/                # 開発管理
│   ├── development_rules.md
│   └── development_log.txt
└── specifications/             # 仕様書管理
    ├── project_spec.txt
    └── project_spec.md
```

## 🎯 典型的な作業フロー

### パターン1: 通常開発
```bash
# 1. 環境起動
./setup.sh myproject
./presidentsetup.sh myproject --auto-claude

# 2. 作業開始（PRESIDENTで）
あなたはpresidentです。指示書に従って

# 3. 自動サイクル起動（別ターミナル）
./boss-auto-cycle.sh myproject
```

### パターン2: 高速開発（90%到達）
```bash
# 1. 環境起動
./setup.sh myproject
./presidentsetup.sh myproject --auto-claude

# 2. 90%自動実装起動
./implementation-90-percent.sh myproject

# 3. 最終API統合（90%完了後）
./final-api-integration.sh myproject
```

### パターン3: 進捗重視
```bash
# 進捗監視ウィンドウで常時実行
./progress-tracker.sh myproject

# 定期的な進捗確認
watch -n 30 "./progress-tracker.sh myproject"
```

## 🔧 トラブルシューティング

### PRESIDENTが起動しない
```bash
# 既存セッション確認
tmux ls | grep president

# 強制新規作成
./presidentsetup.sh myproject --new
```

### 作業が停滞している
```bash
# 自動サイクル起動
./boss-auto-cycle.sh myproject &

# 進捗確認
./progress-tracker.sh myproject
```

### モデル切り替えが必要
```bash
# 重要タスクをOpusに
./model-switcher.sh myproject critical worker1

# 簡単タスクをHaikuに
./model-switcher.sh myproject simple worker2
```

## 📊 成功指標

- **開発速度**: 従来の10倍高速
- **完成度**: 1回で90%到達
- **コスト効率**: 自動モデル切り替えで最適化
- **品質**: 史上最強システム基準

## 🎉 さあ始めましょう！

このシステムで、史上最強・最高クラスの開発を体験してください。Claude Codeの真の力を解き放ち、革新的なプロジェクトを創造しましょう！

---

**サポート**: 問題が発生した場合は、`development/development_log.txt` を確認し、GitHub Issues でお知らせください。