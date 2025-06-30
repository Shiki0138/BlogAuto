"""
Payment Manager - 統合決済管理システム
最終フェーズ: 外部API統合
複数の決済プロバイダを統一インターフェースで管理
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import json
import logging
from decimal import Decimal
from abc import ABC, abstractmethod

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent))

from auth.api_auth import APIAuthManager, APICredential
from scripts.utils import logger, save_json_safely, load_json_safely

class PaymentProvider(Enum):
    """決済プロバイダ列挙型"""
    STRIPE = "stripe"
    PAYPAL = "paypal"
    NONE = "none"  # テスト用

@dataclass
class PaymentRequest:
    """決済リクエストデータクラス"""
    amount: Decimal
    currency: str
    description: str
    customer_email: str
    customer_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    items: Optional[List[Dict[str, Any]]] = None
    return_url: Optional[str] = None
    cancel_url: Optional[str] = None

@dataclass
class PaymentResponse:
    """決済レスポンスデータクラス"""
    provider: PaymentProvider
    transaction_id: str
    status: str
    amount: Decimal
    currency: str
    created_at: datetime
    payment_url: Optional[str] = None
    error_message: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

class PaymentProcessorBase(ABC):
    """決済プロセッサ基底クラス"""
    
    def __init__(self, auth_manager: APIAuthManager):
        self.auth_manager = auth_manager
        self.logger = logger
        
    @abstractmethod
    def create_payment(self, request: PaymentRequest) -> PaymentResponse:
        """決済を作成"""
        pass
    
    @abstractmethod
    def get_payment_status(self, transaction_id: str) -> PaymentResponse:
        """決済ステータスを取得"""
        pass
    
    @abstractmethod
    def refund_payment(self, transaction_id: str, amount: Optional[Decimal] = None) -> PaymentResponse:
        """返金処理"""
        pass
    
    @abstractmethod
    def list_transactions(self, limit: int = 10) -> List[PaymentResponse]:
        """取引履歴を取得"""
        pass

class PaymentManager:
    """統合決済マネージャー"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """初期化"""
        self.config_dir = config_dir or Path.home() / ".blogauto"
        self.config_dir.mkdir(exist_ok=True)
        
        # 認証マネージャー初期化
        self.auth_manager = APIAuthManager(self.config_dir)
        
        # 決済履歴ディレクトリ
        self.transactions_dir = self.config_dir / "transactions"
        self.transactions_dir.mkdir(exist_ok=True)
        
        # プロバイダインスタンス
        self.providers: Dict[PaymentProvider, PaymentProcessorBase] = {}
        
        # レート制限設定
        self.rate_limits = {
            PaymentProvider.STRIPE: {"calls": 0, "max_calls": 100, "reset_time": 3600},
            PaymentProvider.PAYPAL: {"calls": 0, "max_calls": 50, "reset_time": 3600}
        }
        
        logger.info("PaymentManager initialized")
    
    def initialize_provider(self, provider: PaymentProvider) -> bool:
        """プロバイダを初期化"""
        try:
            if provider == PaymentProvider.STRIPE:
                from .stripe_integration import StripePaymentProcessor
                
                # Stripe認証情報取得
                stripe_cred = self.auth_manager.get_credential("stripe")
                if not stripe_cred:
                    logger.warning("Stripe credentials not found")
                    return False
                
                self.providers[provider] = StripePaymentProcessor(self.auth_manager)
                logger.info("Stripe payment processor initialized")
                return True
                
            elif provider == PaymentProvider.PAYPAL:
                from .paypal_integration import PayPalPaymentProcessor
                
                # PayPal認証情報取得
                paypal_cred = self.auth_manager.get_credential("paypal")
                if not paypal_cred:
                    logger.warning("PayPal credentials not found")
                    return False
                
                self.providers[provider] = PayPalPaymentProcessor(self.auth_manager)
                logger.info("PayPal payment processor initialized")
                return True
                
            else:
                logger.error(f"Unknown provider: {provider}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize {provider.value}: {e}")
            return False
    
    def create_payment(self, provider: PaymentProvider, request: PaymentRequest) -> PaymentResponse:
        """決済を作成"""
        try:
            # レート制限チェック
            if not self._check_rate_limit(provider):
                return PaymentResponse(
                    provider=provider,
                    transaction_id="rate_limit_exceeded",
                    status="error",
                    amount=request.amount,
                    currency=request.currency,
                    created_at=datetime.now(),
                    error_message="Rate limit exceeded"
                )
            
            # プロバイダ初期化
            if provider not in self.providers:
                if not self.initialize_provider(provider):
                    return PaymentResponse(
                        provider=provider,
                        transaction_id="init_failed",
                        status="error",
                        amount=request.amount,
                        currency=request.currency,
                        created_at=datetime.now(),
                        error_message="Provider initialization failed"
                    )
            
            # 決済実行
            processor = self.providers[provider]
            response = processor.create_payment(request)
            
            # 履歴保存
            self._save_transaction(response)
            
            # レート制限カウンタ更新
            self._increment_rate_limit(provider)
            
            return response
            
        except Exception as e:
            logger.error(f"Payment creation error: {e}")
            return PaymentResponse(
                provider=provider,
                transaction_id="error",
                status="error",
                amount=request.amount,
                currency=request.currency,
                created_at=datetime.now(),
                error_message=str(e)
            )
    
    def get_payment_status(self, provider: PaymentProvider, transaction_id: str) -> PaymentResponse:
        """決済ステータスを取得"""
        try:
            if provider not in self.providers:
                if not self.initialize_provider(provider):
                    raise ValueError(f"Provider {provider.value} not initialized")
            
            processor = self.providers[provider]
            return processor.get_payment_status(transaction_id)
            
        except Exception as e:
            logger.error(f"Status check error: {e}")
            return PaymentResponse(
                provider=provider,
                transaction_id=transaction_id,
                status="error",
                amount=Decimal(0),
                currency="",
                created_at=datetime.now(),
                error_message=str(e)
            )
    
    def refund_payment(self, provider: PaymentProvider, transaction_id: str, 
                      amount: Optional[Decimal] = None) -> PaymentResponse:
        """返金処理"""
        try:
            if provider not in self.providers:
                if not self.initialize_provider(provider):
                    raise ValueError(f"Provider {provider.value} not initialized")
            
            processor = self.providers[provider]
            response = processor.refund_payment(transaction_id, amount)
            
            # 履歴保存
            self._save_transaction(response)
            
            return response
            
        except Exception as e:
            logger.error(f"Refund error: {e}")
            return PaymentResponse(
                provider=provider,
                transaction_id=transaction_id,
                status="error",
                amount=amount or Decimal(0),
                currency="",
                created_at=datetime.now(),
                error_message=str(e)
            )
    
    def list_all_transactions(self, limit: int = 50) -> List[PaymentResponse]:
        """全プロバイダの取引履歴を取得"""
        all_transactions = []
        
        # 保存された履歴から読み込み
        transaction_files = sorted(
            self.transactions_dir.glob("*.json"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )[:limit]
        
        for file_path in transaction_files:
            try:
                data = load_json_safely(str(file_path))
                if data:
                    # データからPaymentResponseを再構築
                    response = PaymentResponse(
                        provider=PaymentProvider(data["provider"]),
                        transaction_id=data["transaction_id"],
                        status=data["status"],
                        amount=Decimal(str(data["amount"])),
                        currency=data["currency"],
                        created_at=datetime.fromisoformat(data["created_at"]),
                        payment_url=data.get("payment_url"),
                        error_message=data.get("error_message"),
                        raw_response=data.get("raw_response")
                    )
                    all_transactions.append(response)
            except Exception as e:
                logger.error(f"Failed to load transaction {file_path}: {e}")
        
        return all_transactions
    
    def _check_rate_limit(self, provider: PaymentProvider) -> bool:
        """レート制限をチェック"""
        if provider not in self.rate_limits:
            return True
        
        limit_info = self.rate_limits[provider]
        return limit_info["calls"] < limit_info["max_calls"]
    
    def _increment_rate_limit(self, provider: PaymentProvider):
        """レート制限カウンタを増加"""
        if provider in self.rate_limits:
            self.rate_limits[provider]["calls"] += 1
    
    def _save_transaction(self, response: PaymentResponse):
        """取引履歴を保存"""
        try:
            timestamp = response.created_at.strftime("%Y%m%d_%H%M%S")
            filename = f"{response.provider.value}_{response.transaction_id}_{timestamp}.json"
            file_path = self.transactions_dir / filename
            
            transaction_data = {
                "provider": response.provider.value,
                "transaction_id": response.transaction_id,
                "status": response.status,
                "amount": str(response.amount),
                "currency": response.currency,
                "created_at": response.created_at.isoformat(),
                "payment_url": response.payment_url,
                "error_message": response.error_message,
                "raw_response": response.raw_response
            }
            
            save_json_safely(transaction_data, str(file_path))
            logger.info(f"Transaction saved: {filename}")
            
        except Exception as e:
            logger.error(f"Failed to save transaction: {e}")
    
    def get_transaction_summary(self) -> Dict[str, Any]:
        """取引サマリーを取得"""
        try:
            transactions = self.list_all_transactions(limit=1000)
            
            summary = {
                "total_transactions": len(transactions),
                "providers": {},
                "status_breakdown": {},
                "total_amount_by_currency": {},
                "recent_transactions": []
            }
            
            for txn in transactions:
                # プロバイダ別集計
                provider_name = txn.provider.value
                if provider_name not in summary["providers"]:
                    summary["providers"][provider_name] = 0
                summary["providers"][provider_name] += 1
                
                # ステータス別集計
                if txn.status not in summary["status_breakdown"]:
                    summary["status_breakdown"][txn.status] = 0
                summary["status_breakdown"][txn.status] += 1
                
                # 通貨別合計金額
                if txn.status == "succeeded":
                    if txn.currency not in summary["total_amount_by_currency"]:
                        summary["total_amount_by_currency"][txn.currency] = Decimal(0)
                    summary["total_amount_by_currency"][txn.currency] += txn.amount
            
            # 最近の取引（上位5件）
            summary["recent_transactions"] = [
                {
                    "provider": txn.provider.value,
                    "transaction_id": txn.transaction_id,
                    "status": txn.status,
                    "amount": str(txn.amount),
                    "currency": txn.currency,
                    "created_at": txn.created_at.isoformat()
                }
                for txn in transactions[:5]
            ]
            
            # Decimal を str に変換
            for currency, amount in summary["total_amount_by_currency"].items():
                summary["total_amount_by_currency"][currency] = str(amount)
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return {"error": str(e)}

# グローバルインスタンス作成関数
def get_payment_manager() -> PaymentManager:
    """PaymentManagerのシングルトンインスタンスを取得"""
    if not hasattr(get_payment_manager, "_instance"):
        get_payment_manager._instance = PaymentManager()
    return get_payment_manager._instance