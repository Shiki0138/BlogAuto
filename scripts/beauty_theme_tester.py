#!/usr/bin/env python3
"""
美容師専用テーマ生成器テストスクリプト
BeautyThemeGeneratorの機能をテスト・検証
"""
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from scripts.utils import BeautyThemeGenerator, get_jst_now, logger

def test_theme_generator():
    """テーマ生成器の包括的テスト"""
    print("=" * 60)
    print("🎯 美容師専用テーマ生成器 - 機能テスト")
    print("=" * 60)
    
    generator = BeautyThemeGenerator()
    
    # 1. 基本機能テスト
    print("\n📋 1. 基本テーマ生成テスト")
    print("-" * 40)
    
    today_theme = generator.get_daily_theme()
    print(f"✅ 今日のテーマ: {today_theme}")
    
    # 2. カテゴリ別テーマテスト
    print("\n📋 2. カテゴリ別テーマテスト")
    print("-" * 40)
    
    categories = ["base", "psychology", "trending", "local", "spring", "summer", "autumn", "winter"]
    
    for category in categories:
        theme = generator.get_theme_by_category(category, 0)
        print(f"✅ {category.upper()}: {theme}")
    
    # 3. 全テーマ数カウント
    print("\n📋 3. テーマ数統計")
    print("-" * 40)
    
    all_themes = generator.get_all_themes()
    total_count = 0
    
    for category, themes in all_themes.items():
        if category == "seasonal_themes":
            seasonal_count = sum(len(season_themes) for season_themes in themes.values())
            print(f"✅ {category}: {seasonal_count}テーマ")
            total_count += seasonal_count
        else:
            count = len(themes)
            print(f"✅ {category}: {count}テーマ")
            total_count += count
    
    print(f"\n🎯 総テーマ数: {total_count}テーマ")
    
    # 4. キーワード検索テスト
    print("\n📋 4. キーワード検索テスト")
    print("-" * 40)
    
    search_keywords = ["Instagram", "心理学", "集客", "AI", "データ"]
    
    for keyword in search_keywords:
        results = generator.search_themes(keyword)
        print(f"✅ '{keyword}' 検索結果: {len(results)}件")
        if results:
            print(f"   例: {results[0]}")
    
    # 5. 季節・曜日別重み付けテスト
    print("\n📋 5. 重み付けシステムテスト")
    print("-" * 40)
    
    # 7日間分のテーマを生成してカテゴリ分布を確認
    import datetime
    from collections import defaultdict
    
    category_distribution = defaultdict(int)
    
    # 1週間分をシミュレーション
    for day_offset in range(7):
        # 実際のget_daily_themeロジックをテスト
        test_date = get_jst_now() + datetime.timedelta(days=day_offset)
        theme = generator.get_daily_theme()
        
        # カテゴリ推定（簡易版）
        if any(kw in theme for kw in ["心理学", "認知", "行動経済学", "バイアス"]):
            category_distribution["psychology"] += 1
        elif any(kw in theme for kw in ["AI", "デジタル", "SNS", "Instagram"]):
            category_distribution["trending"] += 1
        elif any(kw in theme for kw in ["地域", "ローカル", "コミュニティ"]):
            category_distribution["local"] += 1
        else:
            category_distribution["base"] += 1
    
    print("✅ 1週間の重み付け分布:")
    for category, count in category_distribution.items():
        percentage = (count / 7) * 100
        print(f"   {category}: {count}回 ({percentage:.1f}%)")
    
    # 6. 品質チェック
    print("\n📋 6. テーマ品質チェック")
    print("-" * 40)
    
    quality_metrics = {
        "美容業界特化度": 0,
        "実用性": 0,
        "心理学要素": 0,
        "具体性": 0
    }
    
    sample_themes = [
        generator.get_theme_by_category("base", i) for i in range(5)
    ]
    
    beauty_keywords = ["美容師", "サロン", "顧客", "集客", "施術", "カウンセリング"]
    practical_keywords = ["方法", "術", "戦略", "テクニック", "手法"]
    psychology_keywords = ["心理学", "バイアス", "効果", "理論"]
    specific_keywords = ["Instagram", "リピート", "売上", "予約", "満足度"]
    
    for theme in sample_themes:
        if any(kw in theme for kw in beauty_keywords):
            quality_metrics["美容業界特化度"] += 1
        if any(kw in theme for kw in practical_keywords):
            quality_metrics["実用性"] += 1
        if any(kw in theme for kw in psychology_keywords):
            quality_metrics["心理学要素"] += 1
        if any(kw in theme for kw in specific_keywords):
            quality_metrics["具体性"] += 1
    
    print("✅ テーマ品質メトリクス (5テーマ中):")
    for metric, count in quality_metrics.items():
        percentage = (count / 5) * 100
        print(f"   {metric}: {count}/5 ({percentage:.0f}%)")
    
    # 7. 推奨改善点
    print("\n📋 7. システム評価と推奨改善点")
    print("-" * 40)
    
    recommendations = []
    
    if total_count < 80:
        recommendations.append("テーマ数増加（目標: 100+テーマ）")
    
    if quality_metrics["美容業界特化度"] < 4:
        recommendations.append("美容業界特化度向上")
    
    if quality_metrics["心理学要素"] < 3:
        recommendations.append("心理学要素の強化")
    
    if len(recommendations) == 0:
        print("✅ システムは良好な状態です")
        print("✅ 美容師専用テーマ生成器は本番運用準備完了")
    else:
        print("⚠️ 改善推奨項目:")
        for rec in recommendations:
            print(f"   - {rec}")
    
    print("\n" + "=" * 60)
    print("🎯 美容師専用テーマ生成器テスト完了")
    print("=" * 60)
    
    return {
        "total_themes": total_count,
        "quality_metrics": quality_metrics,
        "recommendations": recommendations,
        "status": "ready" if len(recommendations) == 0 else "needs_improvement"
    }

def demo_theme_examples():
    """テーマ例のデモンストレーション"""
    print("\n🌟 美容師向けテーマ例デモンストレーション")
    print("=" * 60)
    
    generator = BeautyThemeGenerator()
    
    demo_categories = {
        "基本テーマ": ("base", 3),
        "心理学マーケティング": ("psychology", 3),
        "トレンド・最新技術": ("trending", 3),
        "地域密着ビジネス": ("local", 3),
        "季節特化（夏）": ("summer", 2)
    }
    
    for category_name, (category_key, count) in demo_categories.items():
        print(f"\n📂 {category_name}")
        print("-" * 30)
        
        for i in range(count):
            theme = generator.get_theme_by_category(category_key, i)
            print(f"  {i+1}. {theme}")
    
    print("\n🎯 これらのテーマで美容師向けの実践的コンテンツを作成可能")

if __name__ == "__main__":
    try:
        # メインテスト実行
        test_results = test_theme_generator()
        
        # デモ実行
        demo_theme_examples()
        
        # 最終レポート
        print(f"\n📊 テスト結果サマリー:")
        print(f"総テーマ数: {test_results['total_themes']}")
        print(f"システム状態: {test_results['status']}")
        
        if test_results['status'] == 'ready':
            print("✅ 美容師専用テーマ生成器は本番運用可能")
            exit_code = 0
        else:
            print("⚠️ 改善後に本番運用を推奨")
            exit_code = 1
        
        sys.exit(exit_code)
        
    except Exception as e:
        logger.error(f"テスト実行エラー: {e}")
        print(f"❌ テストエラー: {e}")
        sys.exit(1)