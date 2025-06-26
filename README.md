# 🤖 ClaudeAuto - Universal Multi-Agent Development Template

**史上最強・史上最高クラスのマルチエージェント開発システム - 完全テンプレート版**

## 🚀 概要

ClaudeAutoは、Claude Codeを使用した革新的なマルチエージェント開発システムの**完全テンプレート**です。このテンプレートを使用することで、どんなプロジェクトでも：

- **1回の作業で90%の完成度**を達成
- **自動的にモデルを切り替え**てトークン効率を最適化
- **外部API接続は最終フェーズ**で安全に実装
- **作業が停滞しない自動サイクル**システム

## ✨ 主要機能

### 🎯 6つのエージェント構成
- **PRESIDENT**: プロジェクト統括・開発ルール監査・仕様書管理
- **boss1**: チームリーダー・品質管理・自動再指示システム
- **worker1-5**: 実行担当・worker間通信・ルール遵守

### 🔄 4つの自動化システム
1. **自動サイクルシステム** - 作業停滞を防ぐ継続的タスク配信
2. **90%自動実装システム** - 本番リリース直前まで一気に実装
3. **自動モデル切り替え** - タスク複雑度に応じた最適化
4. **進捗トラッキング** - リアルタイム監視とレポート生成

### 🧠 AI判断による最適化
- **Haiku**: 簡単なタスク（ドキュメント、設定等）→ 高速・低コスト
- **Sonnet**: 標準的なタスク（実装、レビュー等）→ バランス重視
- **Opus**: 重要・複雑なタスク（セキュリティ、アーキテクチャ等）→ 最高品質

## 🚀 クイックスタート

### ステップ1: テンプレートのセットアップ
```bash
# ClaudeAutoをプロジェクトディレクトリにコピー
cp -r ClaudeAuto/ my-new-project/
cd my-new-project/

# 実行権限付与
chmod +x *.sh
```

### ステップ2: プロジェクト仕様書の設定
```bash
# プロジェクト仕様書を編集
nano specifications/project_spec.txt

# Markdown形式に変換
./scripts/convert_spec.sh
```

### ステップ3: 環境起動
```bash
# マルチエージェント環境起動
./setup.sh myproject

# 別ターミナルでPRESIDENT起動（自動Claude起動）
./presidentsetup.sh myproject --auto-claude
```

### ステップ4: 90%自動実装開始
```bash
# PRESIDENTセッションで基本指示
あなたはpresidentです。指示書に従って

# または直接90%自動実装を起動
./implementation-90-percent.sh myproject
```

## 📁 ディレクトリ構造

```
ClaudeAuto/
├── setup.sh                    # 環境構築（Claude自動起動）
├── presidentsetup.sh           # PRESIDENT専用起動
├── agent-send.sh               # エージェント間通信
├── boss-auto-cycle.sh          # 自動サイクルシステム
├── implementation-90-percent.sh # 90%自動実装
├── model-switcher.sh           # 自動モデル切り替え
├── final-api-integration.sh    # 最終API統合
├── progress-tracker.sh         # 進捗トラッキング
├── start-communication.sh      # 通信ヘルパー
├── CLAUDE.md                   # システム全体設計
├── USER_GUIDE.md              # 完全ユーザーガイド
├── COMMUNICATION_GUIDE.md      # 通信ガイド
├── instructions/               # エージェント指示書
│   ├── president.md           # PRESIDENT指示書
│   ├── boss.md                # boss1指示書
│   └── worker.md              # worker指示書
├── development/               # 開発管理
│   ├── development_rules.md   # 開発ルール
│   └── development_log.txt    # 開発ログ（自動生成）
├── specifications/            # 仕様書管理
│   ├── project_spec.txt       # プロジェクト仕様書（編集用）
│   ├── project_spec.md        # 変換後仕様書
│   └── development_rules.md   # 開発規約
└── scripts/                   # ユーティリティ
    └── convert_spec.sh        # 仕様書変換
```

## 🎯 使用パターン

### パターン1: 高速開発（推奨）
```bash
# 1. 環境起動
./setup.sh myproject
./presidentsetup.sh myproject --auto-claude

# 2. 90%自動実装（9フェーズ×60秒）
./implementation-90-percent.sh myproject

# 3. 最終API統合（90%完了後）
./final-api-integration.sh myproject
```

### パターン2: 段階的開発
```bash
# 1. 環境起動
./setup.sh myproject
./presidentsetup.sh myproject --auto-claude

# 2. 基本指示開始
あなたはpresidentです。指示書に従って

# 3. 自動サイクル起動（別ターミナル）
./boss-auto-cycle.sh myproject &

# 4. 進捗監視
./progress-tracker.sh myproject
```

### パターン3: カスタム開発
```bash
# モデル指定での実行
./model-switcher.sh myproject critical worker1  # 重要タスクをOpusに
./model-switcher.sh myproject simple worker2    # 簡単タスクをHaikuに

# 手動メッセージ送信
./agent-send.sh myproject president "カスタム指示"
```

## 🛠️ カスタマイズ方法

### 1. プロジェクト仕様書の編集
```bash
# specifications/project_spec.txt を編集
nano specifications/project_spec.txt

# Markdown形式に変換
./scripts/convert_spec.sh
```

### 2. 開発ルールのカスタマイズ
```bash
# specifications/development_rules.md を編集
nano specifications/development_rules.md
```

### 3. エージェント指示書の調整
```bash
# instructions/内のファイルを編集
nano instructions/president.md  # PRESIDENT指示書
nano instructions/boss.md       # boss1指示書
nano instructions/worker.md     # worker指示書
```

## 📊 成功指標

- **開発速度**: 従来の10倍高速
- **完成度**: 1回で90%到達
- **コスト効率**: 自動モデル切り替えで最適化
- **品質**: 史上最強システム基準

## 🔧 トラブルシューティング

### よくある問題と解決方法

1. **PRESIDENTが起動しない**
   ```bash
   ./presidentsetup.sh myproject --new
   ```

2. **作業が停滞している**
   ```bash
   ./boss-auto-cycle.sh myproject &
   ```

3. **進捗が見えない**
   ```bash
   ./progress-tracker.sh myproject
   ```

## 📝 テンプレート使用例

### Webアプリケーション開発
```bash
cp -r ClaudeAuto/ webapp-project/
cd webapp-project/
# specifications/project_spec.txt にWebアプリ仕様を記述
./setup.sh webapp
./implementation-90-percent.sh webapp
```

### APIサーバー開発
```bash
cp -r ClaudeAuto/ api-server/
cd api-server/
# specifications/project_spec.txt にAPI仕様を記述
./setup.sh apiserver
./implementation-90-percent.sh apiserver
```

### モバイルアプリ開発
```bash
cp -r ClaudeAuto/ mobile-app/
cd mobile-app/
# specifications/project_spec.txt にモバイルアプリ仕様を記述
./setup.sh mobileapp
./implementation-90-percent.sh mobileapp
```

## 🎉 さあ始めましょう！

ClaudeAutoテンプレートで、史上最強・最高クラスの開発を体験してください。このテンプレートを使用することで、あらゆるプロジェクトで革新的な開発効率を実現できます。

詳細な使用方法は `USER_GUIDE.md` をご覧ください。

---

**サポート**: 問題が発生した場合は、GitHub Issues でお知らせください。
**ライセンス**: MIT License - 自由に使用・改変・配布可能