#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美容師・ローカルビジネス向けテーマ生成器
心理学・行動経済学・生成AI活用のテーマを自動選択
"""
import random
from pathlib import Path
import sys

# プロジェクトルートをPythonパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from scripts.utils import logger

class BeautyBusinessThemeGenerator:
    """美容師・ローカルビジネス向けテーマ生成クラス"""
    
    def __init__(self):
        """初期化"""
        self.psychology_themes = [
            "美容師が知るべき顧客心理学：リピート率を80%向上させる接客術",
            "行動経済学で解く！美容室の価格設定とメニュー構成戦略",
            "認知バイアスを活用した美容サロンの集客心理テクニック",
            "プロスペクト理論で理解する：なぜ顧客は安いサロンを選ぶのか",
            "社会的証明の法則を使った口コミ・レビュー獲得戦略",
            "美容師のためのコミュニケーション心理学：信頼関係構築術",
            "顧客満足度を科学する：測定方法と改善アプローチ",
            "クレーム対応の心理学：問題を機会に変える接客術"
        ]
        
        self.instagram_marketing_themes = [
            "Instagram集客の心理学：フォロワーの心を掴む投稿戦略",
            "美容師のためのInstagramストーリーズ活用術：予約につながる使い方",
            "ハッシュタグ戦略の科学：美容室が狙うべきキーワード設計",
            "インフルエンサーマーケティング入門：美容サロンの協働戦略",
            "TikTok×美容師：短時間で技術をアピールする動画制作術",
            "美容師のためのパーソナルブランディング戦略",
            "ジェネレーションZ美容師のSNS活用術"
        ]
        
        self.ai_automation_themes = [
            "ChatGPTで美容室経営を効率化：予約管理から接客まで",
            "美容師のためのAIプロンプト設計：顧客カウンセリングに活用",
            "Claude・Geminiを使った美容室のコンテンツ作成自動化",
            "AI画像生成で作る美容室の広告素材：Midjourney活用術",
            "生成AIでペルソナ作成：理想の顧客像を科学的に分析",
            "Python基礎で美容室データ分析：顧客情報の活用方法",
            "Google Apps Scriptで美容室業務自動化：初心者向けガイド",
            "ノーコード・ローコードツールで美容室DX：Notion・Zapier活用"
        ]
        
        self.recruitment_themes = [
            "行動経済学で理解する美容師の転職心理：優秀な人材を採用する方法",
            "求職者の心を掴む求人広告の書き方：心理学的アプローチ",
            "美容師のモチベーション管理：内発的動機を高める経営術",
            "ジェネレーションZ美容師の特徴と育成方法",
            "離職率を下げるサロン文化の作り方：心理的安全性の重要性"
        ]
        
        self.business_strategy_themes = [
            "美容室の差別化戦略：競合分析と独自性の見つけ方",
            "顧客生涯価値（LTV）を最大化する美容サロン経営術",
            "地域密着型マーケティング：ローカルSEOとMEO対策",
            "美容室のブランディング戦略：心理学的アプローチ",
            "サブスクリプション型美容サービスの可能性と設計方法",
            "カスタマージャーニーで理解する美容室の顧客体験設計",
            "美容室のKPI設計：重要指標の設定と追跡方法"
        ]
        
        self.trend_themes = [
            "2024年美容業界トレンド予測：AI・サステナビリティ・個人化",
            "ジェンダーレス美容の台頭：新しい顧客層への対応戦略",
            "メンズ美容市場の拡大：男性顧客獲得の心理学的アプローチ",
            "高齢化社会と美容業界：シニア向けサービス設計",
            "サステナブル美容：環境意識の高い顧客への対応戦略"
        ]
        
        # 全テーマリスト
        self.all_themes = (
            self.psychology_themes + 
            self.instagram_marketing_themes + 
            self.ai_automation_themes + 
            self.recruitment_themes + 
            self.business_strategy_themes + 
            self.trend_themes
        )
        
        # 重み付け（生成AI・心理学系を優先）
        self.category_weights = {
            'psychology': 0.25,      # 心理学系
            'instagram': 0.20,       # Instagram集客
            'ai': 0.30,             # AI活用（重点）
            'recruitment': 0.10,     # 求人系
            'business': 0.10,        # 経営戦略
            'trend': 0.05           # トレンド
        }
    
    def get_random_theme(self, category=None):
        """ランダムにテーマを選択"""
        try:
            if category:
                # 特定カテゴリから選択
                if category == 'psychology':
                    return random.choice(self.psychology_themes)
                elif category == 'instagram':
                    return random.choice(self.instagram_marketing_themes)
                elif category == 'ai':
                    return random.choice(self.ai_automation_themes)
                elif category == 'recruitment':
                    return random.choice(self.recruitment_themes)
                elif category == 'business':
                    return random.choice(self.business_strategy_themes)
                elif category == 'trend':
                    return random.choice(self.trend_themes)
                else:
                    logger.warning(f"不明なカテゴリ: {category}")
                    return random.choice(self.all_themes)
            else:
                # 重み付きランダム選択
                categories = list(self.category_weights.keys())
                weights = list(self.category_weights.values())
                selected_category = random.choices(categories, weights=weights)[0]
                
                logger.info(f"選択されたカテゴリ: {selected_category}")
                return self.get_random_theme(selected_category)
                
        except Exception as e:
            logger.error(f"テーマ選択エラー: {e}")
            return random.choice(self.all_themes)
    
    def get_weekly_themes(self):
        """1週間分のテーマを生成（バランス考慮）"""
        try:
            weekly_themes = []
            
            # 月曜：心理学・行動経済学
            weekly_themes.append(self.get_random_theme('psychology'))
            
            # 火曜：Instagram・SNS集客
            weekly_themes.append(self.get_random_theme('instagram'))
            
            # 水曜：生成AI活用
            weekly_themes.append(self.get_random_theme('ai'))
            
            # 木曜：経営戦略
            weekly_themes.append(self.get_random_theme('business'))
            
            # 金曜：求人・人材育成
            weekly_themes.append(self.get_random_theme('recruitment'))
            
            # 土曜：生成AI活用（週2回）
            weekly_themes.append(self.get_random_theme('ai'))
            
            # 日曜：トレンド・新技術
            weekly_themes.append(self.get_random_theme('trend'))
            
            return weekly_themes
            
        except Exception as e:
            logger.error(f"週間テーマ生成エラー: {e}")
            return [self.get_random_theme() for _ in range(7)]
    
    def get_monthly_themes(self):
        """1ヶ月分のテーマを生成"""
        try:
            monthly_themes = []
            
            # 4週間分
            for week in range(4):
                weekly_themes = self.get_weekly_themes()
                monthly_themes.extend(weekly_themes)
            
            # 月末調整（28-31日対応）
            while len(monthly_themes) < 31:
                monthly_themes.append(self.get_random_theme())
            
            return monthly_themes[:31]  # 最大31日
            
        except Exception as e:
            logger.error(f"月間テーマ生成エラー: {e}")
            return [self.get_random_theme() for _ in range(31)]
    
    def save_themes_to_file(self, themes, filename):
        """テーマ一覧をファイルに保存"""
        try:
            output_path = Path("output") / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, theme in enumerate(themes, 1):
                    f.write(f"{i:2d}. {theme}\n")
            
            logger.info(f"テーマ一覧を保存: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"ファイル保存エラー: {e}")
            return None

def main():
    """メイン実行関数"""
    try:
        generator = BeautyBusinessThemeGenerator()
        
        # 今日のテーマ
        daily_theme = generator.get_random_theme()
        print(f"本日のテーマ: {daily_theme}")
        
        # 週間テーマ
        weekly_themes = generator.get_weekly_themes()
        generator.save_themes_to_file(weekly_themes, "weekly_themes.txt")
        
        # 月間テーマ
        monthly_themes = generator.get_monthly_themes()
        generator.save_themes_to_file(monthly_themes, "monthly_themes.txt")
        
        logger.info("テーマ生成完了")
        return daily_theme
        
    except Exception as e:
        logger.error(f"メイン処理エラー: {e}")
        return "美容師のためのInstagram集客戦略：心理学的アプローチ"

if __name__ == "__main__":
    main()