#!/usr/bin/env python3
"""
エラーハンドリング強化モジュール - フェーズ3実装
共通エラーハンドラーとリトライ機能
"""
import os
import sys
import functools
import time
import traceback
from typing import Callable, Any, Optional, Dict, List, Union
from datetime import datetime
import json
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from scripts.utils import logger, save_json_safely


class BlogAutoError(Exception):
    """BlogAuto基本例外クラス"""
    def __init__(self, message: str, error_code: str = "UNKNOWN", 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()


class APIError(BlogAutoError):
    """API関連エラー"""
    def __init__(self, service: str, message: str, 
                 status_code: Optional[int] = None,
                 response_body: Optional[str] = None):
        super().__init__(
            message,
            error_code=f"API_ERROR_{service.upper()}",
            details={
                "service": service,
                "status_code": status_code,
                "response_body": response_body
            }
        )


class FileOperationError(BlogAutoError):
    """ファイル操作エラー"""
    def __init__(self, operation: str, filepath: str, message: str):
        super().__init__(
            message,
            error_code=f"FILE_{operation.upper()}_ERROR",
            details={
                "operation": operation,
                "filepath": filepath
            }
        )


class ValidationError(BlogAutoError):
    """検証エラー"""
    def __init__(self, field: str, value: Any, message: str):
        super().__init__(
            message,
            error_code="VALIDATION_ERROR",
            details={
                "field": field,
                "value": str(value)[:100]  # 長い値は切り詰め
            }
        )


class ConfigurationError(BlogAutoError):
    """設定エラー"""
    def __init__(self, config_name: str, message: str):
        super().__init__(
            message,
            error_code="CONFIG_ERROR",
            details={
                "config_name": config_name
            }
        )


class ErrorHandler:
    """統合エラーハンドラー"""
    
    def __init__(self, error_log_dir: str = "logs/errors"):
        self.error_log_dir = Path(error_log_dir)
        self.error_log_dir.mkdir(parents=True, exist_ok=True)
        self.error_history: List[Dict[str, Any]] = []
        self.max_history = 100
        
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """エラーを処理し記録"""
        error_info = self._extract_error_info(error, context)
        
        # ログ出力
        self._log_error(error_info)
        
        # エラー履歴に追加
        self._add_to_history(error_info)
        
        # エラーレポート保存
        self._save_error_report(error_info)
        
    def _extract_error_info(self, error: Exception, 
                           context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """エラー情報を抽出"""
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "traceback": traceback.format_exc()
        }
        
        # BlogAutoError の場合は追加情報を含める
        if isinstance(error, BlogAutoError):
            error_info.update({
                "error_code": error.error_code,
                "details": error.details
            })
        
        # 環境情報を追加
        error_info["environment"] = {
            "python_version": sys.version,
            "platform": sys.platform,
            "cwd": os.getcwd()
        }
        
        return error_info
    
    def _log_error(self, error_info: Dict[str, Any]) -> None:
        """エラーをログ出力"""
        error_type = error_info["error_type"]
        error_message = error_info["error_message"]
        error_code = error_info.get("error_code", "UNKNOWN")
        
        log_message = f"[{error_code}] {error_type}: {error_message}"
        
        # コンテキスト情報があれば追加
        if error_info.get("context"):
            log_message += f"\nContext: {json.dumps(error_info['context'], ensure_ascii=False)}"
        
        # 詳細情報があれば追加
        if error_info.get("details"):
            log_message += f"\nDetails: {json.dumps(error_info['details'], ensure_ascii=False)}"
        
        logger.error(log_message)
        
        # デバッグモードの場合はトレースバックも出力
        if os.getenv("DEBUG", "false").lower() == "true":
            logger.debug(f"Traceback:\n{error_info['traceback']}")
    
    def _add_to_history(self, error_info: Dict[str, Any]) -> None:
        """エラー履歴に追加"""
        self.error_history.append(error_info)
        
        # 履歴サイズ制限
        if len(self.error_history) > self.max_history:
            self.error_history = self.error_history[-self.max_history:]
    
    def _save_error_report(self, error_info: Dict[str, Any]) -> None:
        """エラーレポートを保存"""
        try:
            # 日付別ディレクトリ作成
            date_str = datetime.now().strftime("%Y%m%d")
            day_dir = self.error_log_dir / date_str
            day_dir.mkdir(exist_ok=True)
            
            # エラーレポートファイル名
            timestamp = datetime.now().strftime("%H%M%S")
            error_code = error_info.get("error_code", "UNKNOWN")
            filename = f"error_{error_code}_{timestamp}.json"
            
            # 保存
            filepath = day_dir / filename
            save_json_safely(error_info, str(filepath))
            
        except Exception as e:
            # エラーレポート保存自体が失敗した場合は、ログのみ出力
            logger.warning(f"エラーレポート保存失敗: {e}")
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """指定時間内のエラーサマリーを取得"""
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        
        recent_errors = [
            err for err in self.error_history
            if datetime.fromisoformat(err["timestamp"]).timestamp() > cutoff_time
        ]
        
        # エラータイプ別集計
        error_types = {}
        for err in recent_errors:
            err_type = err["error_type"]
            error_types[err_type] = error_types.get(err_type, 0) + 1
        
        # エラーコード別集計
        error_codes = {}
        for err in recent_errors:
            if "error_code" in err:
                code = err["error_code"]
                error_codes[code] = error_codes.get(code, 0) + 1
        
        return {
            "period_hours": hours,
            "total_errors": len(recent_errors),
            "error_types": error_types,
            "error_codes": error_codes,
            "most_recent": recent_errors[-1] if recent_errors else None
        }


# グローバルエラーハンドラーインスタンス
error_handler = ErrorHandler()


def with_error_handling(
    default_return: Any = None,
    raise_on_error: bool = True,
    max_retries: int = 0,
    retry_delay: float = 1.0,
    retry_backoff: float = 2.0
):
    """
    エラーハンドリングデコレータ
    
    Args:
        default_return: エラー時のデフォルト戻り値
        raise_on_error: エラーを再発生させるか
        max_retries: 最大リトライ回数
        retry_delay: リトライ間隔（秒）
        retry_backoff: リトライ間隔の増加率
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_error = None
            current_delay = retry_delay
            
            for attempt in range(max_retries + 1):
                try:
                    # コンテキスト情報作成
                    context = {
                        "function": func.__name__,
                        "module": func.__module__,
                        "attempt": attempt + 1,
                        "max_retries": max_retries
                    }
                    
                    # 関数実行
                    result = func(*args, **kwargs)
                    
                    # 成功した場合
                    if attempt > 0:
                        logger.info(f"{func.__name__} succeeded after {attempt} retries")
                    
                    return result
                    
                except Exception as e:
                    last_error = e
                    
                    # エラーハンドリング
                    error_handler.handle_error(e, context)
                    
                    # リトライ判定
                    if attempt < max_retries:
                        # リトライ可能なエラーかチェック
                        if _is_retryable_error(e):
                            logger.warning(
                                f"{func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}), "
                                f"retrying in {current_delay:.1f}s..."
                            )
                            time.sleep(current_delay)
                            current_delay *= retry_backoff
                            continue
                    
                    # リトライ不可またはリトライ回数超過
                    break
            
            # 最終的な処理
            if raise_on_error and last_error:
                raise last_error
            else:
                return default_return
        
        return wrapper
    return decorator


def _is_retryable_error(error: Exception) -> bool:
    """リトライ可能なエラーかチェック"""
    # ネットワークエラー
    if isinstance(error, (ConnectionError, TimeoutError)):
        return True
    
    # API レート制限エラー
    if isinstance(error, APIError) and error.details.get("status_code") == 429:
        return True
    
    # 一時的なファイルロックエラー
    if isinstance(error, FileOperationError) and "lock" in str(error).lower():
        return True
    
    return False


def safe_file_operation(operation: str, filepath: str, 
                       operation_func: Callable, *args, **kwargs) -> Any:
    """安全なファイル操作"""
    try:
        return operation_func(*args, **kwargs)
    except FileNotFoundError:
        raise FileOperationError(operation, filepath, f"ファイルが見つかりません: {filepath}")
    except PermissionError:
        raise FileOperationError(operation, filepath, f"ファイルアクセス権限がありません: {filepath}")
    except OSError as e:
        raise FileOperationError(operation, filepath, f"ファイル操作エラー: {e}")
    except Exception as e:
        raise FileOperationError(operation, filepath, f"予期しないエラー: {e}")


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """必須フィールドの検証"""
    missing_fields = []
    
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)
    
    if missing_fields:
        raise ValidationError(
            "required_fields",
            missing_fields,
            f"必須フィールドが不足しています: {', '.join(missing_fields)}"
        )


def validate_api_response(response: Any, service: str) -> None:
    """API レスポンスの検証"""
    if not hasattr(response, 'status_code'):
        raise APIError(service, "無効なレスポンスオブジェクト")
    
    if response.status_code >= 400:
        error_body = None
        try:
            error_body = response.text
        except:
            pass
        
        raise APIError(
            service,
            f"APIエラー: {response.status_code}",
            status_code=response.status_code,
            response_body=error_body
        )


# テスト関数
def test_error_handling():
    """エラーハンドリングのテスト"""
    
    @with_error_handling(default_return=None, max_retries=2, retry_delay=0.1)
    def test_function(should_fail: bool = True):
        if should_fail:
            raise ConnectionError("テスト接続エラー")
        return "success"
    
    # エラーケース
    result = test_function(should_fail=True)
    assert result is None
    
    # 成功ケース
    result = test_function(should_fail=False)
    assert result == "success"
    
    # エラーサマリー確認
    summary = error_handler.get_error_summary(hours=1)
    print(f"エラーサマリー: {json.dumps(summary, ensure_ascii=False, indent=2)}")
    
    print("エラーハンドリングテスト完了")


if __name__ == "__main__":
    test_error_handling()