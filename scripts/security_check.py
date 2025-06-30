#!/usr/bin/env python3
"""
デプロイ前セキュリティチェックスクリプト
worker5支援 - 環境変数とコードのセキュリティ検証
"""

import os
import re
import sys
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, List, Tuple

class SecurityChecker:
    """セキュリティチェッククラス"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.security_patterns = {
            # APIキーパターン
            'api_keys': [
                r'["\']?[A-Za-z0-9_]*[Aa][Pp][Ii][_-]?[Kk][Ee][Yy]["\']?\s*[:=]\s*["\'][A-Za-z0-9_\-]{20,}["\']',
                r'["\']?[A-Za-z0-9_]*[Ss][Ee][Cc][Rr][Ee][Tt]["\']?\s*[:=]\s*["\'][A-Za-z0-9_\-]{20,}["\']',
                r'sk_[a-zA-Z0-9]{32,}',  # Stripe
                r'AIza[A-Za-z0-9_\-]{35}',  # Google
                r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'  # UUID形式
            ],
            # パスワードパターン
            'passwords': [
                r'["\']?[Pp][Aa][Ss][Ss][Ww][Oo][Rr][Dd]["\']?\s*[:=]\s*["\'][^"\']{8,}["\']',
                r'["\']?[Pp][Ww][Dd]["\']?\s*[:=]\s*["\'][^"\']{8,}["\']'
            ],
            # URLパターン（認証情報を含む可能性）
            'sensitive_urls': [
                r'https?://[^:]+:[^@]+@[^\s]+',  # http://user:pass@domain
                r'ftp://[^:]+:[^@]+@[^\s]+'      # ftp://user:pass@domain
            ]
        }
        
        self.safe_patterns = [
            r'os\.getenv\(["\'][A-Z_]+["\']\)',  # 環境変数参照
            r'\$\{\{\s*secrets\.[A-Z_]+\s*\}\}',  # GitHub Secrets参照
            r'your_[a-z_]+_here',  # プレースホルダー
            r'mock_[a-z_]+',  # モックデータ
        ]
        
        self.check_results = {
            'timestamp': datetime.now().isoformat(),
            'vulnerabilities': [],
            'warnings': [],
            'safe_practices': [],
            'file_permissions': [],
            'summary': {}
        }
    
    def check_file_permissions(self) -> None:
        """ファイル権限チェック"""
        print("\n🔒 ファイル権限チェック")
        print("=" * 50)
        
        sensitive_files = [
            '.env',
            '.env.example',
            'auth/api_auth.py',
            'scripts/auth_manager.py'
        ]
        
        for file_path in sensitive_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                stat_info = full_path.stat()
                mode = oct(stat_info.st_mode)[-3:]
                
                if mode == '600' or mode == '644':
                    print(f"✅ {file_path}: 適切な権限 ({mode})")
                    self.check_results['safe_practices'].append(
                        f"{file_path}: 適切なファイル権限設定"
                    )
                else:
                    print(f"⚠️  {file_path}: 権限確認推奨 ({mode})")
                    self.check_results['warnings'].append(
                        f"{file_path}: ファイル権限 {mode} - 600または644を推奨"
                    )
                
                self.check_results['file_permissions'].append({
                    'file': file_path,
                    'permissions': mode,
                    'secure': mode in ['600', '644']
                })
    
    def scan_for_secrets(self, file_path: Path) -> List[Dict]:
        """ファイル内の機密情報スキャン"""
        vulnerabilities = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                # 安全なパターンは除外
                if any(re.search(pattern, line) for pattern in self.safe_patterns):
                    continue
                
                # APIキーチェック
                for pattern in self.security_patterns['api_keys']:
                    if re.search(pattern, line):
                        # 実際の値かプレースホルダーかチェック
                        if not any(placeholder in line.lower() for placeholder in 
                                 ['your_', 'example', 'placeholder', 'mock', 'test']):
                            vulnerabilities.append({
                                'type': 'potential_api_key',
                                'file': str(file_path.relative_to(self.project_root)),
                                'line': line_num,
                                'pattern': 'APIキーパターン',
                                'severity': 'high'
                            })
                
                # パスワードチェック
                for pattern in self.security_patterns['passwords']:
                    if re.search(pattern, line):
                        if not any(placeholder in line.lower() for placeholder in 
                                 ['your_', 'example', 'placeholder', 'mock']):
                            vulnerabilities.append({
                                'type': 'potential_password',
                                'file': str(file_path.relative_to(self.project_root)),
                                'line': line_num,
                                'pattern': 'パスワードパターン',
                                'severity': 'high'
                            })
                
                # 認証情報付きURLチェック
                for pattern in self.security_patterns['sensitive_urls']:
                    if re.search(pattern, line):
                        vulnerabilities.append({
                            'type': 'sensitive_url',
                            'file': str(file_path.relative_to(self.project_root)),
                            'line': line_num,
                            'pattern': '認証情報付きURL',
                            'severity': 'medium'
                        })
        
        except Exception as e:
            pass  # バイナリファイルなどは無視
        
        return vulnerabilities
    
    def check_gitignore(self) -> bool:
        """gitignore設定チェック"""
        print("\n📝 .gitignore チェック")
        print("=" * 50)
        
        gitignore_path = self.project_root / '.gitignore'
        required_entries = [
            '.env',
            '*.pyc',
            '__pycache__',
            'output/',
            '*.log',
            '.DS_Store',
            'tmp/',
            '*.key',
            '*.pem'
        ]
        
        if gitignore_path.exists():
            content = gitignore_path.read_text()
            missing_entries = []
            
            for entry in required_entries:
                if entry not in content:
                    missing_entries.append(entry)
            
            if missing_entries:
                print(f"⚠️  以下のエントリを.gitignoreに追加推奨:")
                for entry in missing_entries:
                    print(f"   - {entry}")
                    self.check_results['warnings'].append(
                        f".gitignore: {entry} の追加を推奨"
                    )
            else:
                print("✅ .gitignore は適切に設定されています")
                self.check_results['safe_practices'].append(
                    ".gitignore: 全ての推奨エントリが設定済み"
                )
            
            return len(missing_entries) == 0
        else:
            print("❌ .gitignore ファイルが存在しません")
            self.check_results['vulnerabilities'].append({
                'type': 'missing_gitignore',
                'severity': 'high',
                'description': '.gitignoreファイルが存在しません'
            })
            return False
    
    def scan_project_files(self) -> None:
        """プロジェクト全体のスキャン"""
        print("\n🔍 プロジェクトファイルスキャン")
        print("=" * 50)
        
        exclude_dirs = {
            '.git', '__pycache__', 'node_modules', 'venv', 
            'env', '.env', 'output', 'tmp'
        }
        
        scan_extensions = {'.py', '.yml', '.yaml', '.json', '.md', '.txt', '.sh'}
        
        total_files = 0
        vulnerable_files = 0
        
        for file_path in self.project_root.rglob('*'):
            if file_path.is_file() and file_path.suffix in scan_extensions:
                # 除外ディレクトリチェック
                if any(excluded in file_path.parts for excluded in exclude_dirs):
                    continue
                
                total_files += 1
                vulnerabilities = self.scan_for_secrets(file_path)
                
                if vulnerabilities:
                    vulnerable_files += 1
                    self.check_results['vulnerabilities'].extend(vulnerabilities)
        
        print(f"\n📊 スキャン結果:")
        print(f"   - 総ファイル数: {total_files}")
        print(f"   - 問題検出ファイル: {vulnerable_files}")
        
        if vulnerable_files == 0:
            print("   ✅ セキュリティ問題は検出されませんでした")
            self.check_results['safe_practices'].append(
                "コードスキャン: セキュリティ問題なし"
            )
    
    def check_env_variables_usage(self) -> None:
        """環境変数の適切な使用チェック"""
        print("\n🌍 環境変数使用チェック")
        print("=" * 50)
        
        good_practices = 0
        bad_practices = 0
        
        python_files = list(self.project_root.rglob('*.py'))
        
        for file_path in python_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # 良い実践: os.getenv() の使用
                env_usage = re.findall(r'os\.getenv\(["\']([A-Z_]+)["\']\)', content)
                if env_usage:
                    good_practices += len(env_usage)
                    for var in set(env_usage):
                        self.check_results['safe_practices'].append(
                            f"{file_path.name}: {var} を安全に参照"
                        )
                
                # 悪い実践: ハードコーディング
                hardcoded = re.findall(
                    r'["\'][A-Za-z0-9]{20,}["\']',  # 長い文字列
                    content
                )
                suspicious_hardcoded = [
                    h for h in hardcoded 
                    if not any(safe in h.lower() for safe in 
                             ['mock', 'test', 'example', 'placeholder'])
                ]
                
                if suspicious_hardcoded:
                    bad_practices += len(suspicious_hardcoded)
                    self.check_results['warnings'].append(
                        f"{file_path.name}: ハードコーディングの可能性"
                    )
            
            except Exception:
                pass
        
        print(f"✅ 適切な環境変数参照: {good_practices}件")
        print(f"⚠️  要確認項目: {bad_practices}件")
    
    def generate_security_report(self) -> None:
        """セキュリティレポート生成"""
        report_path = self.project_root / 'output' / 'security_check_report.json'
        report_path.parent.mkdir(exist_ok=True)
        
        # サマリー生成
        self.check_results['summary'] = {
            'total_vulnerabilities': len(self.check_results['vulnerabilities']),
            'total_warnings': len(self.check_results['warnings']),
            'total_safe_practices': len(self.check_results['safe_practices']),
            'deployment_ready': len(self.check_results['vulnerabilities']) == 0,
            'security_score': self._calculate_security_score()
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.check_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 セキュリティレポート生成: {report_path}")
    
    def _calculate_security_score(self) -> float:
        """セキュリティスコア計算"""
        base_score = 100
        
        # 脆弱性による減点
        base_score -= len(self.check_results['vulnerabilities']) * 10
        
        # 警告による減点
        base_score -= len(self.check_results['warnings']) * 2
        
        # 良い実践によるボーナス
        base_score += min(len(self.check_results['safe_practices']) * 1, 20)
        
        return max(0, min(100, base_score))
    
    def display_summary(self) -> None:
        """セキュリティチェックサマリー表示"""
        print("\n" + "=" * 60)
        print("🛡️  セキュリティチェックサマリー")
        print("=" * 60)
        
        score = self.check_results['summary']['security_score']
        
        if score >= 90:
            print(f"✅ セキュリティスコア: {score}/100 - 優秀")
        elif score >= 70:
            print(f"⚠️  セキュリティスコア: {score}/100 - 改善推奨")
        else:
            print(f"❌ セキュリティスコア: {score}/100 - 要対応")
        
        print(f"\n📊 検出結果:")
        print(f"   - 脆弱性: {self.check_results['summary']['total_vulnerabilities']}件")
        print(f"   - 警告: {self.check_results['summary']['total_warnings']}件")
        print(f"   - 良い実践: {self.check_results['summary']['total_safe_practices']}件")
        
        if self.check_results['summary']['deployment_ready']:
            print(f"\n✅ デプロイ準備完了")
        else:
            print(f"\n❌ デプロイ前に脆弱性の修正が必要です")
        
        # 重要な脆弱性を表示
        if self.check_results['vulnerabilities']:
            print(f"\n⚠️  検出された脆弱性:")
            for vuln in self.check_results['vulnerabilities'][:5]:  # 最初の5件
                if isinstance(vuln, dict):
                    print(f"   - {vuln.get('file', 'Unknown')}: "
                          f"{vuln.get('type', 'Unknown')} (Line {vuln.get('line', '?')})")
    
    def run(self) -> bool:
        """セキュリティチェック実行"""
        print("🛡️  BlogAuto セキュリティチェッカー")
        print("worker5 デプロイ前セキュリティ検証")
        print("=" * 60)
        
        # 各種チェック実行
        self.check_file_permissions()
        self.check_gitignore()
        self.scan_project_files()
        self.check_env_variables_usage()
        
        # レポート生成
        self.generate_security_report()
        
        # サマリー表示
        self.display_summary()
        
        return self.check_results['summary']['deployment_ready']

def main():
    """メイン処理"""
    checker = SecurityChecker()
    
    try:
        is_ready = checker.run()
        
        if is_ready:
            print("\n✨ セキュリティチェック完了 - デプロイ可能")
            sys.exit(0)
        else:
            print("\n⚠️  セキュリティ問題を修正してください")
            sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()