"""
Notification Manager - 統合通知管理システム
最終100%完成フェーズ: プッシュ通知API統合
リアルタイム通知システム本番レベル実装
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import json
import logging
from abc import ABC, abstractmethod

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent))

from auth.api_auth import APIAuthManager
from scripts.utils import logger, save_json_safely, load_json_safely

class NotificationProvider(Enum):
    """通知プロバイダ列挙型"""
    PUSH = "push"
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    SLACK = "slack"
    DISCORD = "discord"

@dataclass
class NotificationMessage:
    """通知メッセージデータクラス"""
    title: str
    body: str
    target: str  # デバイストークン、メールアドレス、電話番号等
    provider: NotificationProvider
    data: Optional[Dict[str, Any]] = None
    priority: str = "normal"  # low, normal, high
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
@dataclass 
class NotificationResponse:
    """通知レスポンスデータクラス"""
    provider: NotificationProvider
    message_id: str
    status: str
    target: str
    sent_at: datetime
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    raw_response: Optional[Dict[str, Any]] = None

class NotificationServiceBase(ABC):
    """通知サービス基底クラス"""
    
    def __init__(self, auth_manager: APIAuthManager):
        self.auth_manager = auth_manager
        self.logger = logger
        
    @abstractmethod
    def send_notification(self, message: NotificationMessage) -> NotificationResponse:
        """通知を送信"""
        pass
    
    @abstractmethod
    def get_delivery_status(self, message_id: str) -> NotificationResponse:
        """配信ステータスを取得"""
        pass
    
    @abstractmethod
    def validate_target(self, target: str) -> bool:
        """送信先を検証"""
        pass

class NotificationManager:
    """統合通知マネージャー"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """初期化"""
        self.config_dir = config_dir or Path.home() / ".blogauto"
        self.config_dir.mkdir(exist_ok=True)
        
        # 認証マネージャー初期化
        self.auth_manager = APIAuthManager(self.config_dir)
        
        # 通知履歴ディレクトリ
        self.notifications_dir = self.config_dir / "notifications"
        self.notifications_dir.mkdir(exist_ok=True)
        
        # 送信待ちキュー
        self.queue_file = self.notifications_dir / "queue.json"
        
        # プロバイダーインスタンス
        self.services: Dict[NotificationProvider, NotificationServiceBase] = {}
        
        # レート制限設定
        self.rate_limits = {
            NotificationProvider.PUSH: {"calls": 0, "max_calls": 1000, "reset_time": 3600},
            NotificationProvider.EMAIL: {"calls": 0, "max_calls": 100, "reset_time": 3600},
            NotificationProvider.SMS: {"calls": 0, "max_calls": 50, "reset_time": 3600}
        }
        
        # 統計情報
        self.stats = {
            "total_sent": 0,
            "total_delivered": 0,
            "total_failed": 0,
            "daily_stats": {}
        }
        
        logger.info("NotificationManager initialized")
    
    def initialize_service(self, provider: NotificationProvider) -> bool:
        """通知サービスを初期化"""
        try:
            if provider == NotificationProvider.PUSH:
                from .push_notification import PushNotificationService
                self.services[provider] = PushNotificationService(self.auth_manager)
                logger.info("Push notification service initialized")
                return True
                
            elif provider == NotificationProvider.EMAIL:
                from .email_notification import EmailNotificationService
                self.services[provider] = EmailNotificationService(self.auth_manager)
                logger.info("Email notification service initialized")
                return True
                
            else:
                logger.warning(f"Provider {provider.value} not yet implemented")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize {provider.value}: {e}")
            return False
    
    def send_notification(self, message: NotificationMessage) -> NotificationResponse:
        """通知を送信"""
        try:
            # レート制限チェック
            if not self._check_rate_limit(message.provider):
                return NotificationResponse(
                    provider=message.provider,
                    message_id="rate_limit_exceeded",
                    status="error",
                    target=message.target,
                    sent_at=datetime.now(),
                    error_message="Rate limit exceeded"
                )
            
            # サービス初期化
            if message.provider not in self.services:
                if not self.initialize_service(message.provider):
                    return NotificationResponse(
                        provider=message.provider,
                        message_id="init_failed",
                        status="error",
                        target=message.target,
                        sent_at=datetime.now(),
                        error_message="Service initialization failed"
                    )
            
            # 送信実行
            service = self.services[message.provider]
            response = service.send_notification(message)
            
            # 履歴保存
            self._save_notification(response)
            
            # レート制限カウンタ更新
            self._increment_rate_limit(message.provider)
            
            # 統計更新
            self._update_stats(response)
            
            return response
            
        except Exception as e:
            logger.error(f"Notification send error: {e}")
            return NotificationResponse(
                provider=message.provider,
                message_id="error",
                status="error",
                target=message.target,
                sent_at=datetime.now(),
                error_message=str(e)
            )
    
    def send_batch_notifications(self, messages: List[NotificationMessage]) -> List[NotificationResponse]:
        """バッチ通知送信"""
        responses = []
        
        for message in messages:
            response = self.send_notification(message)
            responses.append(response)
            
            # エラー発生時のリトライ処理
            if response.status == "error" and response.retry_count < 3:
                logger.info(f"Retrying notification {response.message_id}")
                import time
                time.sleep(2 ** response.retry_count)
                retry_response = self.send_notification(message)
                retry_response.retry_count = response.retry_count + 1
                responses[-1] = retry_response
        
        return responses
    
    def schedule_notification(self, message: NotificationMessage) -> bool:
        """通知をスケジュール"""
        try:
            # 送信待ちキューに追加
            queue_data = load_json_safely(str(self.queue_file)) or []
            
            queue_item = {
                "message": {
                    "title": message.title,
                    "body": message.body,
                    "target": message.target,
                    "provider": message.provider.value,
                    "data": message.data,
                    "priority": message.priority
                },
                "scheduled_at": message.scheduled_at.isoformat() if message.scheduled_at else None,
                "expires_at": message.expires_at.isoformat() if message.expires_at else None,
                "created_at": datetime.now().isoformat()
            }
            
            queue_data.append(queue_item)
            save_json_safely(queue_data, str(self.queue_file))
            
            logger.info(f"Notification scheduled: {message.title}")
            return True
            
        except Exception as e:
            logger.error(f"Schedule notification error: {e}")
            return False
    
    def process_scheduled_notifications(self) -> int:
        """スケジュール済み通知を処理"""
        try:
            queue_data = load_json_safely(str(self.queue_file)) or []
            now = datetime.now()
            processed = 0
            remaining_queue = []
            
            for item in queue_data:
                scheduled_at = datetime.fromisoformat(item["scheduled_at"]) if item.get("scheduled_at") else None
                expires_at = datetime.fromisoformat(item["expires_at"]) if item.get("expires_at") else None
                
                # 期限切れチェック
                if expires_at and now > expires_at:
                    logger.info(f"Notification expired: {item['message']['title']}")
                    continue
                
                # 送信時刻チェック
                if not scheduled_at or now >= scheduled_at:
                    # 通知送信
                    message = NotificationMessage(
                        title=item["message"]["title"],
                        body=item["message"]["body"],
                        target=item["message"]["target"],
                        provider=NotificationProvider(item["message"]["provider"]),
                        data=item["message"].get("data"),
                        priority=item["message"].get("priority", "normal")
                    )
                    
                    response = self.send_notification(message)
                    if response.status != "error":
                        processed += 1
                        logger.info(f"Scheduled notification sent: {message.title}")
                    else:
                        # エラー時は再度キューに追加
                        remaining_queue.append(item)
                else:
                    # まだ送信時刻ではない
                    remaining_queue.append(item)
            
            # キューを更新
            save_json_safely(remaining_queue, str(self.queue_file))
            
            return processed
            
        except Exception as e:
            logger.error(f"Process scheduled notifications error: {e}")
            return 0
    
    def get_notification_history(self, limit: int = 50) -> List[NotificationResponse]:
        """通知履歴を取得"""
        history = []
        
        notification_files = sorted(
            self.notifications_dir.glob("*.json"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )[:limit]
        
        for file_path in notification_files:
            if file_path.name == "queue.json":
                continue
                
            try:
                data = load_json_safely(str(file_path))
                if data:
                    response = NotificationResponse(
                        provider=NotificationProvider(data["provider"]),
                        message_id=data["message_id"],
                        status=data["status"],
                        target=data["target"],
                        sent_at=datetime.fromisoformat(data["sent_at"]),
                        delivered_at=datetime.fromisoformat(data["delivered_at"]) if data.get("delivered_at") else None,
                        error_message=data.get("error_message"),
                        retry_count=data.get("retry_count", 0),
                        raw_response=data.get("raw_response")
                    )
                    history.append(response)
            except Exception as e:
                logger.error(f"Failed to load notification {file_path}: {e}")
        
        return history
    
    def get_notification_stats(self) -> Dict[str, Any]:
        """通知統計を取得"""
        try:
            history = self.get_notification_history(limit=1000)
            
            stats = {
                "total_notifications": len(history),
                "providers": {},
                "status_breakdown": {},
                "daily_stats": {},
                "success_rate": 0.0
            }
            
            today = datetime.now().date()
            success_count = 0
            
            for notification in history:
                # プロバイダー別集計
                provider_name = notification.provider.value
                if provider_name not in stats["providers"]:
                    stats["providers"][provider_name] = 0
                stats["providers"][provider_name] += 1
                
                # ステータス別集計
                if notification.status not in stats["status_breakdown"]:
                    stats["status_breakdown"][notification.status] = 0
                stats["status_breakdown"][notification.status] += 1
                
                # 成功率計算
                if notification.status in ["delivered", "sent"]:
                    success_count += 1
                
                # 日別集計
                date_key = notification.sent_at.date().isoformat()
                if date_key not in stats["daily_stats"]:
                    stats["daily_stats"][date_key] = {"sent": 0, "delivered": 0, "failed": 0}
                
                if notification.status == "delivered":
                    stats["daily_stats"][date_key]["delivered"] += 1
                elif notification.status == "error":
                    stats["daily_stats"][date_key]["failed"] += 1
                else:
                    stats["daily_stats"][date_key]["sent"] += 1
            
            # 成功率計算
            if len(history) > 0:
                stats["success_rate"] = (success_count / len(history)) * 100
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to generate stats: {e}")
            return {"error": str(e)}
    
    def _check_rate_limit(self, provider: NotificationProvider) -> bool:
        """レート制限をチェック"""
        if provider not in self.rate_limits:
            return True
        
        limit_info = self.rate_limits[provider]
        return limit_info["calls"] < limit_info["max_calls"]
    
    def _increment_rate_limit(self, provider: NotificationProvider):
        """レート制限カウンタを増加"""
        if provider in self.rate_limits:
            self.rate_limits[provider]["calls"] += 1
    
    def _save_notification(self, response: NotificationResponse):
        """通知履歴を保存"""
        try:
            timestamp = response.sent_at.strftime("%Y%m%d_%H%M%S")
            filename = f"{response.provider.value}_{response.message_id}_{timestamp}.json"
            file_path = self.notifications_dir / filename
            
            notification_data = {
                "provider": response.provider.value,
                "message_id": response.message_id,
                "status": response.status,
                "target": response.target,
                "sent_at": response.sent_at.isoformat(),
                "delivered_at": response.delivered_at.isoformat() if response.delivered_at else None,
                "error_message": response.error_message,
                "retry_count": response.retry_count,
                "raw_response": response.raw_response
            }
            
            save_json_safely(notification_data, str(file_path))
            logger.debug(f"Notification saved: {filename}")
            
        except Exception as e:
            logger.error(f"Failed to save notification: {e}")
    
    def _update_stats(self, response: NotificationResponse):
        """統計情報を更新"""
        self.stats["total_sent"] += 1
        
        if response.status == "delivered":
            self.stats["total_delivered"] += 1
        elif response.status == "error":
            self.stats["total_failed"] += 1
        
        # 日別統計
        today = datetime.now().date().isoformat()
        if today not in self.stats["daily_stats"]:
            self.stats["daily_stats"][today] = {"sent": 0, "delivered": 0, "failed": 0}
        
        self.stats["daily_stats"][today]["sent"] += 1

# グローバルインスタンス作成関数
def get_notification_manager() -> NotificationManager:
    """NotificationManagerのシングルトンインスタンスを取得"""
    if not hasattr(get_notification_manager, "_instance"):
        get_notification_manager._instance = NotificationManager()
    return get_notification_manager._instance