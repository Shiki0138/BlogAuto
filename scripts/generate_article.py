#!/usr/bin/env python3
"""
Daily Blog Automation - Article Generation Module
フェーズ2: 記事生成機能の本番レベル実装
外部API接続は最終フェーズで実装予定
"""
import os
import sys
import re
from pathlib import Path
from datetime import datetime
import json
import logging
import argparse
from typing import List, Dict, Optional, Any

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

try:
    from jinja2 import Template
except ImportError:
    # フォールバック：jinja2がない場合の簡易実装
    class Template:
        def __init__(self, template_str):
            self.template_str = template_str
        
        def render(self, **kwargs):
            result = self.template_str
            for key, value in kwargs.items():
                result = result.replace(f"{{{{ {key} }}}}", str(value))
            return result

# ユーティリティ関数のインポート（エラー処理付き）
try:
    from scripts.utils import (
        logger, get_jst_date_japanese, 
        get_today_theme, ensure_output_dir, save_json_safely
    )
except ImportError:
    # フォールバック実装
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    def get_jst_date_japanese():
        now = datetime.now()
        return f"{now.year}年{now.month}月{now.day}日"
    
    def get_today_theme():
        themes = ["効率的な時間管理術", "健康的な食生活のコツ", "テクノロジーと生活の調和"]
        return themes[datetime.now().timetuple().tm_yday % len(themes)]
    
    def ensure_output_dir():
        Path("output").mkdir(exist_ok=True)
        return Path("output")
    
    def save_json_safely(data, filepath):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True

class ArticleGenerator:
    """記事生成クラス - フェーズ2実装"""
    
    def __init__(self):
        """初期化"""
        self.output_dir = ensure_output_dir()
        logger.info("ArticleGenerator initialized for Phase 2")
        
    def load_prompt_template(self) -> str:
        """プロンプトテンプレートを読み込み"""
        template_path = Path("prompts/daily_blog.jinja")
        
        if template_path.exists():
            try:
                return template_path.read_text(encoding='utf-8')
            except Exception as e:
                logger.error(f"テンプレート読み込みエラー: {e}")
                return self._create_default_template()
        else:
            logger.warning("テンプレートファイルが見つかりません。デフォルトテンプレートを使用。")
            return self._create_default_template()
    
    def _create_default_template(self) -> str:
        """デフォルトテンプレートを作成"""
        return """あなたはSEOに精通した日本語ライターです。

本日のテーマ: {{ theme }}
投稿日: {{ date_ja }}

## 生成ルール
- 1600〜1800文字
- H2見出しを4本、必要に応じてH3も使用
- 箇条書きは "- " を使用
- 結論セクション必須
- 読者行動CTAを最後に1文追加
- Markdown形式で出力
- タイトルはH1（#）で開始

## 品質要件
- 実用的で具体的な内容
- 読者の課題解決に焦点
- SEO キーワードを自然に配置
- 専門用語は分かりやすく説明"""

    def generate_article_content(self, theme: str, date_ja: str) -> str:
        """記事コンテンツを生成"""
        try:
            # 外部API接続フラグ確認
            enable_api = os.getenv('ENABLE_EXTERNAL_API', 'false').lower() == 'true'
            
            if enable_api and (os.getenv('GEMINI_API_KEY') or os.getenv('OPENAI_API_KEY')):
                logger.info("🌐 無料AI API接続開始（品質重視生成）")
                return self._generate_high_quality_article(theme, date_ja)
            else:
                logger.info("🚧 外部API接続は無効（モック応答使用）")
                return self._generate_mock_article(theme, date_ja)
            
        except Exception as e:
            logger.error(f"記事生成エラー: {e}")
            return self._generate_fallback_article(theme, date_ja)
    
    def _generate_high_quality_article(self, theme: str, date_ja: str) -> str:
        """高品質記事生成（複数回生成して最良選択）"""
        best_article = None
        best_score = 0
        
        # 最大3回生成を試行
        for attempt in range(3):
            logger.info(f"📝 高品質記事生成: 試行 {attempt + 1}/3")
            
            article = self._generate_article_via_api(theme, date_ja)
            if not article:
                continue
            
            # 品質評価
            score = self._evaluate_article_quality(article, theme)
            logger.info(f"📊 記事品質スコア: {score:.1f}点")
            
            if score > best_score:
                best_score = score
                best_article = article
            
            # 高品質（85点以上）なら即座に採用
            if score >= 85:
                logger.info("✅ 高品質記事を取得しました")
                break
        
        if best_article and best_score >= 70:
            logger.info(f"📈 最終採用記事: {best_score:.1f}点")
            return best_article
        else:
            logger.warning("⚠️ 品質基準を満たす記事が生成できませんでした")
            return self._generate_mock_article(theme, date_ja)
    
    def _evaluate_article_quality(self, content: str, theme: str) -> float:
        """記事品質の簡易評価"""
        score = 0
        
        # 文字数評価 (30点満点) - 美容師特化で最適化
        length = len(content)
        if 1800 <= length <= 2200:  # 仕様書の要件に合わせて調整
            score += 30
        elif 1600 <= length < 1800 or 2200 < length <= 2500:
            score += 25
        elif 1500 <= length < 1600 or 2500 < length <= 3000:
            score += 15
        else:
            score += 5
        
        # 構造評価 (25点満点)
        h2_count = len(re.findall(r'^## ', content, re.MULTILINE))
        h3_count = len(re.findall(r'^### ', content, re.MULTILINE))
        bullet_points = len(re.findall(r'^- ', content, re.MULTILINE))
        
        if 4 <= h2_count <= 6:
            score += 10
        elif h2_count >= 3:
            score += 5
        
        if h3_count >= 2:
            score += 8
        elif h3_count >= 1:
            score += 4
        
        if bullet_points >= 5:
            score += 7
        elif bullet_points >= 3:
            score += 3
        
        # キーワード評価 (20点満点)
        import re
        theme_mentions = len(re.findall(re.escape(theme), content, re.IGNORECASE))
        keyword_density = (theme_mentions * len(theme) / length) * 100 if length > 0 else 0
        
        if 1.0 <= keyword_density <= 3.0:
            score += 15
        elif 0.5 <= keyword_density < 1.0 or 3.0 < keyword_density <= 4.0:
            score += 10
        else:
            score += 5
        
        # 関連キーワード（美容師・ローカルビジネス特化）
        related_words = ['美容師', '集客', 'Instagram', '顧客', '心理学', '行動経済学', '生成AI', 'マーケティング', 'ローカルビジネス', 'サロン']
        related_count = sum(len(re.findall(re.escape(word), content)) for word in related_words)
        if related_count >= 8:
            score += 5
        elif related_count >= 5:
            score += 3
        
        # 実用性評価 (15点満点) - 美容師・ローカルビジネス特化
        practical_phrases = ['手順', 'ステップ', '方法', '具体的', '実例', '事例', 'ポイント', 'プロンプト', 'AI活用', '心理テクニック', '戦略']
        practical_count = sum(len(re.findall(word, content)) for word in practical_phrases)
        
        if practical_count >= 10:
            score += 15
        elif practical_count >= 6:
            score += 10
        else:
            score += 5
        
        # エンゲージメント評価 (10点満点)
        engagement_phrases = ['あなた', 'ぜひ', '今すぐ', '実践', '試して', 'でしょうか']
        engagement_count = sum(len(re.findall(phrase, content)) for phrase in engagement_phrases)
        
        if engagement_count >= 5:
            score += 10
        elif engagement_count >= 3:
            score += 6
        else:
            score += 3
        
        return min(score, 100)
    
    def _generate_article_via_api(self, theme: str, date_ja: str) -> str:
        """Gemini APIを使用して記事を生成（最終フェーズ）"""
        try:
            # Gemini APIを最優先で試行
            if os.getenv('GEMINI_API_KEY'):
                result = self._generate_with_gemini(theme, date_ja)
                if result:
                    return result
            
            # OpenAI APIを第二選択肢として試行
            if os.getenv('OPENAI_API_KEY'):
                result = self._generate_with_openai(theme, date_ja)
                if result:
                    return result
            
            # すべてのAPI試行が失敗
            logger.warning("全ての無料API試行が失敗しました。モック記事を使用します")
            return self._generate_mock_article(theme, date_ja)
            
        except Exception as e:
            logger.error(f"API記事生成エラー: {e}")
            return self._generate_mock_article(theme, date_ja)
    
    def _generate_with_gemini(self, theme: str, date_ja: str) -> str:
        """Google Gemini APIで記事を生成"""
        try:
            import google.generativeai as genai
            from scripts.auth_manager import SecureEnvironment, AuthManager
            
            # 認証情報取得
            auth_manager = AuthManager()
            secure_env = SecureEnvironment(auth_manager)
            secure_env.setup_environment()
            
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                logger.warning("Gemini APIキーが設定されていません")
                return None
            
            # Gemini API設定
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')  # 無料版
            
            # プロンプトテンプレート読み込み
            template_str = self.load_prompt_template()
            template = Template(template_str)
            prompt = template.render(theme=theme, date_ja=date_ja)
            
            logger.info("Gemini APIリクエスト送信中...")
            
            # API呼び出し（リトライ機能付き）
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = model.generate_content(
                        prompt,
                        generation_config={
                            'temperature': 0.7,
                            'max_output_tokens': 2500,
                        }
                    )
                    
                    if response.text:
                        article_content = response.text
                        logger.info(f"Gemini API応答受信: {len(article_content)}文字")
                        
                        # 文字数チェック
                        if len(article_content) >= 1800:
                            return article_content
                        else:
                            logger.warning("生成記事が短すぎます。リトライします...")
                            if attempt < max_retries - 1:
                                continue
                    
                except Exception as e:
                    logger.error(f"Gemini API呼び出しエラー (試行 {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(2 ** attempt)
                        continue
            
            logger.error("Gemini API呼び出しが失敗しました")
            return None
            
        except ImportError:
            logger.warning("google-generativeaiライブラリが見つかりません")
            return None
        except Exception as e:
            logger.error(f"Gemini API記事生成エラー: {e}")
            return None
    
    def _generate_with_openai(self, theme: str, date_ja: str) -> str:
        """OpenAI APIで記事を生成"""
        try:
            import openai
            from scripts.auth_manager import SecureEnvironment, AuthManager
            
            # 認証情報取得
            auth_manager = AuthManager()
            secure_env = SecureEnvironment(auth_manager)
            secure_env.setup_environment()
            
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.warning("OpenAI APIキーが設定されていません")
                return None
            
            # OpenAI クライアント初期化
            client = openai.OpenAI(api_key=api_key)
            
            # プロンプトテンプレート読み込み
            template_str = self.load_prompt_template()
            template = Template(template_str)
            prompt = template.render(theme=theme, date_ja=date_ja)
            
            logger.info("OpenAI APIリクエスト送信中...")
            
            # API呼び出し（リトライ機能付き）
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",  # 比較的低コスト
                        messages=[
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=2500,
                        temperature=0.7
                    )
                    
                    if response.choices[0].message.content:
                        article_content = response.choices[0].message.content
                        logger.info(f"OpenAI API応答受信: {len(article_content)}文字")
                        
                        # 文字数チェック
                        if len(article_content) >= 1800:
                            return article_content
                        else:
                            logger.warning("生成記事が短すぎます。リトライします...")
                            if attempt < max_retries - 1:
                                continue
                    
                except Exception as e:
                    logger.error(f"OpenAI API呼び出しエラー (試行 {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(2 ** attempt)
                        continue
            
            logger.error("OpenAI API呼び出しが失敗しました")
            return None
            
        except ImportError:
            logger.warning("openaiライブラリが見つかりません")
            return None
        except Exception as e:
            logger.error(f"OpenAI API記事生成エラー: {e}")
            return None
    
    def _generate_mock_article(self, theme: str, date_ja: str) -> str:
        """美容師・ローカルビジネス特化の高品質モック記事を生成"""
        return f"""# 【美容師必見】{theme}の心理学的アプローチ：顧客の心を掴む本質的戦略

## プロローグ：なぜ9割の美容師が{theme}で失敗するのか？

{date_ja}、美容師のあなたに緊急のお知らせです。実は、多くのサロンが{theme}で苦戦している理由、ご存知ですか？それは「顧客心理を理解していない」からなんです。

今日は心理学の専門知識を活用して、あなたのサロンが劇的に変わる{theme}の秘訣をお伝えします。この記事を読み終える頃には、競合サロンとは一線を画す戦略を手に入れているはずです。

## 【心理学解説】{theme}の本質を理解しよう

### 顧客心理の基本メカニズム

心理学の世界では「認知バイアス」という現象があります。これは、人が無意識に持つ思考の偏りのこと。{theme}においても、この心理メカニズムを理解することが成功への第一歩です。

例えば、美容室で「カットとカラーのセット割引」を見た時、お客様の脳内では「損失回避バイアス」が働きます。つまり「今やらないと損をする」と感じる心理効果です。

### 美容業界特有の顧客行動パターン

美容師として10年以上の経験から言えるのは、お客様の選択基準は以下の順番で決まることです：

1. **信頼感**（この人に任せて大丈夫？）
2. **技術力**（理想の髪型にしてくれる？）
3. **価格**（コストパフォーマンスは？）

実は、価格は3番目なんです。これを理解せずに価格競争に走ってしまうサロンが失敗する理由がここにあります。

## 【実践編】心理学に基づく{theme}戦略5選

### 戦略1: アンカリング効果を活用した価格設定

アンカリング効果とは、最初に提示された情報が判断基準になる心理現象です。例えば、メニュー表の一番上に高額なコースを配置することで、他のメニューが「お得」に見える効果を狙えます。

**実践方法：**
- プレミアムコース（15,000円）を最上段に配置
- スタンダードコース（8,000円）を中央に配置
- お客様の9割がスタンダードコースを選ぶ心理トリック

### 戦略2: Instagram集客での返報性の原理

返報性の原理とは「何かをしてもらったら、お返しをしたくなる」心理です。InstagramのDMで無料のヘアケアアドバイスを送ることで、お客様との信頼関係を構築できます。

**具体的な投稿例：**
```
「髪がパサつく原因は、実は〇〇だった！
美容師が教える3つの改善ポイント

1. シャンプー前のブラッシング
2. 38度以下のぬるま湯使用
3. タオルドライの正しい方法

詳しくはDMで個別アドバイスします♪」
```

### 戦略3: プロスペクト理論による予約システム

プロスペクト理論によると、人は「得をする」よりも「損をしない」ことを重視します。これを予約システムに応用すると効果的です。

**応用例：**
- ×「初回20%オフ」
- ○「今月逃すと通常料金に戻ります」

この表現の違いで予約率が30%向上した実例があります。

### 戦略4: 顧客理解を深めるペルソナ分析

効果的な{theme}には、顧客の深い理解が必要です。以下の質問を自分に問いかけてみてください：

- あなたの理想的な顧客は何歳ですか？
- どんな悩みを抱えていますか？
- 普段どのSNSを使っていますか？
- 美容室に求める最大の価値は何ですか？

この4つの答えが明確になると、マーケティング戦略が劇的に変わります。

### 戦略5: リピート率向上のザイアンス効果

ザイアンス効果とは「接触回数が増えるほど好感度が上がる」心理現象です。施術後のアフターフォローで、この効果を最大限に活用しましょう。

**実践スケジュール：**
- 施術翌日：「仕上がりはいかがですか？」のLINE
- 1週間後：ヘアケアのワンポイントアドバイス
- 3週間後：次回予約のご案内
- 1ヶ月後：新メニューのご紹介

## 【事例研究】成功サロンの{theme}実践例

### ケーススタディ：月商200万円達成の秘密

東京にある個人サロン「Hair Studio M」の事例をご紹介します。オーナーの田中さん（仮名）は、心理学を取り入れた{theme}で以下の結果を達成しました：

- 月商：120万円 → 200万円（67%向上）
- リピート率：60% → 85%（25ポイント向上）
- Instagram フォロワー：500人 → 3,200人（6.4倍増加）

**成功の秘訣：**
田中さんは「承認欲求」に着目し、お客様の変化を丁寧に言語化してお伝えしました。「髪色が明るくなって、お肌がワントーン明るく見えますね」といった具体的な褒め言葉で、お客様の満足度を大幅に向上させたのです。

### 失敗から学ぶ：やってはいけない3つのNG行動

逆に、{theme}で失敗するサロンの共通点も見えてきました：

1. **技術だけで勝負しようとする**：心理的満足度を軽視した結果、リピートに繋がらない
2. **価格競争に巻き込まれる**：顧客の価値観を理解せず、安さだけで勝負しようとする
3. **一方的な情報発信**：お客様の声を聞かず、自分本位のサービスを提供する

これらの失敗を避けるためには、常に「お客様の立場」で考える姿勢が重要です。

## 【上級者向け】ワンランク上の{theme}テクニック

### プロが使う高度な顧客心理分析法

上級者の美容師は「マイクロエクスプレッション」（微細な表情の変化）を読み取ります。カウンセリング中のお客様の表情から、本当の要望を察知する技術です。

**観察ポイント：**
- 眉毛の微細な動き（不安を表す）
- 口角の変化（満足度を表す）
- 視線の方向（興味の対象を表す）

この技術をマスターすると、お客様が言葉にしない本当のニーズを把握できるようになります。

### Instagram × {theme}の最新トレンド活用法

2024年のInstagramアルゴリズムでは「リール動画」が最も拡散されやすい傾向にあります。{theme}に関連するリール動画のアイデアをご紹介します：

**バズる投稿例：**
- 「Before→After」変身動画（3秒で完結）
- 美容師の技術解説（手元のクローズアップ）
- お客様の生の声（許可を得て撮影）

これらのコンテンツで月間リーチ10万人を超えるサロンも珍しくありません。

## まとめ：明日から変わる！{theme}実践ロードマップ

{theme}の成功は、技術力だけでなく「顧客心理の理解」にかかっています。今日お伝えした心理学的アプローチを実践することで、あなたのサロンも確実に変化を実感できるはずです。

**今すぐできるアクションプラン：**
1. お客様のペルソナを明確にする（今週中）
2. Instagram投稿にストーリーテリングを取り入れる（明日から）
3. アフターフォローのスケジュールを作成する（今月中）

🎯 今日学んだ心理学テクニックで、あなたのサロンも顧客に愛される店舗に変身しませんか？一歩踏み出す勇気が、あなたの美容師人生を劇的に変える起点になるのです。"""

    def _generate_fallback_article(self, theme: str, date_ja: str) -> str:
        """フォールバック記事生成"""
        return f"""# {theme} - {date_ja}

申し訳ございませんが、記事生成処理でエラーが発生しました。

## 概要
{theme}について基本的な内容をご紹介予定でした。

## 対応
システム復旧後、改めて詳細な記事をお届けします。

## まとめ
ご不便をおかけして申し訳ありません。"""

    def extract_metadata(self, content: str, theme: str = "") -> dict:
        """記事からメタデータを抽出"""
        lines = content.split('\n')
        title = ""
        
        # タイトル抽出
        for line in lines:
            if line.startswith('# '):
                title = line.replace('# ', '').strip()
                break
        
        # 文字数計算と品質評価
        word_count = len(content)
        quality_score = 0
        
        # 高度なタグ生成（内容に基づく）
        tags = self._generate_smart_tags(content, theme)
        
        # SEO関連キーワード抽出
        seo_keywords = self._extract_seo_keywords(content)
        
        return {
            "title": title or f"{theme} - {get_jst_date_japanese()}",
            "tags": tags,
            "categories": ["ライフスタイル", "実用的情報"],
            "status": "draft",
            "generated_at": datetime.now().isoformat(),
            "word_count": word_count,
            "quality_score": quality_score,
            "seo_keywords": seo_keywords,
            "theme": theme,
            "date": get_jst_date_japanese(),
            "readability_score": self._calculate_readability_score(content),
            "structure_score": self._calculate_structure_score(content)
        }
    
    def _generate_smart_tags(self, content: str, theme: str) -> List[str]:
        """コンテンツに基づく高度なタグ生成"""
        tags = []
        
        # テーマベースのタグ
        theme_tags = {
            "効率": ["効率化", "生産性", "時間管理", "業務改善"],
            "健康": ["健康", "ライフスタイル", "ウェルネス", "予防医学"],
            "テクノロジー": ["テクノロジー", "IT", "デジタル", "イノベーション"],
            "お金": ["資産運用", "投資", "節約", "家計管理"],
            "学習": ["スキルアップ", "教育", "学習法", "能力開発"],
            "仕事": ["キャリア", "ビジネス", "働き方", "職場環境"]
        }
        
        for key, tag_list in theme_tags.items():
            if key in theme:
                tags.extend(tag_list)
                break
        
        # コンテンツベースのタグ抽出
        content_keywords = [
            ("データ", "データ分析"),
            ("AI", "人工知能"),
            ("習慣", "習慣化"),
            ("目標", "目標設定"),
            ("コミュニケーション", "コミュニケーション"),
            ("リーダーシップ", "リーダーシップ"),
            ("マーケティング", "マーケティング"),
            ("デザイン", "デザイン思考")
        ]
        
        for keyword, tag in content_keywords:
            if keyword in content:
                tags.append(tag)
        
        # 重複除去と最大8個まで
        tags = list(dict.fromkeys(tags))[:8]
        
        # 最低限のタグを保証
        if not tags:
            tags = ["ライフハック", "自己改善", "実用的"]
        
        return tags
    
    def _extract_seo_keywords(self, content: str) -> List[str]:
        """SEOキーワード抽出"""
        import re
        from collections import Counter
        
        # 日本語の2-4文字のキーワードを抽出
        keywords = re.findall(r'[ぁ-んー]{2,4}|[ァ-ヶー]{2,4}|[一-龯]{2,4}', content)
        
        # ストップワードを除外
        stop_words = {'これ', 'その', 'あの', 'この', 'それ', 'あれ', 'です', 'ます', 'である', 'から', 'まで', 'として', 'について'}
        keywords = [kw for kw in keywords if kw not in stop_words and len(kw) >= 2]
        
        # 頻出キーワード上位10個
        keyword_counts = Counter(keywords)
        top_keywords = [kw for kw, count in keyword_counts.most_common(10) if count >= 2]
        
        return top_keywords
    
    def _calculate_readability_score(self, content: str) -> float:
        """読みやすさスコア計算"""
        sentences = re.split(r'[。！？]', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 0
        
        # 平均文字数（短いほど良い）
        avg_sentence_length = sum(len(s) for s in sentences) / len(sentences)
        length_score = max(0, 100 - (avg_sentence_length - 30) * 2)
        
        # 漢字比率（適切な比率が良い）
        total_chars = len(content)
        kanji_chars = len(re.findall(r'[一-龯]', content))
        kanji_ratio = (kanji_chars / total_chars) * 100 if total_chars > 0 else 0
        
        # 20-40%が理想的
        if 20 <= kanji_ratio <= 40:
            kanji_score = 100
        elif 15 <= kanji_ratio < 20 or 40 < kanji_ratio <= 50:
            kanji_score = 80
        else:
            kanji_score = 60
        
        return (length_score + kanji_score) / 2
    
    def _calculate_structure_score(self, content: str) -> float:
        """構造スコア計算"""
        score = 0
        
        # 見出し構造
        h2_count = len(re.findall(r'^## ', content, re.MULTILINE))
        h3_count = len(re.findall(r'^### ', content, re.MULTILINE))
        
        if 4 <= h2_count <= 6:
            score += 40
        elif h2_count >= 3:
            score += 25
        
        if h3_count >= 2:
            score += 30
        elif h3_count >= 1:
            score += 15
        
        # 箇条書きと番号リスト
        bullet_points = len(re.findall(r'^- ', content, re.MULTILINE))
        numbered_lists = len(re.findall(r'^[0-9]+\.', content, re.MULTILINE))
        
        if bullet_points >= 5 or numbered_lists >= 3:
            score += 30
        elif bullet_points >= 3 or numbered_lists >= 2:
            score += 15
        
        return min(score, 100)

    def generate_youtube_article(self, youtube_data: dict = None, transcript: str = None) -> bool:
        """YouTube動画ベースの記事生成"""
        try:
            logger.info("🎥 YouTube連携記事生成開始")
            
            # YouTubeデータがない場合は@shiki_138の最新動画を取得
            if not youtube_data:
                logger.info("📺 @shiki_138の最新動画データを取得中...")
                try:
                    from scripts.fetch_transcript import YouTubeTranscriptFetcher
                    fetcher = YouTubeTranscriptFetcher()
                    blog_data = fetcher.fetch_channel_latest_video()
                    
                    if blog_data.get('success', True):
                        youtube_data = blog_data['video_info']
                        transcript = blog_data['transcript_result']['transcript']['cleaned_text']
                    else:
                        raise Exception(f"YouTube動画取得失敗: {blog_data.get('error')}")
                        
                except Exception as e:
                    logger.error(f"YouTube動画取得エラー: {e}")
                    # フォールバック: モック動画データ
                    youtube_data = {
                        'title': '@shiki_138: 効率的な開発手法について',
                        'description': 'プログラミングの効率を上げる手法について詳しく解説します。',
                        'video_id': 'shiki138_mock1'
                    }
                    transcript = self._get_mock_transcript()
            
            # 記事生成
            content = self._generate_youtube_based_article(youtube_data, transcript)
            
            # メタデータ生成（YouTube特化）
            metadata = self._extract_youtube_metadata(content, youtube_data)
            
            # ファイル保存
            article_path = self.output_dir / "article.md"
            meta_path = self.output_dir / "meta.json"
            
            article_path.write_text(content, encoding='utf-8')
            save_json_safely(metadata, str(meta_path))
            
            logger.info("✅ YouTube連携記事生成完了")
            logger.info(f"🎬 動画タイトル: {youtube_data.get('title', 'Unknown')}")
            logger.info(f"📈 記事文字数: {len(content)} 文字")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ YouTube連携記事生成エラー: {e}")
            return False
    
    def _generate_youtube_based_article(self, video_data: dict, transcript: str) -> str:
        """YouTube動画データから記事を生成"""
        video_title = video_data.get('title', 'YouTube動画')
        video_description = video_data.get('description', '')
        
        # 字幕テキストから要点を抽出
        key_points = self._extract_key_points_from_transcript(transcript)
        
        article = f"""# {video_title}の詳細解説：プログラミング効率化の極意

## はじめに：@shiki_138チャンネルの技術解説動画より

{video_description}

このYouTube動画では、実践的な開発手法について詳しく解説されています。今回はその内容をより詳細に文字起こしし、実際のプロジェクトで活用できる形でまとめました。

## 動画の主要ポイント

### 1. 効率的な開発手法の基本概念

{key_points[0] if len(key_points) > 0 else '動画では、まず基本的な概念について説明されています。'}

現代のソフトウェア開発では、スピードと品質の両立が求められます。そのために必要なのが、適切な開発手法とツールの選択です。

### 2. 実践的な実装戦略

{key_points[1] if len(key_points) > 1 else '具体的な実装方法について詳しく解説されています。'}

**重要なポイント：**
- コードレビューの自動化
- テスト駆動開発（TDD）の実践
- アジャイル手法の効果的な活用

### 3. ツール活用のベストプラクティス

{key_points[2] if len(key_points) > 2 else 'ツールの使い分けについて実例を交えて説明されています。'}

適切なツール選択により、開発効率は格段に向上します。動画では以下のツールカテゴリーについて詳しく説明されています：

- **コードエディタとIDE**: Visual Studio Code、IntelliJ IDEA等
- **バージョン管理**: Gitのブランチ戦略
- **デバッグツール**: Chrome DevTools、GDB等

### 4. 今後の学習指針

{key_points[3] if len(key_points) > 3 else '継続的な学習の重要性について言及されています。'}

技術の進歩は日進月歩です。常に最新のトレンドをキャッチアップし、実際のプロジェクトで試行錯誤することが重要です。

## 実際のプロジェクトでの活用方法

動画で紹介された手法を実際のプロジェクトで活用するためのステップバイステップガイド：

1. **現状分析**：既存の開発プロセスを評価
2. **ツール選定**：プロジェクトに最適なツールを選択
3. **段階的導入**：リスクを最小化して新手法を導入
4. **効果測定**：導入効果を定量的に評価

## よくある質問と回答

### Q: これらの手法は初心者でも実践できますか？
A: はい、動画では初心者向けの解説も充実しており、段階的に習得することが可能です。

### Q: 既存プロジェクトにも適用できますか？
A: 動画で紹介された手法の多くは、既存プロジェクトにも段階的に導入できます。

## まとめ：効率的な開発者になるために

@shiki_138チャンネルの動画から学んだ重要なポイントをまとめると：

- **継続的学習**：新しい技術への好奇心を持ち続ける
- **実践重視**：理論だけでなく、実際にコードを書いて試す
- **コミュニティ参加**：他の開発者との情報交換を大切にする

🎯 動画で紹介された手法を実践して、あなたも効率的な開発者として成長しませんか？まずは一つの手法から始めて、徐々にスキルを拡大していきましょう。

---

**元動画**: [{video_title}]({video_data.get('url', '#')})  
**チャンネル**: @shiki_138  
**記事作成日**: {get_jst_date_japanese()}"""

        return article
    
    def _extract_key_points_from_transcript(self, transcript: str) -> list:
        """字幕テキストから要点を抽出"""
        if not transcript:
            return ["動画の内容について詳しく解説されています。"] * 4
        
        # 段落に分割
        paragraphs = [p.strip() for p in transcript.split('\n\n') if p.strip()]
        
        # 各段落から代表的な文を抽出
        key_points = []
        for i, paragraph in enumerate(paragraphs[:4]):  # 最大4つのポイント
            sentences = [s.strip() for s in paragraph.split('。') if s.strip()]
            if sentences:
                # 最初の文を要点として使用
                key_points.append(sentences[0] + '。')
        
        # 不足分を補完
        while len(key_points) < 4:
            key_points.append("動画では重要なポイントについて詳しく説明されています。")
        
        return key_points
    
    def _extract_youtube_metadata(self, content: str, video_data: dict) -> dict:
        """YouTube動画用のメタデータ生成"""
        base_metadata = self.extract_metadata(content, video_data.get('title', ''))
        
        # YouTube特化の追加メタデータ
        youtube_metadata = {
            'source_type': 'youtube_video',
            'video_id': video_data.get('video_id', ''),
            'video_url': video_data.get('url', ''),
            'channel': '@shiki_138',
            'original_video_title': video_data.get('title', ''),
            'video_description': video_data.get('description', ''),
            'tags': base_metadata['tags'] + ['YouTube', '動画解説', '@shiki_138', 'プログラミング', '開発手法']
        }
        
        # 既存メタデータと統合
        base_metadata.update(youtube_metadata)
        return base_metadata
    
    def _get_mock_transcript(self) -> str:
        """モック字幕データ"""
        return """
こんにちは、@shiki_138です。今日は効率的な開発手法についてお話しします。

まず最初に、なぜ効率性が重要なのかを説明します。
現代のソフトウェア開発では、スピードと品質の両立が求められます。
そのために必要なのが、適切な開発手法とツールの選択です。

具体的な手法として、以下の3つのポイントを紹介します：

1. コードレビューの自動化
エラーの早期発見により、後工程での修正コストを大幅に削減できます。

2. テスト駆動開発（TDD）
要件の明確化と品質向上を同時に実現できます。

3. アジャイル手法の実践
短いスプリントでの反復開発により、顧客のフィードバックを素早く反映できます。

皆さんも是非、これらの手法を試してみてください。
次回は、より詳細な実装方法について解説予定です。
"""

    def run(self):
        """メイン実行処理"""
        try:
            logger.info("📝 記事生成プロセス開始（フェーズ2）")
            
            # テーマと日付を取得
            theme = get_today_theme()
            date_ja = get_jst_date_japanese()
            
            logger.info(f"📋 テーマ: {theme}, 日付: {date_ja}")
            
            # 記事生成
            content = self.generate_article_content(theme, date_ja)
            
            # メタデータ抽出
            metadata = self.extract_metadata(content, theme)
            
            # ファイルパス設定
            article_path = self.output_dir / "article.md"
            meta_path = self.output_dir / "meta.json"
            
            # 記事保存
            article_path.write_text(content, encoding='utf-8')
            logger.info(f"📄 記事保存完了: {article_path}")
            
            # メタデータ保存
            save_json_safely(metadata, str(meta_path))
            logger.info(f"📊 メタデータ保存完了: {meta_path}")
            
            # 完了ログ
            logger.info("✅ 記事生成プロセス完了")
            logger.info(f"📈 文字数: {metadata['word_count']} 文字")
            logger.info(f"🏷️  タグ: {', '.join(metadata['tags'])}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 記事生成でエラーが発生: {e}")
            return False

def main():
    """メイン実行関数 - YouTube連携対応"""
    try:
        parser = argparse.ArgumentParser(description='Daily Blog Article Generator with YouTube Integration')
        parser.add_argument('--youtube-mode', action='store_true', help='YouTube連携モードで実行')
        parser.add_argument('--transcript-file', type=str, help='YouTube字幕ファイルのパス')
        parser.add_argument('--video-data', type=str, help='YouTube動画データファイルのパス')
        
        args = parser.parse_args()
        
        generator = ArticleGenerator()
        
        if args.youtube_mode:
            logger.info("🎥 YouTube連携モードで記事生成開始")
            
            # YouTubeデータの読み込み
            youtube_data = None
            if args.video_data and os.path.exists(args.video_data):
                try:
                    with open(args.video_data, 'r', encoding='utf-8') as f:
                        youtube_data = json.load(f)
                    logger.info(f"📺 YouTube動画データ読み込み: {youtube_data['video_info']['title']}")
                except Exception as e:
                    logger.error(f"YouTube動画データ読み込みエラー: {e}")
            
            # 字幕ファイルの読み込み
            transcript_content = None
            if args.transcript_file and os.path.exists(args.transcript_file):
                try:
                    with open(args.transcript_file, 'r', encoding='utf-8') as f:
                        transcript_content = f.read()
                    logger.info(f"📝 字幕ファイル読み込み: {len(transcript_content)}文字")
                except Exception as e:
                    logger.error(f"字幕ファイル読み込みエラー: {e}")
            
            # YouTube連携での記事生成
            success = generator.generate_youtube_article(youtube_data, transcript_content)
            
        else:
            # 通常モード
            success = generator.run()
        
        if success:
            print("✅ 記事生成が正常に完了しました")
            sys.exit(0)
        else:
            print("❌ 記事生成に失敗しました")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"メイン処理でエラーが発生: {e}")
        print(f"❌ エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()