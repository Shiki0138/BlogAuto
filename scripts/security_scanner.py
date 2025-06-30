#!/usr/bin/env python3
"""
BlogAuto Security Scanner
本番デプロイ前のセキュリティチェックツール
"""
import os
import sys
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from scripts.utils import logger, save_json_safely

class SecurityScanner:
    """包括的セキュリティスキャナー"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.scan_results = {
            "scan_date": datetime.now().isoformat(),
            "overall_status": "PASS",
            "findings": [],
            "summary": {}
        }
        
    def run_full_scan(self) -> Dict[str, Any]:
        """フルセキュリティスキャン実行"""
        logger.info("🔒 セキュリティスキャン開始...")
        
        # 各種セキュリティチェック実行
        self._scan_for_secrets()
        self._scan_for_vulnerabilities()
        self._check_dependencies()
        self._validate_api_security()
        self._check_file_permissions()
        self._validate_input_sanitization()
        self._check_https_usage()
        
        # 結果サマリー生成
        self._generate_summary()
        
        # レポート保存
        report_path = self.project_root / "output" / "security_scan_report.json"
        save_json_safely(self.scan_results, str(report_path))
        
        logger.info(f"🔒 セキュリティスキャン完了: {self.scan_results['overall_status']}")
        return self.scan_results
    
    def _scan_for_secrets(self):
        """シークレット露出スキャン"""
        logger.info("🔍 シークレット露出チェック...")
        
        secret_patterns = [
            (r'api_key\s*=\s*["\'][^"\']+["\']', "Hardcoded API Key"),
            (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded Password"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "Hardcoded Secret"),
            (r'token\s*=\s*["\'][^"\']+["\']', "Hardcoded Token"),
            (r'sk-[a-zA-Z0-9]{48}', "API Key Pattern (sk-)"),
            (r'AIza[0-9A-Za-z\-_]{35}', "Google API Key Pattern"),
            (r'[0-9a-f]{40}', "Generic Hash/Token Pattern"),
            (r'BEGIN RSA PRIVATE KEY', "Private Key Exposure"),
            (r'AWS[A-Z0-9]{16}', "AWS Access Key Pattern")
        ]
        
        for py_file in self.project_root.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                line_num = 0
                
                for line in content.splitlines():
                    line_num += 1
                    
                    for pattern, desc in secret_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            # 誤検知フィルタ
                            if self._is_false_positive(line, pattern):
                                continue
                                
                            finding = {
                                "type": "SECRET_EXPOSURE",
                                "severity": "CRITICAL",
                                "file": str(py_file.relative_to(self.project_root)),
                                "line": line_num,
                                "description": desc,
                                "pattern": pattern
                            }
                            self.scan_results["findings"].append(finding)
                            self.scan_results["overall_status"] = "FAIL"
                            
            except Exception as e:
                logger.error(f"ファイルスキャンエラー {py_file}: {e}")
    
    def _is_false_positive(self, line: str, pattern: str) -> bool:
        """誤検知判定"""
        false_positive_indicators = [
            "example", "template", "mock", "test", "fake",
            "your_", "_here", "xxx", "placeholder", '""', "''"
        ]
        
        line_lower = line.lower()
        return any(indicator in line_lower for indicator in false_positive_indicators)
    
    def _scan_for_vulnerabilities(self):
        """脆弱性スキャン"""
        logger.info("🔍 脆弱性チェック...")
        
        vuln_patterns = [
            (r'eval\s*\(', "Dangerous eval() usage", "HIGH"),
            (r'exec\s*\(', "Dangerous exec() usage", "HIGH"),
            (r'__import__\s*\(', "Dynamic import usage", "MEDIUM"),
            (r'pickle\.loads?\s*\(', "Pickle deserialization", "HIGH"),
            (r'subprocess\.call\s*\(.*shell\s*=\s*True', "Shell injection risk", "CRITICAL"),
            (r'os\.system\s*\(', "Command injection risk", "HIGH"),
            (r'\.format\s*\(.*request\.', "Format string vulnerability", "MEDIUM"),
            (r'\.execute\s*\(.*%.*\)', "SQL injection risk", "CRITICAL"),
            (r'verify\s*=\s*False', "SSL verification disabled", "HIGH")
        ]
        
        for py_file in self.project_root.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                
                for pattern, desc, severity in vuln_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        
                        finding = {
                            "type": "VULNERABILITY",
                            "severity": severity,
                            "file": str(py_file.relative_to(self.project_root)),
                            "line": line_num,
                            "description": desc,
                            "code": match.group(0)
                        }
                        self.scan_results["findings"].append(finding)
                        
                        if severity in ["CRITICAL", "HIGH"]:
                            self.scan_results["overall_status"] = "FAIL"
                            
            except Exception as e:
                logger.error(f"脆弱性スキャンエラー {py_file}: {e}")
    
    def _check_dependencies(self):
        """依存関係セキュリティチェック"""
        logger.info("🔍 依存関係チェック...")
        
        # 既知の脆弱性を持つパッケージバージョン（例）
        vulnerable_packages = {
            "requests": ["< 2.31.0", "CVE-2023-32681"],
            "pillow": ["< 10.0.1", "CVE-2023-44271"],
            "jinja2": ["< 3.1.3", "CVE-2024-22195"],
            "markdown": ["< 3.5", "XSS vulnerability"]
        }
        
        requirements_file = self.project_root / "requirements.txt"
        if requirements_file.exists():
            try:
                content = requirements_file.read_text()
                for line in content.splitlines():
                    if "==" in line or ">=" in line:
                        pkg_name = re.split(r'[><=]', line)[0].strip()
                        
                        if pkg_name.lower() in vulnerable_packages:
                            finding = {
                                "type": "VULNERABLE_DEPENDENCY",
                                "severity": "HIGH",
                                "package": pkg_name,
                                "description": f"Potential vulnerability: {vulnerable_packages[pkg_name.lower()][1]}",
                                "recommendation": f"Update to version {vulnerable_packages[pkg_name.lower()][0]}"
                            }
                            self.scan_results["findings"].append(finding)
                            
            except Exception as e:
                logger.error(f"依存関係チェックエラー: {e}")
    
    def _validate_api_security(self):
        """API セキュリティ検証"""
        logger.info("🔍 APIセキュリティチェック...")
        
        # 環境変数アクセスパターンチェック
        env_patterns = [
            (r'os\.environ\s*\[', "Direct environ access - use os.getenv()"),
            (r'getenv\s*\([^,)]+\)', "Missing default value in getenv()"),
        ]
        
        for py_file in self.project_root.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                
                for pattern, desc in env_patterns:
                    if re.search(pattern, content):
                        finding = {
                            "type": "API_SECURITY",
                            "severity": "MEDIUM",
                            "file": str(py_file.relative_to(self.project_root)),
                            "description": desc
                        }
                        self.scan_results["findings"].append(finding)
                        
            except Exception as e:
                logger.error(f"APIセキュリティチェックエラー {py_file}: {e}")
    
    def _check_file_permissions(self):
        """ファイルパーミッションチェック"""
        logger.info("🔍 ファイルパーミッションチェック...")
        
        for py_file in self.project_root.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                stat_info = py_file.stat()
                mode = oct(stat_info.st_mode)[-3:]
                
                # 実行権限チェック
                if mode[2] in ['7', '5', '3', '1']:  # Others have execute
                    finding = {
                        "type": "FILE_PERMISSION",
                        "severity": "MEDIUM",
                        "file": str(py_file.relative_to(self.project_root)),
                        "description": f"Excessive permissions: {mode}",
                        "recommendation": "Remove execute permission for others"
                    }
                    self.scan_results["findings"].append(finding)
                    
            except Exception as e:
                logger.error(f"パーミッションチェックエラー {py_file}: {e}")
    
    def _validate_input_sanitization(self):
        """入力サニタイゼーション検証"""
        logger.info("🔍 入力検証チェック...")
        
        sanitization_patterns = [
            "clean_html_content",
            "validate_",
            "sanitize_",
            "escape_"
        ]
        
        files_with_inputs = []
        files_with_sanitization = []
        
        for py_file in self.project_root.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                
                # 入力処理の検出
                if re.search(r'request\.|input\(|sys\.argv|os\.getenv', content):
                    files_with_inputs.append(py_file)
                    
                    # サニタイゼーションチェック
                    has_sanitization = any(
                        pattern in content for pattern in sanitization_patterns
                    )
                    
                    if has_sanitization:
                        files_with_sanitization.append(py_file)
                    else:
                        finding = {
                            "type": "INPUT_VALIDATION",
                            "severity": "MEDIUM",
                            "file": str(py_file.relative_to(self.project_root)),
                            "description": "Input handling without apparent sanitization"
                        }
                        self.scan_results["findings"].append(finding)
                        
            except Exception as e:
                logger.error(f"入力検証チェックエラー {py_file}: {e}")
    
    def _check_https_usage(self):
        """HTTPS使用状況チェック"""
        logger.info("🔍 HTTPS使用状況チェック...")
        
        http_pattern = r'http://(?!localhost|127\.0\.0\.1)'
        
        for py_file in self.project_root.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                
                matches = re.finditer(http_pattern, content)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    
                    finding = {
                        "type": "INSECURE_PROTOCOL",
                        "severity": "MEDIUM",
                        "file": str(py_file.relative_to(self.project_root)),
                        "line": line_num,
                        "description": "HTTP usage instead of HTTPS",
                        "url": match.group(0)
                    }
                    self.scan_results["findings"].append(finding)
                    
            except Exception as e:
                logger.error(f"HTTPSチェックエラー {py_file}: {e}")
    
    def _generate_summary(self):
        """スキャン結果サマリー生成"""
        severity_counts = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0
        }
        
        type_counts = {}
        
        for finding in self.scan_results["findings"]:
            severity = finding.get("severity", "MEDIUM")
            finding_type = finding.get("type", "UNKNOWN")
            
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            type_counts[finding_type] = type_counts.get(finding_type, 0) + 1
        
        self.scan_results["summary"] = {
            "total_findings": len(self.scan_results["findings"]),
            "severity_breakdown": severity_counts,
            "type_breakdown": type_counts,
            "files_scanned": len(list(self.project_root.rglob("*.py")))
        }
        
        # 全体ステータスの決定
        if severity_counts["CRITICAL"] > 0 or severity_counts["HIGH"] > 0:
            self.scan_results["overall_status"] = "FAIL"
        elif severity_counts["MEDIUM"] > 5:
            self.scan_results["overall_status"] = "WARNING"
    
    def print_report(self):
        """レポート出力"""
        print("\n" + "="*60)
        print("🔒 SECURITY SCAN REPORT")
        print("="*60)
        print(f"Scan Date: {self.scan_results['scan_date']}")
        print(f"Overall Status: {self.scan_results['overall_status']}")
        print(f"Total Findings: {self.scan_results['summary']['total_findings']}")
        
        print("\n📊 Severity Breakdown:")
        for severity, count in self.scan_results['summary']['severity_breakdown'].items():
            if count > 0:
                print(f"  {severity}: {count}")
        
        print("\n🔍 Finding Types:")
        for finding_type, count in self.scan_results['summary']['type_breakdown'].items():
            print(f"  {finding_type}: {count}")
        
        if self.scan_results['findings']:
            print("\n⚠️ Critical & High Severity Findings:")
            for finding in self.scan_results['findings']:
                if finding.get('severity') in ['CRITICAL', 'HIGH']:
                    print(f"\n  [{finding['severity']}] {finding['type']}")
                    print(f"  File: {finding.get('file', 'N/A')}")
                    print(f"  Description: {finding['description']}")
        
        print("\n" + "="*60)
        
        if self.scan_results['overall_status'] == 'PASS':
            print("✅ Security scan PASSED - Ready for deployment")
        elif self.scan_results['overall_status'] == 'WARNING':
            print("⚠️ Security scan has WARNINGS - Review before deployment")
        else:
            print("❌ Security scan FAILED - Fix issues before deployment")

def main():
    """メイン実行関数"""
    scanner = SecurityScanner()
    results = scanner.run_full_scan()
    scanner.print_report()
    
    # Exit code based on scan results
    if results['overall_status'] == 'PASS':
        sys.exit(0)
    elif results['overall_status'] == 'WARNING':
        sys.exit(1)
    else:
        sys.exit(2)

if __name__ == "__main__":
    main()