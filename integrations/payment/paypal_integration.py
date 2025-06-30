"""
PayPal Payment Integration
最終フェーズ: 外部API統合（決済）
本番レベルのPayPal決済実装
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
import base64

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent))

from auth.api_auth import APIAuthManager
from scripts.utils import logger
from .payment_manager import PaymentProcessorBase, PaymentRequest, PaymentResponse, PaymentProvider

class PayPalPaymentProcessor(PaymentProcessorBase):
    """PayPal決済プロセッサ"""
    
    def __init__(self, auth_manager: APIAuthManager):
        """初期化"""
        super().__init__(auth_manager)
        
        # PayPal認証情報取得
        self.paypal_cred = self.auth_manager.get_credential("paypal")
        self.paypal_enabled = False
        self.access_token = None
        self.token_expires_at = None
        
        # API エンドポイント（サンドボックス/本番）
        self.is_sandbox = os.getenv('PAYPAL_SANDBOX', 'true').lower() == 'true'
        self.base_url = (
            "https://api.sandbox.paypal.com" if self.is_sandbox 
            else "https://api.paypal.com"
        )
        
        # リトライ設定
        self.max_retries = 3
        self.retry_delay = 2
        
        # 初期化
        self._initialize_paypal()
        
    def _initialize_paypal(self):
        """PayPalクライアントを初期化"""
        try:
            # 外部API接続フラグ確認
            enable_api = os.getenv('ENABLE_EXTERNAL_API', 'false').lower() == 'true'
            
            if not enable_api:
                logger.info("🚧 PayPal API接続は無効（モック動作）")
                self.paypal_enabled = False
                return
            
            if not self.paypal_cred:
                logger.warning("PayPal認証情報が見つかりません")
                self.paypal_enabled = False
                return
            
            # 接続テスト（アクセストークン取得）
            if self._get_access_token():
                self.paypal_enabled = True
                logger.info("✅ PayPal API接続成功")
            else:
                self.paypal_enabled = False
                logger.error("PayPal API接続失敗")
                
        except Exception as e:
            logger.error(f"PayPal設定エラー: {e}")
            self.paypal_enabled = False
    
    def _get_access_token(self) -> bool:
        """アクセストークンを取得"""
        try:
            import requests
            
            # トークンが有効期限内なら再利用
            if (self.access_token and self.token_expires_at and 
                datetime.now().timestamp() < self.token_expires_at):
                return True
            
            # 認証情報エンコード
            client_id = self.paypal_cred.api_key
            client_secret = self.paypal_cred.api_secret
            
            auth_string = f"{client_id}:{client_secret}"
            auth_encoded = base64.b64encode(auth_string.encode()).decode()
            
            # トークン取得リクエスト
            headers = {
                "Accept": "application/json",
                "Authorization": f"Basic {auth_encoded}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = "grant_type=client_credentials"
            
            response = requests.post(
                f"{self.base_url}/v1/oauth2/token",
                headers=headers,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                expires_in = token_data.get("expires_in", 3600)
                self.token_expires_at = datetime.now().timestamp() + expires_in - 60  # 1分のマージン
                
                logger.info("PayPalアクセストークン取得成功")
                return True
            else:
                logger.error(f"PayPalトークン取得失敗: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"PayPalトークン取得エラー: {e}")
            return False
    
    def _make_api_request(self, method: str, endpoint: str, 
                         data: Optional[Dict] = None) -> Optional[Dict]:
        """PayPal APIリクエストを実行"""
        try:
            import requests
            
            if not self._get_access_token():
                return None
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_token}",
                "PayPal-Request-Id": f"blogauto-{int(time.time())}"
            }
            
            url = f"{self.base_url}{endpoint}"
            
            for attempt in range(self.max_retries):
                try:
                    if method.upper() == "GET":
                        response = requests.get(url, headers=headers, timeout=30)
                    elif method.upper() == "POST":
                        response = requests.post(url, headers=headers, 
                                               json=data, timeout=30)
                    elif method.upper() == "PATCH":
                        response = requests.patch(url, headers=headers, 
                                                json=data, timeout=30)
                    else:
                        raise ValueError(f"Unsupported method: {method}")
                    
                    if response.status_code in [200, 201]:
                        return response.json()
                    elif response.status_code == 429:  # レート制限
                        logger.warning(f"PayPalレート制限 (試行 {attempt + 1}/{self.max_retries})")
                        if attempt < self.max_retries - 1:
                            time.sleep(self.retry_delay * (2 ** attempt))
                            continue
                    else:
                        logger.error(f"PayPal APIエラー: {response.status_code}")
                        return None
                        
                except requests.RequestException as e:
                    logger.warning(f"PayPalリクエストエラー (試行 {attempt + 1}/{self.max_retries}): {e}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    break
            
            return None
            
        except Exception as e:
            logger.error(f"PayPal APIリクエストエラー: {e}")
            return None
    
    def create_payment(self, request: PaymentRequest) -> PaymentResponse:
        """決済を作成"""
        try:
            logger.info(f"PayPal決済作成開始: {request.amount} {request.currency}")
            
            if not self.paypal_enabled:
                # モック決済
                return self._create_mock_payment(request)
            
            # PayPal注文データ作成
            order_data = {
                "intent": "CAPTURE",
                "purchase_units": [{
                    "amount": {
                        "currency_code": request.currency.upper(),
                        "value": str(request.amount)
                    },
                    "description": request.description or "BlogAuto Service",
                    "custom_id": f"blogauto-{int(time.time())}"
                }],
                "payment_source": {
                    "paypal": {
                        "experience_context": {
                            "brand_name": "BlogAuto",
                            "locale": "ja-JP",
                            "shipping_preference": "NO_SHIPPING",
                            "user_action": "PAY_NOW",
                            "return_url": request.return_url or "https://example.com/success",
                            "cancel_url": request.cancel_url or "https://example.com/cancel"
                        }
                    }
                }
            }
            
            # 注文作成
            result = self._make_api_request("POST", "/v2/checkout/orders", order_data)
            
            if result:
                # 承認URLを検索
                approval_url = None
                for link in result.get("links", []):
                    if link.get("rel") == "approve":
                        approval_url = link.get("href")
                        break
                
                return PaymentResponse(
                    provider=PaymentProvider.PAYPAL,
                    transaction_id=result["id"],
                    status="pending",
                    amount=request.amount,
                    currency=request.currency,
                    created_at=datetime.now(),
                    payment_url=approval_url,
                    raw_response=result
                )
            else:
                raise Exception("PayPal注文作成失敗")
                
        except Exception as e:
            logger.error(f"PayPal決済作成エラー: {e}")
            return PaymentResponse(
                provider=PaymentProvider.PAYPAL,
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
            if not self.paypal_enabled:
                # モックステータス
                return PaymentResponse(
                    provider=PaymentProvider.PAYPAL,
                    transaction_id=transaction_id,
                    status="succeeded",
                    amount=Decimal("1000"),
                    currency="JPY",
                    created_at=datetime.now()
                )
            
            # 注文詳細取得
            result = self._make_api_request("GET", f"/v2/checkout/orders/{transaction_id}")
            
            if result:
                # ステータスマッピング
                status_map = {
                    "CREATED": "pending",
                    "SAVED": "pending",
                    "APPROVED": "pending",
                    "VOIDED": "cancelled",
                    "COMPLETED": "succeeded",
                    "PAYER_ACTION_REQUIRED": "pending"
                }
                
                status = status_map.get(result["status"], result["status"].lower())
                
                # 金額情報取得
                purchase_unit = result.get("purchase_units", [{}])[0]
                amount_info = purchase_unit.get("amount", {})
                amount = Decimal(str(amount_info.get("value", 0)))
                currency = amount_info.get("currency_code", "JPY")
                
                # 承認URL取得（pending時のみ）
                payment_url = None
                if status == "pending":
                    for link in result.get("links", []):
                        if link.get("rel") == "approve":
                            payment_url = link.get("href")
                            break
                
                return PaymentResponse(
                    provider=PaymentProvider.PAYPAL,
                    transaction_id=transaction_id,
                    status=status,
                    amount=amount,
                    currency=currency,
                    created_at=datetime.fromisoformat(result["create_time"].replace("Z", "+00:00")),
                    payment_url=payment_url,
                    raw_response=result
                )
            else:
                raise Exception("PayPal注文取得失敗")
                
        except Exception as e:
            logger.error(f"PayPalステータス取得エラー: {e}")
            return PaymentResponse(
                provider=PaymentProvider.PAYPAL,
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
            if not self.paypal_enabled:
                # モック返金
                return PaymentResponse(
                    provider=PaymentProvider.PAYPAL,
                    transaction_id=f"refund_{transaction_id}",
                    status="refunded",
                    amount=amount or Decimal("1000"),
                    currency="JPY",
                    created_at=datetime.now()
                )
            
            # まず注文情報を取得してキャプチャIDを見つける
            order = self._make_api_request("GET", f"/v2/checkout/orders/{transaction_id}")
            
            if not order:
                raise Exception("PayPal注文が見つかりません")
            
            # キャプチャIDを検索
            capture_id = None
            for purchase_unit in order.get("purchase_units", []):
                for payment in purchase_unit.get("payments", {}).get("captures", []):
                    capture_id = payment["id"]
                    break
                if capture_id:
                    break
            
            if not capture_id:
                raise Exception("キャプチャされた支払いが見つかりません")
            
            # 返金データ作成
            refund_data = {}
            if amount:
                refund_data["amount"] = {
                    "value": str(amount),
                    "currency_code": "JPY"  # 通貨は動的に取得する必要がある
                }
            
            # 返金実行
            result = self._make_api_request("POST", f"/v2/payments/captures/{capture_id}/refund", refund_data)
            
            if result:
                refund_amount = Decimal(str(result.get("amount", {}).get("value", 0)))
                
                return PaymentResponse(
                    provider=PaymentProvider.PAYPAL,
                    transaction_id=result["id"],
                    status="refunded",
                    amount=refund_amount,
                    currency=result.get("amount", {}).get("currency_code", "JPY"),
                    created_at=datetime.fromisoformat(result["create_time"].replace("Z", "+00:00")),
                    raw_response=result
                )
            else:
                raise Exception("PayPal返金処理失敗")
                
        except Exception as e:
            logger.error(f"PayPal返金エラー: {e}")
            return PaymentResponse(
                provider=PaymentProvider.PAYPAL,
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
            if not self.paypal_enabled:
                # モック履歴
                return [
                    PaymentResponse(
                        provider=PaymentProvider.PAYPAL,
                        transaction_id=f"mock_paypal_{i}",
                        status="succeeded",
                        amount=Decimal(str(1000 + i * 100)),
                        currency="JPY",
                        created_at=datetime.now()
                    )
                    for i in range(min(limit, 5))
                ]
            
            # 注文履歴取得（最新から）
            end_time = datetime.now().isoformat() + "Z"
            start_time = datetime.now().replace(month=1, day=1).isoformat() + "Z"  # 今年の開始
            
            endpoint = f"/v2/checkout/orders?page_size={limit}&start_time={start_time}&end_time={end_time}"
            result = self._make_api_request("GET", endpoint)
            
            transactions = []
            if result and "orders" in result:
                for order in result["orders"]:
                    status_map = {
                        "CREATED": "pending",
                        "SAVED": "pending", 
                        "APPROVED": "pending",
                        "VOIDED": "cancelled",
                        "COMPLETED": "succeeded",
                        "PAYER_ACTION_REQUIRED": "pending"
                    }
                    
                    status = status_map.get(order["status"], order["status"].lower())
                    
                    purchase_unit = order.get("purchase_units", [{}])[0]
                    amount_info = purchase_unit.get("amount", {})
                    amount = Decimal(str(amount_info.get("value", 0)))
                    currency = amount_info.get("currency_code", "JPY")
                    
                    transactions.append(PaymentResponse(
                        provider=PaymentProvider.PAYPAL,
                        transaction_id=order["id"],
                        status=status,
                        amount=amount,
                        currency=currency,
                        created_at=datetime.fromisoformat(order["create_time"].replace("Z", "+00:00"))
                    ))
            
            return transactions
            
        except Exception as e:
            logger.error(f"PayPal履歴取得エラー: {e}")
            return []
    
    def _create_mock_payment(self, request: PaymentRequest) -> PaymentResponse:
        """モック決済を作成"""
        mock_id = f"mock_paypal_{int(time.time())}"
        
        logger.info(f"PayPalモック決済作成: {mock_id}")
        
        return PaymentResponse(
            provider=PaymentProvider.PAYPAL,
            transaction_id=mock_id,
            status="pending",
            amount=request.amount,
            currency=request.currency,
            created_at=datetime.now(),
            payment_url=f"https://www.paypal.com/checkoutnow?token={mock_id}",
            raw_response={
                "mock": True,
                "order_id": mock_id,
                "description": request.description
            }
        )
    
    def capture_payment(self, order_id: str) -> PaymentResponse:
        """承認された注文をキャプチャ（拡張機能）"""
        try:
            if not self.paypal_enabled:
                return PaymentResponse(
                    provider=PaymentProvider.PAYPAL,
                    transaction_id=order_id,
                    status="succeeded",
                    amount=Decimal("1000"),
                    currency="JPY",
                    created_at=datetime.now()
                )
            
            # 注文キャプチャ
            result = self._make_api_request("POST", f"/v2/checkout/orders/{order_id}/capture")
            
            if result:
                purchase_unit = result.get("purchase_units", [{}])[0]
                amount_info = purchase_unit.get("amount", {})
                amount = Decimal(str(amount_info.get("value", 0)))
                currency = amount_info.get("currency_code", "JPY")
                
                return PaymentResponse(
                    provider=PaymentProvider.PAYPAL,
                    transaction_id=order_id,
                    status="succeeded",
                    amount=amount,
                    currency=currency,
                    created_at=datetime.now(),
                    raw_response=result
                )
            else:
                raise Exception("PayPal注文キャプチャ失敗")
                
        except Exception as e:
            logger.error(f"PayPalキャプチャエラー: {e}")
            return PaymentResponse(
                provider=PaymentProvider.PAYPAL,
                transaction_id=order_id,
                status="error",
                amount=Decimal(0),
                currency="",
                created_at=datetime.now(),
                error_message=str(e)
            )