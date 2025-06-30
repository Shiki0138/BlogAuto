#!/usr/bin/env python3
"""
YouTube連携ワークフロー統合スクリプト
@shiki_138チャンネルの動画をブログ記事に変換する完全自動化システム
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
import json

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

try:
    from scripts.utils import logger, ensure_output_dir, save_json_safely
    from scripts.fetch_transcript import YouTubeTranscriptFetcher
    from scripts.generate_article import ArticleGenerator
except ImportError:
    # フォールバック実装
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    def ensure_output_dir():
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        return output_dir
    
    def save_json_safely(data, file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

class YouTubeWorkflow:
    """@shiki_138チャンネル向けYouTube連携ワークフロー"""
    
    def __init__(self):
        self.output_dir = ensure_output_dir()
        self.channel = "@shiki_138"
        logger.info(f"YouTubeWorkflow initialized for {self.channel}")
    
    def run_full_workflow(self) -> dict:
        """完全自動YouTube連携ワークフロー実行"""
        try:
            logger.info("🎬 YouTube連携ワークフロー開始")
            
            workflow_result = {
                'workflow_id': f"youtube_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'start_time': datetime.now().isoformat(),
                'channel': self.channel,
                'steps': {},
                'success': False
            }
            
            # ステップ1: YouTube動画データ取得
            logger.info("📺 ステップ1: @shiki_138の最新動画取得")
            step1_result = self._step1_fetch_youtube_data()
            workflow_result['steps']['fetch_youtube_data'] = step1_result
            
            if not step1_result['success']:
                raise Exception("YouTube動画データ取得に失敗")
            
            # ステップ2: 記事生成
            logger.info("📝 ステップ2: YouTube動画ベース記事生成")
            step2_result = self._step2_generate_article(step1_result['data'])
            workflow_result['steps']['generate_article'] = step2_result
            
            if not step2_result['success']:
                raise Exception("記事生成に失敗")
            
            # ステップ3: 品質チェック
            logger.info("🔍 ステップ3: 記事品質チェック")
            step3_result = self._step3_quality_check()
            workflow_result['steps']['quality_check'] = step3_result
            
            # ステップ4: 出力統合
            logger.info("📋 ステップ4: 出力ファイル統合")
            step4_result = self._step4_integrate_outputs(workflow_result)
            workflow_result['steps']['integrate_outputs'] = step4_result
            
            # 完了処理
            workflow_result['end_time'] = datetime.now().isoformat()
            workflow_result['success'] = True
            workflow_result['message'] = "@shiki_138チャンネル連携ワークフロー完了"
            
            # ワークフロー結果保存
            result_file = self.output_dir / 'youtube_workflow_result.json'
            save_json_safely(workflow_result, result_file)
            
            logger.info("✅ YouTube連携ワークフロー完了")
            logger.info(f"📊 結果ファイル: {result_file}")
            
            return workflow_result
            
        except Exception as e:
            logger.error(f"❌ YouTube連携ワークフロー失敗: {e}")
            
            error_result = {
                'workflow_id': f"youtube_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'start_time': workflow_result.get('start_time', datetime.now().isoformat()),
                'end_time': datetime.now().isoformat(),
                'channel': self.channel,
                'success': False,
                'error': str(e),
                'steps': workflow_result.get('steps', {})
            }
            
            return error_result
    
    def _step1_fetch_youtube_data(self) -> dict:
        """ステップ1: YouTube動画データ取得"""
        try:
            fetcher = YouTubeTranscriptFetcher()
            blog_data = fetcher.fetch_channel_latest_video()
            
            if blog_data.get('success', True):
                return {
                    'success': True,
                    'data': blog_data,
                    'video_title': blog_data['video_info']['title'],
                    'video_id': blog_data['video_info']['video_id'],
                    'transcript_length': len(blog_data['transcript_result']['transcript']['cleaned_text']),
                    'execution_time': datetime.now().isoformat()
                }
            else:
                raise Exception(f"YouTube動画取得失敗: {blog_data.get('error')}")
                
        except Exception as e:
            logger.error(f"ステップ1エラー: {e}")
            return {
                'success': False,
                'error': str(e),
                'execution_time': datetime.now().isoformat()
            }
    
    def _step2_generate_article(self, youtube_data: dict) -> dict:
        """ステップ2: 記事生成"""
        try:
            generator = ArticleGenerator()
            
            # YouTube連携記事生成
            success = generator.generate_youtube_article(
                youtube_data['video_info'],
                youtube_data['transcript_result']['transcript']['cleaned_text']
            )
            
            if success:
                # 生成された記事の情報を取得
                article_path = generator.output_dir / "article.md"
                meta_path = generator.output_dir / "meta.json"
                
                article_content = ""
                metadata = {}
                
                if article_path.exists():
                    article_content = article_path.read_text(encoding='utf-8')
                
                if meta_path.exists():
                    with open(meta_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                
                return {
                    'success': True,
                    'article_length': len(article_content),
                    'article_title': metadata.get('title', 'Unknown'),
                    'word_count': metadata.get('word_count', 0),
                    'tags_count': len(metadata.get('tags', [])),
                    'execution_time': datetime.now().isoformat()
                }
            else:
                raise Exception("記事生成に失敗")
                
        except Exception as e:
            logger.error(f"ステップ2エラー: {e}")
            return {
                'success': False,
                'error': str(e),
                'execution_time': datetime.now().isoformat()
            }
    
    def _step3_quality_check(self) -> dict:
        """ステップ3: 品質チェック"""
        try:
            article_path = self.output_dir / "article.md"
            
            if not article_path.exists():
                raise Exception("記事ファイルが見つかりません")
            
            content = article_path.read_text(encoding='utf-8')
            
            # 基本的な品質チェック
            checks = {
                'length_check': len(content) >= 1800,  # 最低文字数
                'title_check': content.startswith('#'),  # タイトルの存在
                'structure_check': '##' in content,  # 見出し構造
                'youtube_reference': '@shiki_138' in content,  # YouTube参照
                'link_check': 'youtube.com' in content or 'youtu.be' in content  # 動画リンク
            }
            
            passed_checks = sum(checks.values())
            total_checks = len(checks)
            quality_score = (passed_checks / total_checks) * 100
            
            return {
                'success': True,
                'quality_score': quality_score,
                'passed_checks': passed_checks,
                'total_checks': total_checks,
                'check_details': checks,
                'execution_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"ステップ3エラー: {e}")
            return {
                'success': False,
                'error': str(e),
                'execution_time': datetime.now().isoformat()
            }
    
    def _step4_integrate_outputs(self, workflow_result: dict) -> dict:
        """ステップ4: 出力統合"""
        try:
            # YouTube連携用の統合メタデータ生成
            integration_data = {
                'workflow_type': 'youtube_integration',
                'channel': self.channel,
                'workflow_id': workflow_result['workflow_id'],
                'processing_summary': {
                    'video_title': workflow_result['steps']['fetch_youtube_data']['data']['video_info']['title'],
                    'article_title': workflow_result['steps']['generate_article']['article_title'],
                    'quality_score': workflow_result['steps']['quality_check']['quality_score'],
                    'article_length': workflow_result['steps']['generate_article']['article_length']
                },
                'files_generated': [
                    'output/article.md',
                    'output/meta.json',
                    'output/transcript.txt',
                    'output/transcript_meta.json',
                    'output/shiki138_latest_blog_data.json',
                    'output/youtube_workflow_result.json'
                ],
                'integration_timestamp': datetime.now().isoformat()
            }
            
            # 統合ファイル保存
            integration_file = self.output_dir / 'youtube_integration_summary.json'
            save_json_safely(integration_data, integration_file)
            
            return {
                'success': True,
                'integration_file': str(integration_file),
                'files_count': len(integration_data['files_generated']),
                'execution_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"ステップ4エラー: {e}")
            return {
                'success': False,
                'error': str(e),
                'execution_time': datetime.now().isoformat()
            }

def main():
    """メイン処理"""
    
    print("🎬 YouTube連携ワークフロー (@shiki_138)")
    print("=" * 50)
    
    workflow = YouTubeWorkflow()
    result = workflow.run_full_workflow()
    
    if result['success']:
        print("✅ YouTube連携ワークフロー完了!")
        print(f"📺 チャンネル: {result['channel']}")
        print(f"🎯 品質スコア: {result['steps']['quality_check']['quality_score']:.1f}%")
        print(f"📄 記事文字数: {result['steps']['generate_article']['article_length']} 文字")
        print(f"📁 結果ファイル: output/youtube_workflow_result.json")
    else:
        print(f"❌ ワークフロー失敗: {result['error']}")
        
    return result['success']

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)