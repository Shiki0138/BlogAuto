"""
Payment API Integration Package
最終フェーズ: 外部API統合（Stripe/PayPal）
進捗目標: 92%
"""
from .payment_manager import PaymentManager, PaymentProvider
from .stripe_integration import StripePaymentProcessor
from .paypal_integration import PayPalPaymentProcessor

__all__ = [
    'PaymentManager',
    'PaymentProvider',
    'StripePaymentProcessor',
    'PayPalPaymentProcessor'
]

__version__ = '1.0.0'