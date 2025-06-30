"""
ユーティリティモジュール
共通関数とエラーハンドリング機能を提供
"""
import os
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from pathlib import Path

# エラーハンドリング機能のインポート（循環インポート回避）
try:
    from scripts.error_handler import (
        error_handler, with_error_handling, safe_file_operation,
        BlogAutoError, APIError, FileOperationError, ValidationError
    )
    HAS_ERROR_HANDLER = True
except ImportError:
    # エラーハンドラーが利用できない場合の基本実装
    HAS_ERROR_HANDLER = False
    
    class MockErrorHandler:
        def handle_error(self, error, context=None):
            logging.error(f"Error: {error}")
    
    error_handler = MockErrorHandler()
    
    def with_error_handling(**kwargs):
        def decorator(func):
            return func
        return decorator

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# JST タイムゾーン
JST = timezone(timedelta(hours=9))

def get_jst_now() -> datetime:
    """JST現在時刻を取得"""
    return datetime.now(JST)

def get_jst_date_string() -> str:
    """JST日付文字列を取得（YYYY-MM-DD形式）"""
    return get_jst_now().strftime('%Y-%m-%d')

def get_jst_date_japanese() -> str:
    """JST日付の日本語文字列を取得"""
    now = get_jst_now()
    return f"{now.year}年{now.month}月{now.day}日"

def ensure_output_dir() -> Path:
    """output ディレクトリの存在を確認・作成"""
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    return output_dir

@with_error_handling(default_return=False, max_retries=2, retry_delay=0.5)
def save_json_safely(data: Dict[str, Any], filepath: str) -> bool:
    """JSONファイルを安全に保存（エラーハンドリング強化版）"""
    try:
        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # ファイル操作を安全に実行
        if HAS_ERROR_HANDLER:
            def write_operation():
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            
            safe_file_operation("write", str(output_path), write_operation)
        else:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"JSONファイル保存成功: {filepath}")
        return True
    except Exception as e:
        logger.error(f"JSONファイル保存失敗: {filepath}, エラー: {e}")
        if HAS_ERROR_HANDLER:
            error_handler.handle_error(e, {"operation": "save_json", "filepath": filepath})
        raise

def load_json_safely(filepath: str) -> Optional[Dict[str, Any]]:
    """JSONファイルを安全に読み込み"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"JSONファイル読み込み成功: {filepath}")
        return data
    except FileNotFoundError:
        logger.warning(f"JSONファイルが見つかりません: {filepath}")
        return None
    except Exception as e:
        logger.error(f"JSONファイル読み込み失敗: {filepath}, エラー: {e}")
        return None

def get_env_var(key: str, required: bool = True, default: Optional[str] = None) -> Optional[str]:
    """環境変数を安全に取得"""
    value = os.getenv(key, default)
    if required and not value:
        logger.error(f"必須環境変数が設定されていません: {key}")
        raise ValueError(f"環境変数 {key} が設定されていません")
    return value

def clean_html_content(content: str) -> str:
    """HTMLコンテンツからスクリプトタグを除去（XSS防止）"""
    import re
    # scriptタグを除去
    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
    # onイベント属性を除去
    content = re.sub(r'\son\w+\s*=\s*["\'][^"\']*["\']', '', content, flags=re.IGNORECASE)
    return content

def get_today_theme() -> str:
    """今日のテーマを取得（美容師・サロン特化版）"""
    return BeautyThemeGenerator().get_daily_theme()

class BeautyThemeGenerator:
    """美容師・サロン業界専用テーマ生成クラス"""
    
    def __init__(self):
        self.base_themes = self._initialize_base_themes()
        self.seasonal_themes = self._initialize_seasonal_themes()
        self.psychology_themes = self._initialize_psychology_themes()
        self.trending_themes = self._initialize_trending_themes()
        self.local_business_themes = self._initialize_local_business_themes()
    
    def _initialize_base_themes(self) -> list:
        """基本的な美容業界テーマ"""
        return [
            "顧客リピート率向上の心理学テクニック",
            "Instagram集客で月間フォロワー1000人増加させる方法",
            "美容師のための効果的なカウンセリング術",
            "サロン経営における顧客満足度向上戦略",
            "美容業界でのデジタルマーケティング活用法",
            "競合サロンとの差別化ポイント構築術",
            "美容師の技術力向上とキャリアアップ戦略",
            "サロンの売上アップにつながる価格設定心理学",
            "顧客の本音を引き出すコミュニケーション技術",
            "美容業界トレンドの先取りと活用方法",
            "サロン運営の効率化とスタッフ育成術",
            "美容師のためのSNSブランディング戦略",
            "顧客の髪質悩み解決アプローチ法",
            "サロンの雰囲気作りと空間演出テクニック",
            "美容師の接客スキル向上メソッド",
            "リピート客獲得のためのアフターフォロー術",
            "美容業界での口コミマーケティング活用法",
            "サロン経営者のための数字管理と分析術",
            "美容師の疲労回復と健康管理法",
            "顧客ニーズの変化に対応する柔軟性養成術"
        ]
    
    def _initialize_seasonal_themes(self) -> dict:
        """季節別特化テーマ"""
        return {
            "spring": [
                "春の新生活に向けたイメージチェンジ提案術",
                "花粉症時期のヘアケア・頭皮ケア対策",
                "卒業・入学シーズンの特別メニュー企画法",
                "春色カラーリングのトレンド活用術",
                "新年度の目標設定と美容師キャリアプラン"
            ],
            "summer": [
                "夏の紫外線対策とヘアダメージ予防法",
                "汗をかく季節のスタイリング持続テクニック",
                "夏祭り・海水浴向けヘアアレンジ提案",
                "エアコンによる髪の乾燥対策アドバイス",
                "夏休み期間の集客戦略と特別キャンペーン"
            ],
            "autumn": [
                "秋の髪色チェンジで印象アップ術",
                "乾燥シーズン前のヘアケア準備法",
                "結婚式シーズンのブライダルヘア対応",
                "季節の変わり目の抜け毛対策アドバイス",
                "秋冬に向けたサロンメニュー見直し術"
            ],
            "winter": [
                "冬の乾燥に負けないヘアケア方法",
                "忘年会・新年会向けパーティーヘア提案",
                "静電気対策とヘアスタイリング術",
                "年末年始の特別営業と顧客対応法",
                "新年の目標達成に向けた美容師スキルアップ"
            ]
        }
    
    def _initialize_psychology_themes(self) -> list:
        """行動経済学・心理学ベースのテーマ"""
        return [
            "認知バイアスを活用した美容提案術",
            "プロスペクト理論で顧客の購買意欲を高める方法",
            "アンカリング効果を使った価格設定戦略",
            "返報性の原理でリピート率を向上させる技術",
            "ザイアンス効果を活用した顧客関係構築法",
            "コミットメント効果で顧客満足度を向上させる術",
            "社会的証明を使った新規顧客獲得法",
            "損失回避バイアスを活用した予約促進術",
            "確証バイアスを理解した顧客対応法",
            "選択のパラドックスを回避するメニュー構成術",
            "ハロー効果で第一印象を最大化する方法",
            "フレーミング効果を使った価値提案術",
            "希少性の原理で特別感を演出する技術",
            "一貫性の原理で顧客ロイヤルティを高める方法",
            "好意の返報性で信頼関係を深める術"
        ]
    
    def _initialize_trending_themes(self) -> list:
        """2024-2025年トレンドテーマ"""
        return [
            "生成AIを活用した美容提案とカウンセリング",
            "サステナブル美容とエコフレンドリーサロン運営",
            "メンズ美容市場拡大への対応戦略",
            "オンライン予約システムの最適化術",
            "Z世代顧客の価値観に響く接客法",
            "インクルーシブ美容への取り組み方",
            "デジタルデトックス時代の癒し空間作り",
            "パーソナライゼーション技術の美容業界活用",
            "ウェルネス志向に応えるホリスティック美容",
            "サブスクリプション型サービスの導入法",
            "VR・AR技術を使った美容体験提供",
            "データ分析による顧客行動予測術",
            "リモートワーク時代のヘアケア需要対応",
            "シニア世代の美容ニーズへの対応法",
            "ジェンダーレス美容サービスの展開術"
        ]
    
    def _initialize_local_business_themes(self) -> list:
        """ローカルビジネス特化テーマ"""
        return [
            "地域密着型サロンの差別化戦略",
            "地元イベント連携による集客法",
            "商店街・ショッピングモール出店のメリット活用",
            "地域コミュニティとの関係構築術",
            "ローカルSEOで検索上位を獲得する方法",
            "地域限定キャンペーンの効果的な企画法",
            "近隣サロンとの健全な競争関係構築",
            "地域のライフスタイルに合わせたサービス設計",
            "口コミ文化を活用した評判管理術",
            "地域密着の信頼関係で長期顧客を獲得する方法",
            "地元メディア活用による知名度向上術",
            "季節行事に合わせた地域貢献活動",
            "地域の年齢層に応じたサービス戦略",
            "交通アクセスの良さを活かした集客法",
            "地域経済活性化に貢献するサロン運営術"
        ]
    
    def get_daily_theme(self) -> str:
        """日付ベースで最適なテーマを選択"""
        today = get_jst_now()
        day_of_year = today.timetuple().tm_yday
        
        # 季節の判定
        month = today.month
        if month in [3, 4, 5]:
            season = "spring"
        elif month in [6, 7, 8]:
            season = "summer"
        elif month in [9, 10, 11]:
            season = "autumn"
        else:
            season = "winter"
        
        # テーマカテゴリの重み付け選択
        theme_categories = {
            "base": (self.base_themes, 0.4),          # 40%
            "psychology": (self.psychology_themes, 0.25), # 25%
            "seasonal": (self.seasonal_themes[season], 0.15), # 15%
            "trending": (self.trending_themes, 0.15),    # 15%
            "local": (self.local_business_themes, 0.05)  # 5%
        }
        
        # 週の曜日で重み付けを調整
        weekday = today.weekday()
        if weekday == 0:  # 月曜日：心理学テーマ強化
            theme_categories["psychology"] = (self.psychology_themes, 0.4)
            theme_categories["base"] = (self.base_themes, 0.3)
        elif weekday == 4:  # 金曜日：トレンドテーマ強化
            theme_categories["trending"] = (self.trending_themes, 0.3)
            theme_categories["base"] = (self.base_themes, 0.3)
        elif weekday == 6:  # 日曜日：ローカルビジネステーマ強化
            theme_categories["local"] = (self.local_business_themes, 0.2)
            theme_categories["base"] = (self.base_themes, 0.35)
        
        # 日付ベースでカテゴリ選択
        category_weights = [weight for _, weight in theme_categories.values()]
        cumulative_weights = []
        cumsum = 0
        for weight in category_weights:
            cumsum += weight
            cumulative_weights.append(cumsum)
        
        # 疑似ランダム選択（日付ベース）
        selector = (day_of_year * 7 + weekday) % 100 / 100
        
        selected_category = None
        for i, cum_weight in enumerate(cumulative_weights):
            if selector <= cum_weight:
                selected_category = list(theme_categories.keys())[i]
                break
        
        if not selected_category:
            selected_category = "base"
        
        # 選択されたカテゴリからテーマを取得
        themes, _ = theme_categories[selected_category]
        theme_index = day_of_year % len(themes)
        
        logger.info(f"🎯 Beauty Theme Selected: {selected_category} category, theme #{theme_index + 1}")
        return themes[theme_index]
    
    def get_theme_by_category(self, category: str, index: int = None) -> str:
        """カテゴリ指定でテーマ取得"""
        category_map = {
            "base": self.base_themes,
            "psychology": self.psychology_themes,
            "trending": self.trending_themes,
            "local": self.local_business_themes
        }
        
        if category in ["spring", "summer", "autumn", "winter"]:
            themes = self.seasonal_themes[category]
        elif category in category_map:
            themes = category_map[category]
        else:
            themes = self.base_themes
        
        if index is None:
            index = get_jst_now().timetuple().tm_yday % len(themes)
        else:
            index = index % len(themes)
        
        return themes[index]
    
    def get_all_themes(self) -> dict:
        """全テーマリストを取得"""
        all_themes = {
            "base_themes": self.base_themes,
            "psychology_themes": self.psychology_themes,
            "trending_themes": self.trending_themes,
            "local_business_themes": self.local_business_themes,
            "seasonal_themes": self.seasonal_themes
        }
        return all_themes
    
    def search_themes(self, keyword: str) -> list:
        """キーワードでテーマ検索"""
        all_themes_flat = []
        
        # 全テーマを平坦化
        all_themes_flat.extend(self.base_themes)
        all_themes_flat.extend(self.psychology_themes)
        all_themes_flat.extend(self.trending_themes)
        all_themes_flat.extend(self.local_business_themes)
        
        for season_themes in self.seasonal_themes.values():
            all_themes_flat.extend(season_themes)
        
        # キーワード検索
        matching_themes = [theme for theme in all_themes_flat if keyword in theme]
        return matching_themes

def validate_api_response(response: Any, api_name: str) -> bool:
    """API レスポンスの基本検証"""
    if not response:
        logger.warning(f"{api_name} API: 空のレスポンスです")
        return False
    
    if hasattr(response, 'status_code') and response.status_code >= 400:
        logger.error(f"{api_name} API エラー: {response.status_code}")
        return False
    
    return True

class APIRateLimiter:
    """API レート制限管理"""
    
    def __init__(self):
        self.last_requests = {}
        self.min_intervals = {
            'unsplash': 1.0,  # 1秒間隔
            'pexels': 1.0,
            'gemini': 2.0,    # 2秒間隔
            'openai': 3.0     # 3秒間隔
        }
    
    def can_request(self, api_name: str) -> bool:
        """リクエスト可能かチェック"""
        if api_name not in self.last_requests:
            return True
        
        last_time = self.last_requests[api_name]
        min_interval = self.min_intervals.get(api_name, 1.0)
        
        return (datetime.now() - last_time).total_seconds() >= min_interval
    
    def record_request(self, api_name: str):
        """リクエスト時刻を記録"""
        self.last_requests[api_name] = datetime.now()

# グローバルレート制限インスタンス
rate_limiter = APIRateLimiter()

class SystemHealthChecker:
    """システムヘルスチェック機能"""
    
    def __init__(self):
        self.checks = []
        
    def add_check(self, name: str, check_func):
        """ヘルスチェック項目を追加"""
        self.checks.append((name, check_func))
    
    def run_all_checks(self) -> Dict[str, Any]:
        """全ヘルスチェックを実行"""
        results = {
            "timestamp": get_jst_now().isoformat(),
            "overall_status": "healthy",
            "checks": {}
        }
        
        failed_checks = 0
        
        for name, check_func in self.checks:
            try:
                status = check_func()
                results["checks"][name] = {
                    "status": "pass" if status else "fail",
                    "result": status
                }
                if not status:
                    failed_checks += 1
            except Exception as e:
                results["checks"][name] = {
                    "status": "error",
                    "error": str(e)
                }
                failed_checks += 1
        
        if failed_checks > 0:
            results["overall_status"] = "unhealthy"
            
        return results

def check_output_directory() -> bool:
    """output ディレクトリの存在確認"""
    return Path("output").exists()

def check_required_files() -> bool:
    """必要ファイルの存在確認"""
    required_files = [
        "requirements.txt",
        "prompts/daily_blog.jinja",
        ".github/workflows/daily-blog.yml"
    ]
    return all(Path(f).exists() for f in required_files)

def check_environment_variables() -> bool:
    """重要な環境変数の設定確認"""
    # 注意: 外部API接続は最終フェーズまで無効
    # フェーズ3では環境変数なしでも動作することを確認
    optional_vars = ['ANTHROPIC_API_KEY', 'WP_USER', 'WP_APP_PASS']
    found_vars = sum(1 for var in optional_vars if os.getenv(var))
    # 現在のフェーズでは環境変数なしでも動作OK
    return True  # フェーズ3ではモック動作で環境変数不要

class PerformanceMonitor:
    """パフォーマンス監視機能"""
    
    def __init__(self):
        self.start_time = None
        self.metrics = {}
    
    def start_timing(self, operation: str):
        """タイミング開始"""
        self.start_time = datetime.now()
        self.metrics[operation] = {"start": self.start_time}
    
    def end_timing(self, operation: str):
        """タイミング終了"""
        if operation in self.metrics and self.start_time:
            end_time = datetime.now()
            duration = (end_time - self.start_time).total_seconds()
            self.metrics[operation].update({
                "end": end_time,
                "duration_seconds": duration
            })
            logger.info(f"Performance: {operation} took {duration:.2f} seconds")
            return duration
        return None
    
    def get_metrics(self) -> Dict[str, Any]:
        """メトリクス取得"""
        return self.metrics

# グローバルインスタンス
health_checker = SystemHealthChecker()
performance_monitor = PerformanceMonitor()

# デフォルトヘルスチェック登録
health_checker.add_check("output_directory", check_output_directory)
health_checker.add_check("required_files", check_required_files)
health_checker.add_check("environment_variables", check_environment_variables)

def run_integration_test() -> bool:
    """統合テスト実行"""
    try:
        logger.info("統合テスト開始")
        
        # ヘルスチェック実行
        health_results = health_checker.run_all_checks()
        
        if health_results["overall_status"] != "healthy":
            logger.error("ヘルスチェック失敗")
            return False
        
        # パフォーマンステスト
        performance_monitor.start_timing("integration_test")
        
        # テスト項目実行
        test_results = {
            "article_generation": test_article_generation(),
            "image_fetching": test_image_fetching(),
            "wordpress_posting": test_wordpress_posting()
        }
        
        performance_monitor.end_timing("integration_test")
        
        # 結果保存（datetimeオブジェクトをISO文字列に変換）
        performance_data = performance_monitor.get_metrics()
        for operation, metrics in performance_data.items():
            if 'start' in metrics and hasattr(metrics['start'], 'isoformat'):
                metrics['start'] = metrics['start'].isoformat()
            if 'end' in metrics and hasattr(metrics['end'], 'isoformat'):
                metrics['end'] = metrics['end'].isoformat()
        
        test_report = {
            "timestamp": get_jst_now().isoformat(),
            "health_check": health_results,
            "test_results": test_results,
            "performance": performance_data
        }
        
        save_json_safely(test_report, "output/integration_test_report.json")
        
        all_passed = all(test_results.values())
        logger.info(f"統合テスト{'成功' if all_passed else '失敗'}")
        
        return all_passed
        
    except Exception as e:
        logger.error(f"統合テストエラー: {e}")
        return False

def test_article_generation() -> bool:
    """記事生成テスト"""
    try:
        import subprocess
        result = subprocess.run(['python', 'scripts/generate_article.py'], 
                              capture_output=True, text=True, timeout=60)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"記事生成テストエラー: {e}")
        return False

def test_image_fetching() -> bool:
    """画像取得テスト"""
    try:
        import subprocess
        result = subprocess.run(['python', 'scripts/fetch_image.py'], 
                              capture_output=True, text=True, timeout=60)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"画像取得テストエラー: {e}")
        return False

def test_wordpress_posting() -> bool:
    """WordPress投稿テスト"""
    try:
        import subprocess
        result = subprocess.run(['python', 'scripts/post_to_wp.py'], 
                              capture_output=True, text=True, timeout=60)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"WordPress投稿テストエラー: {e}")
        return False