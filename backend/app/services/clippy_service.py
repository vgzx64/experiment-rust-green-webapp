"""Clippy service for Rust linting and auto-fixing."""
import asyncio
import json
import logging
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.config.sast_config import sast_config
from app.models.sast_result import SastIssue, SastReport, SastSeverity

logger = logging.getLogger(__name__)


class ClippyService:
    """Service for running Clippy linter on Rust code."""
    
    def __init__(self):
        self.enabled = sast_config.clippy_enabled
        self.auto_fix = sast_config.clippy_auto_fix
        self.timeout = sast_config.clippy_timeout
        self.warn_lints = sast_config.clippy_warn_lints
    
    async def run_scan(
        self, 
        project_path: str, 
        apply_fixes: bool = False
    ) -> SastReport:
        """
        Run Clippy scan on a Rust project.
        
        Args:
            project_path: Path to the Rust project directory
            apply_fixes: Whether to apply auto-fixes
            
        Returns:
            SastReport with scan results
        """
        scan_id = str(uuid.uuid4())[:8]
        
        if not self.enabled:
            logger.info("Clippy scanning is disabled")
            return SastReport(
                scan_id=scan_id,
                tool="clippy",
                status="disabled",
                timestamp=datetime.utcnow(),
                issues=[],
                total_issues=0,
                summary={}
            )
        
        logger.info(f"Running Clippy scan {scan_id} on {project_path}")
        
        try:
            # Run cargo clippy
            issues, raw_output = await self._run_clippy(project_path)
            
            # Apply auto-fixes if requested
            auto_fixes_applied = 0
            auto_fixes_failed = 0
            
            if apply_fixes and self.auto_fix:
                auto_fixes_applied, auto_fixes_failed = await self._apply_fixes(project_path)
                # Re-scan after fixes to get remaining issues
                if auto_fixes_applied > 0:
                    issues, raw_output = await self._run_clippy(project_path)
            
            # Build summary
            summary = self._build_summary(issues)
            
            return SastReport(
                scan_id=scan_id,
                tool="clippy",
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
            logger.error(f"Clippy scan {scan_id} timed out")
            return SastReport(
                scan_id=scan_id,
                tool="clippy",
                status="timeout",
                timestamp=datetime.utcnow(),
                issues=[],
                total_issues=0,
                summary={},
                error_message=f"Scan timed out after {self.timeout} seconds"
            )
        except Exception as e:
            logger.error(f"Clippy scan {scan_id} failed: {e}")
            return SastReport(
                scan_id=scan_id,
                tool="clippy",
                status="error",
                timestamp=datetime.utcnow(),
                issues=[],
                total_issues=0,
                summary={},
                error_message=str(e)
            )
    
    async def _run_clippy(self, project_path: str) -> Tuple[List[SastIssue], Dict]:
        """Run cargo clippy and parse output."""
        
        # Build clippy command
        # Use -W for warnings on specific lint groups
        lint_args = []
        for lint_group in self.warn_lints:
            lint_args.extend(["-W", lint_group])
        
        cmd = [
            "cargo", "clippy",
            "--all-targets",
            "--all-features",
            "--", "-D", "warnings"
        ] + lint_args
        
        logger.debug(f"Running command: {' '.join(cmd)}")
        
        # Run command
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=project_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            raise
        
        output = stdout.decode('utf-8', errors='replace')
        error_output = stderr.decode('utf-8', errors='replace')
        combined_output = output + "\n" + error_output
        
        # Parse issues from output
        issues = self._parse_clippy_output(combined_output, project_path)
        
        raw_output = {
            "stdout": output,
            "stderr": error_output,
            "return_code": process.returncode
        }
        
        return issues, raw_output
    
    def _parse_clippy_output(self, output: str, project_path: str) -> List[SastIssue]:
        """Parse Clippy output to extract issues."""
        issues = []
        
        # Clippy output format:
        # error: message
        #   --> src/main.rs:10:5
        #    |
        # 10 |     code here
        #    |     ^^^^^^^^ hint
        
        # Also handles warnings:
        # warning: message
        #   --> src/main.rs:10:5
        
        # Regex patterns
        # Pattern for error/warning with file location
        issue_pattern = re.compile(
            r'^(error|warning):\s*(.+?)$(?:\n\s*-->\s*(.+?):(\d+):(\d+))?',
            re.MULTILINE
        )
        
        # Alternative pattern for JSON output (if using --message-format=json)
        json_pattern = re.compile(r'^\{.*\}$', re.MULTILINE)
        
        # Try JSON parsing first
        json_matches = json_pattern.findall(output)
        if json_matches:
            for json_str in json_matches:
                try:
                    data = json.loads(json_str)
                    issue = self._parse_clippy_json_message(data, project_path)
                    if issue:
                        issues.append(issue)
                except json.JSONDecodeError:
                    continue
        else:
            # Parse text output
            for match in issue_pattern.finditer(output):
                severity_str, message, file_path, line, column = match.groups()
                
                if not file_path:
                    continue
                
                # Map severity
                severity = self._map_severity(severity_str)
                
                # Make path relative
                if file_path.startswith(project_path):
                    file_path = os.path.relpath(file_path, project_path)
                
                # Extract rule ID from message if present
                rule_id = "clippy::unknown"
                if "[" in message and "]" in message:
                    rule_start = message.rfind("[")
                    rule_end = message.rfind("]")
                    rule_id = "clippy::" + message[rule_start+1:rule_end]
                    message = message[:rule_start].strip()
                
                issue = SastIssue(
                    issue_id=str(uuid.uuid4())[:8],
                    rule_id=rule_id,
                    tool="clippy",
                    severity=severity,
                    message=message,
                    file_path=file_path,
                    line_start=int(line) if line else 1,
                    line_end=int(line) if line else 1,
                    column_start=int(column) if column else None,
                    column_end=None,
                    auto_fixable=self._is_auto_fixable(rule_id)
                )
                issues.append(issue)
        
        return issues
    
    def _parse_clippy_json_message(self, data: Dict, project_path: str) -> Optional[SastIssue]:
        """Parse a single Clippy JSON message."""
        try:
            if data.get("reason") != "compiler-message":
                return None
            
            message = data.get("message", {})
            if not message:
                return None
            
            level = message.get("level", "")
            if level not in ("error", "warning"):
                return None
            
            # Get primary span
            spans = message.get("spans", [])
            primary_span = None
            for span in spans:
                if span.get("is_primary"):
                    primary_span = span
                    break
            
            if not primary_span:
                return None
            
            file_path = primary_span.get("file_name", "")
            line_start = primary_span.get("line_start", 1)
            line_end = primary_span.get("line_end", line_start)
            column_start = primary_span.get("column_start")
            column_end = primary_span.get("column_end")
            
            # Make path relative
            if file_path.startswith(project_path):
                file_path = os.path.relpath(file_path, project_path)
            
            # Get code/rule ID
            code = message.get("code", {})
            rule_id = code.get("code", "clippy::unknown")
            if not rule_id.startswith("clippy::"):
                rule_id = "clippy::" + rule_id
            
            return SastIssue(
                issue_id=str(uuid.uuid4())[:8],
                rule_id=rule_id,
                tool="clippy",
                severity=self._map_severity(level),
                message=message.get("message", ""),
                file_path=file_path,
                line_start=line_start,
                line_end=line_end,
                column_start=column_start,
                column_end=column_end,
                snippet=primary_span.get("text", [{}])[0].get("text"),
                auto_fixable=self._is_auto_fixable(rule_id),
                raw_output=data
            )
        except Exception as e:
            logger.debug(f"Failed to parse Clippy JSON message: {e}")
            return None
    
    async def _apply_fixes(self, project_path: str) -> Tuple[int, int]:
        """Apply Clippy auto-fixes using cargo clippy --fix."""
        
        cmd = [
            "cargo", "clippy", "--fix",
            "--allow-dirty",
            "--allow-staged",
            "--"
        ]
        
        # Add lint warnings
        for lint_group in self.warn_lints:
            cmd.extend(["-W", lint_group])
        
        logger.info(f"Applying Clippy fixes in {project_path}")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout
            )
            
            output = stdout.decode('utf-8', errors='replace')
            error_output = stderr.decode('utf-8', errors='replace')
            
            # Count fixes applied
            # Clippy --fix outputs something like "Fixed 3 errors"
            fixes_applied = 0
            fixes_failed = 0
            
            fix_pattern = re.compile(r'Fixed (\d+) errors?')
            match = fix_pattern.search(output + error_output)
            if match:
                fixes_applied = int(match.group(1))
            
            if process.returncode != 0:
                fixes_failed = output.count("error:")
            
            logger.info(f"Clippy fixes: {fixes_applied} applied, {fixes_failed} failed")
            return fixes_applied, fixes_failed
            
        except asyncio.TimeoutError:
            logger.error("Clippy fix timed out")
            return 0, 0
        except Exception as e:
            logger.error(f"Failed to apply Clippy fixes: {e}")
            return 0, 0
    
    def _map_severity(self, level: str) -> str:
        """Map Clippy level to SAST severity."""
        level = level.lower()
        if level == "error":
            return SastSeverity.MAJOR.value
        elif level == "warning":
            return SastSeverity.MINOR.value
        else:
            return SastSeverity.INFO.value
    
    def _is_auto_fixable(self, rule_id: str) -> bool:
        """Check if a Clippy rule is auto-fixable."""
        # Many Clippy lints are auto-fixable
        auto_fixable_rules = {
            "clippy::needless_return",
            "clippy::unnecessary_cast",
            "clippy::redundant_pattern",
            "clippy::unused_unit",
            "clippy::double_neg",
            "clippy::identity_op",
            "clippy::cmp_owned",
            "clippy::explicit_write",
            "clippy::format_in_format_args",
            "clippy::map_identity",
            "clippy::needless_borrow",
            "clippy::redundant_clone",
            "clippy::redundant_closure",
            "clippy::unnecessary_lazy_evaluations",
            # Add more as needed
        }
        return rule_id in auto_fixable_rules
    
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
        """Format Clippy issues for LLM prompt context."""
        if not issues:
            return "No Clippy issues found."
        
        lines = ["Clippy found the following issues:\n"]
        
        for i, issue in enumerate(issues, 1):
            lines.append(f"{i}. [{issue.severity.upper()}] {issue.rule_id}")
            lines.append(f"   File: {issue.file_path}:{issue.line_start}")
            lines.append(f"   Message: {issue.message}")
            if issue.remediation_hint:
                lines.append(f"   Hint: {issue.remediation_hint}")
            lines.append("")
        
        return "\n".join(lines)


# Global service instance
clippy_service = ClippyService()