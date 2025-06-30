#!/usr/bin/env python3
"""
画像取得スクリプト
Unsplash → Pexels → Gemini → OpenAI の順に無料枠を優先して画像を取得
"""
import os
import sys
import time
import requests
import base64
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dotenv import load_dotenv

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.utils import (
    logger, ensure_output_dir, save_json_safely,
    get_env_var, rate_limiter, validate_api_response
)

# 環境変数読み込み
load_dotenv()

class ImageFetcher:
    """画像取得クラス - フェーズ3コア機能実装"""
    
    def __init__(self):
        """初期化"""
        self.output_dir = ensure_output_dir()
        self.retry_count = 3
        self.timeout = 30
        
        # API設定
        self.apis = {
            'unsplash': {
                'key': os.getenv('UNSPLASH_ACCESS_KEY'),
                'url': 'https://api.unsplash.com/photos/random',
                'priority': 1
            },
            'pexels': {
                'key': os.getenv('PEXELS_API_KEY'),
                'url': 'https://api.pexels.com/v1/search',
                'priority': 2
            },
            'gemini': {
                'key': os.getenv('GEMINI_API_KEY'),
                'url': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent',
                'priority': 3
            },
            'openai': {
                'key': os.getenv('OPENAI_API_KEY'),
                'url': 'https://api.openai.com/v1/images/generations',
                'priority': 4
            }
        }
        
        logger.info("ImageFetcher initialized for Phase 3")
    
    def fetch_unsplash_image(self, query: str) -> Optional[Dict[str, Any]]:
        """Unsplash APIから画像を取得"""
        try:
            if not self.apis['unsplash']['key']:
                logger.warning("Unsplash API key not found")
                return None
            
            if not rate_limiter.can_request('unsplash'):
                logger.info("Unsplash API rate limit waiting...")
                time.sleep(2)
            
            headers = {
                'Authorization': f"Client-ID {self.apis['unsplash']['key']}",
                'Accept-Version': 'v1'
            }
            
            params = {
                'query': query,
                'orientation': 'landscape',
                'content_filter': 'high',
                'count': 1
            }
            
            # 外部API接続フラグ確認
            enable_api = os.getenv('ENABLE_EXTERNAL_API', 'false').lower() == 'true'
            
            if enable_api:
                logger.info("🌅 Unsplash API request (本番実装)")
                
                response = requests.get(
                    self.apis['unsplash']['url'],
                    headers=headers,
                    params=params,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) and data:
                        data = data[0]  # 最初の画像を使用
                    
                    rate_limiter.record_request('unsplash')
                    logger.info("✅ Unsplash API response received")
                    
                    return {
                        'url': data.get('urls', {}).get('regular'),
                        'credit': f"Photo by {data.get('user', {}).get('name', 'Unknown')} on Unsplash",
                        'description': data.get('description', data.get('alt_description', '')),
                        'source': 'unsplash'
                    }
                else:
                    logger.warning(f"Unsplash API error: {response.status_code}")
                    return None
            else:
                logger.info("🌅 Unsplash API request (モック実装)")
                
                # モック実装
                mock_response = {
                    'urls': {
                        'regular': 'https://images.unsplash.com/photo-sample?w=1080&q=80',
                        'small': 'https://images.unsplash.com/photo-sample?w=400&q=80'
                    },
                    'user': {
                        'name': 'Sample Photographer',
                        'username': 'sample_user'
                    },
                    'description': f'Stock photo related to {query}',
                    'alt_description': f'A beautiful image about {query}'
                }
                
                rate_limiter.record_request('unsplash')
                logger.info("✅ Unsplash mock response generated")
            
            return {
                'url': mock_response['urls']['regular'],
                'credit': f"Photo by {mock_response['user']['name']} on Unsplash",
                'description': mock_response.get('description', ''),
                'source': 'unsplash'
            }
            
        except Exception as e:
            logger.error(f"Unsplash API error: {e}")
            return None
    
    def fetch_pexels_image(self, query: str) -> Optional[Dict[str, Any]]:
        """Pexels APIから画像を取得"""
        try:
            if not self.apis['pexels']['key']:
                logger.warning("Pexels API key not found")
                return None
            
            if not rate_limiter.can_request('pexels'):
                logger.info("Pexels API rate limit waiting...")
                time.sleep(2)
            
            # 外部API接続フラグ確認
            enable_api = os.getenv('ENABLE_EXTERNAL_API', 'false').lower() == 'true'
            
            if enable_api:
                logger.info("📸 Pexels API request (本番実装)")
                
                headers = {
                    'Authorization': self.apis['pexels']['key']
                }
                
                params = {
                    'query': query,
                    'per_page': 1,
                    'orientation': 'landscape'
                }
                
                response = requests.get(
                    self.apis['pexels']['url'],
                    headers=headers,
                    params=params,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    rate_limiter.record_request('pexels')
                    logger.info("✅ Pexels API response received")
                    
                    if data.get('photos'):
                        photo = data['photos'][0]
                        return {
                            'url': photo.get('src', {}).get('large'),
                            'credit': f"Photo by {photo.get('photographer', 'Unknown')} from Pexels",
                            'description': photo.get('alt', ''),
                            'source': 'pexels'
                        }
                else:
                    logger.warning(f"Pexels API error: {response.status_code}")
                    return None
            else:
                logger.info("📸 Pexels API request (モック実装)")
                
                # モック実装
                mock_response = {
                    'photos': [{
                        'src': {
                            'large': f'https://images.pexels.com/photos/sample/pexels-photo-sample.jpeg?w=1080&q=80',
                            'medium': f'https://images.pexels.com/photos/sample/pexels-photo-sample.jpeg?w=500&q=80'
                        },
                        'photographer': 'Sample Artist',
                        'photographer_url': 'https://www.pexels.com/@sample-artist',
                        'alt': f'Pexels stock photo about {query}'
                    }]
                }
                
                rate_limiter.record_request('pexels')
                logger.info("✅ Pexels mock response generated")
            
            if mock_response.get('photos'):
                photo = mock_response['photos'][0]
                return {
                    'url': photo['src']['large'],
                    'credit': f"Photo by {photo['photographer']} from Pexels",
                    'description': photo.get('alt', ''),
                    'source': 'pexels'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Pexels API error: {e}")
            return None
    
    def fetch_gemini_image(self, query: str) -> Optional[Dict[str, Any]]:
        """Gemini APIで美容師向け最適化画像を生成"""
        try:
            if not self.apis['gemini']['key']:
                logger.warning("Gemini API key not found")
                return None
            
            if not rate_limiter.can_request('gemini'):
                logger.info("Gemini API rate limit waiting...")
                time.sleep(3)
            
            # 美容師向け画像プロンプト最適化
            optimized_prompt = self._optimize_beauty_prompt(query)
            
            # 外部API接続フラグ確認
            enable_api = os.getenv('ENABLE_EXTERNAL_API', 'false').lower() == 'true'
            
            if enable_api:
                logger.info("🤖 Gemini API request (美容師特化画像生成)")
                
                # Gemini Pro Vision APIを使用
                url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent"
                
                payload = {
                    "contents": [{
                        "parts": [{
                            "text": optimized_prompt
                        }]
                    }],
                    "generationConfig": {
                        "temperature": 0.7,  # 創造性を高める
                        "topK": 40,
                        "topP": 0.95,
                        "maxOutputTokens": 2048
                    },
                    "safetySettings": [
                        {
                            "category": "HARM_CATEGORY_HARASSMENT",
                            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                        },
                        {
                            "category": "HARM_CATEGORY_HATE_SPEECH", 
                            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                        },
                        {
                            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                        },
                        {
                            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                        }
                    ]
                }
                
                headers = {
                    'Content-Type': 'application/json',
                    'x-goog-api-key': self.apis['gemini']['key']
                }
                
                response = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    rate_limiter.record_request('gemini')
                    logger.info("✅ Gemini API response received")
                    
                    # レスポンス処理（画像説明生成）
                    if 'candidates' in data and data['candidates']:
                        candidate = data['candidates'][0]
                        if 'content' in candidate and 'parts' in candidate['content']:
                            generated_text = candidate['content']['parts'][0].get('text', '')
                            
                            # 生成されたテキストから画像コンセプトを抽出
                            return {
                                'concept': generated_text,
                                'credit': "AI-generated concept by Google Gemini",
                                'description': f'Professional beauty salon image concept about {query}',
                                'source': 'gemini',
                                'optimized_prompt': optimized_prompt,
                                'quality_score': self._evaluate_image_concept(generated_text)
                            }
                else:
                    logger.warning(f"Gemini API error: {response.status_code} - {response.text}")
                    return None
            else:
                logger.info("🤖 Gemini API request (美容師特化モック実装)")
                
                # 美容師向け高品質モック画像データ
                mock_concept = self._generate_mock_beauty_concept(query)
                
                rate_limiter.record_request('gemini')
                logger.info("✅ Gemini mock beauty image generated")
            
            return {
                'data': "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
                'concept': mock_concept,
                'credit': "AI-generated image by Google Gemini",
                'description': f'Professional beauty salon image about {query}',
                'source': 'gemini'
            }
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return None
    
    def _optimize_beauty_prompt(self, query: str) -> str:
        """美容師向け画像プロンプトを最適化"""
        # 美容師業界キーワードマッピング
        beauty_keywords = {
            'マーケティング': 'salon marketing strategy',
            '集客': 'salon customer acquisition',
            'Instagram': 'social media beauty marketing',
            '心理学': 'customer psychology in beauty salon',
            '顧客満足': 'customer satisfaction beauty service',
            'サロン経営': 'professional salon management',
            'カット': 'professional hair cutting',
            'カラー': 'hair coloring technique',
            'スタイリング': 'hair styling',
            'ヘアケア': 'hair care treatment',
            'トレンド': 'beauty trends',
            'ブランディング': 'salon branding'
        }
        
        # キーワードマッチングと英語変換
        english_terms = []
        for jp_word, en_word in beauty_keywords.items():
            if jp_word in query:
                english_terms.append(en_word)
        
        # ベースプロンプト構築
        base_prompt = f"""Create a professional, high-quality image concept for a beauty salon blog article about "{query}". 

The image should convey:
- Professional beauty salon atmosphere
- Modern, clean, and inviting design
- Warm lighting and welcoming environment
- Professional beauty tools or styling in the background
- Aspirational and inspiring mood
- High-end salon aesthetic

Style requirements:
- Photography style: Professional beauty salon photography
- Color palette: Warm, natural tones with gold/rose gold accents
- Composition: Clean, minimalist, Instagram-worthy
- Mood: Professional yet approachable, luxurious yet accessible

Specific elements to include:
"""
        
        # 特化要素の追加
        if english_terms:
            base_prompt += f"- Focus on {', '.join(english_terms)}\n"
        
        if 'Instagram' in query or 'SNS' in query:
            base_prompt += "- Social media friendly composition\n- Eye-catching visual elements\n"
        
        if 'マーケティング' in query or '集客' in query:
            base_prompt += "- Business growth imagery\n- Customer engagement visual metaphors\n"
        
        if '心理学' in query:
            base_prompt += "- Subtle psychology-related visual elements\n- Trust and comfort conveying imagery\n"
        
        base_prompt += """
Technical specifications:
- Aspect ratio: 16:9 (blog header format)
- Resolution: High resolution suitable for web
- Quality: Professional photography standard
- Lighting: Soft, professional salon lighting

Please describe this image concept in detail, focusing on how it would look and feel to potential salon customers."""
        
        return base_prompt
    
    def _generate_mock_beauty_concept(self, query: str) -> str:
        """美容師向けモック画像コンセプトを生成"""
        beauty_concepts = {
            'マーケティング': """
明るく洗練されたヘアサロンの内装を背景に、スタイリッシュなスタイリングチェアとプロフェッショナルなヘアツールが整然と配置された空間。
暖かいゴールドの照明が心地よい雰囲気を演出し、鏡に映る笑顔の顧客とスタイリストの姿が信頼関係を表現。
前景にはInstagramのようなソーシャルメディアのアイコンやグラフィックが重なり、デジタルマーケティングの要素を示唆。
""",
            '集客': """
サロンの外観から内装まで一望できるワイドショット。ガラス張りの明るい店舗デザインで、通りすがりの人々が興味深く覗き込む姿。
店内では複数のスタイリストが顧客にサービスを提供し、活気ある雰囲気を演出。
窓には「新規顧客歓迎」などの温かみのあるメッセージが掲示され、親しみやすさをアピール。
""",
            'Instagram': """
インスタ映えする美しいヘアスタイルのクローズアップ。完璧にスタイリングされた髪が自然光の下で輝き、
スマートフォンのカメラフレームが画面に重なって、SNS投稿の瞬間を表現。
背景にはおしゃれなサロンインテリアがボケ味で映り込み、プロフェッショナルな環境を示唆。
""",
            '心理学': """
カウンセリングシーンを捉えた温かい画像。スタイリストと顧客が向かい合って座り、
真剣に会話を交わしている様子。表情は穏やかで信頼関係が感じられる。
背景には心理学的な要素として、色彩心理を意識したカラーチャートや、
顧客の感情に寄り添うような柔らかい色調の照明が配置されている。
""",
            'default': """
プロフェッショナルな美容サロンの内装。モダンで清潔感のあるデザインに、
最新の美容機器とスタイリングツールが配置されている。
温かい照明が心地よい空間を演出し、顧客がリラックスできる環境を表現。
全体的に高級感がありながらも親しみやすい雰囲気を醸し出している。
"""
        }
        
        # クエリに最も関連するコンセプトを選択
        for keyword, concept in beauty_concepts.items():
            if keyword in query:
                return concept.strip()
        
        return beauty_concepts['default'].strip()
    
    def _evaluate_image_concept(self, concept: str) -> float:
        """画像コンセプトの品質を評価"""
        score = 50.0  # ベーススコア
        
        # 美容業界関連キーワードの評価
        beauty_terms = [
            'salon', 'professional', 'hair', 'beauty', 'styling', 'customer',
            'modern', 'clean', 'lighting', 'atmosphere', 'service', 'quality'
        ]
        
        found_terms = sum(1 for term in beauty_terms if term.lower() in concept.lower())
        score += found_terms * 5  # 関連用語1個につき5点追加
        
        # 詳細度の評価（文字数ベース）
        if len(concept) > 200:
            score += 15
        elif len(concept) > 100:
            score += 10
        elif len(concept) > 50:
            score += 5
        
        # プロフェッショナル要素の評価
        professional_terms = ['professional', 'high-quality', 'luxurious', 'premium', 'expert']
        professional_count = sum(1 for term in professional_terms if term.lower() in concept.lower())
        score += professional_count * 8
        
        # 感情的要素の評価
        emotional_terms = ['warm', 'welcoming', 'comfortable', 'trust', 'relaxing', 'inspiring']
        emotional_count = sum(1 for term in emotional_terms if term.lower() in concept.lower())
        score += emotional_count * 6
        
        return min(score, 100.0)  # 最大100点
    
    def fetch_openai_image(self, query: str) -> Optional[Dict[str, Any]]:
        """OpenAI DALL-E APIで画像を生成"""
        try:
            if not self.apis['openai']['key']:
                logger.warning("OpenAI API key not found")
                return None
            
            if not rate_limiter.can_request('openai'):
                logger.info("OpenAI API rate limit waiting...")
                time.sleep(4)
            
            # 外部API接続フラグ確認
            enable_api = os.getenv('ENABLE_EXTERNAL_API', 'false').lower() == 'true'
            
            if enable_api:
                logger.info("🎨 OpenAI DALL-E API request (本番実装)")
                
                headers = {
                    'Authorization': f"Bearer {self.apis['openai']['key']}",
                    'Content-Type': 'application/json'
                }
                
                payload = {
                    'model': 'dall-e-3',
                    'prompt': f"A professional blog header image about {query}, modern business style, clean design, high quality",
                    'n': 1,
                    'size': '1792x1024',
                    'quality': 'standard',
                    'style': 'natural'
                }
                
                response = requests.post(
                    self.apis['openai']['url'],
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    rate_limiter.record_request('openai')
                    logger.info("✅ OpenAI DALL-E API response received")
                    
                    if data.get('data'):
                        image_data = data['data'][0]
                        return {
                            'url': image_data.get('url'),
                            'credit': "AI-generated image by OpenAI DALL-E",
                            'description': image_data.get('revised_prompt', ''),
                            'source': 'openai'
                        }
                else:
                    logger.warning(f"OpenAI API error: {response.status_code}")
                    if response.status_code == 401:
                        logger.error("OpenAI API key is invalid or expired")
                    return None
            else:
                logger.info("🎨 OpenAI DALL-E API request (モック実装)")
                
                # モック実装
                mock_response = {
                    'data': [{
                        'url': f'https://oaidalleapiprodscus.blob.core.windows.net/private/sample-image.png?{query}',
                        'revised_prompt': f'A professional blog header image about {query}'
                    }]
                }
                
                rate_limiter.record_request('openai')
                logger.info("✅ OpenAI DALL-E mock image generated")
            
            if mock_response.get('data'):
                image_data = mock_response['data'][0]
                return {
                    'url': image_data['url'],
                    'credit': "AI-generated image by OpenAI DALL-E",
                    'description': image_data.get('revised_prompt', ''),
                    'source': 'openai'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return None
    
    def download_image(self, image_url: str, filename: str) -> bool:
        """画像をダウンロードして保存"""
        try:
            # 外部API接続フラグ確認
            enable_api = os.getenv('ENABLE_EXTERNAL_API', 'false').lower() == 'true'
            
            if enable_api and image_url.startswith('http'):
                logger.info(f"📥 Downloading image: {filename}")
                
                response = requests.get(image_url, timeout=self.timeout, stream=True)
                if response.status_code == 200:
                    image_path = self.output_dir / filename
                    with open(image_path, 'wb') as f:
                        for chunk in response.iter_content(1024):
                            f.write(chunk)
                    
                    logger.info(f"✅ Image downloaded: {image_path}")
                    return True
                else:
                    logger.error(f"Image download failed: {response.status_code}")
                    return False
            else:
                logger.info(f"📥 Downloading image (モック実装): {filename}")
                
                # モック実装：1x1ピクセルの透明PNG画像を作成
                mock_image_data = base64.b64decode(
                    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
                )
                
                image_path = self.output_dir / filename
                with open(image_path, 'wb') as f:
                    f.write(mock_image_data)
                
                logger.info(f"✅ Mock image saved: {image_path}")
                return True
            
        except Exception as e:
            logger.error(f"Image download error: {e}")
            return False
    
    def save_image_data(self, image_data: str, filename: str) -> bool:
        """Base64画像データを保存"""
        try:
            image_path = self.output_dir / filename
            
            # Base64データを画像ファイルに保存
            with open(image_path, 'wb') as f:
                f.write(base64.b64decode(image_data))
            
            logger.info(f"✅ Image data saved: {image_path}")
            return True
            
        except Exception as e:
            logger.error(f"Image data save error: {e}")
            return False
    
    def get_image_query(self) -> str:
        """記事のメタデータから画像検索クエリを生成"""
        try:
            meta_path = self.output_dir / "meta.json"
            if meta_path.exists():
                import json
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                
                theme = meta.get('theme', '')
                title = meta.get('title', '')
                
                # テーマに基づいてクエリを最適化
                if "テクノロジー" in theme:
                    return "technology innovation digital business"
                elif "マーケティング" in theme:
                    return "business marketing strategy growth"
                elif "健康" in theme:
                    return "health wellness lifestyle balance"
                elif "AI" in theme or "人工知能" in theme:
                    return "artificial intelligence technology future"
                else:
                    return "business professional modern clean"
            
            return "business technology modern"
            
        except Exception as e:
            logger.error(f"Query generation error: {e}")
            return "business professional"
    
    def fetch_image_with_fallback(self) -> Dict[str, Any]:
        """フォールバック機能付きで画像を取得"""
        query = self.get_image_query()
        logger.info(f"🔍 Image search query: {query}")
        
        # 優先順位に従って画像取得を試行
        fetch_methods = [
            ('unsplash', self.fetch_unsplash_image),
            ('pexels', self.fetch_pexels_image),
            ('gemini', self.fetch_gemini_image),
            ('openai', self.fetch_openai_image)
        ]
        
        for api_name, fetch_method in fetch_methods:
            logger.info(f"🔄 Trying {api_name} API...")
            
            for attempt in range(self.retry_count):
                try:
                    result = fetch_method(query)
                    if result:
                        logger.info(f"✅ Image fetched successfully from {api_name}")
                        
                        # 画像を保存
                        filename = f"cover.jpg"
                        
                        if 'url' in result:
                            # URL形式の場合はダウンロード
                            if self.download_image(result['url'], filename):
                                result['filepath'] = str(self.output_dir / filename)
                        elif 'data' in result:
                            # Base64データの場合は直接保存
                            if self.save_image_data(result['data'], filename):
                                result['filepath'] = str(self.output_dir / filename)
                        
                        return result
                        
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed for {api_name}: {e}")
                    if attempt < self.retry_count - 1:
                        time.sleep(2 ** attempt)  # 指数バックオフ
            
            logger.warning(f"❌ All attempts failed for {api_name}")
        
        # すべて失敗した場合のフォールバック
        logger.warning("🚨 All image APIs failed, using fallback")
        
        # フォールバック用のプレースホルダー画像を作成
        fallback_filename = "cover.jpg"
        fallback_path = self.output_dir / fallback_filename
        
        try:
            # 1x1ピクセルの透明PNG画像をJPEG用にアップデート
            mock_image_data = base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            )
            
            with open(fallback_path, 'wb') as f:
                f.write(mock_image_data)
            
            logger.info(f"✅ Fallback image created: {fallback_path}")
            
            return {
                'filepath': str(fallback_path),
                'credit': 'Fallback placeholder image',
                'description': 'Generated placeholder when external APIs unavailable',
                'source': 'fallback',
                'query': query
            }
        except Exception as e:
            logger.error(f"Failed to create fallback image: {e}")
            return {
                'filepath': None,
                'credit': 'No image available',
                'description': 'Image could not be fetched',
                'source': 'fallback',
                'query': query
            }
    
    def run(self) -> bool:
        """メイン実行処理"""
        try:
            logger.info("🖼️ Image fetching process started (Phase 3)")
            
            # 画像取得実行
            result = self.fetch_image_with_fallback()
            
            # 結果をJSONファイルに保存
            image_info_path = self.output_dir / "image_info.json"
            if save_json_safely(result, str(image_info_path)):
                logger.info(f"📊 Image metadata saved: {image_info_path}")
            
            # 成功判定
            success = result.get('filepath') is not None
            
            if success:
                logger.info("✅ Image fetching completed successfully")
                logger.info(f"📁 Image saved: {result['filepath']}")
                logger.info(f"🏷️ Source: {result['source']}")
                logger.info(f"📝 Credit: {result['credit']}")
            else:
                logger.warning("⚠️ Image fetching completed with fallback")
            
            return True  # 画像なしでも続行可能
            
        except Exception as e:
            logger.error(f"❌ Image fetching process failed: {e}")
            return False

def main():
    """メイン実行関数"""
    try:
        fetcher = ImageFetcher()
        success = fetcher.run()
        
        if success:
            print("✅ Image fetching completed")
            sys.exit(0)
        else:
            print("❌ Image fetching failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Main process error: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()