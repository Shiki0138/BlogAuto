#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
見出し画像挿入スクリプト
各見出し（最後の見出しを除く）の直下に画像を挿入
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple
import json

sys.path.append(str(Path(__file__).resolve().parent.parent))

from scripts.utils import logger, load_json_safely, save_json_safely
from scripts.fetch_image import ImageFetcher


class HeadingImageInserter:
    """見出しごとに画像を挿入するクラス"""
    
    def __init__(self):
        self.output_dir = Path("output")
        self.image_fetcher = ImageFetcher()
        
    def extract_headings(self, content: str) -> List[Tuple[int, str, str]]:
        """記事から見出しを抽出
        Returns: [(行番号, 見出しレベル, 見出しテキスト), ...]
        """
        headings = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # Markdown見出しを検出（## のみ）
            match = re.match(r'^(#{2})\s+(.+)$', line)
            if match:
                level = match.group(1)
                text = match.group(2)
                headings.append((i, level, text))
                
        return headings
    
    def generate_image_query(self, heading_text: str, article_theme: str) -> str:
        """見出しテキストから画像検索クエリを生成"""
        # 美容技術関連のキーワードマッピング
        keyword_map = {
            # ヘアスタイル関連
            "ヘアアレンジ": "hair arrangement hairstyle updo",
            "夏祭り": "summer festival hairstyle yukata hair",
            "海水浴": "beach hairstyle summer hair waterproof",
            "浴衣": "yukata hairstyle japanese traditional",
            "編み込み": "braided hairstyle braid hair",
            "アップ": "updo hairstyle elegant hair",
            "ボブ": "bob hairstyle short hair",
            "カラー": "hair color dyeing salon",
            "パーマ": "perm hairstyle curly hair",
            "トリートメント": "hair treatment salon care",
            "ヘアケア": "hair care treatment salon",
            
            # 季節・イベント関連
            "春": "spring hairstyle fresh flowers",
            "夏": "summer hairstyle beach festival",
            "秋": "autumn hairstyle fall colors",
            "冬": "winter hairstyle cozy elegant",
            "成人式": "coming of age ceremony hairstyle",
            "結婚式": "wedding hairstyle bridal hair",
            "卒業式": "graduation ceremony hairstyle",
            
            # ビジネス関連
            "心理学": "salon customer psychology service",
            "Instagram": "instagram beauty salon social media",
            "顧客": "salon customer service beauty",
            "集客": "salon marketing business strategy",
            "技術": "hairstyling technique professional",
            "トレンド": "hair trend 2024 modern style",
            "事例": "hair salon success story",
            "価格": "salon pricing menu beauty"
        }
        
        # デフォルトクエリを技術的なものに
        query = "professional hairstylist salon work"
        
        # 最も関連性の高いキーワードを探す
        for keyword, eng_query in keyword_map.items():
            if keyword in heading_text:
                query = eng_query
                # 複数のキーワードがマッチする場合は組み合わせる
                for other_keyword, other_query in keyword_map.items():
                    if other_keyword != keyword and other_keyword in heading_text:
                        query = f"{eng_query} {other_query.split()[0]}"
                        break
                break
        
        # テーマに基づく追加（より具体的に）
        if "ヘアアレンジ" in article_theme:
            if "夏" in article_theme or "海" in article_theme:
                query += " summer beach waterproof"
            elif "祭" in article_theme:
                query += " festival traditional japanese"
        elif "カラー" in article_theme:
            query += " hair color chart salon"
        elif "AI" in article_theme or "テクノロジー" in article_theme:
            query += " technology digital innovation"
            
        return query
    
    def fetch_image_for_heading(self, heading_text: str, article_theme: str, index: int) -> dict:
        """見出し用の画像を取得"""
        query = self.generate_image_query(heading_text, article_theme)
        logger.info(f"🔍 Fetching image for heading {index}: {query}")
        
        # 既存の画像取得メソッドを使用（優先順位に従ってフォールバック）
        result = None
        
        # 各APIを試行
        for api_name, fetch_method in [
            ('unsplash', self.image_fetcher.fetch_unsplash_image),
            ('pexels', self.image_fetcher.fetch_pexels_image)
        ]:
            try:
                result = fetch_method(query)
                if result:
                    # 画像を保存
                    filename = f"heading_{index}.jpg"
                    if 'url' in result and self.image_fetcher.download_image(result['url'], filename):
                        result['filepath'] = str(self.output_dir / filename)
                        result['alt_text'] = f"{heading_text}のイメージ画像"
                        break
            except Exception as e:
                logger.warning(f"Failed to fetch from {api_name}: {e}")
        
        # フォールバック画像
        if not result:
            result = {
                'filepath': None,
                'credit': 'Image unavailable',
                'alt_text': f"{heading_text}のイメージ画像",
                'source': 'fallback'
            }
            
        return result
    
    def create_image_html(self, image_info: dict) -> str:
        """画像情報からHTMLを生成"""
        if not image_info.get('filepath'):
            return ""
            
        alt_text = image_info.get('alt_text', '記事イメージ画像')
        credit = image_info.get('credit', '')
        
        # WordPressのブロックエディタ形式
        html = f"""
<!-- wp:image {{"sizeSlug":"large","align":"center"}} -->
<figure class="wp-block-image aligncenter size-large">
    <img src="{{IMAGE_URL_PLACEHOLDER_{image_info.get('filepath', '').split('/')[-1]}}}" alt="{alt_text}" />
"""
        
        if credit:
            html += f'    <figcaption class="wp-element-caption">{credit}</figcaption>\n'
            
        html += '</figure>\n<!-- /wp:image -->\n'
        
        return html
    
    def insert_heading_images(self, content: str) -> Tuple[str, List[dict]]:
        """記事の各見出しに画像を挿入
        Returns: (更新された記事内容, 画像情報リスト)
        """
        # メタデータから記事テーマを取得
        meta = load_json_safely(str(self.output_dir / "meta.json")) or {}
        article_theme = meta.get('theme', '')
        
        # 見出しを抽出
        headings = self.extract_headings(content)
        
        if len(headings) <= 1:
            logger.info("見出しが1つ以下のため、画像挿入をスキップします")
            return content, []
        
        # 最後の見出しを除外
        headings_to_process = headings[:-1]
        logger.info(f"📸 {len(headings_to_process)}個の見出しに画像を挿入します")
        
        # 画像情報を収集
        image_infos = []
        lines = content.split('\n')
        offset = 0
        
        for idx, (line_num, level, heading_text) in enumerate(headings_to_process):
            # 画像を取得
            image_info = self.fetch_image_for_heading(heading_text, article_theme, idx + 1)
            image_infos.append(image_info)
            
            # 画像HTMLを生成
            image_html = self.create_image_html(image_info)
            
            if image_html:
                # 見出しの次の行に画像を挿入
                insert_line = line_num + offset + 1
                
                # 空行を追加してから画像を挿入
                lines.insert(insert_line, "")
                lines.insert(insert_line + 1, image_html.rstrip())
                lines.insert(insert_line + 2, "")
                
                offset += 3  # 挿入した行数分オフセットを更新
                
                logger.info(f"✅ 画像を挿入: {heading_text}")
        
        # 更新された内容を結合
        updated_content = '\n'.join(lines)
        
        return updated_content, image_infos
    
    def run(self) -> bool:
        """メイン処理"""
        try:
            # 記事ファイルを読み込み
            article_path = self.output_dir / "article.md"
            if not article_path.exists():
                logger.error("記事ファイルが見つかりません")
                return False
                
            content = article_path.read_text(encoding='utf-8')
            
            # 環境変数で機能の有効/無効を制御
            import os
            if os.getenv('ENABLE_HEADING_IMAGES', 'true').lower() != 'true':
                logger.info("見出し画像挿入機能が無効になっています")
                return True
            
            # 見出しに画像を挿入
            updated_content, image_infos = self.insert_heading_images(content)
            
            # 更新された記事を保存
            article_path.write_text(updated_content, encoding='utf-8')
            
            # 画像情報を保存
            heading_images_path = self.output_dir / "heading_images.json"
            save_json_safely({
                'images': image_infos,
                'total_count': len(image_infos)
            }, str(heading_images_path))
            
            logger.info(f"✅ 見出し画像挿入完了: {len(image_infos)}個の画像を追加")
            return True
            
        except Exception as e:
            logger.error(f"見出し画像挿入エラー: {e}")
            return False


def main():
    """エントリーポイント"""
    inserter = HeadingImageInserter()
    success = inserter.run()
    
    if success:
        print("✅ Heading images inserted successfully")
    else:
        print("❌ Failed to insert heading images")
        
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()