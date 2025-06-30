#!/usr/bin/env python3
"""
環境変数検証スクリプト - 本番デプロイ前チェック
worker5の環境変数設定確認支援ツール
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, List, Tuple, Optional
try:
    from colorama import init, Fore, Style
    # coloramaの初期化
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    # coloramaが利用できない場合のフォールバック
    class DummyColor:
        def __getattr__(self, name):
            return ""
    
    Fore = DummyColor()
    Style = DummyColor()
    COLORAMA_AVAILABLE = False

class EnvironmentValidator:
    """環境変数検証クラス"""
    
    def __init__(self):
        self.required_vars = {
            # 必須API Keys
            'AI_GENERATION': [
                'GEMINI_API_KEY',     # 推奨
                'OPENAI_API_KEY',     # 代替
                # 'ANTHROPIC_API_KEY' # 有料のため非推奨
            ],
            'WORDPRESS': [
                'WP_USER',
                'WP_APP_PASS', 
                'WP_SITE_URL'
            ]
        }
        
        self.optional_vars = {
            'IMAGE_APIS': [
                'UNSPLASH_ACCESS_KEY',
                'PEXELS_API_KEY'
            ],
            'YOUTUBE': [
                'YT_API_KEY'
            ],
            'SYSTEM': [
                'WP_STATUS',
                'LOG_LEVEL',
                'ENABLE_EXTERNAL_API',
                'TZ'
            ]
        }
        
        self.validation_results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'warnings': [],
            'errors': [],
            'recommendations': []
        }
    
    def check_env_file(self) -> bool:
        """環境変数ファイルの存在確認"""
        env_file = Path('.env')
        env_example = Path('.env.example')
        
        print(f"\n{Fore.CYAN}📁 環境変数ファイルチェック")
        print("=" * 50)
        
        if env_example.exists():
            print(f"{Fore.GREEN}✅ .env.example が存在します")
        else:
            print(f"{Fore.RED}❌ .env.example が見つかりません")
            self.validation_results['errors'].append(".env.example ファイルが存在しません")
        
        if env_file.exists():
            print(f"{Fore.GREEN}✅ .env ファイルが存在します")
            return True
        else:
            print(f"{Fore.YELLOW}⚠️  .env ファイルが見つかりません")
            print(f"{Fore.YELLOW}   → .env.example をコピーして作成してください")
            self.validation_results['warnings'].append(".env ファイルが存在しません")
            return False
    
    def validate_required_vars(self) -> Dict[str, bool]:
        """必須環境変数の検証"""
        print(f"\n{Fore.CYAN}🔍 必須環境変数チェック")
        print("=" * 50)
        
        results = {}
        
        # AI API Keys (少なくとも1つ必要)
        print(f"\n{Fore.BLUE}【AI API Keys】")
        ai_keys_found = []
        for key in self.required_vars['AI_GENERATION']:
            value = os.getenv(key, '')
            if value and value != f'your_{key.lower()}_here':
                print(f"{Fore.GREEN}✅ {key}: 設定済み")
                ai_keys_found.append(key)
                results[key] = True
            else:
                print(f"{Fore.YELLOW}⚠️  {key}: 未設定")
                results[key] = False
        
        if not ai_keys_found:
            print(f"{Fore.RED}❌ エラー: AI API Keyが1つも設定されていません")
            self.validation_results['errors'].append("AI API Keyが未設定です")
        else:
            if 'GEMINI_API_KEY' in ai_keys_found:
                self.validation_results['recommendations'].append(
                    "✨ Gemini APIが設定されています（推奨・無料枠大）"
                )
            elif 'OPENAI_API_KEY' in ai_keys_found:
                self.validation_results['recommendations'].append(
                    "📌 OpenAI APIが設定されています（無料クレジット付き）"
                )
        
        # WordPress設定
        print(f"\n{Fore.BLUE}【WordPress設定】")
        wp_all_set = True
        for key in self.required_vars['WORDPRESS']:
            value = os.getenv(key, '')
            if value and not value.startswith('your_'):
                print(f"{Fore.GREEN}✅ {key}: 設定済み")
                results[key] = True
                
                # URL形式の検証
                if key == 'WP_SITE_URL' and not value.startswith('http'):
                    print(f"{Fore.YELLOW}   ⚠️  URLは https:// で始まる必要があります")
                    self.validation_results['warnings'].append(
                        f"{key}: URLフォーマットを確認してください"
                    )
            else:
                print(f"{Fore.RED}❌ {key}: 未設定")
                results[key] = False
                wp_all_set = False
        
        if not wp_all_set:
            self.validation_results['errors'].append("WordPress設定が不完全です")
        
        return results
    
    def validate_optional_vars(self) -> Dict[str, bool]:
        """オプション環境変数の検証"""
        print(f"\n{Fore.CYAN}📋 オプション環境変数チェック")
        print("=" * 50)
        
        results = {}
        
        # 画像API
        print(f"\n{Fore.BLUE}【画像API】")
        image_apis_found = []
        for key in self.optional_vars['IMAGE_APIS']:
            value = os.getenv(key, '')
            if value and not value.startswith('your_'):
                print(f"{Fore.GREEN}✅ {key}: 設定済み")
                results[key] = True
                image_apis_found.append(key)
            else:
                print(f"{Fore.YELLOW}⚠️  {key}: 未設定")
                results[key] = False
        
        if not image_apis_found:
            self.validation_results['warnings'].append(
                "画像APIが未設定です - 画像なしで動作します"
            )
        
        # YouTube API
        print(f"\n{Fore.BLUE}【YouTube API】")
        yt_key = os.getenv('YT_API_KEY', '')
        if yt_key and not yt_key.startswith('your_'):
            print(f"{Fore.GREEN}✅ YT_API_KEY: 設定済み")
            results['YT_API_KEY'] = True
            self.validation_results['recommendations'].append(
                "🎥 YouTube連携機能が利用可能です"
            )
        else:
            print(f"{Fore.YELLOW}⚠️  YT_API_KEY: 未設定")
            results['YT_API_KEY'] = False
        
        # システム設定
        print(f"\n{Fore.BLUE}【システム設定】")
        for key in self.optional_vars['SYSTEM']:
            value = os.getenv(key, '')
            if value:
                print(f"{Fore.GREEN}✅ {key}: {value}")
                results[key] = True
                
                # 特定値の検証
                if key == 'WP_STATUS' and value not in ['draft', 'publish', 'private']:
                    self.validation_results['warnings'].append(
                        f"{key}: 値は draft/publish/private のいずれかにしてください"
                    )
                elif key == 'ENABLE_EXTERNAL_API' and value == 'true':
                    self.validation_results['recommendations'].append(
                        "⚡ 外部API接続が有効化されています"
                    )
            else:
                print(f"{Fore.YELLOW}⚠️  {key}: デフォルト値使用")
                results[key] = False
        
        return results
    
    def check_github_secrets_format(self) -> None:
        """GitHub Secrets設定用フォーマット生成"""
        print(f"\n{Fore.CYAN}🔐 GitHub Secrets 設定ガイド")
        print("=" * 50)
        
        secrets_guide = {
            'required': [],
            'optional': []
        }
        
        # 設定されている必須変数
        for category, vars_list in self.required_vars.items():
            for var in vars_list:
                if os.getenv(var):
                    secrets_guide['required'].append(var)
        
        # 設定されているオプション変数
        for category, vars_list in self.optional_vars.items():
            for var in vars_list:
                if os.getenv(var):
                    secrets_guide['optional'].append(var)
        
        print(f"\n{Fore.BLUE}以下の環境変数をGitHub Secretsに設定してください：")
        print(f"\n{Fore.YELLOW}【必須】")
        for var in secrets_guide['required']:
            print(f"  - {var}")
        
        if secrets_guide['optional']:
            print(f"\n{Fore.YELLOW}【オプション】")
            for var in secrets_guide['optional']:
                print(f"  - {var}")
        
        # GitHub Secrets設定手順
        print(f"\n{Fore.BLUE}設定手順:")
        print("1. GitHubリポジトリの Settings → Secrets and variables → Actions")
        print("2. 'New repository secret' をクリック")
        print("3. Name に環境変数名、Secret に値を入力")
        print("4. 'Add secret' をクリック")
    
    def generate_validation_report(self) -> None:
        """検証レポートの生成"""
        report_file = Path('output/deployment_env_validation_report.json')
        report_file.parent.mkdir(exist_ok=True)
        
        # 全体の検証結果を集計
        total_checks = sum(len(vars_list) for vars_list in self.required_vars.values())
        total_checks += sum(len(vars_list) for vars_list in self.optional_vars.values())
        
        self.validation_results['summary'] = {
            'total_checks': total_checks,
            'errors_count': len(self.validation_results['errors']),
            'warnings_count': len(self.validation_results['warnings']),
            'ready_for_deployment': len(self.validation_results['errors']) == 0
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.validation_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n{Fore.GREEN}📄 検証レポート保存: {report_file}")
    
    def display_summary(self) -> None:
        """検証結果サマリー表示"""
        print(f"\n{Fore.CYAN}📊 検証結果サマリー")
        print("=" * 50)
        
        if self.validation_results['errors']:
            print(f"\n{Fore.RED}❌ エラー ({len(self.validation_results['errors'])}件):")
            for error in self.validation_results['errors']:
                print(f"   - {error}")
        
        if self.validation_results['warnings']:
            print(f"\n{Fore.YELLOW}⚠️  警告 ({len(self.validation_results['warnings'])}件):")
            for warning in self.validation_results['warnings']:
                print(f"   - {warning}")
        
        if self.validation_results['recommendations']:
            print(f"\n{Fore.GREEN}💡 推奨事項:")
            for rec in self.validation_results['recommendations']:
                print(f"   - {rec}")
        
        # デプロイ準備状態
        print(f"\n{Fore.CYAN}🚀 デプロイ準備状態:")
        if self.validation_results['summary']['ready_for_deployment']:
            print(f"{Fore.GREEN}✅ 本番デプロイ可能です！")
        else:
            print(f"{Fore.RED}❌ エラーを修正してください")
    
    def run(self) -> bool:
        """検証実行"""
        print(f"{Fore.CYAN}🔧 BlogAuto 環境変数検証ツール")
        print(f"{Fore.CYAN}worker5 環境変数設定支援")
        print("=" * 60)
        
        # 環境変数ファイルチェック
        if not self.check_env_file():
            print(f"\n{Fore.YELLOW}💡 ヒント: cp .env.example .env を実行してください")
            return False
        
        # 環境変数読み込み
        from dotenv import load_dotenv
        load_dotenv()
        
        # 必須変数検証
        required_results = self.validate_required_vars()
        self.validation_results['checks']['required'] = required_results
        
        # オプション変数検証
        optional_results = self.validate_optional_vars()
        self.validation_results['checks']['optional'] = optional_results
        
        # GitHub Secrets設定ガイド
        self.check_github_secrets_format()
        
        # レポート生成
        self.generate_validation_report()
        
        # サマリー表示
        self.display_summary()
        
        return self.validation_results['summary']['ready_for_deployment']

def main():
    """メイン処理"""
    validator = EnvironmentValidator()
    
    try:
        is_ready = validator.run()
        
        if is_ready:
            print(f"\n{Fore.GREEN}✨ 環境変数設定が完了しています！")
            print(f"{Fore.GREEN}次のステップ: GitHub Actionsでデプロイを実行してください")
            sys.exit(0)
        else:
            print(f"\n{Fore.YELLOW}⚠️  環境変数設定を確認してください")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n{Fore.RED}❌ エラーが発生しました: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()