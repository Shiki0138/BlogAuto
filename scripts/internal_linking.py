#!/usr/bin/env python3
"""
内部リンク自動生成システム
関連記事の自動検索とリンク挿入機能
"""
import os
import sys
import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from difflib import SequenceMatcher
from urllib.parse import quote

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

try:
    from scripts.utils import logger, save_json_safely, load_json_safely
    from scripts.post_to_wp import WordPressPublisher
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

class InternalLinkingEngine:
    """内部リンク自動生成エンジン"""
    
    def __init__(self):
        """初期化"""
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
        # WordPress投稿履歴ファイル
        self.post_history_file = self.output_dir / "post_history.json"
        
        # 関連度スコアの閾値
        self.similarity_threshold = 0.3
        self.max_internal_links = 5
        
        # 除外キーワード（汎用的すぎるもの）
        self.exclude_keywords = {
            'について', 'ための', 'による', 'こと', 'もの', 'どの', 'その', 'この', 
            'あの', 'という', 'する', 'なる', 'ある', 'いる', 'です', 'ます'
        }
        
        logger.info("InternalLinkingEngine initialized")
    
    def extract_keywords(self, content: str, title: str = "") -> List[str]:
        """記事からキーワードを抽出"""
        try:
            # タイトルからキーワード抽出（重要度高）
            title_keywords = []
            if title:
                # タイトルを単語に分割
                title_words = re.findall(r'[ぁ-んァ-ヶー一-龯]{2,}', title)
                title_keywords = [word for word in title_words if len(word) >= 2 and word not in self.exclude_keywords]
            
            # 本文からキーワード抽出
            content_keywords = []
            
            # 見出しからキーワード抽出（重要度中）
            headings = re.findall(r'^#+\s*(.+)$', content, re.MULTILINE)
            for heading in headings:
                heading_words = re.findall(r'[ぁ-んァ-ヶー一-龯]{2,}', heading)
                content_keywords.extend([word for word in heading_words if len(word) >= 2 and word not in self.exclude_keywords])
            
            # 本文から頻出キーワード抽出
            text_words = re.findall(r'[ぁ-んァ-ヶー一-龯]{2,}', content)
            word_freq = {}
            for word in text_words:
                if len(word) >= 2 and word not in self.exclude_keywords:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # 頻度順でソート（上位20個）
            frequent_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]
            content_keywords.extend([word for word, freq in frequent_words if freq >= 2])
            
            # タイトルキーワードを優先して結合
            all_keywords = title_keywords + [kw for kw in content_keywords if kw not in title_keywords]
            
            return all_keywords[:30]  # 最大30個のキーワード
            
        except Exception as e:
            logger.error(f"キーワード抽出エラー: {e}")
            return []
    
    def calculate_similarity(self, keywords1: List[str], keywords2: List[str]) -> float:
        """2つの記事間の類似度を計算"""
        try:
            if not keywords1 or not keywords2:
                return 0.0
            
            # 共通キーワード数による基本スコア
            common_keywords = set(keywords1) & set(keywords2)
            common_count = len(common_keywords)
            
            if common_count == 0:
                return 0.0
            
            # Jaccard係数ベースの類似度
            union_count = len(set(keywords1) | set(keywords2))
            jaccard_score = common_count / union_count if union_count > 0 else 0
            
            # キーワードの重要度重み付け（タイトルキーワードを重視）
            title_keyword_bonus = 0
            for keyword in common_keywords:
                if keyword in keywords1[:5] or keyword in keywords2[:5]:  # 上位5個をタイトルキーワードとみなす
                    title_keyword_bonus += 0.2
            
            final_score = min(jaccard_score + title_keyword_bonus, 1.0)
            return final_score
            
        except Exception as e:
            logger.error(f"類似度計算エラー: {e}")
            return 0.0
    
    def load_post_history(self) -> List[Dict[str, Any]]:
        """投稿履歴を読み込み"""
        try:
            if self.post_history_file.exists():
                return load_json_safely(str(self.post_history_file)) or []
            return []
        except Exception as e:
            logger.error(f"投稿履歴読み込みエラー: {e}")
            return []
    
    def save_post_history(self, history: List[Dict[str, Any]]):
        """投稿履歴を保存"""
        try:
            save_json_safely(history, str(self.post_history_file))
            logger.info(f"投稿履歴保存完了: {len(history)}件")
        except Exception as e:
            logger.error(f"投稿履歴保存エラー: {e}")
    
    def add_post_to_history(self, title: str, content: str, url: str, post_id: str = None):
        """新しい投稿を履歴に追加"""
        try:
            history = self.load_post_history()
            
            # キーワード抽出
            keywords = self.extract_keywords(content, title)
            
            new_post = {
                "title": title,
                "url": url,
                "post_id": post_id,
                "keywords": keywords,
                "created_at": datetime.now().isoformat(),
                "content_length": len(content)
            }
            
            history.append(new_post)
            
            # 履歴が多すぎる場合は古いものを削除（最大100件）
            if len(history) > 100:
                history = history[-100:]
            
            self.save_post_history(history)
            logger.info(f"投稿履歴に追加: {title}")
            
        except Exception as e:
            logger.error(f"投稿履歴追加エラー: {e}")
    
    def find_related_articles(self, current_title: str, current_content: str, 
                            max_results: int = None) -> List[Dict[str, Any]]:
        """関連記事を検索"""
        try:
            max_results = max_results or self.max_internal_links
            
            # 現在の記事のキーワード抽出
            current_keywords = self.extract_keywords(current_content, current_title)
            
            if not current_keywords:
                logger.warning("現在の記事からキーワードを抽出できませんでした")
                return []
            
            # 投稿履歴を読み込み
            history = self.load_post_history()
            
            if not history:
                logger.info("投稿履歴が空です")
                return []
            
            # 各記事との類似度を計算
            similarities = []
            for post in history:
                similarity = self.calculate_similarity(current_keywords, post.get('keywords', []))
                
                if similarity >= self.similarity_threshold:
                    similarities.append({
                        "title": post['title'],
                        "url": post['url'],
                        "similarity": similarity,
                        "keywords": post.get('keywords', []),
                        "created_at": post.get('created_at', '')
                    })
            
            # 類似度でソート（降順）
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            logger.info(f"関連記事検索完了: {len(similarities)}件見つかりました")
            return similarities[:max_results]
            
        except Exception as e:
            logger.error(f"関連記事検索エラー: {e}")
            return []
    
    def insert_internal_links(self, content: str, related_articles: List[Dict[str, Any]]) -> str:
        """記事に内部リンクを挿入"""
        try:
            if not related_articles:
                logger.info("関連記事がないため、リンク挿入をスキップします")
                return content
            
            modified_content = content
            links_inserted = 0
            
            for article in related_articles:
                if links_inserted >= self.max_internal_links:
                    break
                
                title = article['title']
                url = article['url']
                keywords = article.get('keywords', [])
                
                # 記事のキーワードに基づいてリンク挿入位置を検索
                for keyword in keywords[:5]:  # 上位5個のキーワードのみ使用
                    if keyword in modified_content and links_inserted < self.max_internal_links:
                        # 既にリンクが設定されていないかチェック
                        link_pattern = rf'\[([^\]]*{re.escape(keyword)}[^\]]*)\]\([^\)]+\)'
                        if not re.search(link_pattern, modified_content):
                            # キーワードを内部リンクに置換（最初の出現のみ）
                            link_text = f"[{keyword}]({url})"
                            modified_content = re.sub(
                                rf'\b{re.escape(keyword)}\b',
                                link_text,
                                modified_content,
                                count=1
                            )
                            links_inserted += 1
                            logger.info(f"内部リンク挿入: {keyword} -> {title}")
                            break
            
            # 関連記事セクションを記事末尾に追加
            if related_articles and links_inserted > 0:
                related_section = "\n\n## 関連記事\n\n"
                for article in related_articles[:3]:  # 最大3つの関連記事を表示
                    related_section += f"- [{article['title']}]({article['url']})\n"
                
                modified_content += related_section
            
            logger.info(f"内部リンク挿入完了: {links_inserted}個のリンクを挿入")
            return modified_content
            
        except Exception as e:
            logger.error(f"内部リンク挿入エラー: {e}")
            return content
    
    def generate_internal_links(self, title: str, content: str, wp_url: str = None) -> Tuple[str, Dict[str, Any]]:
        """内部リンクを生成して記事に挿入"""
        try:
            logger.info("🔗 内部リンク自動生成開始")
            
            # 関連記事を検索
            related_articles = self.find_related_articles(title, content)
            
            # 内部リンクを挿入
            modified_content = self.insert_internal_links(content, related_articles)
            
            # 結果をまとめ
            result = {
                "related_articles_found": len(related_articles),
                "links_inserted": len(re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', modified_content)) - len(re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', content)),
                "related_articles": related_articles,
                "generated_at": datetime.now().isoformat()
            }
            
            # 結果をファイルに保存
            result_file = self.output_dir / "internal_links_result.json"
            save_json_safely(result, str(result_file))
            
            logger.info(f"✅ 内部リンク生成完了: {result['links_inserted']}個のリンクを挿入")
            
            return modified_content, result
            
        except Exception as e:
            logger.error(f"内部リンク生成エラー: {e}")
            return content, {"error": str(e)}
    
    def update_post_with_links(self, title: str, content: str, wp_url: str = None) -> Tuple[str, Dict[str, Any]]:
        """記事を内部リンク付きで更新し、履歴に追加"""
        try:
            # 内部リンクを生成
            modified_content, result = self.generate_internal_links(title, content, wp_url)
            
            # 投稿履歴に追加（将来の関連記事検索用）
            if wp_url:
                self.add_post_to_history(title, content, wp_url)
            
            return modified_content, result
            
        except Exception as e:
            logger.error(f"投稿更新エラー: {e}")
            return content, {"error": str(e)}

def main():
    """メイン実行関数"""
    try:
        engine = InternalLinkingEngine()
        
        # テスト用のサンプル記事
        test_title = "効果的な時間管理術について"
        test_content = """# 効果的な時間管理術について

## はじめに

現代社会において、時間管理は非常に重要なスキルです。効率的な時間管理により、生産性を向上させ、ストレスを軽減できます。

## 時間管理の基本原則

### 優先順位の設定
- 重要度と緊急度の4象限
- Eisenhowerマトリクス
- GTD（Getting Things Done）

### スケジュール管理
- カレンダーアプリの活用
- タイムブロッキング
- バッファ時間の確保

## まとめ

時間管理は継続的な改善が必要です。自分に合った方法を見つけて、日々実践していきましょう。
"""
        
        # 内部リンク生成テスト
        modified_content, result = engine.generate_internal_links(test_title, test_content)
        
        print("🔗 内部リンク生成テスト完了")
        print(f"関連記事数: {result['related_articles_found']}")
        print(f"挿入リンク数: {result['links_inserted']}")
        
        # 履歴にテスト投稿を追加
        engine.add_post_to_history(
            test_title, 
            test_content, 
            "https://example.com/time-management"
        )
        
        print("✅ 内部リンクシステムの動作確認完了")
        
    except Exception as e:
        logger.error(f"メイン実行エラー: {e}")
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    main()