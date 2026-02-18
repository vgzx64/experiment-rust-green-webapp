"""Semgrep service for SAST scanning with auto-fix support."""
import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.config.sast_config import sast_config
from app.models.sast_result import SastIssue, SastReport, SastSeverity

logger = logging.getLogger(__name__)


class SemgrepService:
    """Service for running Semgrep SAST scanner on code."""
    
    def __init__(self):
        self.enabled = sast_config.semgrep_enabled
        self.auto_fix = sast_config.semgrep_auto_fix
        self.timeout = sast_config.semgrep_timeout
        self.config = sast_config.semgrep_config
        self.use_container = sast_config.semgrep_use_container
        self.container_image = sast_config.semgrep_container_image
        self.podman_path = sast_config.podman_path
    
    async def run_scan(
        self, 
        project_path: str, 
        apply_fixes: bool = False
    ) -> SastReport:
        """
        Run Semgrep scan on a project.
        
        Args:
            project_path: Path to the project directory
            apply_fixes: Whether to apply auto-fixes
            
        Returns:
            SastReport with scan results
        """
        scan_id = str(uuid.uuid4())[:8]
        
        if not self.enabled:
            logger.info("Semgrep scanning is disabled")
            return SastReport(
                scan_id=scan_id,
                tool="semgrep",
                status="disabled",
                timestamp=datetime.utcnow(),
                issues=[],
                total_issues=0,
                summary={}
            )
        
        logger.info(f"Running Semgrep scan {scan_id} on {project_path}")
        
        try:
            # Run semgrep scan
            issues, raw_output = await self._run_semgrep(project_path)
            
            # Apply auto-fixes if requested
            auto_fixes_applied = 0
            auto_fixes_failed = 0
            
            if apply_fixes and self.auto_fix:
                auto_fixes_applied, auto_fixes_failed = await self._apply_fixes(project_path)
                # Re-scan after fixes to get remaining issues
                if auto_fixes_applied > 0:
                    issues, raw_output = await self._run_semgrep(project_path)
            
            # Build summary
            summary = self._build_summary(issues)
            
            return SastReport(
                scan_id=scan_id,
                tool="semgrep",
                status="success",
                timestamp=datetime.utcnow(),
                issues=issues,
                total_issues=len(issues),
                summary=summary,
                auto_fixes_applied=auto_fixes_applied,
                auto_fixes_failed=auto_fixes_failed,
                raw_output=raw_output
            )
            
        except asyncio.TimeoutError:
            logger.error(f"Semgrep scan {scan_id} timed out")
            return SastReport(
                scan_id=scan_id,
                tool="semgrep",
                status="timeout",
                timestamp=datetime.utcnow(),
                issues=[],
                total_issues=0,
                summary={},
                error_message=f"Scan timed out after {self.timeout} seconds"
            )
        except Exception as e:
            logger.error(f"Semgrep scan {scan_id} failed: {e}")
            return SastReport(
                scan_id=scan_id,
                tool="semgrep",
                status="error",
                timestamp=datetime.utcnow(),
                issues=[],
                total_issues=0,
                summary={},
                error_message=str(e)
            )
    
    async def _run_semgrep(self, project_path: str) -> Tuple[List[SastIssue], Dict]:
        """Run semgrep and parse output."""
        
        # Ensure project_path is a str (callers may pass a Path object)
        project_path = str(project_path)
        
        if self.use_container:
            return await self._run_semgrep_container(project_path)
        else:
            return await self._run_semgrep_native(project_path)
    
    async def _run_semgrep_native(self, project_path: str) -> Tuple[List[SastIssue], Dict]:
        """Run semgrep natively (pip installed)."""
        
        cmd = [
            "semgrep",
            "--config", self.config,
            "--json",
            "--quiet",
            "--no-git-ignore",
            project_path
        ]
        
        logger.debug(f"Running command: {' '.join(cmd)}")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout
            )
        except (asyncio.TimeoutError, asyncio.CancelledError):
            process.kill()
            raise
        
        output = stdout.decode('utf-8', errors='replace')
        error_output = stderr.decode('utf-8', errors='replace')
        
        # Parse JSON output
        issues = []
        raw_output = {
            "stdout": output,
            "stderr": error_output,
            "return_code": process.returncode
        }
        
        try:
            data = json.loads(output)
            issues = self._parse_semgrep_json(data, project_path)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Semgrep JSON output: {e}")
        
        return issues, raw_output
    
    async def _run_semgrep_container(self, project_path: str) -> Tuple[List[SastIssue], Dict]:
        """Run semgrep in a container using Podman."""
        
        # Convert to absolute path for volume mount
        abs_path = os.path.abspath(project_path)
        
        cmd = [
            self.podman_path, "run", "--rm",
            "-v", f"{abs_path}:/src:Z",
            self.container_image,
            "semgrep",
            "--config", self.config,
            "--json",
            "--quiet",
            "/src"
        ]
        
        logger.debug(f"Running command: {' '.join(cmd)}")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout
            )
        except (asyncio.TimeoutError, asyncio.CancelledError):
            process.kill()
            raise
        
        output = stdout.decode('utf-8', errors='replace')
        error_output = stderr.decode('utf-8', errors='replace')
        
        # Parse JSON output
        issues = []
        raw_output = {
            "stdout": output,
            "stderr": error_output,
            "return_code": process.returncode,
            "container": True
        }
        
        try:
            data = json.loads(output)
            issues = self._parse_semgrep_json(data, project_path)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Semgrep JSON output: {e}")
        
        return issues, raw_output
    
    def _parse_semgrep_json(self, data: Dict, project_path: str) -> List[SastIssue]:
        """Parse Semgrep JSON output to extract issues."""
        issues = []
        
        results = data.get("results", [])
        
        for result in results:
            try:
                issue = self._parse_semgrep_result(result, project_path)
                if issue:
                    issues.append(issue)
            except Exception as e:
                logger.debug(f"Failed to parse Semgrep result: {e}")
                continue
        
        return issues
    
    def _parse_semgrep_result(self, result: Dict, project_path: str) -> Optional[SastIssue]:
        """Parse a single Semgrep result."""
        
        # Extract check info
        check_id = result.get("check_id", "unknown")
        extra = result.get("extra", {})
        
        # Extract location
        path = result.get("path", "")
        start = result.get("start", {})
        end = result.get("end", {})
        
        # Make path relative
        if path.startswith(project_path):
            path = os.path.relpath(path, project_path)
        
        # Extract severity
        severity = self._map_severity(extra.get("severity", "INFO"))
        
        # Extract message
        message = extra.get("message", result.get("extra", {}).get("lines", ""))
        
        # Extract CWE if available
        cwe_id = None
        metadata = extra.get("metadata", {})
        if "cwe" in metadata:
            cwe_list = metadata["cwe"]
            if isinstance(cwe_list, list) and cwe_list:
                cwe_id = cwe_list[0]
            elif isinstance(cwe_list, str):
                cwe_id = cwe_list
        
        # Extract category
        category = metadata.get("category")
        
        # Check if auto-fixable
        fix_suggestion = None
        auto_fixable = False
        
        # Semgrep provides fix suggestions
        if "fix" in extra:
            fix_suggestion = extra["fix"]
            auto_fixable = True
        elif "fixed_lines" in result:
            fix_suggestion = "\n".join(result["fixed_lines"])
            auto_fixable = True
        
        # Extract code snippet
        snippet = None
        lines = result.get("extra", {}).get("lines")
        if lines:
            snippet = lines
        
        return SastIssue(
            issue_id=str(uuid.uuid4())[:8],
            rule_id=check_id,
            tool="semgrep",
            severity=severity,
            message=message,
            file_path=path,
            line_start=start.get("line", 1),
            line_end=end.get("line", start.get("line", 1)),
            column_start=start.get("col"),
            column_end=end.get("col"),
            snippet=snippet,
            cwe_id=cwe_id,
            category=category,
            remediation_hint=extra.get("fix_regex", {}).get("replacement") if "fix_regex" in extra else None,
            auto_fixable=auto_fixable,
            fix_suggestion=fix_suggestion,
            raw_output=result
        )
    
    async def _apply_fixes(self, project_path: str) -> Tuple[int, int]:
        """Apply Semgrep auto-fixes."""
        
        if self.use_container:
            return await self._apply_fixes_container(project_path)
        else:
            return await self._apply_fixes_native(project_path)
    
    async def _apply_fixes_native(self, project_path: str) -> Tuple[int, int]:
        """Apply Semgrep auto-fixes natively."""
        
        cmd = [
            "semgrep",
            "--config", self.config,
            "--autofix",
            "--quiet",
            project_path
        ]
        
        logger.info(f"Applying Semgrep fixes in {project_path}")
        
        process = None
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout
            )
            
            output = stdout.decode('utf-8', errors='replace')
            error_output = stderr.decode('utf-8', errors='replace')
            
            # Count fixes - Semgrep outputs number of changes
            fixes_applied = 0
            fixes_failed = 0
            
            # Parse output for fix count
            # Semgrep outputs something like "Successfully modified 3 files"
            import re
            match = re.search(r'modified (\d+) files?', output + error_output)
            if match:
                fixes_applied = int(match.group(1))
            
            logger.info(f"Semgrep fixes: {fixes_applied} applied")
            return fixes_applied, fixes_failed
            
        except asyncio.CancelledError:
            if process:
                process.kill()
            raise
        except asyncio.TimeoutError:
            logger.error("Semgrep fix timed out")
            if process:
                process.kill()
            return 0, 0
        except Exception as e:
            logger.error(f"Failed to apply Semgrep fixes: {e}")
            return 0, 0
    
    async def _apply_fixes_container(self, project_path: str) -> Tuple[int, int]:
        """Apply Semgrep auto-fixes using container."""
        
        abs_path = os.path.abspath(project_path)
        
        cmd = [
            self.podman_path, "run", "--rm",
            "-v", f"{abs_path}:/src:Z",
            self.container_image,
            "semgrep",
            "--config", self.config,
            "--autofix",
            "--quiet",
            "/src"
        ]
        
        logger.info(f"Applying Semgrep fixes in {project_path} (container)")
        
        process = None
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout
            )
            
            output = stdout.decode('utf-8', errors='replace')
            error_output = stderr.decode('utf-8', errors='replace')
            
            fixes_applied = 0
            fixes_failed = 0
            
            import re
            match = re.search(r'modified (\d+) files?', output + error_output)
            if match:
                fixes_applied = int(match.group(1))
            
            logger.info(f"Semgrep fixes: {fixes_applied} applied")
            return fixes_applied, fixes_failed
            
        except asyncio.CancelledError:
            if process:
                process.kill()
            raise
        except asyncio.TimeoutError:
            logger.error("Semgrep fix timed out")
            if process:
                process.kill()
            return 0, 0
        except Exception as e:
            logger.error(f"Failed to apply Semgrep fixes: {e}")
            return 0, 0
    
    def _map_severity(self, severity: str) -> str:
        """Map Semgrep severity to SAST severity."""
        severity = severity.upper()
        
        mapping = {
            "ERROR": SastSeverity.CRITICAL.value,
            "WARNING": SastSeverity.MAJOR.value,
            "INFO": SastSeverity.INFO.value,
            "INVENTORY": SastSeverity.INFO.value
        }
        
        return mapping.get(severity, SastSeverity.INFO.value)
    
    def _build_summary(self, issues: List[SastIssue]) -> Dict[str, int]:
        """Build severity summary from issues."""
        summary = {
            SastSeverity.BLOCKER.value: 0,
            SastSeverity.CRITICAL.value: 0,
            SastSeverity.MAJOR.value: 0,
            SastSeverity.MINOR.value: 0,
            SastSeverity.INFO.value: 0
        }
        
        for issue in issues:
            if issue.severity in summary:
                summary[issue.severity] += 1
        
        return summary
    
    def format_for_llm(self, issues: List[SastIssue]) -> str:
        """Format Semgrep issues for LLM prompt context."""
        if not issues:
            return "No Semgrep security issues found."
        
        lines = ["Semgrep found the following security issues:\n"]
        
        for i, issue in enumerate(issues, 1):
            lines.append(f"{i}. [{issue.severity.upper()}] {issue.rule_id}")
            lines.append(f"   File: {issue.file_path}:{issue.line_start}")
            lines.append(f"   Message: {issue.message}")
            if issue.cwe_id:
                lines.append(f"   CWE: {issue.cwe_id}")
            if issue.fix_suggestion:
                lines.append(f"   Suggested fix: {issue.fix_suggestion}")
            lines.append("")
        
        return "\n".join(lines)


# Global service instance
semgrep_service = SemgrepService()