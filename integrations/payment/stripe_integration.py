"""
Stripe Payment Integration
最終フェーズ: 外部API統合（決済）
本番レベルのStripe決済実装
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from decimal import Decimal
from datetime import datetime
import json
import time
import logging

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent))

from auth.api_auth import APIAuthManager
from scripts.utils import logger
from .payment_manager import PaymentProcessorBase, PaymentRequest, PaymentResponse, PaymentProvider

class StripePaymentProcessor(PaymentProcessorBase):
    """Stripe決済プロセッサ"""
    
    def __init__(self, auth_manager: APIAuthManager):
        """初期化"""
        super().__init__(auth_manager)
        
        # Stripe認証情報取得
        self.stripe_cred = self.auth_manager.get_credential("stripe")
        self.stripe_enabled = False
        self.stripe_client = None
        
        # APIバージョン
        self.api_version = "2024-06-20"
        
        # リトライ設定
        self.max_retries = 3
        self.retry_delay = 2
        
        # 初期化
        self._initialize_stripe()
        
    def _initialize_stripe(self):
        """Stripeクライアントを初期化"""
        try:
            # 外部API接続フラグ確認
            enable_api = os.getenv('ENABLE_EXTERNAL_API', 'false').lower() == 'true'
            
            if not enable_api:
                logger.info("🚧 Stripe API接続は無効（モック動作）")
                self.stripe_enabled = False
                return
            
            if not self.stripe_cred:
                logger.warning("Stripe認証情報が見つかりません")
                self.stripe_enabled = False
                return
            
            # Stripeライブラリインポート
            try:
                import stripe
                
                # APIキー設定
                stripe.api_key = self.stripe_cred.api_key
                stripe.api_version = self.api_version
                
                # 接続テスト
                stripe.Account.retrieve()
                
                self.stripe_client = stripe
                self.stripe_enabled = True
                logger.info("✅ Stripe API接続成功")
                
            except ImportError:
                logger.warning("stripeライブラリがインストールされていません")
                self.stripe_enabled = False
            except Exception as e:
                logger.error(f"Stripe初期化エラー: {e}")
                self.stripe_enabled = False
                
        except Exception as e:
            logger.error(f"Stripe設定エラー: {e}")
            self.stripe_enabled = False
    
    def create_payment(self, request: PaymentRequest) -> PaymentResponse:
        """決済を作成"""
        try:
            logger.info(f"Stripe決済作成開始: {request.amount} {request.currency}")
            
            if not self.stripe_enabled:
                # モック決済
                return self._create_mock_payment(request)
            
            # 本番決済実行
            for attempt in range(self.max_retries):
                try:
                    # 商品価格を作成
                    price_data = {
                        "unit_amount": int(request.amount * 100),  # セント単位
                        "currency": request.currency.lower(),
                        "product_data": {
                            "name": request.description or "BlogAuto Service",
                            "description": request.description
                        }
                    }
                    
                    # チェックアウトセッション作成
                    session = self.stripe_client.checkout.Session.create(
                        payment_method_types=["card"],
                        line_items=[{
                            "price_data": price_data,
                            "quantity": 1
                        }],
                        mode="payment",
                        success_url=request.return_url or "https://example.com/success",
                        cancel_url=request.cancel_url or "https://example.com/cancel",
                        customer_email=request.customer_email,
                        metadata=request.metadata or {},
                        expires_at=int(time.time() + 1800)  # 30分有効
                    )
                    
                    # レスポンス作成
                    return PaymentResponse(
                        provider=PaymentProvider.STRIPE,
                        transaction_id=session.id,
                        status="pending",
                        amount=request.amount,
                        currency=request.currency,
                        created_at=datetime.now(),
                        payment_url=session.url,
                        raw_response={
                            "session_id": session.id,
                            "payment_intent": session.payment_intent,
                            "status": session.status,
                            "url": session.url
                        }
                    )
                    
                except self.stripe_client.error.RateLimitError as e:
                    logger.warning(f"Stripeレート制限 (試行 {attempt + 1}/{self.max_retries}): {e}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (2 ** attempt))
                        continue
                    raise
                    
                except self.stripe_client.error.StripeError as e:
                    logger.error(f"Stripe APIエラー: {e}")
                    return PaymentResponse(
                        provider=PaymentProvider.STRIPE,
                        transaction_id="error",
                        status="error",
                        amount=request.amount,
                        currency=request.currency,
                        created_at=datetime.now(),
                        error_message=str(e)
                    )
                    
        except Exception as e:
            logger.error(f"Stripe決済作成エラー: {e}")
            return PaymentResponse(
                provider=PaymentProvider.STRIPE,
                transaction_id="error",
                status="error",
                amount=request.amount,
                currency=request.currency,
                created_at=datetime.now(),
                error_message=str(e)
            )
    
    def get_payment_status(self, transaction_id: str) -> PaymentResponse:
        """決済ステータスを取得"""
        try:
            if not self.stripe_enabled:
                # モックステータス
                return PaymentResponse(
                    provider=PaymentProvider.STRIPE,
                    transaction_id=transaction_id,
                    status="succeeded",
                    amount=Decimal("1000"),
                    currency="JPY",
                    created_at=datetime.now()
                )
            
            # セッション取得
            session = self.stripe_client.checkout.Session.retrieve(transaction_id)
            
            # ステータスマッピング
            status_map = {
                "complete": "succeeded",
                "expired": "cancelled",
                "open": "pending"
            }
            
            status = status_map.get(session.status, session.status)
            
            # 金額情報取得
            amount = Decimal(str(session.amount_total / 100)) if session.amount_total else Decimal(0)
            
            return PaymentResponse(
                provider=PaymentProvider.STRIPE,
                transaction_id=transaction_id,
                status=status,
                amount=amount,
                currency=session.currency.upper() if session.currency else "JPY",
                created_at=datetime.fromtimestamp(session.created),
                payment_url=session.url if status == "pending" else None,
                raw_response={
                    "session_id": session.id,
                    "payment_intent": session.payment_intent,
                    "status": session.status,
                    "payment_status": session.payment_status
                }
            )
            
        except Exception as e:
            logger.error(f"Stripeステータス取得エラー: {e}")
            return PaymentResponse(
                provider=PaymentProvider.STRIPE,
                transaction_id=transaction_id,
                status="error",
                amount=Decimal(0),
                currency="",
                created_at=datetime.now(),
                error_message=str(e)
            )
    
    def refund_payment(self, transaction_id: str, amount: Optional[Decimal] = None) -> PaymentResponse:
        """返金処理"""
        try:
            if not self.stripe_enabled:
                # モック返金
                return PaymentResponse(
                    provider=PaymentProvider.STRIPE,
                    transaction_id=f"refund_{transaction_id}",
                    status="refunded",
                    amount=amount or Decimal("1000"),
                    currency="JPY",
                    created_at=datetime.now()
                )
            
            # セッション情報取得
            session = self.stripe_client.checkout.Session.retrieve(transaction_id)
            
            if not session.payment_intent:
                raise ValueError("Payment intent not found")
            
            # 返金パラメータ
            refund_params = {
                "payment_intent": session.payment_intent
            }
            
            if amount:
                refund_params["amount"] = int(amount * 100)  # セント単位
            
            # 返金実行
            refund = self.stripe_client.Refund.create(**refund_params)
            
            return PaymentResponse(
                provider=PaymentProvider.STRIPE,
                transaction_id=refund.id,
                status="refunded",
                amount=Decimal(str(refund.amount / 100)),
                currency=refund.currency.upper(),
                created_at=datetime.fromtimestamp(refund.created),
                raw_response={
                    "refund_id": refund.id,
                    "payment_intent": refund.payment_intent,
                    "status": refund.status,
                    "reason": refund.reason
                }
            )
            
        except Exception as e:
            logger.error(f"Stripe返金エラー: {e}")
            return PaymentResponse(
                provider=PaymentProvider.STRIPE,
                transaction_id=transaction_id,
                status="error",
                amount=amount or Decimal(0),
                currency="",
                created_at=datetime.now(),
                error_message=str(e)
            )
    
    def list_transactions(self, limit: int = 10) -> List[PaymentResponse]:
        """取引履歴を取得"""
        try:
            if not self.stripe_enabled:
                # モック履歴
                return [
                    PaymentResponse(
                        provider=PaymentProvider.STRIPE,
                        transaction_id=f"mock_stripe_{i}",
                        status="succeeded",
                        amount=Decimal(str(1000 + i * 100)),
                        currency="JPY",
                        created_at=datetime.now()
                    )
                    for i in range(min(limit, 5))
                ]
            
            # チェックアウトセッション一覧取得
            sessions = self.stripe_client.checkout.Session.list(limit=limit)
            
            transactions = []
            for session in sessions.data:
                amount = Decimal(str(session.amount_total / 100)) if session.amount_total else Decimal(0)
                
                status_map = {
                    "complete": "succeeded",
                    "expired": "cancelled",
                    "open": "pending"
                }
                
                transactions.append(PaymentResponse(
                    provider=PaymentProvider.STRIPE,
                    transaction_id=session.id,
                    status=status_map.get(session.status, session.status),
                    amount=amount,
                    currency=session.currency.upper() if session.currency else "JPY",
                    created_at=datetime.fromtimestamp(session.created),
                    payment_url=session.url if session.status == "open" else None
                ))
            
            return transactions
            
        except Exception as e:
            logger.error(f"Stripe履歴取得エラー: {e}")
            return []
    
    def _create_mock_payment(self, request: PaymentRequest) -> PaymentResponse:
        """モック決済を作成"""
        mock_id = f"mock_stripe_{int(time.time())}"
        
        logger.info(f"Stripeモック決済作成: {mock_id}")
        
        return PaymentResponse(
            provider=PaymentProvider.STRIPE,
            transaction_id=mock_id,
            status="pending",
            amount=request.amount,
            currency=request.currency,
            created_at=datetime.now(),
            payment_url=f"https://checkout.stripe.com/mock/{mock_id}",
            raw_response={
                "mock": True,
                "session_id": mock_id,
                "description": request.description
            }
        )
    
    def create_subscription(self, customer_email: str, price_id: str, 
                          trial_days: int = 0) -> Dict[str, Any]:
        """サブスクリプションを作成（拡張機能）"""
        try:
            if not self.stripe_enabled:
                return {
                    "success": False,
                    "message": "Stripe API disabled",
                    "mock_subscription_id": f"sub_mock_{int(time.time())}"
                }
            
            # 顧客作成または取得
            customers = self.stripe_client.Customer.list(email=customer_email, limit=1)
            
            if customers.data:
                customer = customers.data[0]
            else:
                customer = self.stripe_client.Customer.create(email=customer_email)
            
            # サブスクリプション作成
            subscription_params = {
                "customer": customer.id,
                "items": [{"price": price_id}],
                "payment_behavior": "default_incomplete",
                "expand": ["latest_invoice.payment_intent"]
            }
            
            if trial_days > 0:
                subscription_params["trial_period_days"] = trial_days
            
            subscription = self.stripe_client.Subscription.create(**subscription_params)
            
            return {
                "success": True,
                "subscription_id": subscription.id,
                "customer_id": customer.id,
                "status": subscription.status,
                "current_period_end": subscription.current_period_end,
                "trial_end": subscription.trial_end
            }
            
        except Exception as e:
            logger.error(f"Stripeサブスクリプション作成エラー: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_payment_link(self, price_id: str, quantity: int = 1) -> Dict[str, Any]:
        """決済リンクを作成（拡張機能）"""
        try:
            if not self.stripe_enabled:
                return {
                    "success": False,
                    "message": "Stripe API disabled",
                    "mock_link": "https://buy.stripe.com/mock_link"
                }
            
            # 決済リンク作成
            link = self.stripe_client.PaymentLink.create(
                line_items=[{
                    "price": price_id,
                    "quantity": quantity
                }]
            )
            
            return {
                "success": True,
                "payment_link_id": link.id,
                "url": link.url,
                "active": link.active
            }
            
        except Exception as e:
            logger.error(f"Stripe決済リンク作成エラー: {e}")
            return {
                "success": False,
                "error": str(e)
            }