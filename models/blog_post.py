#!/usr/bin/env python3
"""
ブログ記事データモデル
フェーズ2: データモデル設計と実装
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
import json
from pathlib import Path

@dataclass
class BlogPost:
    """ブログ記事のデータモデル"""
    title: str
    content: str
    theme: str
    tags: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    status: str = "draft"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    published_at: Optional[datetime] = None
    word_count: int = 0
    featured_image_id: Optional[int] = None
    meta_description: Optional[str] = None
    
    def __post_init__(self):
        """初期化後の処理"""
        if not self.word_count:
            self.word_count = len(self.content)
        
        if not self.meta_description:
            self.meta_description = self._generate_meta_description()
    
    def _generate_meta_description(self) -> str:
        """メタディスクリプションを自動生成"""
        # 最初の150文字を抽出
        description = self.content.replace('\n', ' ').strip()
        if len(description) > 150:
            description = description[:147] + "..."
        return description
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'title': self.title,
            'content': self.content,
            'theme': self.theme,
            'tags': self.tags,
            'categories': self.categories,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'word_count': self.word_count,
            'featured_image_id': self.featured_image_id,
            'meta_description': self.meta_description
        }
    
    def to_json(self, indent: int = 2) -> str:
        """JSON形式に変換"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BlogPost':
        """辞書から生成"""
        # 日時文字列をdatetimeオブジェクトに変換
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        if 'published_at' in data and data['published_at'] and isinstance(data['published_at'], str):
            data['published_at'] = datetime.fromisoformat(data['published_at'])
        
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'BlogPost':
        """JSONから生成"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def save_to_file(self, filepath: Path) -> bool:
        """ファイルに保存"""
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.to_json())
            return True
        except Exception as e:
            print(f"Error saving blog post: {e}")
            return False
    
    @classmethod
    def load_from_file(cls, filepath: Path) -> Optional['BlogPost']:
        """ファイルから読み込み"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                json_str = f.read()
            return cls.from_json(json_str)
        except Exception as e:
            print(f"Error loading blog post: {e}")
            return None
    
    def update_status(self, new_status: str) -> None:
        """ステータスを更新"""
        self.status = new_status
        self.updated_at = datetime.now()
        
        if new_status == "publish" and not self.published_at:
            self.published_at = datetime.now()
    
    def add_tag(self, tag: str) -> None:
        """タグを追加"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now()
    
    def add_category(self, category: str) -> None:
        """カテゴリを追加"""
        if category not in self.categories:
            self.categories.append(category)
            self.updated_at = datetime.now()
    
    def __str__(self) -> str:
        """文字列表現"""
        return f"BlogPost(title='{self.title}', status='{self.status}', words={self.word_count})"