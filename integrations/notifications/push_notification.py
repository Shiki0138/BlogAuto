"""
Push Notification Service
最終100%完成フェーズ: プッシュ通知API統合
Firebase/APNS/FCM対応実装
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import time
import logging

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent))

from auth.api_auth import APIAuthManager
from scripts.utils import logger
from .notification_manager import (
    NotificationServiceBase, NotificationMessage, NotificationResponse, NotificationProvider
)

class PushNotificationService(NotificationServiceBase):
    """プッシュ通知サービス"""
    
    def __init__(self, auth_manager: APIAuthManager):
        """初期化"""
        super().__init__(auth_manager)
        
        # 認証情報取得
        self.firebase_cred = self.auth_manager.get_credential("firebase")
        self.apns_cred = self.auth_manager.get_credential("apns")
        
        self.push_enabled = False
        self.firebase_client = None
        self.apns_client = None
        
        # リトライ設定
        self.max_retries = 3
        self.retry_delay = 2
        
        # 初期化
        self._initialize_push_services()
        
    def _initialize_push_services(self):
        """プッシュ通知サービスを初期化"""
        try:
            # 外部API接続フラグ確認
            enable_api = os.getenv('ENABLE_EXTERNAL_API', 'false').lower() == 'true'
            
            if not enable_api:
                logger.info("🚧 Push notification API接続は無効（モック動作）")
                self.push_enabled = False
                return
            
            # Firebase初期化
            if self.firebase_cred:
                try:
                    import firebase_admin
                    from firebase_admin import credentials, messaging
                    
                    # Firebase認証情報設定
                    if not firebase_admin._apps:
                        cred = credentials.Certificate(self.firebase_cred.api_key)
                        firebase_admin.initialize_app(cred)
                    
                    self.firebase_client = messaging
                    logger.info("✅ Firebase push notification initialized")
                    
                except ImportError:
                    logger.warning("firebase-admin library not installed")
                except Exception as e:
                    logger.error(f"Firebase initialization error: {e}")
            
            # APNS初期化（iOS向け）
            if self.apns_cred:
                try:
                    from apns2.client import APNsClient
                    from apns2.credentials import TokenCredentials
                    
                    credentials_obj = TokenCredentials(
                        auth_key_path=self.apns_cred.api_key,
                        auth_key_id=self.apns_cred.api_secret,
                        team_id=os.getenv('APNS_TEAM_ID')
                    )
                    
                    self.apns_client = APNsClient(
                        credentials=credentials_obj,
                        use_sandbox=os.getenv('APNS_SANDBOX', 'true').lower() == 'true'
                    )
                    
                    logger.info("✅ APNS push notification initialized")
                    
                except ImportError:
                    logger.warning("apns2 library not installed")
                except Exception as e:
                    logger.error(f"APNS initialization error: {e}")
            
            # 有効な通知サービスがあるかチェック
            if self.firebase_client or self.apns_client:
                self.push_enabled = True
            else:
                self.push_enabled = False
                logger.warning("No push notification services available")
                
        except Exception as e:
            logger.error(f"Push notification setup error: {e}")
            self.push_enabled = False
    
    def send_notification(self, message: NotificationMessage) -> NotificationResponse:
        """プッシュ通知を送信"""
        try:
            logger.info(f"Push notification送信開始: {message.title}")
            
            if not self.push_enabled:
                # モック通知
                return self._send_mock_notification(message)
            
            # デバイスタイプ判定（簡易版）
            if self._is_ios_token(message.target):
                return self._send_apns_notification(message)
            else:
                return self._send_firebase_notification(message)
                
        except Exception as e:
            logger.error(f"Push notification送信エラー: {e}")
            return NotificationResponse(
                provider=NotificationProvider.PUSH,
                message_id="error",
                status="error",
                target=message.target,
                sent_at=datetime.now(),
                error_message=str(e)
            )
    
    def _send_firebase_notification(self, message: NotificationMessage) -> NotificationResponse:
        """Firebase経由でプッシュ通知を送信"""
        try:
            if not self.firebase_client:
                raise Exception("Firebase client not initialized")
            
            # Firebase Messaging形式に変換
            firebase_message = self.firebase_client.Message(
                notification=self.firebase_client.Notification(
                    title=message.title,
                    body=message.body
                ),
                data=message.data or {},
                token=message.target,
                android=self.firebase_client.AndroidConfig(
                    priority='high' if message.priority == 'high' else 'normal',
                    notification=self.firebase_client.AndroidNotification(
                        icon='ic_notification',
                        color='#FF0000'
                    )
                ),
                apns=self.firebase_client.APNSConfig(
                    payload=self.firebase_client.APNSPayload(
                        aps=self.firebase_client.Aps(
                            alert=self.firebase_client.ApsAlert(
                                title=message.title,
                                body=message.body
                            ),
                            badge=1,
                            sound='default'
                        )
                    )
                )
            )
            
            # 送信実行
            response = self.firebase_client.send(firebase_message)
            
            return NotificationResponse(
                provider=NotificationProvider.PUSH,
                message_id=response,
                status="sent",
                target=message.target,
                sent_at=datetime.now(),
                raw_response={"firebase_message_id": response}
            )
            
        except Exception as e:
            logger.error(f"Firebase notification error: {e}")
            return NotificationResponse(
                provider=NotificationProvider.PUSH,
                message_id="firebase_error",
                status="error",
                target=message.target,
                sent_at=datetime.now(),
                error_message=str(e)
            )
    
    def _send_apns_notification(self, message: NotificationMessage) -> NotificationResponse:
        """APNS経由でプッシュ通知を送信（iOS）"""
        try:
            if not self.apns_client:
                raise Exception("APNS client not initialized")
            
            from apns2.payload import Payload
            
            # APNS Payload作成
            payload = Payload(
                alert={
                    'title': message.title,
                    'body': message.body
                },
                badge=1,
                sound='default',
                custom=message.data or {}
            )
            
            # 送信実行
            response = self.apns_client.send_notification(
                token_hex=message.target,
                notification=payload,
                topic=os.getenv('APNS_BUNDLE_ID', 'com.blogauto.app')
            )
            
            if response.is_successful:
                return NotificationResponse(
                    provider=NotificationProvider.PUSH,
                    message_id=response.apns_id or "apns_success",
                    status="sent",
                    target=message.target,
                    sent_at=datetime.now(),
                    raw_response={"apns_id": response.apns_id}
                )
            else:
                return NotificationResponse(
                    provider=NotificationProvider.PUSH,
                    message_id="apns_error",
                    status="error",
                    target=message.target,
                    sent_at=datetime.now(),
                    error_message=f"APNS error: {response.description}"
                )
                
        except Exception as e:
            logger.error(f"APNS notification error: {e}")
            return NotificationResponse(
                provider=NotificationProvider.PUSH,
                message_id="apns_error",
                status="error",
                target=message.target,
                sent_at=datetime.now(),
                error_message=str(e)
            )
    
    def _send_mock_notification(self, message: NotificationMessage) -> NotificationResponse:
        """モックプッシュ通知を送信"""
        mock_id = f"mock_push_{int(time.time())}"
        
        logger.info(f"Push notificationモック送信: {mock_id}")
        
        return NotificationResponse(
            provider=NotificationProvider.PUSH,
            message_id=mock_id,
            status="sent",
            target=message.target,
            sent_at=datetime.now(),
            raw_response={
                "mock": True,
                "title": message.title,
                "body": message.body,
                "priority": message.priority
            }
        )
    
    def get_delivery_status(self, message_id: str) -> NotificationResponse:
        """配信ステータスを取得"""
        try:
            if not self.push_enabled:
                # モックステータス
                return NotificationResponse(
                    provider=NotificationProvider.PUSH,
                    message_id=message_id,
                    status="delivered",
                    target="mock_token",
                    sent_at=datetime.now(),
                    delivered_at=datetime.now()
                )
            
            # 実際のステータス取得は複雑なため、簡易実装
            # 本番環境では各プラットフォームの詳細APIを使用
            return NotificationResponse(
                provider=NotificationProvider.PUSH,
                message_id=message_id,
                status="sent",  # 送信済み（配信確認は実装複雑）
                target="unknown",
                sent_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Push notification status error: {e}")
            return NotificationResponse(
                provider=NotificationProvider.PUSH,
                message_id=message_id,
                status="error",
                target="unknown",
                sent_at=datetime.now(),
                error_message=str(e)
            )
    
    def validate_target(self, target: str) -> bool:
        """デバイストークンを検証"""
        try:
            # 基本的なトークン形式チェック
            if not target or len(target) < 10:
                return False
            
            # iOS APNSトークン（64文字の16進数）
            if len(target) == 64 and all(c in '0123456789abcdefABCDEF' for c in target):
                return True
            
            # Firebase トークン（通常152文字程度）
            if len(target) > 100 and ':' in target:
                return True
            
            # その他の一般的なトークン形式
            if len(target) > 20:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return False
    
    def _is_ios_token(self, token: str) -> bool:
        """iOSトークンかどうか判定"""
        # 簡易判定：64文字の16進数はAPNSトークン
        return len(token) == 64 and all(c in '0123456789abcdefABCDEF' for c in token)
    
    def send_topic_notification(self, topic: str, message: NotificationMessage) -> NotificationResponse:
        """トピック通知を送信（拡張機能）"""
        try:
            if not self.push_enabled or not self.firebase_client:
                return self._send_mock_notification(message)
            
            # Firebase Topic Messaging
            firebase_message = self.firebase_client.Message(
                notification=self.firebase_client.Notification(
                    title=message.title,
                    body=message.body
                ),
                data=message.data or {},
                topic=topic
            )
            
            response = self.firebase_client.send(firebase_message)
            
            return NotificationResponse(
                provider=NotificationProvider.PUSH,
                message_id=response,
                status="sent",
                target=f"topic:{topic}",
                sent_at=datetime.now(),
                raw_response={"firebase_message_id": response, "topic": topic}
            )
            
        except Exception as e:
            logger.error(f"Topic notification error: {e}")
            return NotificationResponse(
                provider=NotificationProvider.PUSH,
                message_id="topic_error",
                status="error",
                target=f"topic:{topic}",
                sent_at=datetime.now(),
                error_message=str(e)
            )
    
    def subscribe_to_topic(self, tokens: List[str], topic: str) -> Dict[str, Any]:
        """デバイスをトピックに登録（拡張機能）"""
        try:
            if not self.push_enabled or not self.firebase_client:
                return {
                    "success": False,
                    "message": "Firebase not available",
                    "mock_subscription": True
                }
            
            response = self.firebase_client.subscribe_to_topic(tokens, topic)
            
            return {
                "success": True,
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "topic": topic
            }
            
        except Exception as e:
            logger.error(f"Topic subscription error: {e}")
            return {
                "success": False,
                "error": str(e)
            }