#!/usr/bin/env python3
"""
パイプラインオーケストレーター - フェーズ3実装
全コンポーネントの統合実行とワークフロー管理
"""
import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from scripts.utils import (
    logger, ensure_output_dir, save_json_safely,
    get_jst_now, health_checker, performance_monitor,
    run_integration_test
)

class PipelineOrchestrator:
    """パイプライン統合実行クラス"""
    
    def __init__(self, enable_external_api: bool = False):
        """初期化
        
        Args:
            enable_external_api: 外部API接続を有効化するか
        """
        self.output_dir = ensure_output_dir()
        self.execution_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.enable_external_api = enable_external_api
        
        # 環境変数設定
        if self.enable_external_api:
            os.environ['ENABLE_EXTERNAL_API'] = 'true'
            logger.info("🌐 外部API接続モード有効")
        else:
            os.environ['ENABLE_EXTERNAL_API'] = 'false'
            logger.info("🔒 ローカルモード（外部API接続無効）")
        
        self.pipeline_state = {
            "execution_id": self.execution_id,
            "start_time": None,
            "end_time": None,
            "stages": {},
            "overall_status": "pending",
            "external_api_enabled": self.enable_external_api
        }
        
    def execute_stage(self, stage_name: str, script_path: str, 
                     required_files: List[str] = None, 
                     output_files: List[str] = None) -> bool:
        """ステージ実行"""
        try:
            logger.info(f"ステージ開始: {stage_name}")
            
            stage_start = time.time()
            
            # 前提条件チェック
            if required_files:
                missing_files = [f for f in required_files if not Path(f).exists()]
                if missing_files:
                    logger.error(f"必要ファイルが不足: {missing_files}")
                    self.pipeline_state["stages"][stage_name] = {
                        "status": "failed",
                        "error": f"Missing files: {missing_files}",
                        "duration": 0
                    }
                    return False
            
            # スクリプト実行
            import subprocess
            result = subprocess.run(
                ['python', script_path],
                capture_output=True,
                text=True,
                timeout=300  # 5分タイムアウト
            )
            
            stage_duration = time.time() - stage_start
            
            if result.returncode == 0:
                # 出力ファイル確認
                if output_files:
                    missing_outputs = [f for f in output_files if not Path(f).exists()]
                    if missing_outputs:
                        logger.warning(f"期待される出力ファイルが見つかりません: {missing_outputs}")
                
                self.pipeline_state["stages"][stage_name] = {
                    "status": "success",
                    "duration": stage_duration,
                    "stdout": result.stdout,
                    "output_files": output_files or []
                }
                logger.info(f"ステージ完了: {stage_name} ({stage_duration:.2f}秒)")
                return True
            else:
                self.pipeline_state["stages"][stage_name] = {
                    "status": "failed",
                    "duration": stage_duration,
                    "error": result.stderr,
                    "stdout": result.stdout
                }
                logger.error(f"ステージ失敗: {stage_name} - {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.pipeline_state["stages"][stage_name] = {
                "status": "timeout",
                "duration": 300,
                "error": "Script execution timeout"
            }
            logger.error(f"ステージタイムアウト: {stage_name}")
            return False
        except Exception as e:
            self.pipeline_state["stages"][stage_name] = {
                "status": "error",
                "duration": 0,
                "error": str(e)
            }
            logger.error(f"ステージエラー: {stage_name} - {e}")
            return False
    
    def run_full_pipeline(self) -> bool:
        """完全パイプライン実行"""
        try:
            logger.info("ブログ自動化パイプライン開始")
            self.pipeline_state["start_time"] = get_jst_now().isoformat()
            
            # ステージ1: 記事生成
            success1 = self.execute_stage(
                stage_name="article_generation",
                script_path="scripts/generate_article.py",
                output_files=["output/article.md", "output/meta.json"]
            )
            
            if not success1:
                logger.error("記事生成に失敗しました")
                self.pipeline_state["overall_status"] = "failed"
                return False
            
            # ステージ2: 画像取得
            success2 = self.execute_stage(
                stage_name="image_fetching",
                script_path="scripts/fetch_image.py",
                output_files=["output/image_info.json"]
            )
            
            # 画像取得は失敗しても続行
            if not success2:
                logger.warning("画像取得に失敗しましたが、処理を続行します")
            
            # ステージ3: WordPress投稿
            success3 = self.execute_stage(
                stage_name="wordpress_posting",
                script_path="scripts/post_to_wp.py",
                required_files=["output/article.md", "output/meta.json"],
                output_files=["output/wp_result.json"]
            )
            
            if not success3:
                logger.error("WordPress投稿に失敗しました")
                self.pipeline_state["overall_status"] = "failed"
                return False
            
            # パイプライン完了
            self.pipeline_state["end_time"] = get_jst_now().isoformat()
            self.pipeline_state["overall_status"] = "success"
            
            # パフォーマンス情報追加
            total_duration = sum(
                stage.get("duration", 0) 
                for stage in self.pipeline_state["stages"].values()
            )
            self.pipeline_state["total_duration"] = total_duration
            
            logger.info(f"パイプライン完了 (合計時間: {total_duration:.2f}秒)")
            return True
            
        except Exception as e:
            logger.error(f"パイプライン実行エラー: {e}")
            self.pipeline_state["overall_status"] = "error"
            self.pipeline_state["error"] = str(e)
            return False
        
        finally:
            # 実行結果保存
            self.save_pipeline_report()
    
    def save_pipeline_report(self):
        """パイプライン実行レポート保存"""
        try:
            report_path = self.output_dir / f"pipeline_report_{self.execution_id}.json"
            save_json_safely(self.pipeline_state, str(report_path))
            
            # 最新レポートとしてもコピー
            latest_report_path = self.output_dir / "pipeline_report_latest.json"
            save_json_safely(self.pipeline_state, str(latest_report_path))
            
            logger.info(f"パイプラインレポート保存: {report_path}")
        except Exception as e:
            logger.error(f"レポート保存エラー: {e}")
    
    def run_health_check(self) -> bool:
        """ヘルスチェック実行"""
        try:
            logger.info("システムヘルスチェック開始")
            
            health_results = health_checker.run_all_checks()
            
            # ヘルスチェック結果保存
            health_report_path = self.output_dir / "health_check_latest.json"
            save_json_safely(health_results, str(health_report_path))
            
            is_healthy = health_results["overall_status"] == "healthy"
            
            if is_healthy:
                logger.info("システムヘルスチェック: 正常")
            else:
                logger.warning("システムヘルスチェック: 問題あり")
                for check_name, check_result in health_results["checks"].items():
                    if check_result["status"] != "pass":
                        logger.warning(f"  - {check_name}: {check_result}")
            
            return is_healthy
            
        except Exception as e:
            logger.error(f"ヘルスチェックエラー: {e}")
            return False
    
    def run_integration_tests(self) -> bool:
        """統合テスト実行"""
        try:
            logger.info("統合テスト開始")
            return run_integration_test()
        except Exception as e:
            logger.error(f"統合テストエラー: {e}")
            return False

class WorkflowManager:
    """ワークフロー管理クラス"""
    
    def __init__(self, enable_external_api: bool = False):
        self.orchestrator = PipelineOrchestrator(enable_external_api)
        
    def run_daily_workflow(self) -> bool:
        """日次ワークフロー実行"""
        try:
            logger.info("=== 日次ワークフロー開始 ===")
            
            # 1. ヘルスチェック
            health_ok = self.orchestrator.run_health_check()
            if not health_ok:
                logger.warning("ヘルスチェックで問題が検出されましたが、処理を続行します")
            
            # 2. 統合テスト（オプション）
            if os.getenv('RUN_INTEGRATION_TESTS', 'false').lower() == 'true':
                test_ok = self.orchestrator.run_integration_tests()
                if not test_ok:
                    logger.error("統合テストに失敗しました")
                    return False
            
            # 3. メインパイプライン実行
            pipeline_ok = self.orchestrator.run_full_pipeline()
            
            if pipeline_ok:
                logger.info("=== 日次ワークフロー正常完了 ===")
            else:
                logger.error("=== 日次ワークフロー失敗 ===")
            
            return pipeline_ok
            
        except Exception as e:
            logger.error(f"ワークフローエラー: {e}")
            return False
    
    def run_test_workflow(self) -> bool:
        """テストワークフロー実行"""
        try:
            logger.info("=== テストワークフロー開始 ===")
            
            # ヘルスチェックのみ実行
            health_ok = self.orchestrator.run_health_check()
            
            # 統合テスト実行
            test_ok = self.orchestrator.run_integration_tests()
            
            success = health_ok and test_ok
            
            if success:
                logger.info("=== テストワークフロー正常完了 ===")
            else:
                logger.error("=== テストワークフロー失敗 ===")
            
            return success
            
        except Exception as e:
            logger.error(f"テストワークフローエラー: {e}")
            return False

def main():
    """メイン関数"""
    import argparse
    
    try:
        parser = argparse.ArgumentParser(description='BlogAuto Pipeline Orchestrator')
        parser.add_argument(
            'workflow_type',
            choices=['daily', 'test', 'health', 'integration', 'api-test'],
            nargs='?',
            default='daily',
            help='実行ワークフロー: daily（日次実行）, test（テスト）, health（ヘルスチェック）, integration（統合テスト）, api-test（API統合テスト）'
        )
        parser.add_argument(
            '--enable-api',
            action='store_true',
            help='外部API接続を有効化'
        )
        
        args = parser.parse_args()
        
        # API統合テストモードの場合は自動的にAPI有効化
        if args.workflow_type == 'api-test':
            args.enable_api = True
        
        manager = WorkflowManager(enable_external_api=args.enable_api)
        
        if args.workflow_type in ['test', 'api-test']:
            success = manager.run_test_workflow()
        elif args.workflow_type == 'health':
            success = manager.orchestrator.run_health_check()
        elif args.workflow_type == 'integration':
            success = manager.orchestrator.run_integration_tests()
        else:
            success = manager.run_daily_workflow()
        
        if success:
            print(f"ワークフロー({args.workflow_type})が正常完了しました")
            if args.enable_api:
                print("✅ 外部API統合テスト完了")
            sys.exit(0)
        else:
            print(f"ワークフロー({args.workflow_type})が失敗しました")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"メイン処理エラー: {e}")
        print(f"エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()