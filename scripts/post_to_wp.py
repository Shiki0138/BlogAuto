#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WordPress投稿スクリプト - フェーズ3実装
記事をWordPressに投稿する本番レベル実装
"""
import os
import sys
import base64
import requests
from pathlib import Path
from typing import Optional, Dict, Any
import json
import time

# プロジェクトルートをPythonパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from scripts.utils import (
    logger, get_env_var, load_json_safely, 
    clean_html_content, validate_api_response, save_json_safely
)

class WordPressPublisher:
    """WordPress投稿クラス - フェーズ3強化版"""
    
    def __init__(self):
        """初期化"""
        self.wp_user = get_env_var('WP_USER', required=False)
        self.wp_password = get_env_var('WP_APP_PASS', required=False)
        self.wp_site_url = get_env_var('WP_SITE_URL', required=False)
        
        # 外部API接続フラグ確認
        enable_api = os.getenv('ENABLE_EXTERNAL_API', 'false').lower() == 'true'
        
        if not all([self.wp_user, self.wp_password, self.wp_site_url]):
            logger.warning("WordPress認証情報が設定されていません（モック動作）")
            self.mock_mode = True
        elif not enable_api:
            logger.info("WordPress認証情報検出済み（外部API接続無効のためモック動作）")
            self.mock_mode = True
        else:
            logger.info("WordPress認証情報検出済み（本番モード）")
            self.mock_mode = False
        
        self.session = requests.Session()
        
        # リトライ設定
        self.max_retries = 3
        self.retry_delay = 2
        self.timeout = 30
        
        if not self.mock_mode:
            # Basic認証設定
            credentials = f"{self.wp_user}:{self.wp_password}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            self.session.headers.update({
                'Authorization': f'Basic {encoded_credentials}',
                'Content-Type': 'application/json',
                'User-Agent': 'BlogAuto/1.0 (Daily Blog Automation)'
            })
    
    def markdown_to_html(self, markdown_content: str) -> str:
        """MarkdownをHTMLに変換"""
        try:
            import markdown
            
            # Markdown拡張機能
            extensions = [
                'markdown.extensions.extra',
                'markdown.extensions.codehilite',
                'markdown.extensions.toc'
            ]
            
            md = markdown.Markdown(extensions=extensions)
            html_content = md.convert(markdown_content)
            
            # XSS防止のためHTMLコンテンツをクリーン
            clean_content = clean_html_content(html_content)
            
            logger.info("Markdown→HTML変換完了")
            return clean_content
            
        except ImportError:
            logger.warning("markdown ライブラリが見つかりません。簡易変換を使用")
            return self._simple_markdown_to_html(markdown_content)
        except Exception as e:
            logger.error(f"Markdown変換エラー: {e}")
            return markdown_content
    
    def _simple_markdown_to_html(self, content: str) -> str:
        """簡易Markdown→HTML変換"""
        import re
        
        # 見出し変換
        content = re.sub(r'^# (.+)$', r'<h1>\1</h1>', content, flags=re.MULTILINE)
        content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', content, flags=re.MULTILINE)
        content = re.sub(r'^### (.+)$', r'<h3>\1</h3>', content, flags=re.MULTILINE)
        
        # リスト変換
        content = re.sub(r'^\- (.+)$', r'<li>\1</li>', content, flags=re.MULTILINE)
        content = re.sub(r'(<li>.*?</li>)', r'<ul>\1</ul>', content, flags=re.DOTALL)
        
        # 段落変換
        content = content.replace('\n\n', '</p><p>')
        content = f'<p>{content}</p>'
        
        # 不要なタグクリーンアップ
        content = re.sub(r'<p>\s*</p>', '', content)
        content = re.sub(r'</ul>\s*<ul>', '', content)
        
        return content
    
    def upload_image(self, image_path: str) -> Optional[int]:
        """画像をWordPressにアップロード"""
        try:
            if not Path(image_path).exists():
                logger.error(f"画像ファイルが見つかりません: {image_path}")
                return None
            
            if self.mock_mode:
                logger.info(f"画像アップロード（モック）: {image_path}")
                return 12345  # モック画像ID
            
            # WordPress REST API を使用
            url = f"{self.wp_site_url.rstrip('/')}/wp-json/wp/v2/media"
            
            with open(image_path, 'rb') as img_file:
                img_data = img_file.read()
            
            filename = Path(image_path).name
            
            files = {
                'file': (filename, img_data, 'image/jpeg')
            }
            
            # リトライ機能付きアップロード
            for attempt in range(self.max_retries):
                try:
                    response = self.session.post(url, files=files, timeout=self.timeout)
                    
                    if validate_api_response(response, "WordPress Media"):
                        media_data = response.json()
                        media_id = media_data.get('id')
                        logger.info(f"画像アップロード完了: ID={media_id}")
                        return media_id
                    else:
                        logger.warning(f"画像アップロード失敗 (試行 {attempt + 1}/{self.max_retries}): {response.status_code}")
                        
                except requests.RequestException as e:
                    logger.warning(f"画像アップロードエラー (試行 {attempt + 1}/{self.max_retries}): {e}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
            
            logger.error("画像アップロードが最大試行回数で失敗")
            return None
                
        except Exception as e:
            logger.error(f"画像アップロード処理エラー: {e}")
            return None
    
    def create_post(self, title: str, content: str, 
                   featured_image_id: Optional[int] = None,
                   tags: list = None, categories: list = None,
                   status: str = "draft") -> Optional[int]:
        """WordPress記事投稿"""
        try:
            if self.mock_mode:
                logger.info(f"記事投稿（モック）: {title}")
                logger.info(f"記事状態: {status}")
                logger.info(f"文字数: {len(content)} 文字")
                return 67890  # モック記事ID
            
            url = f"{self.wp_site_url.rstrip('/')}/wp-json/wp/v2/posts"
            
            post_data = {
                "title": title,
                "content": content,
                "status": status,
                "format": "standard"
            }
            
            if featured_image_id:
                post_data["featured_media"] = featured_image_id
            
            if tags:
                post_data["tags"] = tags
            
            if categories:
                post_data["categories"] = categories
            
            # リトライ機能付き投稿
            for attempt in range(self.max_retries):
                try:
                    response = self.session.post(url, json=post_data, timeout=self.timeout)
                    
                    if validate_api_response(response, "WordPress Posts"):
                        post_info = response.json()
                        post_id = post_info.get('id')
                        post_url = post_info.get('link', '')
                        
                        logger.info(f"記事投稿完了: ID={post_id}, URL={post_url}")
                        return post_id
                    else:
                        logger.warning(f"記事投稿失敗 (試行 {attempt + 1}/{self.max_retries}): {response.status_code}")
                        
                except requests.RequestException as e:
                    logger.warning(f"記事投稿エラー (試行 {attempt + 1}/{self.max_retries}): {e}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
            
            logger.error("記事投稿が最大試行回数で失敗")
            return None
                
        except Exception as e:
            logger.error(f"記事投稿処理エラー: {e}")
            return None
    
    def add_image_credit(self, content: str, credit: str) -> str:
        """画像クレジットを本文に追加"""
        if not credit:
            return content
        
        credit_html = f"""
<figure class="image-credit">
    <figcaption style="text-align: center; font-size: 0.9em; color: #666; margin-top: 1em;">
        {credit}
    </figcaption>
</figure>
"""
        return content + credit_html
    
    def validate_content(self, content: str, title: str) -> bool:
        """コンテンツ品質検証"""
        try:
            # 基本検証
            if not title or len(title.strip()) < 5:
                logger.error("タイトルが短すぎます")
                return False
            
            if not content or len(content.strip()) < 100:
                logger.error("コンテンツが短すぎます")
                return False
            
            # 文字数確認
            content_length = len(content)
            if content_length > 50000:
                logger.warning(f"コンテンツが長すぎます: {content_length} 文字")
            
            # HTMLタグ検証
            if '<script' in content.lower():
                logger.error("危険なスクリプトタグが検出されました")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"コンテンツ検証エラー: {e}")
            return False
    
    def run(self) -> bool:
        """WordPress投稿メイン処理"""
        try:
            logger.info("WordPress投稿処理開始")
            
            # ファイル確認
            article_path = Path("output/article.md")
            meta_path = Path("output/meta.json")
            
            if not article_path.exists():
                logger.error("記事ファイルが見つかりません")
                return False
            
            # 記事読み込み
            markdown_content = article_path.read_text(encoding='utf-8')
            
            # 内部リンク生成と挿入
            try:
                from scripts.internal_linking import InternalLinkingEngine
                
                # メタデータから記事タイトルを取得
                metadata = load_json_safely(str(meta_path)) or {}
                title = metadata.get('title', '無題記事')
                
                # 内部リンクエンジンを初期化
                linking_engine = InternalLinkingEngine()
                
                # 内部リンクを生成して記事に挿入
                markdown_content, link_result = linking_engine.update_post_with_links(
                    title=title,
                    content=markdown_content,
                    wp_url=f"{self.wp_site_url}/posts/{title.replace(' ', '-').lower()}" if not self.mock_mode else None
                )
                
                logger.info(f"🔗 内部リンク処理完了: {link_result.get('links_inserted', 0)}個のリンクを挿入")
                
            except ImportError:
                logger.warning("内部リンクエンジンが利用できません")
            except Exception as e:
                logger.warning(f"内部リンク処理エラー: {e}")
            
            html_content = self.markdown_to_html(markdown_content)
            
            # メタデータ読み込み
            metadata = load_json_safely(str(meta_path)) or {}
            title = metadata.get('title', '無題記事')
            tags = metadata.get('tags', [])
            categories = metadata.get('categories', [])
            status = os.getenv('WP_STATUS', metadata.get('status', 'draft'))
            
            # コンテンツ検証
            if not self.validate_content(html_content, title):
                logger.error("コンテンツ品質検証に失敗")
                return False
            
            # 画像情報取得
            image_info_path = Path("output/image_info.json")
            image_info = load_json_safely(str(image_info_path))
            
            featured_image_id = None
            skip_image = os.getenv('SKIP_IMAGE_UPLOAD', 'false').lower() == 'true'
            
            if image_info and not skip_image:
                image_path = image_info.get('filepath')
                if image_path and Path(image_path).exists():
                    try:
                        featured_image_id = self.upload_image(image_path)
                        if not featured_image_id:
                            logger.warning("画像アップロードに失敗しました。画像なしで投稿を続行します")
                    except Exception as e:
                        logger.warning(f"画像アップロードエラー: {e}. 画像なしで投稿を続行します")
                
                # 画像クレジット追加（画像アップロード失敗時でもクレジットは表示）
                credit = image_info.get('credit', '')
                if credit and featured_image_id:  # 画像が正常にアップロードされた場合のみクレジット追加
                    html_content = self.add_image_credit(html_content, credit)
            elif skip_image:
                logger.info("画像アップロードをスキップします（SKIP_IMAGE_UPLOAD=true）")
            
            # 記事投稿
            post_id = self.create_post(
                title=title,
                content=html_content,
                featured_image_id=featured_image_id,
                tags=tags,
                categories=categories,
                status=status
            )
            
            if post_id:
                # 結果保存
                result = {
                    "post_id": post_id,
                    "title": title,
                    "status": status,
                    "featured_image_id": featured_image_id,
                    "published_at": time.time() if status == "publish" else None,
                    "word_count": len(html_content),
                    "tags": tags,
                    "categories": categories,
                    "mock_mode": self.mock_mode
                }
                
                save_json_safely(result, "output/wp_result.json")
                
                logger.info(f"✅ WordPress投稿完了: ID={post_id}")
                logger.info(f"📊 状態: {status}")
                logger.info(f"📈 文字数: {result['word_count']} 文字")
                return True
            else:
                logger.error("WordPress投稿に失敗しました")
                return False
                
        except Exception as e:
            logger.error(f"WordPress投稿処理でエラーが発生: {e}")
            return False

def main():
    """メイン実行関数"""
    try:
        publisher = WordPressPublisher()
        success = publisher.run()
        
        if success:
            print("✅ WordPress投稿処理が完了しました")
            sys.exit(0)
        else:
            print("❌ WordPress投稿に失敗しました")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"メイン処理でエラーが発生: {e}")
        print(f"❌ エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()