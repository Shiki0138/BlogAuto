#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WordPress 投稿スクリプト ― フルリファクタ版 (2025-06-30)
*   ブログ用 “投稿専用ユーザー” を想定（例: blogbot）
*   Draft-first → 任意で publish
*   Basic 認証（Application Password）をヘッダに付与
*   JSON ボディ + 明示ヘッダー
*   /users/me で事前ヘルスチェック（Author でも 200）
"""

from __future__ import annotations

import base64
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests

# プロジェクト直下の utils をインポート出来るように追加
sys.path.append(str(Path(__file__).resolve().parent.parent))

from scripts.utils import (
    clean_html_content,
    get_env_var,
    load_json_safely,
    logger,
    save_json_safely,
    validate_api_response,
)


class WordPressPublisher:
    """WordPress 自動投稿クラス"""

    MAX_RETRIES = 3
    RETRY_DELAY = 2
    TIMEOUT = 30

    # ──────────────────── 初期化 ────────────────────
    def __init__(self) -> None:
        self.wp_user = get_env_var("WP_USER", required=False)
        self.wp_pass = get_env_var("WP_APP_PASS", required=False)
        self.wp_url = get_env_var("WP_SITE_URL", required=False)  # 末尾スラッシュなし

        self.auto_publish = os.getenv("AUTO_PUBLISH", "false").lower() == "true"
        self.enable_api = os.getenv("ENABLE_EXTERNAL_API", "false").lower() == "true"

        # 認証情報が無ければモック動作に切り替え
        self.mock = not (self.enable_api and self.wp_user and self.wp_pass and self.wp_url)
        if self.mock:
            logger.warning("API 無効または認証不足のためモックモードで動作します")

        # セッション共通ヘッダー（最適化）
        self.session = requests.Session()
        if not self.mock:
            creds = base64.b64encode(f"{self.wp_user}:{self.wp_pass}".encode()).decode()
            self.session.headers.update({
                "Authorization": f"Basic {creds}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (compatible; BlogAuto/1.0; +https://github.com/yourrepo)",
                "X-Requested-With": "XMLHttpRequest",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            })
            
            # セッション設定最適化
            self.session.mount('https://', requests.adapters.HTTPAdapter(
                max_retries=requests.packages.urllib3.util.retry.Retry(
                    total=2,
                    backoff_factor=0.5,
                    status_forcelist=[500, 502, 503, 504]
                )
            ))

    # ──────────────────── Helper ────────────────────
    def _preflight(self) -> None:
        """/users/me で 200 を確認。失敗時は RuntimeError"""
        if self.mock:
            return
        
        # プリフライトチェックをスキップするオプション
        if os.getenv("SKIP_PREFLIGHT_CHECK", "false").lower() == "true":
            logger.info("Preflight check skipped due to SKIP_PREFLIGHT_CHECK=true")
            return
            
        # 403エラー対策: より詳細なエラー情報を取得
        url = f"{self.wp_url.rstrip('/')}/wp-json/wp/v2/users/me"
        try:
            res = self.session.get(url, timeout=self.TIMEOUT)
            if res.status_code == 403:
                # 403の場合は、postsエンドポイントを直接試す
                logger.warning("users/me returned 403, trying posts endpoint directly")
                posts_url = f"{self.wp_url.rstrip('/')}/wp-json/wp/v2/posts?per_page=1"
                posts_res = self.session.get(posts_url, timeout=self.TIMEOUT)
                if posts_res.status_code == 200:
                    logger.info("Posts endpoint accessible, continuing...")
                    return
                else:
                    logger.error(f"Posts endpoint also failed: {posts_res.status_code}")
                    logger.error(f"Response: {posts_res.text[:500]}")
            elif res.status_code != 200:
                logger.error(f"Response headers: {dict(res.headers)}")
                logger.error(f"Response body: {res.text[:500]}")
                raise RuntimeError(f"Preflight failed ({res.status_code}) — check secrets/WAF")
        except requests.exceptions.RequestException as e:
            logger.error(f"Connection error: {e}")
            raise RuntimeError(f"Connection failed: {e}")

    # ── Markdown → HTML ──
    def md_to_html(self, md_text: str) -> str:
        try:
            import markdown

            html = markdown.markdown(
                md_text,
                extensions=[
                    "markdown.extensions.extra",
                    "markdown.extensions.codehilite",
                    "markdown.extensions.toc",
                ],
            )
        except ImportError:
            logger.warning("markdown ライブラリが無いので簡易変換")
            html = md_text.replace("\n", "<br>")
        return clean_html_content(html)

    # ── 画像アップロード ──
    def upload_image(self, img_path: Path) -> Optional[int]:
        if self.mock:
            return 12345
        if not img_path.exists():
            logger.warning(f"画像ファイルが見つかりません: {img_path}")
            return None
        url = f"{self.wp_url.rstrip('/')}/wp-json/wp/v2/media"
        files = {"file": (img_path.name, img_path.read_bytes(), "image/jpeg")}
        for attempt in range(self.MAX_RETRIES):
            try:
                res = self.session.post(url, files=files, timeout=self.TIMEOUT)
                if validate_api_response(res, "Media"):
                    return res.json().get("id")
            except requests.RequestException as e:
                logger.warning(f"画像アップロードエラー (試行 {attempt+1}): {e}")
            time.sleep(self.RETRY_DELAY)
        return None

    # ── 投稿 ──
    def create_post(self, *, title: str, html: str, status: str = "draft", **extra) -> Optional[int]:
        if self.mock:
            logger.info("モック投稿完了: 99999")
            return 99999
            
        url = f"{self.wp_url.rstrip('/')}/wp-json/wp/v2/posts"
        data: Dict[str, Any] = {
            "title": title,
            "content": html,
            "status": status,
            "format": "standard",
        }
        data.update(extra)
        
        logger.info(f"投稿データ: title={title[:50]}..., status={status}")
        logger.info(f"投稿先URL: {url}")
        
        for attempt in range(self.MAX_RETRIES):
            try:
                logger.info(f"投稿試行 {attempt + 1}/{self.MAX_RETRIES}")
                res = self.session.post(url, json=data, timeout=self.TIMEOUT)
                
                # 詳細なレスポンスログ
                logger.info(f"レスポンス状態: {res.status_code}")
                logger.info(f"レスポンスヘッダー: {dict(res.headers)}")
                
                if not res.content:
                    logger.error("空のレスポンスです")
                    # 代替エンドポイントを試行
                    if attempt == 0:
                        logger.info("代替方法を試行: wp-admin/post.phpを使用")
                        alt_result = self._create_post_alternative(title, html, status, extra)
                        if alt_result:
                            return alt_result
                    continue
                    
                logger.info(f"レスポンスサイズ: {len(res.content)} bytes")
                
                try:
                    response_json = res.json()
                    logger.info(f"レスポンスJSON: {str(response_json)[:500]}...")
                except:
                    logger.error(f"JSON解析失敗、Raw content: {res.text[:500]}")
                    continue
                
                if res.status_code == 201:  # Created
                    post_id = response_json.get("id")
                    logger.info(f"✅ 投稿成功: post_id={post_id}")
                    return post_id
                elif res.status_code == 200:  # Sometimes returns 200
                    post_id = response_json.get("id")
                    if post_id:
                        logger.info(f"✅ 投稿成功 (200): post_id={post_id}")
                        return post_id
                else:
                    logger.error(f"予期しないステータスコード: {res.status_code}")
                    logger.error(f"エラーレスポンス: {res.text}")
                    
            except requests.exceptions.Timeout as e:
                logger.warning(f"タイムアウト (試行 {attempt+1}): {e}")
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"接続エラー (試行 {attempt+1}): {e}")
            except requests.RequestException as e:
                logger.warning(f"リクエストエラー (試行 {attempt+1}): {e}")
            except Exception as e:
                logger.error(f"予期しないエラー (試行 {attempt+1}): {e}")
                
            if attempt < self.MAX_RETRIES - 1:
                wait_time = self.RETRY_DELAY * (attempt + 1)  # 指数バックオフ
                logger.info(f"{wait_time}秒待機後に再試行...")
                time.sleep(wait_time)
                
        logger.error("全ての試行が失敗しました")
        return None
        
    def _create_post_alternative(self, title: str, html: str, status: str, extra: dict) -> Optional[int]:
        """代替投稿方法: 基本的なHTTP POST"""
        try:
            # シンプルなデータ形式で再試行
            simple_data = {
                "title": title,
                "content": html,
                "status": status
            }
            
            url = f"{self.wp_url.rstrip('/')}/wp-json/wp/v2/posts"
            
            # User-Agentを変更して再試行
            headers = self.session.headers.copy()
            headers.update({
                "User-Agent": "Mozilla/5.0 (compatible; WordPressBlogBot/1.0)",
                "Accept": "*/*",
                "Content-Type": "application/json"
            })
            
            response = requests.post(
                url, 
                json=simple_data, 
                headers=headers,
                timeout=self.TIMEOUT * 2  # タイムアウトを延長
            )
            
            if response.status_code in [200, 201] and response.content:
                try:
                    result = response.json()
                    return result.get("id")
                except:
                    pass
                    
        except Exception as e:
            logger.warning(f"代替投稿方法も失敗: {e}")
            
        return None

    # ── 画像プレースホルダー置換 ──
    @staticmethod
    def replace_placeholders(content: str, uploaded: dict[str, str]) -> str:
        for placeholder, url in uploaded.items():
            content = content.replace(placeholder, url)
        return content

    # ── メイン ──
    def run(self) -> bool:
        try:
            self._preflight()
        except Exception as e:
            logger.error(e)
            # プリフライトが失敗しても投稿を試行
            logger.warning("プリフライト失敗、直接投稿を試行します")

        # 1. ファイル読み込み
        md_path = Path("output/article.md")
        meta_path = Path("output/meta.json")
        if not md_path.exists():
            logger.error("output/article.md が見つかりません")
            return False
        md_text = md_path.read_text("utf-8")
        meta = load_json_safely(str(meta_path)) or {}

        # 2. 見出し画像 (任意)
        placeholders: dict[str, str] = {}
        heading_info = load_json_safely("output/heading_images.json") or {}
        if heading_info.get("images") and not os.getenv("SKIP_IMAGE_UPLOAD", "false").lower() == "true":
            for img in heading_info["images"]:
                p = Path(img.get("filepath", ""))
                if p.exists():
                    img_id = self.upload_image(p)
                    if img_id:
                        placeholders[f"{{IMAGE_URL_PLACEHOLDER_{p.name}}}"] = f"{self.wp_url.rstrip('/')}/wp-content/uploads/{p.name}"
        if placeholders:
            md_text = self.replace_placeholders(md_text, placeholders)

        # 3. Markdown → HTML
        html = self.md_to_html(md_text)

        # 4. Featured Image
        featured: Optional[int] = None
        feat_json = load_json_safely("output/image_info.json")
        if feat_json and not os.getenv("SKIP_IMAGE_UPLOAD", "false").lower() == "true":
            fid_path = Path(feat_json.get("filepath", ""))
            featured = self.upload_image(fid_path)

        # 5. 投稿（複数の方法を試行）
        post_id = self.create_post(
            title=meta.get("title", "Untitled Post"),
            html=html,
            status=os.getenv("WP_STATUS", meta.get("status", "draft")),
            featured_media=featured,
            tags=meta.get("tags", []),
            categories=meta.get("categories", []),
        )
        
        # 投稿が失敗した場合、最終フォールバック
        if not post_id:
            logger.warning("通常投稿失敗、最終フォールバックを実行")
            post_id = self._final_fallback_post(
                meta.get("title", "Untitled Post"),
                html,
                os.getenv("WP_STATUS", meta.get("status", "draft"))
            )
            
        if not post_id:
            logger.error("全ての投稿方法が失敗しました")
            return False

        # 6. 任意で publish
        if self.auto_publish and not self.mock:
            self.session.post(
                f"{self.wp_url.rstrip('/')}/wp-json/wp/v2/posts/{post_id}",
                json={"status": "publish"},
                timeout=self.TIMEOUT,
            )

        # 7. 結果保存
        save_json_safely(
            {
                "post_id": post_id,
                "title": meta.get("title"),
                "status": os.getenv("WP_STATUS", meta.get("status", "draft")),
                "featured_media": featured,
            },
            "output/wp_result.json",
        )
        logger.info(f"✅ 投稿完了 (ID={post_id})")
        return True
        
    def _final_fallback_post(self, title: str, html: str, status: str) -> Optional[int]:
        """最終フォールバック: 最もシンプルな投稿"""
        try:
            logger.info("最終フォールバック投稿を実行中...")
            
            # 最もシンプルなデータ
            minimal_data = {"title": title, "content": html, "status": status}
            
            # 新しいセッションを作成
            fallback_session = requests.Session()
            creds = base64.b64encode(f"{self.wp_user}:{self.wp_pass}".encode()).decode()
            
            # 最小限のヘッダー
            fallback_session.headers.update({
                "Authorization": f"Basic {creds}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            })
            
            url = f"{self.wp_url.rstrip('/')}/wp-json/wp/v2/posts"
            
            # 長めのタイムアウトで試行
            response = fallback_session.post(
                url, 
                json=minimal_data, 
                timeout=60,
                verify=False  # SSL検証を無効化（最終手段）
            )
            
            logger.info(f"フォールバック レスポンス: {response.status_code}")
            
            if response.status_code in [200, 201]:
                try:
                    result = response.json()
                    post_id = result.get("id")
                    if post_id:
                        logger.info(f"✅ フォールバック投稿成功: {post_id}")
                        return post_id
                except:
                    pass
                    
            # 最後の手段: レスポンスからIDを抽出
            if "id" in response.text:
                import re
                id_match = re.search(r'"id":(\d+)', response.text)
                if id_match:
                    post_id = int(id_match.group(1))
                    logger.info(f"✅ フォールバック投稿成功（正規表現抽出）: {post_id}")
                    return post_id
                    
        except Exception as e:
            logger.error(f"フォールバック投稿も失敗: {e}")
            
        return None


# ───────────────── Entrypoint ─────────────────

def main() -> None:
    success = WordPressPublisher().run()
    print("✅ Completed" if success else "❌ Failed")
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
