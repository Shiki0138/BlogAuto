#!/usr/bin/env python3
"""
API認証システム
フェーズ3: 認証システム構築（criticalタスク）
"""
import os
import base64
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import json
from pathlib import Path
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class APICredential:
    """API認証情報を管理するデータクラス"""
    api_name: str
    api_key: str
    is_valid: bool = True
    created_at: datetime = None
    last_used: datetime = None
    usage_count: int = 0
    rate_limit: int = 0
    remaining_quota: int = 0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def mask_key(self) -> str:
        """APIキーをマスク表示"""
        if len(self.api_key) <= 8:
            return "****"
        return f"{self.api_key[:4]}...{self.api_key[-4:]}"

class APIAuthManager:
    """API認証を管理するクラス"""
    
    def __init__(self, config_dir: Path = None):
        """初期化"""
        self.config_dir = config_dir or Path.home() / ".blogauto"
        self.config_dir.mkdir(exist_ok=True)
        self.credentials_file = self.config_dir / "credentials.enc"
        self.master_key_file = self.config_dir / "master.key"
        self._credentials: Dict[str, APICredential] = {}
        self._master_key: Optional[bytes] = None
        
        # マスターキーの初期化
        self._init_master_key()
        
        # 既存の認証情報を読み込み
        self._load_credentials()
    
    def _init_master_key(self) -> None:
        """マスターキーの初期化または読み込み"""
        if self.master_key_file.exists():
            # 既存のマスターキーを読み込み
            with open(self.master_key_file, 'rb') as f:
                self._master_key = f.read()
        else:
            # 新しいマスターキーを生成
            self._master_key = secrets.token_bytes(32)
            with open(self.master_key_file, 'wb') as f:
                f.write(self._master_key)
            
            # ファイル権限を600に設定（所有者のみ読み書き可能）
            os.chmod(self.master_key_file, 0o600)
            
            logger.info("新しいマスターキーを生成しました")
    
    def _encrypt_data(self, data: str) -> str:
        """データを暗号化（簡易実装）"""
        # 本番環境では cryptography ライブラリなどを使用すべき
        # ここでは簡易的にXOR暗号化を実装
        if not self._master_key:
            raise ValueError("マスターキーが初期化されていません")
        
        encrypted = []
        key_len = len(self._master_key)
        
        for i, char in enumerate(data.encode('utf-8')):
            encrypted.append(char ^ self._master_key[i % key_len])
        
        return base64.b64encode(bytes(encrypted)).decode('utf-8')
    
    def _decrypt_data(self, encrypted_data: str) -> str:
        """データを復号化（簡易実装）"""
        if not self._master_key:
            raise ValueError("マスターキーが初期化されていません")
        
        encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
        decrypted = []
        key_len = len(self._master_key)
        
        for i, byte in enumerate(encrypted_bytes):
            decrypted.append(byte ^ self._master_key[i % key_len])
        
        return bytes(decrypted).decode('utf-8')
    
    def add_credential(self, api_name: str, api_key: str) -> bool:
        """API認証情報を追加"""
        try:
            # 認証情報を作成
            credential = APICredential(
                api_name=api_name,
                api_key=api_key,
                created_at=datetime.now()
            )
            
            # メモリに保存
            self._credentials[api_name] = credential
            
            # ファイルに保存
            self._save_credentials()
            
            logger.info(f"API認証情報を追加しました: {api_name}")
            return True
            
        except Exception as e:
            logger.error(f"認証情報の追加に失敗: {e}")
            return False
    
    def get_credential(self, api_name: str) -> Optional[APICredential]:
        """API認証情報を取得"""
        credential = self._credentials.get(api_name)
        
        if credential:
            # 使用履歴を更新
            credential.last_used = datetime.now()
            credential.usage_count += 1
            self._save_credentials()
        
        return credential
    
    def remove_credential(self, api_name: str) -> bool:
        """API認証情報を削除"""
        if api_name in self._credentials:
            del self._credentials[api_name]
            self._save_credentials()
            logger.info(f"API認証情報を削除しました: {api_name}")
            return True
        return False
    
    def validate_credential(self, api_name: str) -> bool:
        """API認証情報の妥当性をチェック"""
        credential = self._credentials.get(api_name)
        
        if not credential:
            return False
        
        # APIキーの基本的な検証
        if not credential.api_key or len(credential.api_key) < 10:
            return False
        
        # 有効フラグのチェック
        if not credential.is_valid:
            return False
        
        return True
    
    def _save_credentials(self) -> None:
        """認証情報をファイルに保存"""
        try:
            # 認証情報を辞書に変換
            data = {}
            for api_name, credential in self._credentials.items():
                data[api_name] = {
                    'api_key': credential.api_key,
                    'is_valid': credential.is_valid,
                    'created_at': credential.created_at.isoformat(),
                    'last_used': credential.last_used.isoformat() if credential.last_used else None,
                    'usage_count': credential.usage_count,
                    'rate_limit': credential.rate_limit,
                    'remaining_quota': credential.remaining_quota
                }
            
            # JSON形式に変換
            json_data = json.dumps(data, ensure_ascii=False, indent=2)
            
            # 暗号化して保存
            encrypted_data = self._encrypt_data(json_data)
            
            with open(self.credentials_file, 'w', encoding='utf-8') as f:
                f.write(encrypted_data)
            
            # ファイル権限を600に設定
            os.chmod(self.credentials_file, 0o600)
            
        except Exception as e:
            logger.error(f"認証情報の保存に失敗: {e}")
    
    def _load_credentials(self) -> None:
        """認証情報をファイルから読み込み"""
        if not self.credentials_file.exists():
            logger.info("認証情報ファイルが存在しません")
            return
        
        try:
            # 暗号化されたデータを読み込み
            with open(self.credentials_file, 'r', encoding='utf-8') as f:
                encrypted_data = f.read()
            
            # 復号化
            json_data = self._decrypt_data(encrypted_data)
            data = json.loads(json_data)
            
            # APICredentialオブジェクトに変換
            self._credentials = {}
            for api_name, cred_data in data.items():
                credential = APICredential(
                    api_name=api_name,
                    api_key=cred_data['api_key'],
                    is_valid=cred_data.get('is_valid', True),
                    created_at=datetime.fromisoformat(cred_data['created_at']),
                    last_used=datetime.fromisoformat(cred_data['last_used']) if cred_data.get('last_used') else None,
                    usage_count=cred_data.get('usage_count', 0),
                    rate_limit=cred_data.get('rate_limit', 0),
                    remaining_quota=cred_data.get('remaining_quota', 0)
                )
                self._credentials[api_name] = credential
            
            logger.info(f"認証情報を読み込みました: {len(self._credentials)}件")
            
        except Exception as e:
            logger.error(f"認証情報の読み込みに失敗: {e}")
    
    def load_from_env(self) -> int:
        """環境変数からAPI認証情報を読み込み"""
        loaded_count = 0
        
        # 各APIの環境変数名
        env_mappings = {
            'ANTHROPIC_API_KEY': 'anthropic',
            'UNSPLASH_ACCESS_KEY': 'unsplash',
            'PEXELS_API_KEY': 'pexels',
            'GEMINI_API_KEY': 'gemini',
            'OPENAI_API_KEY': 'openai',
            'WP_USER': 'wordpress_user',
            'WP_APP_PASS': 'wordpress_pass'
        }
        
        for env_name, api_name in env_mappings.items():
            api_key = os.getenv(env_name)
            if api_key:
                if self.add_credential(api_name, api_key):
                    loaded_count += 1
                    logger.info(f"環境変数から認証情報を読み込み: {api_name}")
        
        return loaded_count
    
    def get_status(self) -> Dict[str, Any]:
        """認証システムの状態を取得"""
        return {
            'total_credentials': len(self._credentials),
            'active_credentials': sum(1 for c in self._credentials.values() if c.is_valid),
            'credentials': {
                api_name: {
                    'is_valid': cred.is_valid,
                    'masked_key': cred.mask_key(),
                    'usage_count': cred.usage_count,
                    'last_used': cred.last_used.isoformat() if cred.last_used else None
                }
                for api_name, cred in self._credentials.items()
            }
        }

# グローバルインスタンス
_auth_manager = None

def get_auth_manager() -> APIAuthManager:
    """認証マネージャーのシングルトンインスタンスを取得"""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = APIAuthManager()
        # 環境変数から自動読み込み
        _auth_manager.load_from_env()
    return _auth_manager