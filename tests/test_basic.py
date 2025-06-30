#!/usr/bin/env python3
"""
Basic Test Suite for BlogAuto - Phase 1
フェーズ1: 基本環境とコンポーネントのテスト
"""
import sys
import os
from pathlib import Path
import unittest

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

class TestPhase1Environment(unittest.TestCase):
    """フェーズ1: 環境構築テスト"""
    
    def setUp(self):
        """テスト準備"""
        self.project_root = Path(__file__).parent.parent
        
    def test_project_structure(self):
        """プロジェクト構造の確認"""
        required_dirs = [
            "scripts",
            "prompts", 
            "output",
            "tests",
            ".github/workflows"
        ]
        
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            self.assertTrue(dir_path.exists(), f"Required directory missing: {dir_name}")
    
    def test_required_files(self):
        """必須ファイルの存在確認"""
        required_files = [
            "README.md",
            "requirements.txt",
            ".env.example",
            "scripts/utils.py",
            "scripts/generate_article.py",
            "scripts/fetch_image.py",
            "scripts/post_to_wp.py",
            ".github/workflows/daily-blog.yml"
        ]
        
        for file_name in required_files:
            file_path = self.project_root / file_name
            self.assertTrue(file_path.exists(), f"Required file missing: {file_name}")
    
    def test_python_imports(self):
        """Pythonモジュールのインポート確認"""
        try:
            # 基本ライブラリ
            import json
            import datetime
            import logging
            import pathlib
            
            # 外部ライブラリ（optional）
            try:
                import requests
                import jinja2
                import markdown
            except ImportError:
                pass  # フェーズ1では外部ライブラリは必須ではない
            
        except ImportError as e:
            self.fail(f"Python import failed: {e}")
    
    def test_environment_variables_template(self):
        """環境変数テンプレートの確認"""
        env_example_path = self.project_root / ".env.example"
        self.assertTrue(env_example_path.exists(), ".env.example file missing")
        
        content = env_example_path.read_text(encoding='utf-8')
        
        # 必須の環境変数設定例が含まれているかチェック
        required_vars = [
            "ANTHROPIC_API_KEY",
            "WP_USER",
            "WP_APP_PASS", 
            "WP_SITE_URL",
            "ENABLE_EXTERNAL_API"
        ]
        
        for var in required_vars:
            self.assertIn(var, content, f"Required environment variable {var} not found in .env.example")
    
    def test_github_workflow(self):
        """GitHub Actionsワークフローの確認"""
        workflow_path = self.project_root / ".github/workflows/daily-blog.yml"
        self.assertTrue(workflow_path.exists(), "GitHub Actions workflow file missing")
        
        content = workflow_path.read_text(encoding='utf-8')
        
        # 基本的なワークフロー要素の確認
        workflow_elements = [
            "name:",
            "on:",
            "schedule:",
            "jobs:",
            "runs-on:",
            "steps:"
        ]
        
        for element in workflow_elements:
            self.assertIn(element, content, f"Workflow element {element} not found")

class TestPhase1Configuration(unittest.TestCase):
    """フェーズ1: 設定ファイルテスト"""
    
    def setUp(self):
        """テスト準備"""
        self.project_root = Path(__file__).parent.parent
    
    def test_requirements_txt_format(self):
        """requirements.txtの形式確認"""
        req_path = self.project_root / "requirements.txt"
        self.assertTrue(req_path.exists(), "requirements.txt missing")
        
        content = req_path.read_text(encoding='utf-8')
        
        # 基本的な依存関係の確認
        core_dependencies = [
            "anthropic",
            "requests",
            "markdown",
            "jinja2",
            "Pillow"
        ]
        
        for dep in core_dependencies:
            self.assertIn(dep, content, f"Core dependency {dep} not found in requirements.txt")
    
    def test_readme_content(self):
        """README.mdの内容確認"""
        readme_path = self.project_root / "README.md"
        self.assertTrue(readme_path.exists(), "README.md missing")
        
        content = readme_path.read_text(encoding='utf-8')
        
        # README必須セクションの確認
        required_sections = [
            "BlogAuto",
            "## 🚀 概要",
            "## 🔧 インストール",
            "## 🏗️ アーキテクチャ",
            "## 🚨 トラブルシューティング"
        ]
        
        for section in required_sections:
            self.assertIn(section, content, f"Required README section {section} not found")

class TestPhase1Scripts(unittest.TestCase):
    """フェーズ1: スクリプト基本テスト"""
    
    def setUp(self):
        """テスト準備"""
        self.project_root = Path(__file__).parent.parent
        sys.path.append(str(self.project_root))
    
    def test_utils_import(self):
        """utils.pyのインポート確認"""
        try:
            from scripts import utils
            self.assertTrue(hasattr(utils, 'logger'), "logger not found in utils")
        except ImportError as e:
            self.fail(f"Failed to import utils: {e}")
    
    def test_scripts_syntax(self):
        """スクリプトファイルの構文確認"""
        script_files = [
            "scripts/generate_article.py",
            "scripts/fetch_image.py", 
            "scripts/post_to_wp.py",
            "scripts/utils.py"
        ]
        
        for script_file in script_files:
            script_path = self.project_root / script_file
            if script_path.exists():
                # 基本的な構文チェック
                try:
                    with open(script_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Pythonファイルとしてコンパイル可能かチェック
                    compile(content, script_path, 'exec')
                    
                except SyntaxError as e:
                    self.fail(f"Syntax error in {script_file}: {e}")
                except Exception as e:
                    self.fail(f"Error checking {script_file}: {e}")

def run_phase1_tests():
    """フェーズ1テスト実行"""
    test_suite = unittest.TestSuite()
    
    # テストクラスを追加
    test_classes = [
        TestPhase1Environment,
        TestPhase1Configuration,
        TestPhase1Scripts
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # テスト実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    print("🧪 BlogAuto Phase 1 Test Suite")
    print("=" * 50)
    
    success = run_phase1_tests()
    
    if success:
        print("\n✅ All Phase 1 tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some Phase 1 tests failed!")
        sys.exit(1)