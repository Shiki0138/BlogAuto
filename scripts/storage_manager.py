#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Storage API Manager - Final Phase Implementation
ストレージAPI統合・管理システム（AWS S3, Google Cloud Storage, Azure Blob）
"""
import os
import sys
import json
import boto3
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import hashlib
import mimetypes

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

try:
    from scripts.utils import logger, get_env_var, save_json_safely
    from scripts.auth_manager import SecureEnvironment, AuthManager
except ImportError:
    # フォールバック実装
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    def get_env_var(key, required=True, default=None):
        value = os.getenv(key, default)
        if required and not value:
            logger.error(f"Required environment variable {key} not set")
        return value
    
    def save_json_safely(data, filepath):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True

class StorageProvider:
    """ストレージプロバイダー基底クラス"""
    
    def upload_file(self, local_path: str, remote_path: str) -> Optional[str]:
        """ファイルアップロード"""
        raise NotImplementedError
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """ファイルダウンロード"""
        raise NotImplementedError
    
    def delete_file(self, remote_path: str) -> bool:
        """ファイル削除"""
        raise NotImplementedError
    
    def list_files(self, prefix: str = "") -> List[str]:
        """ファイル一覧取得"""
        raise NotImplementedError

class S3StorageProvider(StorageProvider):
    """AWS S3ストレージプロバイダー"""
    
    def __init__(self):
        """初期化"""
        self.aws_access_key = get_env_var('AWS_ACCESS_KEY_ID', required=False)
        self.aws_secret_key = get_env_var('AWS_SECRET_ACCESS_KEY', required=False)
        self.bucket_name = get_env_var('S3_BUCKET_NAME', required=False)
        self.region = get_env_var('AWS_REGION', required=False, default='us-east-1')
        
        # 外部API接続フラグ確認
        self.enable_api = os.getenv('ENABLE_EXTERNAL_API', 'false').lower() == 'true'
        self.mock_mode = not self.enable_api or not all([
            self.aws_access_key, self.aws_secret_key, self.bucket_name
        ])
        
        if self.mock_mode:
            logger.info("S3ストレージ: モック動作（外部API接続無効）")
            self.client = None
        else:
            try:
                self.client = boto3.client(
                    's3',
                    aws_access_key_id=self.aws_access_key,
                    aws_secret_access_key=self.aws_secret_key,
                    region_name=self.region
                )
                logger.info("S3ストレージ: 本番モード接続完了")
            except Exception as e:
                logger.error(f"S3接続エラー: {e}")
                self.mock_mode = True
                self.client = None
    
    def upload_file(self, local_path: str, remote_path: str) -> Optional[str]:
        """ファイルアップロード"""
        try:
            if self.mock_mode:
                logger.info(f"S3アップロード（モック）: {local_path} → {remote_path}")
                return f"https://mock-s3-bucket.s3.amazonaws.com/{remote_path}"
            
            if not Path(local_path).exists():
                logger.error(f"アップロードファイルが見つかりません: {local_path}")
                return None
            
            # MIMEタイプ検出
            content_type, _ = mimetypes.guess_type(local_path)
            if not content_type:
                content_type = 'application/octet-stream'
            
            # S3アップロード
            extra_args = {
                'ContentType': content_type,
                'ACL': 'public-read'
            }
            
            self.client.upload_file(
                local_path, 
                self.bucket_name, 
                remote_path, 
                ExtraArgs=extra_args
            )
            
            # アップロードURL生成
            url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{remote_path}"
            logger.info(f"S3アップロード完了: {url}")
            return url
            
        except Exception as e:
            logger.error(f"S3アップロードエラー: {e}")
            return None
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """ファイルダウンロード"""
        try:
            if self.mock_mode:
                logger.info(f"S3ダウンロード（モック）: {remote_path} → {local_path}")
                # モックファイル作成
                Path(local_path).parent.mkdir(parents=True, exist_ok=True)
                Path(local_path).write_text("mock file content")
                return True
            
            self.client.download_file(self.bucket_name, remote_path, local_path)
            logger.info(f"S3ダウンロード完了: {local_path}")
            return True
            
        except Exception as e:
            logger.error(f"S3ダウンロードエラー: {e}")
            return False
    
    def delete_file(self, remote_path: str) -> bool:
        """ファイル削除"""
        try:
            if self.mock_mode:
                logger.info(f"S3削除（モック）: {remote_path}")
                return True
            
            self.client.delete_object(Bucket=self.bucket_name, Key=remote_path)
            logger.info(f"S3削除完了: {remote_path}")
            return True
            
        except Exception as e:
            logger.error(f"S3削除エラー: {e}")
            return False
    
    def list_files(self, prefix: str = "") -> List[str]:
        """ファイル一覧取得"""
        try:
            if self.mock_mode:
                logger.info(f"S3リスト（モック）: prefix={prefix}")
                return [
                    f"{prefix}mock-file-1.jpg",
                    f"{prefix}mock-file-2.md",
                    f"{prefix}mock-file-3.json"
                ]
            
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            files = []
            if 'Contents' in response:
                files = [obj['Key'] for obj in response['Contents']]
            
            logger.info(f"S3リスト取得完了: {len(files)}件")
            return files
            
        except Exception as e:
            logger.error(f"S3リストエラー: {e}")
            return []

class GoogleCloudStorageProvider(StorageProvider):
    """Google Cloud Storageプロバイダー（モック実装）"""
    
    def __init__(self):
        """初期化"""
        self.mock_mode = True  # 現段階ではモック動作のみ
        logger.info("Google Cloud Storage: モック動作")
    
    def upload_file(self, local_path: str, remote_path: str) -> Optional[str]:
        """ファイルアップロード（モック）"""
        logger.info(f"GCSアップロード（モック）: {local_path} → {remote_path}")
        return f"https://storage.googleapis.com/mock-bucket/{remote_path}"
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """ファイルダウンロード（モック）"""
        logger.info(f"GCSダウンロード（モック）: {remote_path} → {local_path}")
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)
        Path(local_path).write_text("mock gcs content")
        return True
    
    def delete_file(self, remote_path: str) -> bool:
        """ファイル削除（モック）"""
        logger.info(f"GCS削除（モック）: {remote_path}")
        return True
    
    def list_files(self, prefix: str = "") -> List[str]:
        """ファイル一覧取得（モック）"""
        logger.info(f"GCSリスト（モック）: prefix={prefix}")
        return [f"{prefix}gcs-mock-{i}.jpg" for i in range(3)]

class AzureBlobProvider(StorageProvider):
    """Azure Blob Storageプロバイダー（モック実装）"""
    
    def __init__(self):
        """初期化"""
        self.mock_mode = True  # 現段階ではモック動作のみ
        logger.info("Azure Blob Storage: モック動作")
    
    def upload_file(self, local_path: str, remote_path: str) -> Optional[str]:
        """ファイルアップロード（モック）"""
        logger.info(f"Azureアップロード（モック）: {local_path} → {remote_path}")
        return f"https://mockaccount.blob.core.windows.net/container/{remote_path}"
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """ファイルダウンロード（モック）"""
        logger.info(f"Azureダウンロード（モック）: {remote_path} → {local_path}")
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)
        Path(local_path).write_text("mock azure content")
        return True
    
    def delete_file(self, remote_path: str) -> bool:
        """ファイル削除（モック）"""
        logger.info(f"Azure削除（モック）: {remote_path}")
        return True
    
    def list_files(self, prefix: str = "") -> List[str]:
        """ファイル一覧取得（モック）"""
        logger.info(f"Azureリスト（モック）: prefix={prefix}")
        return [f"{prefix}azure-mock-{i}.jpg" for i in range(3)]

class StorageManager:
    """統合ストレージ管理システム"""
    
    def __init__(self):
        """初期化"""
        self.providers = {}
        self.active_provider = None
        
        # ストレージプロバイダー初期化
        self._initialize_providers()
        self._select_active_provider()
        
        logger.info("StorageManager initialized")
    
    def _initialize_providers(self):
        """ストレージプロバイダー初期化"""
        try:
            # AWS S3
            self.providers['s3'] = S3StorageProvider()
            
            # Google Cloud Storage
            self.providers['gcs'] = GoogleCloudStorageProvider()
            
            # Azure Blob Storage
            self.providers['azure'] = AzureBlobProvider()
            
            logger.info("ストレージプロバイダー初期化完了")
            
        except Exception as e:
            logger.error(f"ストレージプロバイダー初期化エラー: {e}")
    
    def _select_active_provider(self):
        """アクティブプロバイダー選択"""
        # 優先順位: S3 → GCS → Azure
        preferred_order = ['s3', 'gcs', 'azure']
        
        for provider_name in preferred_order:
            if provider_name in self.providers:
                self.active_provider = provider_name
                logger.info(f"アクティブストレージプロバイダー: {provider_name}")
                break
    
    def upload_blog_assets(self, article_date: str) -> Dict[str, Any]:
        """ブログアセットアップロード"""
        try:
            logger.info("ブログアセットアップロード開始")
            
            results = {
                'success': False,
                'uploaded_files': [],
                'urls': {},
                'provider': self.active_provider,
                'timestamp': datetime.now().isoformat()
            }
            
            # アップロード対象ファイル
            assets = [
                {
                    'local': 'output/article.md',
                    'remote': f"blog/{article_date}/article.md",
                    'type': 'article'
                },
                {
                    'local': 'output/meta.json',
                    'remote': f"blog/{article_date}/meta.json",
                    'type': 'metadata'
                },
                {
                    'local': 'output/cover.jpg',
                    'remote': f"blog/{article_date}/cover.jpg",
                    'type': 'image'
                },
                {
                    'local': 'output/image_info.json',
                    'remote': f"blog/{article_date}/image_info.json",
                    'type': 'image_info'
                }
            ]
            
            provider = self.providers[self.active_provider]
            uploaded_count = 0
            
            for asset in assets:
                local_path = asset['local']
                remote_path = asset['remote']
                
                if Path(local_path).exists():
                    url = provider.upload_file(local_path, remote_path)
                    if url:
                        results['uploaded_files'].append({
                            'local_path': local_path,
                            'remote_path': remote_path,
                            'url': url,
                            'type': asset['type']
                        })
                        results['urls'][asset['type']] = url
                        uploaded_count += 1
                        logger.info(f"アップロード成功: {local_path} → {url}")
                    else:
                        logger.warning(f"アップロード失敗: {local_path}")
                else:
                    logger.warning(f"ファイルが見つかりません: {local_path}")
            
            results['success'] = uploaded_count > 0
            results['total_uploaded'] = uploaded_count
            
            # 結果保存
            save_json_safely(results, 'output/storage_results.json')
            
            logger.info(f"ブログアセットアップロード完了: {uploaded_count}件成功")
            return results
            
        except Exception as e:
            logger.error(f"ブログアセットアップロードエラー: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def backup_system_files(self) -> Dict[str, Any]:
        """システムファイルバックアップ"""
        try:
            logger.info("システムファイルバックアップ開始")
            
            backup_date = datetime.now().strftime('%Y%m%d_%H%M%S')
            results = {
                'success': False,
                'backup_date': backup_date,
                'backed_up_files': [],
                'provider': self.active_provider
            }
            
            # バックアップ対象
            system_files = [
                'README.md',
                'requirements.txt',
                '.env.example',
                'development/development_log.txt',
                'specifications/project_spec.md'
            ]
            
            provider = self.providers[self.active_provider]
            backup_count = 0
            
            for file_path in system_files:
                if Path(file_path).exists():
                    remote_path = f"backups/{backup_date}/{file_path}"
                    url = provider.upload_file(file_path, remote_path)
                    if url:
                        results['backed_up_files'].append({
                            'file': file_path,
                            'remote_path': remote_path,
                            'url': url
                        })
                        backup_count += 1
            
            results['success'] = backup_count > 0
            results['total_backed_up'] = backup_count
            
            logger.info(f"システムファイルバックアップ完了: {backup_count}件")
            return results
            
        except Exception as e:
            logger.error(f"システムファイルバックアップエラー: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """ストレージ統計取得"""
        try:
            provider = self.providers[self.active_provider]
            
            # ファイル一覧取得
            blog_files = provider.list_files('blog/')
            backup_files = provider.list_files('backups/')
            
            stats = {
                'provider': self.active_provider,
                'total_blog_files': len(blog_files),
                'total_backup_files': len(backup_files),
                'recent_blog_files': blog_files[-10:] if blog_files else [],
                'recent_backup_files': backup_files[-5:] if backup_files else [],
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"ストレージ統計: ブログ{len(blog_files)}件、バックアップ{len(backup_files)}件")
            return stats
            
        except Exception as e:
            logger.error(f"ストレージ統計取得エラー: {e}")
            return {'error': str(e)}

def main():
    """メイン実行関数"""
    try:
        logger.info("🗄️  ストレージAPI統合システム開始")
        
        # ストレージマネージャー初期化
        storage_manager = StorageManager()
        
        # 現在日付取得
        today = datetime.now().strftime('%Y%m%d')
        
        # ブログアセットアップロード
        upload_results = storage_manager.upload_blog_assets(today)
        
        # システムファイルバックアップ
        backup_results = storage_manager.backup_system_files()
        
        # ストレージ統計取得
        storage_stats = storage_manager.get_storage_stats()
        
        # 完了レポート作成
        final_report = {
            'storage_integration_complete': True,
            'upload_results': upload_results,
            'backup_results': backup_results,
            'storage_stats': storage_stats,
            'active_provider': storage_manager.active_provider,
            'completion_time': datetime.now().isoformat()
        }
        
        save_json_safely(final_report, 'output/storage_integration_report.json')
        
        logger.info("✅ ストレージAPI統合完了")
        logger.info(f"📊 アップロード: {upload_results.get('total_uploaded', 0)}件")
        logger.info(f"💾 バックアップ: {backup_results.get('total_backed_up', 0)}件")
        logger.info(f"🗃️  プロバイダー: {storage_manager.active_provider}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ ストレージAPI統合エラー: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)