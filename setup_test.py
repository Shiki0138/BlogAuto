#!/usr/bin/env python3
"""
BlogAuto環境セットアップテストスクリプト
フェーズ1: 環境構築と基盤設定の検証
"""
import os
import sys
from pathlib import Path
import logging

# ロガー設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_directory_structure():
    """ディレクトリ構造の確認"""
    required_dirs = [
        '.github/workflows',
        'scripts',
        'prompts',
        'output',
        'development',
        'specifications',
        'logs',
        'tmp',
        'tests'
    ]
    
    logger.info("📁 Checking directory structure...")
    all_exists = True
    
    for dir_name in required_dirs:
        if Path(dir_name).exists():
            logger.info(f"✅ {dir_name}/ exists")
        else:
            logger.error(f"❌ {dir_name}/ missing")
            all_exists = False
    
    return all_exists

def check_required_files():
    """必要ファイルの確認"""
    required_files = [
        'requirements.txt',
        '.github/workflows/daily-blog.yml',
        'scripts/generate_article.py',
        'scripts/fetch_image.py',
        'scripts/post_to_wp.py',
        'scripts/utils.py',
        'prompts/daily_blog.jinja',
        'specifications/project_spec.md'
    ]
    
    logger.info("\n📄 Checking required files...")
    all_exists = True
    
    for file_name in required_files:
        if Path(file_name).exists():
            logger.info(f"✅ {file_name} exists")
        else:
            logger.error(f"❌ {file_name} missing")
            all_exists = False
    
    return all_exists

def check_python_environment():
    """Python環境の確認"""
    logger.info("\n🐍 Checking Python environment...")
    
    # Python version
    python_version = sys.version.split()[0]
    logger.info(f"Python version: {python_version}")
    
    # Check if we can import required modules
    required_modules = ['jinja2', 'markdown', 'requests']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            logger.info(f"✅ {module} is available")
        except ImportError:
            logger.warning(f"⚠️  {module} is not installed")
            missing_modules.append(module)
    
    return len(missing_modules) == 0

def check_environment_variables():
    """環境変数の確認（オプション）"""
    logger.info("\n🔐 Checking environment variables...")
    
    optional_vars = [
        'ANTHROPIC_API_KEY',
        'UNSPLASH_ACCESS_KEY', 
        'PEXELS_API_KEY',
        'GEMINI_API_KEY',
        'OPENAI_API_KEY',
        'WP_USER',
        'WP_APP_PASS',
        'WP_SITE_URL'
    ]
    
    found_count = 0
    for var in optional_vars:
        if os.getenv(var):
            logger.info(f"✅ {var} is set")
            found_count += 1
        else:
            logger.info(f"⚠️  {var} is not set (optional)")
    
    logger.info(f"\n📊 Environment variables: {found_count}/{len(optional_vars)} set")
    return True  # 環境変数は任意なので常にTrue

def run_basic_import_test():
    """基本的なインポートテスト"""
    logger.info("\n📦 Testing basic imports...")
    
    try:
        # Add project root to path
        sys.path.insert(0, str(Path(__file__).parent))
        
        # Test utils import
        from scripts.utils import logger as util_logger, ensure_output_dir
        logger.info("✅ scripts.utils imported successfully")
        
        # Test output directory creation
        output_dir = ensure_output_dir()
        logger.info(f"✅ Output directory: {output_dir}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Import test failed: {e}")
        return False

def main():
    """メイン実行関数"""
    logger.info("🚀 BlogAuto Setup Test - Phase 1")
    logger.info("=" * 50)
    
    results = {
        'directory_structure': check_directory_structure(),
        'required_files': check_required_files(),
        'python_environment': check_python_environment(),
        'environment_variables': check_environment_variables(),
        'import_test': run_basic_import_test()
    }
    
    # 結果サマリー
    logger.info("\n📊 Test Results Summary")
    logger.info("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("✅ All tests passed! Environment is ready.")
        return 0
    else:
        logger.warning("⚠️  Some tests failed. Please check the logs above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())