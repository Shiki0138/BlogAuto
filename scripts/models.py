#!/usr/bin/env python3
"""
データモデル定義 - フェーズ2実装
BlogAutoシステムのコアデータモデル
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
import json
from pathlib import Path


class PostStatus(Enum):
    """記事の公開状態"""
    DRAFT = "draft"
    PUBLISHED = "publish"
    PRIVATE = "private"
    PENDING = "pending"


class ImageSource(Enum):
    """画像取得元"""
    UNSPLASH = "unsplash"
    PEXELS = "pexels"
    GEMINI = "gemini"
    OPENAI = "openai"
    PLACEHOLDER = "placeholder"
    FALLBACK = "fallback"


@dataclass
class BlogMetadata:
    """ブログ記事メタデータ"""
    title: str
    tags: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    status: PostStatus = PostStatus.DRAFT
    theme: str = ""
    date: str = ""
    word_count: int = 0
    generated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "title": self.title,
            "tags": self.tags,
            "categories": self.categories,
            "status": self.status.value,
            "theme": self.theme,
            "date": self.date,
            "word_count": self.word_count,
            "generated_at": self.generated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BlogMetadata':
        """辞書から生成"""
        data = data.copy()
        if 'status' in data:
            data['status'] = PostStatus(data['status'])
        if 'generated_at' in data:
            data['generated_at'] = datetime.fromisoformat(data['generated_at'])
        return cls(**data)


@dataclass
class ImageMetadata:
    """画像メタデータ"""
    filepath: Optional[str] = None
    url: Optional[str] = None
    credit: str = ""
    source: ImageSource = ImageSource.FALLBACK
    description: str = ""
    width: int = 0
    height: int = 0
    query: str = ""
    fallback_used: bool = False
    generated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "filepath": self.filepath,
            "url": self.url,
            "credit": self.credit,
            "source": self.source.value,
            "description": self.description,
            "width": self.width,
            "height": self.height,
            "query": self.query,
            "fallback_used": self.fallback_used,
            "generated_at": self.generated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ImageMetadata':
        """辞書から生成"""
        data = data.copy()
        if 'source' in data:
            data['source'] = ImageSource(data['source'])
        if 'generated_at' in data:
            data['generated_at'] = datetime.fromisoformat(data['generated_at'])
        return cls(**data)


@dataclass
class WordPressResult:
    """WordPress投稿結果"""
    post_id: Optional[int] = None
    title: str = ""
    status: PostStatus = PostStatus.DRAFT
    featured_image_id: Optional[int] = None
    published_at: Optional[datetime] = None
    word_count: int = 0
    tags: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    mock_mode: bool = True
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "post_id": self.post_id,
            "title": self.title,
            "status": self.status.value,
            "featured_image_id": self.featured_image_id,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "word_count": self.word_count,
            "tags": self.tags,
            "categories": self.categories,
            "mock_mode": self.mock_mode,
            "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WordPressResult':
        """辞書から生成"""
        data = data.copy()
        if 'status' in data:
            data['status'] = PostStatus(data['status'])
        if 'published_at' in data and data['published_at']:
            data['published_at'] = datetime.fromisoformat(data['published_at'])
        return cls(**data)


@dataclass
class PipelineState:
    """パイプライン実行状態"""
    execution_id: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    overall_status: str = "pending"
    current_stage: str = ""
    stages: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    total_duration: float = 0.0
    error_count: int = 0
    warning_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "execution_id": self.execution_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "overall_status": self.overall_status,
            "current_stage": self.current_stage,
            "stages": self.stages,
            "total_duration": self.total_duration,
            "error_count": self.error_count,
            "warning_count": self.warning_count
        }
    
    def add_stage(self, stage_name: str, status: str, duration: float, **kwargs):
        """ステージ情報を追加"""
        self.stages[stage_name] = {
            "status": status,
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
        
        if status == "error":
            self.error_count += 1
        elif status == "warning":
            self.warning_count += 1


@dataclass
class HealthCheckResult:
    """ヘルスチェック結果"""
    timestamp: datetime = field(default_factory=datetime.now)
    overall_status: str = "healthy"
    checks: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def add_check(self, name: str, status: str, **kwargs):
        """チェック結果を追加"""
        self.checks[name] = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
        
        # 全体ステータスの更新
        if status in ["fail", "error"] and self.overall_status == "healthy":
            self.overall_status = "unhealthy"
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "overall_status": self.overall_status,
            "checks": self.checks
        }


class DataManager:
    """データ管理クラス"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def save_metadata(self, metadata: BlogMetadata) -> bool:
        """メタデータを保存"""
        try:
            filepath = self.output_dir / "meta.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(metadata.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"メタデータ保存エラー: {e}")
            return False
    
    def load_metadata(self) -> Optional[BlogMetadata]:
        """メタデータを読み込み"""
        try:
            filepath = self.output_dir / "meta.json"
            if not filepath.exists():
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return BlogMetadata.from_dict(data)
        except Exception as e:
            print(f"メタデータ読み込みエラー: {e}")
            return None
    
    def save_image_metadata(self, metadata: ImageMetadata) -> bool:
        """画像メタデータを保存"""
        try:
            filepath = self.output_dir / "image_info.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(metadata.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"画像メタデータ保存エラー: {e}")
            return False
    
    def load_image_metadata(self) -> Optional[ImageMetadata]:
        """画像メタデータを読み込み"""
        try:
            filepath = self.output_dir / "image_info.json"
            if not filepath.exists():
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return ImageMetadata.from_dict(data)
        except Exception as e:
            print(f"画像メタデータ読み込みエラー: {e}")
            return None
    
    def save_wordpress_result(self, result: WordPressResult) -> bool:
        """WordPress投稿結果を保存"""
        try:
            filepath = self.output_dir / "wp_result.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"WordPress結果保存エラー: {e}")
            return False
    
    def load_wordpress_result(self) -> Optional[WordPressResult]:
        """WordPress投稿結果を読み込み"""
        try:
            filepath = self.output_dir / "wp_result.json"
            if not filepath.exists():
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return WordPressResult.from_dict(data)
        except Exception as e:
            print(f"WordPress結果読み込みエラー: {e}")
            return None
    
    def save_pipeline_state(self, state: PipelineState) -> bool:
        """パイプライン状態を保存"""
        try:
            filepath = self.output_dir / f"pipeline_state_{state.execution_id}.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)
            
            # 最新版としてもコピー
            latest_filepath = self.output_dir / "pipeline_state_latest.json"
            with open(latest_filepath, 'w', encoding='utf-8') as f:
                json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"パイプライン状態保存エラー: {e}")
            return False


# テスト用メイン関数
def test_models():
    """モデルのテスト"""
    # BlogMetadataテスト
    metadata = BlogMetadata(
        title="テスト記事",
        tags=["テスト", "サンプル"],
        categories=["技術"],
        theme="テクノロジー",
        date="2025年6月28日",
        word_count=1500
    )
    print("BlogMetadata:", metadata.to_dict())
    
    # ImageMetadataテスト
    image_meta = ImageMetadata(
        filepath="/output/cover.jpg",
        credit="Photo by Test User",
        source=ImageSource.UNSPLASH,
        description="テスト画像"
    )
    print("ImageMetadata:", image_meta.to_dict())
    
    # DataManagerテスト
    manager = DataManager()
    assert manager.save_metadata(metadata)
    loaded_meta = manager.load_metadata()
    assert loaded_meta is not None
    print("DataManager test passed")


if __name__ == "__main__":
    test_models()