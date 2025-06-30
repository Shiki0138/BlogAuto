#!/usr/bin/env python3
"""
認証システム管理 - フェーズ3実装
APIキー管理とセキュアな認証処理
"""
import os
import base64
import hashlib
import secrets
from typing import Dict, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime, timedelta
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from scripts.utils import logger, get_env_var


class AuthManager:
    """認証管理クラス - セキュアなAPIキー管理"""
    
    def __init__(self, config_dir: str = ".config"):
        """初期化"""
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True, mode=0o700)  # 700権限で作成
        self.credentials_file = self.config_dir / "credentials.enc"
        self.salt_file = self.config_dir / "salt.key"
        self._cipher = None
        self._credentials_cache = {}
        self._cache_expiry = {}
        
    def _get_or_create_salt(self) -> bytes:
        """ソルト取得または生成"""
        if self.salt_file.exists():
            return self.salt_file.read_bytes()
        else:
            salt = secrets.token_bytes(32)
            self.salt_file.write_bytes(salt)
            self.salt_file.chmod(0o600)  # 600権限
            return salt
    
    def _derive_key(self, password: str) -> bytes:
        """パスワードから暗号化キーを導出"""
        salt = self._get_or_create_salt()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def _get_cipher(self, password: Optional[str] = None) -> Fernet:
        """暗号化オブジェクト取得"""
        if self._cipher is None:
            if password is None:
                # 環境変数から取得
                password = os.getenv('BLOGAUTO_MASTER_KEY', 'default_key_for_development')
            key = self._derive_key(password)
            self._cipher = Fernet(key)
        return self._cipher
    
    def store_credential(self, service: str, key: str, value: str, 
                        password: Optional[str] = None) -> bool:
        """認証情報を暗号化して保存"""
        try:
            # 既存の認証情報を読み込み
            credentials = self._load_credentials(password)
            
            # サービス情報を追加/更新
            if service not in credentials:
                credentials[service] = {}
            
            credentials[service][key] = {
                'value': value,
                'created_at': datetime.now().isoformat(),
                'expires_at': None  # 必要に応じて有効期限設定
            }
            
            # 暗号化して保存
            self._save_credentials(credentials, password)
            
            logger.info(f"認証情報を保存: {service}/{key}")
            return True
            
        except Exception as e:
            logger.error(f"認証情報保存エラー: {e}")
            return False
    
    def get_credential(self, service: str, key: str, 
                      password: Optional[str] = None) -> Optional[str]:
        """認証情報を復号化して取得"""
        try:
            # キャッシュ確認
            cache_key = f"{service}:{key}"
            if cache_key in self._credentials_cache:
                expiry = self._cache_expiry.get(cache_key)
                if expiry and datetime.now() < expiry:
                    return self._credentials_cache[cache_key]
            
            # 認証情報を読み込み
            credentials = self._load_credentials(password)
            
            if service in credentials and key in credentials[service]:
                cred_data = credentials[service][key]
                
                # 有効期限確認
                if cred_data.get('expires_at'):
                    expires_at = datetime.fromisoformat(cred_data['expires_at'])
                    if datetime.now() > expires_at:
                        logger.warning(f"認証情報期限切れ: {service}/{key}")
                        return None
                
                value = cred_data['value']
                
                # キャッシュに保存（5分間）
                self._credentials_cache[cache_key] = value
                self._cache_expiry[cache_key] = datetime.now() + timedelta(minutes=5)
                
                return value
            
            return None
            
        except Exception as e:
            logger.error(f"認証情報取得エラー: {e}")
            return None
    
    def _load_credentials(self, password: Optional[str] = None) -> Dict[str, Any]:
        """暗号化された認証情報を読み込み"""
        if not self.credentials_file.exists():
            return {}
        
        try:
            cipher = self._get_cipher(password)
            encrypted_data = self.credentials_file.read_bytes()
            decrypted_data = cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            logger.error(f"認証情報読み込みエラー: {e}")
            return {}
    
    def _save_credentials(self, credentials: Dict[str, Any], 
                         password: Optional[str] = None) -> None:
        """認証情報を暗号化して保存"""
        try:
            cipher = self._get_cipher(password)
            json_data = json.dumps(credentials).encode()
            encrypted_data = cipher.encrypt(json_data)
            self.credentials_file.write_bytes(encrypted_data)
            self.credentials_file.chmod(0o600)  # 600権限
        except Exception as e:
            logger.error(f"認証情報保存エラー: {e}")
            raise
    
    def clear_cache(self):
        """キャッシュクリア"""
        self._credentials_cache.clear()
        self._cache_expiry.clear()
        self._cipher = None


class APIKeyValidator:
    """APIキー検証クラス"""
    
    @staticmethod
    def validate_wordpress_creds(user: str, password: str, site_url: str) -> bool:
        """WordPress認証情報の検証"""
        if not all([user, password, site_url]):
            return False
        
        # 基本的な形式チェック
        if not site_url.startswith(('http://', 'https://')):
            return False
        
        if len(password) < 16:  # Application Passwordは通常24文字
            return False
        
        return True
    
    @staticmethod
    def validate_api_key(service: str, key: str) -> bool:
        """APIキーの基本検証"""
        if not key:
            return False
        
        # サービス別の検証
        validations = {
            'anthropic': lambda k: k.startswith('sk-') and len(k) > 40,
            'unsplash': lambda k: len(k) > 20,
            'pexels': lambda k: len(k) > 20,
            'gemini': lambda k: len(k) > 30,
            'openai': lambda k: k.startswith('sk-') and len(k) > 40,
        }
        
        validator = validations.get(service.lower())
        if validator:
            return validator(key)
        
        # デフォルト: 最低限の長さチェック
        return len(key) >= 16


class SecureEnvironment:
    """セキュアな環境変数管理"""
    
    def __init__(self, auth_manager: AuthManager):
        self.auth_manager = auth_manager
        self.validator = APIKeyValidator()
    
    def load_credentials(self) -> Dict[str, str]:
        """環境変数と暗号化ストレージから認証情報をロード"""
        credentials = {}
        
        # WordPress認証情報
        wp_user = self._get_secure_value('wordpress', 'user', 'WP_USER')
        wp_pass = self._get_secure_value('wordpress', 'password', 'WP_APP_PASS')
        wp_url = self._get_secure_value('wordpress', 'site_url', 'WP_SITE_URL')
        
        if self.validator.validate_wordpress_creds(wp_user, wp_pass, wp_url):
            credentials['WP_USER'] = wp_user
            credentials['WP_APP_PASS'] = wp_pass
            credentials['WP_SITE_URL'] = wp_url
        
        # API Keys
        api_services = [
            ('anthropic', 'ANTHROPIC_API_KEY'),
            ('unsplash', 'UNSPLASH_ACCESS_KEY'),
            ('pexels', 'PEXELS_API_KEY'),
            ('gemini', 'GEMINI_API_KEY'),
            ('openai', 'OPENAI_API_KEY'),
        ]
        
        for service, env_key in api_services:
            api_key = self._get_secure_value(service, 'api_key', env_key)
            if api_key and self.validator.validate_api_key(service, api_key):
                credentials[env_key] = api_key
        
        return credentials
    
    def _get_secure_value(self, service: str, key: str, env_key: str) -> Optional[str]:
        """環境変数または暗号化ストレージから値を取得"""
        # 1. 環境変数から取得
        value = os.getenv(env_key)
        if value:
            return value
        
        # 2. 暗号化ストレージから取得
        value = self.auth_manager.get_credential(service, key)
        if value:
            # 環境変数にセット（現在のセッションのみ）
            os.environ[env_key] = value
            return value
        
        return None
    
    def setup_environment(self) -> bool:
        """セキュアな環境をセットアップ"""
        try:
            credentials = self.load_credentials()
            
            if not credentials:
                logger.warning("認証情報が見つかりません")
                return False
            
            # 現在のフェーズでは外部API接続無効
            os.environ['ENABLE_EXTERNAL_API'] = 'false'
            
            logger.info(f"環境セットアップ完了: {len(credentials)}個の認証情報をロード")
            return True
            
        except Exception as e:
            logger.error(f"環境セットアップエラー: {e}")
            return False


# 認証情報の初期設定ヘルパー
def setup_credentials_interactive():
    """対話的に認証情報をセットアップ"""
    print("BlogAuto 認証情報セットアップ")
    print("-" * 40)
    
    auth = AuthManager()
    
    # マスターパスワード設定
    import getpass
    password = getpass.getpass("マスターパスワードを設定: ")
    
    # WordPress情報
    print("\n[WordPress設定]")
    wp_user = input("ユーザー名: ")
    wp_pass = getpass.getpass("Application Password: ")
    wp_url = input("サイトURL (https://example.com): ")
    
    if wp_user and wp_pass and wp_url:
        auth.store_credential('wordpress', 'user', wp_user, password)
        auth.store_credential('wordpress', 'password', wp_pass, password)
        auth.store_credential('wordpress', 'site_url', wp_url, password)
    
    # API Keys
    print("\n[API Keys（オプション）]")
    
    services = [
        ('anthropic', 'Claude API Key'),
        ('unsplash', 'Unsplash Access Key'),
        ('pexels', 'Pexels API Key'),
        ('gemini', 'Gemini API Key'),
        ('openai', 'OpenAI API Key'),
    ]
    
    for service, display_name in services:
        key = getpass.getpass(f"{display_name} (Enterでスキップ): ")
        if key:
            auth.store_credential(service, 'api_key', key, password)
    
    print("\n✅ 認証情報のセットアップが完了しました")
    print("環境変数 BLOGAUTO_MASTER_KEY にマスターパスワードを設定してください")


# テスト用メイン関数
def test_auth_system():
    """認証システムのテスト"""
    auth = AuthManager()
    
    # テスト用認証情報
    test_password = "test_password_123"
    
    # 保存テスト
    assert auth.store_credential('test_service', 'api_key', 'test_key_value', test_password)
    
    # 取得テスト
    retrieved = auth.get_credential('test_service', 'api_key', test_password)
    assert retrieved == 'test_key_value'
    
    # バリデーションテスト
    validator = APIKeyValidator()
    assert validator.validate_api_key('anthropic', 'sk-' + 'a' * 40)
    assert not validator.validate_api_key('anthropic', 'invalid_key')
    
    print("認証システムテスト: すべて成功")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        setup_credentials_interactive()
    else:
        test_auth_system()