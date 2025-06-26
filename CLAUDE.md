# Agent Communication System

## 🚀 プロジェクト起動
```bash
# 方法1: プロンプト入力（推奨）
./setup.sh

# 方法2: 引数指定
./setup.sh [プロジェクト名]
```

## エージェント構成
- **PRESIDENT** (別セッション): 統括責任者 + **開発ルール監査責任者**
- **boss1** (multiagent:0.0): チームリーダー + 自動再指示システム + 品質管理
- **worker1,2,3,4,5** (multiagent:0.1-5): 実行担当 + worker間通信 + ルール遵守

## 📋 開発ルール・仕様書システム
**全エージェント必須遵守**: 
- `development/development_rules.md` (開発ルール)
- `specifications/project_spec.md` (プロジェクト仕様書)

**重要事項**:
- **ユーザ第一主義での開発**
- **史上最強システム作りの意識**
- **仕様書準拠の徹底**
- **UX/UI変更時のPRESIDENT確認**
- **定期的なGitHubデプロイ**
- **開発ログ記録の徹底**

## あなたの役割
- **PRESIDENT**: @instructions/president.md (開発ルール・仕様書管理監査)
- **boss1**: @instructions/boss.md (チーム品質監督・仕様書確認)
- **worker1,2,3,4,5**: @instructions/worker.md (ルール・仕様書遵守実行)

## メッセージ送信（プロジェクト名必須）
```bash
./agent-send.sh [プロジェクト名] [相手] "[メッセージ]"
```

## 📊 開発ログ・仕様書システム
- **通信ログ**: 自動記録（agent-send.sh使用時）
- **作業ログ**: 各エージェントが手動記録
- **ログファイル**: `development/development_log.txt`
- **仕様書配置**: `specifications/project_spec.txt`
- **仕様書変換後**: `specifications/project_spec.md`
- **変換コマンド**: `./scripts/convert_spec.sh`

## 拡張フロー
### 基本フロー
PRESIDENT (ルール・仕様書管理) → boss1 (品質・仕様確認) → workers(1-5) (仕様書準拠実行) → boss1 → PRESIDENT

### worker間通信フロー
worker1 ⇄ worker2 ⇄ worker3 ⇄ worker4 ⇄ worker5 (全て開発ログ記録・仕様書準拠)

### 自動再指示サイクル
boss1 → 完了報告受信 → 自動的に新サイクル開始 → workers(1-5) (品質・仕様書準拠維持)

## 🔧 競合対策
- **プロジェクト名によるセッション分離**
- **複数プロジェクト同時実行可能**  
- **環境変数ファイル**: `.env_[プロジェクト名]`

## 🎯 品質基準
- **史上最強・史上最高クラスのシステム開発**
- **Claude Codeの技術最大限活用**
- **ユーザビリティ最優先**
- **継続的改善と学習** 