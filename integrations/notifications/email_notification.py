"""
Email Notification Service
最終100%完成フェーズ: メール通知API統合
SendGrid/AWS SES/SMTP対応実装
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import time
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent))

from auth.api_auth import APIAuthManager
from scripts.utils import logger
from .notification_manager import (
    NotificationServiceBase, NotificationMessage, NotificationResponse, NotificationProvider
)

class EmailNotificationService(NotificationServiceBase):
    """メール通知サービス"""
    
    def __init__(self, auth_manager: APIAuthManager):
        """初期化"""
        super().__init__(auth_manager)
        
        # 認証情報取得
        self.sendgrid_cred = self.auth_manager.get_credential("sendgrid")
        self.ses_cred = self.auth_manager.get_credential("aws_ses")
        self.smtp_cred = self.auth_manager.get_credential("smtp")
        
        self.email_enabled = False
        self.sendgrid_client = None
        self.ses_client = None
        
        # リトライ設定
        self.max_retries = 3
        self.retry_delay = 2
        
        # 初期化
        self._initialize_email_services()
        
    def _initialize_email_services(self):
        """メールサービスを初期化"""
        try:
            # 外部API接続フラグ確認
            enable_api = os.getenv('ENABLE_EXTERNAL_API', 'false').lower() == 'true'
            
            if not enable_api:
                logger.info("🚧 Email notification API接続は無効（モック動作）")
                self.email_enabled = False
                return
            
            # SendGrid初期化
            if self.sendgrid_cred:
                try:
                    import sendgrid
                    from sendgrid.helpers.mail import Mail
                    
                    self.sendgrid_client = sendgrid.SendGridAPIClient(
                        api_key=self.sendgrid_cred.api_key
                    )
                    logger.info("✅ SendGrid email service initialized")
                    
                except ImportError:
                    logger.warning("sendgrid library not installed")
                except Exception as e:
                    logger.error(f"SendGrid initialization error: {e}")
            
            # AWS SES初期化
            if self.ses_cred:
                try:
                    import boto3
                    
                    self.ses_client = boto3.client(
                        'ses',
                        aws_access_key_id=self.ses_cred.api_key,
                        aws_secret_access_key=self.ses_cred.api_secret,
                        region_name=os.getenv('AWS_REGION', 'us-east-1')
                    )
                    logger.info("✅ AWS SES email service initialized")
                    
                except ImportError:
                    logger.warning("boto3 library not installed")
                except Exception as e:
                    logger.error(f"AWS SES initialization error: {e}")
            
            # 有効なメールサービスがあるかチェック
            if self.sendgrid_client or self.ses_client or self.smtp_cred:
                self.email_enabled = True
            else:
                self.email_enabled = False
                logger.warning("No email services available")
                
        except Exception as e:
            logger.error(f"Email notification setup error: {e}")
            self.email_enabled = False
    
    def send_notification(self, message: NotificationMessage) -> NotificationResponse:
        """メール通知を送信"""
        try:
            logger.info(f"Email notification送信開始: {message.title}")
            
            if not self.email_enabled:
                # モック通知
                return self._send_mock_email(message)
            
            # 優先順位でサービス選択
            if self.sendgrid_client:
                return self._send_sendgrid_email(message)
            elif self.ses_client:
                return self._send_ses_email(message)
            elif self.smtp_cred:
                return self._send_smtp_email(message)
            else:
                raise Exception("No email service available")
                
        except Exception as e:
            logger.error(f"Email notification送信エラー: {e}")
            return NotificationResponse(
                provider=NotificationProvider.EMAIL,
                message_id="error",
                status="error",
                target=message.target,
                sent_at=datetime.now(),
                error_message=str(e)
            )
    
    def _send_sendgrid_email(self, message: NotificationMessage) -> NotificationResponse:
        """SendGrid経由でメールを送信"""
        try:
            from sendgrid.helpers.mail import Mail, To
            
            # メール構築
            mail = Mail(
                from_email=os.getenv('SENDGRID_FROM_EMAIL', 'noreply@blogauto.com'),
                to_emails=To(message.target),
                subject=message.title,
                html_content=self._format_email_body(message)
            )
            
            # カスタムデータ追加
            if message.data:
                for key, value in message.data.items():
                    mail.custom_arg = {key: str(value)}
            
            # 送信実行
            response = self.sendgrid_client.send(mail)
            
            return NotificationResponse(
                provider=NotificationProvider.EMAIL,
                message_id=response.headers.get('X-Message-Id', 'sendgrid_success'),
                status="sent" if response.status_code == 202 else "error",
                target=message.target,
                sent_at=datetime.now(),
                raw_response={
                    "status_code": response.status_code,
                    "body": response.body,
                    "headers": dict(response.headers)
                }
            )
            
        except Exception as e:
            logger.error(f"SendGrid email error: {e}")
            return NotificationResponse(
                provider=NotificationProvider.EMAIL,
                message_id="sendgrid_error",
                status="error",
                target=message.target,
                sent_at=datetime.now(),
                error_message=str(e)
            )
    
    def _send_ses_email(self, message: NotificationMessage) -> NotificationResponse:
        """AWS SES経由でメールを送信"""
        try:
            # メール送信
            response = self.ses_client.send_email(
                Source=os.getenv('AWS_SES_FROM_EMAIL', 'noreply@blogauto.com'),
                Destination={
                    'ToAddresses': [message.target]
                },
                Message={
                    'Subject': {
                        'Data': message.title,
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Html': {
                            'Data': self._format_email_body(message),
                            'Charset': 'UTF-8'
                        },
                        'Text': {
                            'Data': message.body,
                            'Charset': 'UTF-8'
                        }
                    }
                }
            )
            
            return NotificationResponse(
                provider=NotificationProvider.EMAIL,
                message_id=response['MessageId'],
                status="sent",
                target=message.target,
                sent_at=datetime.now(),
                raw_response=response
            )
            
        except Exception as e:
            logger.error(f"AWS SES email error: {e}")
            return NotificationResponse(
                provider=NotificationProvider.EMAIL,
                message_id="ses_error",
                status="error",
                target=message.target,
                sent_at=datetime.now(),
                error_message=str(e)
            )
    
    def _send_smtp_email(self, message: NotificationMessage) -> NotificationResponse:
        """SMTP経由でメールを送信"""
        try:
            # SMTP設定取得
            smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_user = self.smtp_cred.api_key
            smtp_pass = self.smtp_cred.api_secret
            
            # メール構築
            msg = MIMEMultipart('alternative')
            msg['Subject'] = message.title
            msg['From'] = smtp_user
            msg['To'] = message.target
            
            # HTMLとテキスト版の本文
            text_part = MIMEText(message.body, 'plain', 'utf-8')
            html_part = MIMEText(self._format_email_body(message), 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # SMTP送信
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                text = msg.as_string()
                server.sendmail(smtp_user, message.target, text)
            
            message_id = f"smtp_{int(time.time())}"
            
            return NotificationResponse(
                provider=NotificationProvider.EMAIL,
                message_id=message_id,
                status="sent",
                target=message.target,
                sent_at=datetime.now(),
                raw_response={
                    "smtp_host": smtp_host,
                    "smtp_port": smtp_port
                }
            )
            
        except Exception as e:
            logger.error(f"SMTP email error: {e}")
            return NotificationResponse(
                provider=NotificationProvider.EMAIL,
                message_id="smtp_error",
                status="error",
                target=message.target,
                sent_at=datetime.now(),
                error_message=str(e)
            )
    
    def _send_mock_email(self, message: NotificationMessage) -> NotificationResponse:
        """モックメールを送信"""
        mock_id = f"mock_email_{int(time.time())}"
        
        logger.info(f"Email notificationモック送信: {mock_id}")
        
        return NotificationResponse(
            provider=NotificationProvider.EMAIL,
            message_id=mock_id,
            status="sent",
            target=message.target,
            sent_at=datetime.now(),
            raw_response={
                "mock": True,
                "subject": message.title,
                "body": message.body,
                "priority": message.priority
            }
        )
    
    def _format_email_body(self, message: NotificationMessage) -> str:
        """メール本文をHTML形式にフォーマット"""
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{message.title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .content {{ padding: 20px 0; }}
        .footer {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 20px; font-size: 12px; color: #666; }}
        .priority-high {{ border-left: 4px solid #dc3545; }}
        .priority-normal {{ border-left: 4px solid #007bff; }}
        .priority-low {{ border-left: 4px solid #28a745; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header priority-{message.priority}">
            <h1>{message.title}</h1>
        </div>
        <div class="content">
            {message.body.replace(chr(10), '<br>')}
        </div>
        <div class="footer">
            <p>このメールはBlogAuto システムから自動送信されました。</p>
            <p>送信日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
        return html_body
    
    def get_delivery_status(self, message_id: str) -> NotificationResponse:
        """配信ステータスを取得"""
        try:
            if not self.email_enabled:
                # モックステータス
                return NotificationResponse(
                    provider=NotificationProvider.EMAIL,
                    message_id=message_id,
                    status="delivered",
                    target="mock@example.com",
                    sent_at=datetime.now(),
                    delivered_at=datetime.now()
                )
            
            # 実際のステータス取得は各サービスのWebhook/API経由
            # ここでは簡易実装
            return NotificationResponse(
                provider=NotificationProvider.EMAIL,
                message_id=message_id,
                status="sent",  # 送信済み（詳細ステータスは実装複雑）
                target="unknown",
                sent_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Email status error: {e}")
            return NotificationResponse(
                provider=NotificationProvider.EMAIL,
                message_id=message_id,
                status="error",
                target="unknown",
                sent_at=datetime.now(),
                error_message=str(e)
            )
    
    def validate_target(self, target: str) -> bool:
        """メールアドレスを検証"""
        try:
            import re
            
            # 基本的なメールアドレス形式チェック
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return bool(re.match(email_pattern, target))
            
        except Exception as e:
            logger.error(f"Email validation error: {e}")
            return False
    
    def send_template_email(self, template_id: str, target: str, 
                          template_data: Dict[str, Any]) -> NotificationResponse:
        """テンプレートメールを送信（拡張機能）"""
        try:
            if not self.email_enabled or not self.sendgrid_client:
                # モック送信
                return NotificationResponse(
                    provider=NotificationProvider.EMAIL,
                    message_id=f"mock_template_{int(time.time())}",
                    status="sent",
                    target=target,
                    sent_at=datetime.now(),
                    raw_response={"mock": True, "template_id": template_id}
                )
            
            from sendgrid.helpers.mail import Mail
            
            # テンプレートメール構築
            mail = Mail(
                from_email=os.getenv('SENDGRID_FROM_EMAIL', 'noreply@blogauto.com'),
                to_emails=target
            )
            
            mail.template_id = template_id
            mail.dynamic_template_data = template_data
            
            # 送信実行
            response = self.sendgrid_client.send(mail)
            
            return NotificationResponse(
                provider=NotificationProvider.EMAIL,
                message_id=response.headers.get('X-Message-Id', 'template_success'),
                status="sent" if response.status_code == 202 else "error",
                target=target,
                sent_at=datetime.now(),
                raw_response={
                    "template_id": template_id,
                    "status_code": response.status_code
                }
            )
            
        except Exception as e:
            logger.error(f"Template email error: {e}")
            return NotificationResponse(
                provider=NotificationProvider.EMAIL,
                message_id="template_error",
                status="error",
                target=target,
                sent_at=datetime.now(),
                error_message=str(e)
            )
    
    def send_bulk_email(self, targets: List[str], 
                       message: NotificationMessage) -> List[NotificationResponse]:
        """一括メール送信（拡張機能）"""
        responses = []
        
        for target in targets:
            # 個別メッセージ作成
            individual_message = NotificationMessage(
                title=message.title,
                body=message.body,
                target=target,
                provider=NotificationProvider.EMAIL,
                data=message.data,
                priority=message.priority
            )
            
            response = self.send_notification(individual_message)
            responses.append(response)
            
            # レート制限考慮
            if len(responses) % 10 == 0:
                time.sleep(1)  # 10件ごとに1秒待機
        
        return responses