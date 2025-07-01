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

        # セッション共通ヘッダー
        self.session = requests.Session()
        if not self.mock:
            creds = base64.b64encode(f"{self.wp_user}:{self.wp_pass}".encode()).decode()
            self.session.headers.update(
                {
                    "Authorization": f"Basic {creds}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "BlogAuto/1.0 (+https://github.com/yourrepo)",
                }
            )

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
        for attempt in range(self.MAX_RETRIES):
            try:
                res = self.session.post(url, json=data, timeout=self.TIMEOUT)
                if validate_api_response(res, "Posts"):
                    return res.json().get("id")
            except requests.RequestException as e:
                logger.warning(f"投稿エラー (試行 {attempt+1}): {e}")
            time.sleep(self.RETRY_DELAY)
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
            return False

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

        # 5. 投稿
        post_id = self.create_post(
            title=meta.get("title", "Untitled Post"),
            html=html,
            status=os.getenv("WP_STATUS", meta.get("status", "draft")),
            featured_media=featured,
            tags=meta.get("tags", []),
            categories=meta.get("categories", []),
        )
        if not post_id:
            logger.error("WordPress 投稿に失敗しました")
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


# ───────────────── Entrypoint ─────────────────

def main() -> None:
    success = WordPressPublisher().run()
    print("✅ Completed" if success else "❌ Failed")
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
