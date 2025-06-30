"""
Payment Integration Tests
最終フェーズ: 外部API統合（決済）テスト
"""
import os
import sys
import pytest
from pathlib import Path
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from integrations.payment.payment_manager import (
    PaymentManager, PaymentProvider, PaymentRequest, PaymentResponse, get_payment_manager
)
from integrations.payment.stripe_integration import StripePaymentProcessor
from integrations.payment.paypal_integration import PayPalPaymentProcessor
from auth.api_auth import APIAuthManager, APICredential

class TestPaymentManager:
    """PaymentManagerのテストクラス"""
    
    def setup_method(self):
        """テストセットアップ"""
        # テスト用ディレクトリ
        self.test_dir = Path("/tmp/blogauto_test")
        self.test_dir.mkdir(exist_ok=True)
        
        # PaymentManagerインスタンス作成
        self.payment_manager = PaymentManager(self.test_dir)
    
    def teardown_method(self):
        """テストクリーンアップ"""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_payment_manager_initialization(self):
        """PaymentManager初期化テスト"""
        assert self.payment_manager.config_dir == self.test_dir
        assert self.payment_manager.transactions_dir.exists()
        assert isinstance(self.payment_manager.auth_manager, APIAuthManager)
        assert len(self.payment_manager.providers) == 0
    
    def test_payment_request_creation(self):
        """PaymentRequestの作成テスト"""
        request = PaymentRequest(
            amount=Decimal("1000"),
            currency="JPY",
            description="Test Payment",
            customer_email="test@example.com",
            customer_name="Test Customer",
            metadata={"order_id": "12345"},
            return_url="https://example.com/success",
            cancel_url="https://example.com/cancel"
        )
        
        assert request.amount == Decimal("1000")
        assert request.currency == "JPY"
        assert request.description == "Test Payment"
        assert request.customer_email == "test@example.com"
        assert request.customer_name == "Test Customer"
        assert request.metadata["order_id"] == "12345"
    
    @patch.dict(os.environ, {'ENABLE_EXTERNAL_API': 'false'})
    def test_stripe_mock_payment(self):
        """Stripeモック決済テスト"""
        # モックStripe認証情報設定
        stripe_cred = APICredential(
            api_name="stripe",
            api_key="sk_test_mock"
        )
        stripe_cred.api_secret = "sk_test_secret"
        self.payment_manager.auth_manager._credentials["stripe"] = stripe_cred
        
        # 決済リクエスト作成
        request = PaymentRequest(
            amount=Decimal("1500"),
            currency="JPY",
            description="Test Stripe Payment",
            customer_email="stripe@example.com"
        )
        
        # 決済実行
        response = self.payment_manager.create_payment(PaymentProvider.STRIPE, request)
        
        # レスポンス検証
        assert response.provider == PaymentProvider.STRIPE
        assert response.status == "pending"
        assert response.amount == Decimal("1500")
        assert response.currency == "JPY"
        assert response.transaction_id.startswith("mock_stripe_")
        assert response.payment_url is not None
        assert response.raw_response["mock"] is True
    
    @patch.dict(os.environ, {'ENABLE_EXTERNAL_API': 'false'})
    def test_paypal_mock_payment(self):
        """PayPalモック決済テスト"""
        # モックPayPal認証情報設定
        paypal_cred = APICredential(
            api_name="paypal",
            api_key="client_id_mock"
        )
        paypal_cred.api_secret = "client_secret_mock"
        self.payment_manager.auth_manager._credentials["paypal"] = paypal_cred
        
        # 決済リクエスト作成
        request = PaymentRequest(
            amount=Decimal("2000"),
            currency="USD",
            description="Test PayPal Payment",
            customer_email="paypal@example.com"
        )
        
        # 決済実行
        response = self.payment_manager.create_payment(PaymentProvider.PAYPAL, request)
        
        # レスポンス検証
        assert response.provider == PaymentProvider.PAYPAL
        assert response.status == "pending"
        assert response.amount == Decimal("2000")
        assert response.currency == "USD"
        assert response.transaction_id.startswith("mock_paypal_")
        assert response.payment_url is not None
        assert response.raw_response["mock"] is True
    
    def test_rate_limiting(self):
        """レート制限テスト"""
        # レート制限を0に設定
        self.payment_manager.rate_limits[PaymentProvider.STRIPE]["max_calls"] = 0
        
        request = PaymentRequest(
            amount=Decimal("1000"),
            currency="JPY",
            description="Rate Limited Payment",
            customer_email="test@example.com"
        )
        
        response = self.payment_manager.create_payment(PaymentProvider.STRIPE, request)
        
        assert response.status == "error"
        assert response.transaction_id == "rate_limit_exceeded"
        assert "Rate limit exceeded" in response.error_message
    
    def test_transaction_history(self):
        """取引履歴テスト"""
        # モック決済を複数作成
        requests = [
            PaymentRequest(Decimal("1000"), "JPY", f"Payment {i}", f"test{i}@example.com")
            for i in range(3)
        ]
        
        responses = []
        for request in requests:
            response = self.payment_manager.create_payment(PaymentProvider.STRIPE, request)
            responses.append(response)
        
        # 履歴取得
        history = self.payment_manager.list_all_transactions(limit=5)
        
        assert len(history) == 3
        assert all(txn.provider == PaymentProvider.STRIPE for txn in history)
    
    def test_transaction_summary(self):
        """取引サマリーテスト"""
        # 複数の決済を作成
        stripe_request = PaymentRequest(Decimal("1000"), "JPY", "Stripe Payment", "stripe@example.com")
        paypal_request = PaymentRequest(Decimal("2000"), "USD", "PayPal Payment", "paypal@example.com")
        
        self.payment_manager.create_payment(PaymentProvider.STRIPE, stripe_request)
        self.payment_manager.create_payment(PaymentProvider.PAYPAL, paypal_request)
        
        # サマリー取得
        summary = self.payment_manager.get_transaction_summary()
        
        assert summary["total_transactions"] == 2
        assert "stripe" in summary["providers"]
        assert "paypal" in summary["providers"]
        assert "pending" in summary["status_breakdown"]
        assert len(summary["recent_transactions"]) == 2

class TestStripeIntegration:
    """Stripe統合テストクラス"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.test_dir = Path("/tmp/blogauto_stripe_test")
        self.test_dir.mkdir(exist_ok=True)
        self.auth_manager = APIAuthManager(self.test_dir)
    
    def teardown_method(self):
        """テストクリーンアップ"""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    @patch.dict(os.environ, {'ENABLE_EXTERNAL_API': 'false'})
    def test_stripe_initialization(self):
        """Stripe初期化テスト"""
        processor = StripePaymentProcessor(self.auth_manager)
        
        assert processor.stripe_enabled is False
        assert processor.api_version == "2024-06-20"
        assert processor.max_retries == 3
    
    @patch.dict(os.environ, {'ENABLE_EXTERNAL_API': 'false'})
    def test_stripe_mock_payment_creation(self):
        """Stripeモック決済作成テスト"""
        processor = StripePaymentProcessor(self.auth_manager)
        
        request = PaymentRequest(
            amount=Decimal("3000"),
            currency="JPY",
            description="Mock Stripe Payment",
            customer_email="mock@stripe.com"
        )
        
        response = processor.create_payment(request)
        
        assert response.provider == PaymentProvider.STRIPE
        assert response.status == "pending"
        assert response.amount == Decimal("3000")
        assert response.currency == "JPY"
        assert response.payment_url.startswith("https://checkout.stripe.com/mock/")
    
    @patch.dict(os.environ, {'ENABLE_EXTERNAL_API': 'false'})
    def test_stripe_payment_status(self):
        """Stripe決済ステータステスト"""
        processor = StripePaymentProcessor(self.auth_manager)
        
        response = processor.get_payment_status("mock_transaction_123")
        
        assert response.transaction_id == "mock_transaction_123"
        assert response.status == "succeeded"
        assert response.amount == Decimal("1000")
        assert response.currency == "JPY"
    
    @patch.dict(os.environ, {'ENABLE_EXTERNAL_API': 'false'})
    def test_stripe_refund(self):
        """Stripe返金テスト"""
        processor = StripePaymentProcessor(self.auth_manager)
        
        response = processor.refund_payment("mock_transaction_123", Decimal("500"))
        
        assert response.status == "refunded"
        assert response.amount == Decimal("500")
        assert response.currency == "JPY"

class TestPayPalIntegration:
    """PayPal統合テストクラス"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.test_dir = Path("/tmp/blogauto_paypal_test")
        self.test_dir.mkdir(exist_ok=True)
        self.auth_manager = APIAuthManager(self.test_dir)
    
    def teardown_method(self):
        """テストクリーンアップ"""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    @patch.dict(os.environ, {'ENABLE_EXTERNAL_API': 'false'})
    def test_paypal_initialization(self):
        """PayPal初期化テスト"""
        processor = PayPalPaymentProcessor(self.auth_manager)
        
        assert processor.paypal_enabled is False
        assert processor.is_sandbox is True
        assert processor.base_url == "https://api.sandbox.paypal.com"
    
    @patch.dict(os.environ, {'ENABLE_EXTERNAL_API': 'false'})
    def test_paypal_mock_payment_creation(self):
        """PayPalモック決済作成テスト"""
        processor = PayPalPaymentProcessor(self.auth_manager)
        
        request = PaymentRequest(
            amount=Decimal("2500"),
            currency="USD",
            description="Mock PayPal Payment",
            customer_email="mock@paypal.com"
        )
        
        response = processor.create_payment(request)
        
        assert response.provider == PaymentProvider.PAYPAL
        assert response.status == "pending"
        assert response.amount == Decimal("2500")
        assert response.currency == "USD"
        assert response.payment_url.startswith("https://www.paypal.com/checkoutnow?token=")
    
    @patch.dict(os.environ, {'ENABLE_EXTERNAL_API': 'false'})
    def test_paypal_payment_status(self):
        """PayPal決済ステータステスト"""
        processor = PayPalPaymentProcessor(self.auth_manager)
        
        response = processor.get_payment_status("mock_order_456")
        
        assert response.transaction_id == "mock_order_456"
        assert response.status == "succeeded"
        assert response.amount == Decimal("1000")
        assert response.currency == "JPY"

class TestErrorHandling:
    """エラーハンドリングテストクラス"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.test_dir = Path("/tmp/blogauto_error_test")
        self.test_dir.mkdir(exist_ok=True)
        self.payment_manager = PaymentManager(self.test_dir)
    
    def teardown_method(self):
        """テストクリーンアップ"""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_invalid_provider(self):
        """無効なプロバイダーテスト"""
        request = PaymentRequest(
            amount=Decimal("1000"),
            currency="JPY",
            description="Invalid Provider Test",
            customer_email="test@example.com"
        )
        
        # プロバイダーが初期化されていない場合
        response = self.payment_manager.create_payment(PaymentProvider.STRIPE, request)
        
        assert response.status == "error"
        assert "initialization failed" in response.error_message.lower()
    
    def test_invalid_amount(self):
        """無効な金額テスト"""
        request = PaymentRequest(
            amount=Decimal("0"),
            currency="JPY",
            description="Zero Amount Test",
            customer_email="test@example.com"
        )
        
        # 金額が0の場合の処理をテスト
        response = self.payment_manager.create_payment(PaymentProvider.STRIPE, request)
        
        # モックモードでは通常通り処理される
        assert response.amount == Decimal("0")

def test_singleton_payment_manager():
    """PaymentManagerシングルトンテスト"""
    manager1 = get_payment_manager()
    manager2 = get_payment_manager()
    
    assert manager1 is manager2

# パフォーマンステスト
class TestPerformance:
    """パフォーマンステストクラス"""
    
    def test_concurrent_payments(self):
        """並行決済テスト"""
        import threading
        import time
        
        payment_manager = get_payment_manager()
        results = []
        
        def create_payment(i):
            request = PaymentRequest(
                amount=Decimal("1000"),
                currency="JPY",
                description=f"Concurrent Payment {i}",
                customer_email=f"test{i}@example.com"
            )
            response = payment_manager.create_payment(PaymentProvider.STRIPE, request)
            results.append(response)
        
        # 10個の並行決済を実行
        threads = []
        start_time = time.time()
        
        for i in range(10):
            thread = threading.Thread(target=create_payment, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        
        assert len(results) == 10
        assert all(r.status in ["pending", "error"] for r in results)
        assert end_time - start_time < 5  # 5秒以内で完了

if __name__ == "__main__":
    # テスト実行
    pytest.main([__file__, "-v"])