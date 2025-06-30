#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WordPress 投稿スクリプト ― フルリファクタ版 (2025-06-30)
・ブログ用“投稿専用ユーザー”を想定（例: blogbot）
・REST API Draft-First → Optional Publish
・Basic 認証（Application Password）をヘッダに付与
・JSON ボディ + 明示ヘッダ
・事前ヘルスチェックで 401/403 を即検知
"""

from __future__ import annotations

import os
import sys
import time
import base64
import json
from pathlib import Path
from typing import Any, Dict, Optional

import requests

# ルート参照用にパス追加（utils.py がプロジェクト直下にある想定）
sys.path.append(str(Path(__file__).resolve().parent.parent))

from scripts.utils import (
    logger,
    get_env_var,
    load_json_safely,
    save_json_safely,
    clean_html_content,
    validate_api_response,
)


class WordPressPublisher:
    """WordPress 自動投稿クラス"""

    MAX_RETRIES = 3
    RETRY_DELAY = 2
    TIMEOUT = 30

    def __init__(self) -> None:
        # ───────────────────────────────────────────
        # 環境変数読み込み
        #   ※ GitHub / Vercel の Secrets と合わせる
        # ───────────────────────────────────────────
        self.wp_user = get_env_var("WP_USERNAME", required=False)
        self.wp_pass = get_env_var("WP_APP_PASSWORD", required=False)
        self.wp_url = get_env_var("WP_BASE_URL", required=False)  # 末尾スラッシュ不要

        self.auto_publish = os.getenv("AUTO_PUBLISH", "false").lower() == "true"
        self.enable_api = os.getenv("ENABLE_EXTERNAL_API", "false").lower() == "true"

        # モック判定
        if not self.enable_api or not all([self.wp_user, self.wp_pass, self.wp_url]):
            logger.warning("API 無効または認証情報不足のためモックモードで動作します")
            self.mock = True
        else:
            self.mock = False

        # セッションセットアップ
        self.session = requests.Session()
        if not self.mock:
            creds = f"{self.wp_user}:{self.wp_pass}"
            basic = base64.b64encode(creds.encode()).decode()
            self.session.headers.update(
                {
                    "Authorization": f"Basic {basic}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "BlogAuto/1.0 (+https://github.com/yourrepo)",
                }
            )

    # ───────────────────────── Helper ──────────────────────────
    def _preflight(self) -> None:
        """GET /posts で 200 を確認。失敗時は例外"""
        if self.mock:
            return
        url = f"{self.wp_url.rstrip('/')}/wp-json/wp/v2/posts?per_page=1"
        r = self.session.get(url, timeout=self.TIMEOUT)
        if r.status_code != 200:
            raise RuntimeError(
                f"Preflight REST check failed ({r.status_code}) — Secrets/WAF を確認してください"
            )

    # ───────────────────── Markdown → HTML ─────────────────────
    def replace_image_placeholders(self, content: str, uploaded_images: dict) -> str:
        """画像プレースホルダーを実際のURLに置換"""
        for placeholder, url in uploaded_images.items():
            content = content.replace(placeholder, url)
        return content
    
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
            logger.warning("markdown ライブラリが無いため簡易変換にフォールバック")
            html = md_text.replace("\n", "<br>")
        # XSS サニタイズ
        return clean_html_content(html)

    # ───────────────────── 画像アップロード ─────────────────────
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

    # ───────────────────── 投稿 ─────────────────────
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
        for attempt in range(self.MAX_RETRIES):
            try:
                res = self.session.post(url, json=data, timeout=self.TIMEOUT)
                if validate_api_response(res, "Posts"):
                    post = res.json()
                    return post.get("id")
            except requests.RequestException as e:
                logger.warning(f"投稿エラー (試行 {attempt+1}): {e}")
            time.sleep(self.RETRY_DELAY)
        return None

    # ───────────────────── Main Run ─────────────────────
    def run(self) -> bool:
        # 0. Preflight
        try:
            self._preflight()
        except Exception as e:
            logger.error(e)
            return False

        # 1. ファイル存在確認
        md_path = Path("output/article.md")
        meta_path = Path("output/meta.json")
        if not md_path.exists():
            logger.error("output/article.md が見つかりません")
            return False

        md_text = md_path.read_text("utf-8")
        
        # 見出し画像情報を読み込み
        heading_images_info = load_json_safely("output/heading_images.json") or {}
        uploaded_images = {}
        
        # 見出し画像をアップロード（オプション）
        if heading_images_info.get('images') and not self.mock:
            for idx, img_info in enumerate(heading_images_info['images']):
                if img_info.get('filepath'):
                    img_path = Path(img_info['filepath'])
                    if img_path.exists():
                        img_id = self.upload_image(img_path)
                        if img_id:
                            # プレースホルダーとURLのマッピングを作成
                            placeholder = f"{{IMAGE_URL_PLACEHOLDER_{img_path.name}}}"
                            img_url = f"{self.wp_url.rstrip('/')}/wp-content/uploads/{img_path.name}"
                            uploaded_images[placeholder] = img_url
        
        # プレースホルダーを実際のURLに置換
        if uploaded_images:
            md_text = self.replace_image_placeholders(md_text, uploaded_images)
        
        html = self.md_to_html(md_text)
        meta = load_json_safely(str(meta_path)) or {}

        title = meta.get("title", "Untitled Post")
        tags = meta.get("tags", [])
        cats = meta.get("categories", [])
        status = os.getenv("WP_STATUS", meta.get("status", "draft"))

        # 2. Featured Image
        featured_id: Optional[int] = None
        img_json = load_json_safely("output/image_info.json")
        if img_json and not os.getenv("SKIP_IMAGE_UPLOAD", "false").lower() == "true":
            img_path = Path(img_json.get("filepath", ""))
            featured_id = self.upload_image(img_path)

        # 3. Post
        post_id = self.create_post(
            title=title,
            html=html,
            status=status,
            featured_media=featured_id,
            tags=tags,
            categories=cats,
        )
        if not post_id:
            logger.error("WordPress 投稿に失敗しました")
            return False

        # 4. Optional publish
        if status == "draft" and self.auto_publish and not self.mock:
            self.session.post(
                f"{self.wp_url.rstrip('/')}/wp-json/wp/v2/posts/{post_id}",
                json={"status": "publish"},
                timeout=self.TIMEOUT,
            )

        # 5. 結果保存
        save_json_safely(
            {
                "post_id": post_id,
                "title": title,
                "status": status,
                "featured_media": featured_id,
            },
            "output/wp_result.json",
        )
        logger.info(f"✅ 投稿完了 (ID={post_id})")
        return True


# ────────────────────────── Entrypoint ──────────────────────────

def main():
    publisher = WordPressPublisher()
    success = publisher.run()
    print("✅ Completed" if success else "❌ Failed")
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
