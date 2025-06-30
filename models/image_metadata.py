#!/usr/bin/env python3
"""
画像メタデータモデル
フェーズ2: データモデル設計と実装
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
import json
from pathlib import Path

@dataclass
class ImageMetadata:
    """画像メタデータのデータモデル"""
    filepath: Optional[str] = None
    url: Optional[str] = None
    credit: str = ""
    source: str = ""
    description: str = ""
    width: int = 0
    height: int = 0
    format: str = "jpeg"
    file_size: int = 0
    query: str = ""
    api_used: str = ""
    fallback_used: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """初期化後の処理"""
        # ファイルパスが存在する場合、ファイルサイズを取得
        if self.filepath and Path(self.filepath).exists():
            self.file_size = Path(self.filepath).stat().st_size
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'filepath': self.filepath,
            'url': self.url,
            'credit': self.credit,
            'source': self.source,
            'description': self.description,
            'width': self.width,
            'height': self.height,
            'format': self.format,
            'file_size': self.file_size,
            'query': self.query,
            'api_used': self.api_used,
            'fallback_used': self.fallback_used,
            'created_at': self.created_at.isoformat()
        }
    
    def to_json(self, indent: int = 2) -> str:
        """JSON形式に変換"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ImageMetadata':
        """辞書から生成"""
        # 日時文字列をdatetimeオブジェクトに変換
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ImageMetadata':
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
            print(f"Error saving image metadata: {e}")
            return False
    
    @classmethod
    def load_from_file(cls, filepath: Path) -> Optional['ImageMetadata']:
        """ファイルから読み込み"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                json_str = f.read()
            return cls.from_json(json_str)
        except Exception as e:
            print(f"Error loading image metadata: {e}")
            return None
    
    def is_valid(self) -> bool:
        """有効な画像メタデータかチェック"""
        # ファイルパスまたはURLが存在すること
        if not self.filepath and not self.url:
            return False
        
        # ファイルが存在する場合は実際に存在するかチェック
        if self.filepath and not Path(self.filepath).exists():
            return False
        
        return True
    
    def get_display_credit(self) -> str:
        """表示用のクレジット文字列を取得"""
        if self.credit:
            return self.credit
        elif self.source:
            return f"Image from {self.source}"
        else:
            return "Image credit unavailable"
    
    def __str__(self) -> str:
        """文字列表現"""
        return f"ImageMetadata(source='{self.source}', query='{self.query}', valid={self.is_valid()})"