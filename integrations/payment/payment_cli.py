"""
Payment API CLI Interface
最終フェーズ: 外部API統合（決済）
コマンドライン管理ツール
"""
import sys
import argparse
from pathlib import Path
from decimal import Decimal
from typing import Optional
import json

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent))

from integrations.payment.payment_manager import (
    PaymentManager, PaymentProvider, PaymentRequest, get_payment_manager
)
from auth.api_auth import APICredential
from scripts.utils import logger

class PaymentCLI:
    """決済管理CLIクラス"""
    
    def __init__(self):
        """初期化"""
        self.payment_manager = get_payment_manager()
        
    def setup_credentials(self, provider: str, api_key: str, api_secret: Optional[str] = None):
        """認証情報を設定"""
        try:
            if provider.lower() == "stripe":
                credential = APICredential(
                    service="stripe",
                    api_key=api_key,
                    api_secret=api_secret or ""
                )
                self.payment_manager.auth_manager.save_credential(credential)
                print(f"✅ Stripe認証情報を保存しました")
                
            elif provider.lower() == "paypal":
                if not api_secret:
                    print("❌ PayPalにはclient_secretが必要です")
                    return False
                    
                credential = APICredential(
                    service="paypal",
                    api_key=api_key,
                    api_secret=api_secret
                )
                self.payment_manager.auth_manager.save_credential(credential)
                print(f"✅ PayPal認証情報を保存しました")
                
            else:
                print(f"❌ 未対応のプロバイダー: {provider}")
                return False
                
            return True
            
        except Exception as e:
            print(f"❌ 認証情報設定エラー: {e}")
            return False
    
    def create_payment(self, provider: str, amount: str, currency: str, 
                      description: str, email: str, **kwargs):
        """決済を作成"""
        try:
            # プロバイダー変換
            if provider.lower() == "stripe":
                pay_provider = PaymentProvider.STRIPE
            elif provider.lower() == "paypal":
                pay_provider = PaymentProvider.PAYPAL
            else:
                print(f"❌ 未対応のプロバイダー: {provider}")
                return False
            
            # 決済リクエスト作成
            request = PaymentRequest(
                amount=Decimal(amount),
                currency=currency.upper(),
                description=description,
                customer_email=email,
                customer_name=kwargs.get('name'),
                return_url=kwargs.get('return_url'),
                cancel_url=kwargs.get('cancel_url'),
                metadata=kwargs.get('metadata', {})
            )
            
            # 決済実行
            response = self.payment_manager.create_payment(pay_provider, request)
            
            # 結果表示
            self._display_payment_response(response)
            
            return response.status != "error"
            
        except Exception as e:
            print(f"❌ 決済作成エラー: {e}")
            return False
    
    def get_payment_status(self, provider: str, transaction_id: str):
        """決済ステータスを取得"""
        try:
            # プロバイダー変換
            if provider.lower() == "stripe":
                pay_provider = PaymentProvider.STRIPE
            elif provider.lower() == "paypal":
                pay_provider = PaymentProvider.PAYPAL
            else:
                print(f"❌ 未対応のプロバイダー: {provider}")
                return False
            
            # ステータス取得
            response = self.payment_manager.get_payment_status(pay_provider, transaction_id)
            
            # 結果表示
            self._display_payment_response(response)
            
            return response.status != "error"
            
        except Exception as e:
            print(f"❌ ステータス取得エラー: {e}")
            return False
    
    def refund_payment(self, provider: str, transaction_id: str, amount: Optional[str] = None):
        """返金処理"""
        try:
            # プロバイダー変換
            if provider.lower() == "stripe":
                pay_provider = PaymentProvider.STRIPE
            elif provider.lower() == "paypal":
                pay_provider = PaymentProvider.PAYPAL
            else:
                print(f"❌ 未対応のプロバイダー: {provider}")
                return False
            
            # 返金実行
            refund_amount = Decimal(amount) if amount else None
            response = self.payment_manager.refund_payment(pay_provider, transaction_id, refund_amount)
            
            # 結果表示
            self._display_payment_response(response)
            
            return response.status != "error"
            
        except Exception as e:
            print(f"❌ 返金処理エラー: {e}")
            return False
    
    def list_transactions(self, limit: int = 10):
        """取引履歴を表示"""
        try:
            transactions = self.payment_manager.list_all_transactions(limit)
            
            if not transactions:
                print("📭 取引履歴はありません")
                return True
            
            print(f"📋 取引履歴（最新{len(transactions)}件）")
            print("-" * 80)
            
            for txn in transactions:
                print(f"ID: {txn.transaction_id}")
                print(f"プロバイダー: {txn.provider.value}")
                print(f"ステータス: {txn.status}")
                print(f"金額: {txn.amount} {txn.currency}")
                print(f"作成日時: {txn.created_at}")
                if txn.payment_url:
                    print(f"決済URL: {txn.payment_url}")
                print("-" * 80)
            
            return True
            
        except Exception as e:
            print(f"❌ 履歴取得エラー: {e}")
            return False
    
    def show_summary(self):
        """取引サマリーを表示"""
        try:
            summary = self.payment_manager.get_transaction_summary()
            
            if "error" in summary:
                print(f"❌ サマリー取得エラー: {summary['error']}")
                return False
            
            print("📊 取引サマリー")
            print(f"総取引数: {summary['total_transactions']}")
            
            if summary['providers']:
                print("\n📈 プロバイダー別:")
                for provider, count in summary['providers'].items():
                    print(f"  {provider}: {count}件")
            
            if summary['status_breakdown']:
                print("\n📊 ステータス別:")
                for status, count in summary['status_breakdown'].items():
                    print(f"  {status}: {count}件")
            
            if summary['total_amount_by_currency']:
                print("\n💰 通貨別合計:")
                for currency, amount in summary['total_amount_by_currency'].items():
                    print(f"  {currency}: {amount}")
            
            return True
            
        except Exception as e:
            print(f"❌ サマリー取得エラー: {e}")
            return False
    
    def _display_payment_response(self, response):
        """決済レスポンス表示"""
        print(f"🔍 決済情報")
        print(f"取引ID: {response.transaction_id}")
        print(f"プロバイダー: {response.provider.value}")
        print(f"ステータス: {response.status}")
        print(f"金額: {response.amount} {response.currency}")
        print(f"作成日時: {response.created_at}")
        
        if response.payment_url:
            print(f"決済URL: {response.payment_url}")
        
        if response.error_message:
            print(f"❌ エラー: {response.error_message}")
        
        print("-" * 60)

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="Payment API CLI Manager")
    subparsers = parser.add_subparsers(dest="command", help="利用可能なコマンド")
    
    # 認証情報設定
    auth_parser = subparsers.add_parser("auth", help="認証情報を設定")
    auth_parser.add_argument("provider", choices=["stripe", "paypal"], help="決済プロバイダー")
    auth_parser.add_argument("api_key", help="API Key")
    auth_parser.add_argument("--secret", help="API Secret (PayPalで必須)")
    
    # 決済作成
    create_parser = subparsers.add_parser("create", help="決済を作成")
    create_parser.add_argument("provider", choices=["stripe", "paypal"], help="決済プロバイダー")
    create_parser.add_argument("amount", help="金額")
    create_parser.add_argument("currency", help="通貨コード")
    create_parser.add_argument("description", help="決済の説明")
    create_parser.add_argument("email", help="顧客メールアドレス")
    create_parser.add_argument("--name", help="顧客名")
    create_parser.add_argument("--return-url", help="成功時リダイレクトURL")
    create_parser.add_argument("--cancel-url", help="キャンセル時リダイレクトURL")
    
    # ステータス確認
    status_parser = subparsers.add_parser("status", help="決済ステータスを確認")
    status_parser.add_argument("provider", choices=["stripe", "paypal"], help="決済プロバイダー")
    status_parser.add_argument("transaction_id", help="取引ID")
    
    # 返金処理
    refund_parser = subparsers.add_parser("refund", help="返金処理")
    refund_parser.add_argument("provider", choices=["stripe", "paypal"], help="決済プロバイダー")
    refund_parser.add_argument("transaction_id", help="取引ID")
    refund_parser.add_argument("--amount", help="返金金額（指定しない場合は全額）")
    
    # 履歴表示
    list_parser = subparsers.add_parser("list", help="取引履歴を表示")
    list_parser.add_argument("--limit", type=int, default=10, help="表示件数")
    
    # サマリー表示
    subparsers.add_parser("summary", help="取引サマリーを表示")
    
    # 引数解析
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # CLI実行
    cli = PaymentCLI()
    
    try:
        if args.command == "auth":
            success = cli.setup_credentials(args.provider, args.api_key, args.secret)
            
        elif args.command == "create":
            success = cli.create_payment(
                args.provider, args.amount, args.currency, 
                args.description, args.email,
                name=args.name, return_url=args.return_url, cancel_url=args.cancel_url
            )
            
        elif args.command == "status":
            success = cli.get_payment_status(args.provider, args.transaction_id)
            
        elif args.command == "refund":
            success = cli.refund_payment(args.provider, args.transaction_id, args.amount)
            
        elif args.command == "list":
            success = cli.list_transactions(args.limit)
            
        elif args.command == "summary":
            success = cli.show_summary()
            
        else:
            print(f"❌ 未知のコマンド: {args.command}")
            success = False
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⏹️  処理が中断されました")
        return 1
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())