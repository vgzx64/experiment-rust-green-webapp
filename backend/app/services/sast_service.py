"""Unified SAST service that orchestrates all SAST tools."""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.sast_config import sast_config
from app.models.sast_result import (
    SastIssue, SastReport, SastVerification,
    SastResult, SastVerificationResult
)
from app.services.clippy_service import clippy_service
from app.services.semgrep_service import semgrep_service

logger = logging.getLogger(__name__)


class SastService:
    """Unified service for running SAST scans and verification."""
    
    def __init__(self):
        self.enabled = sast_config.enabled
        self.clippy = clippy_service
        self.semgrep = semgrep_service
    
    async def run_full_scan(
        self,
        project_path: str,
        apply_fixes: bool = False,
        session_id: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, SastReport]:
        """
        Run all enabled SAST tools on a project.
        
        Args:
            project_path: Path to the project directory
            apply_fixes: Whether to apply auto-fixes
            session_id: Optional session ID for database storage
            db: Optional database session for storing results
            
        Returns:
            Dict mapping tool name to SastReport
        """
        if not self.enabled:
            logger.info("SAST scanning is disabled")
            return {}
        
        logger.info(f"Running full SAST scan on {project_path}")
        
        results = {}
        
        # Run Clippy first (Rust-specific)
        if sast_config.clippy_enabled:
            logger.info("Running Clippy scan...")
            clippy_report = await self.clippy.run_scan(project_path, apply_fixes=apply_fixes)
            results["clippy"] = clippy_report
            
            if session_id and db:
                await self._save_sast_result(
                    db, session_id, clippy_report, 
                    scan_phase="after_auto_fix" if apply_fixes else "before_auto_fix"
                )
        
        # Run Semgrep (security patterns)
        if sast_config.semgrep_enabled:
            logger.info("Running Semgrep scan...")
            semgrep_report = await self.semgrep.run_scan(project_path, apply_fixes=apply_fixes)
            results["semgrep"] = semgrep_report
            
            if session_id and db:
                await self._save_sast_result(
                    db, session_id, semgrep_report,
                    scan_phase="after_auto_fix" if apply_fixes else "before_auto_fix"
                )
        
        return results
    
    async def run_auto_fix_phase(self, project_path: str) -> Tuple[int, int]:
        """
        Run auto-fix phase: apply all automatic fixes from SAST tools.
        
        This should be run BEFORE LLM analysis.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Tuple of (total_fixes_applied, total_fixes_failed)
        """
        if not self.enabled:
            logger.info("SAST scanning is disabled, skipping auto-fix phase")
            return 0, 0
        
        logger.info(f"Running SAST auto-fix phase on {project_path}")
        
        total_applied = 0
        total_failed = 0
        
        # Run Clippy fixes first
        if sast_config.clippy_enabled and sast_config.clippy_auto_fix:
            logger.info("Applying Clippy auto-fixes...")
            applied, failed = await self.clippy._apply_fixes(project_path)
            total_applied += applied
            total_failed += failed
        
        # Run Semgrep fixes second
        if sast_config.semgrep_enabled and sast_config.semgrep_auto_fix:
            logger.info("Applying Semgrep auto-fixes...")
            applied, failed = await self.semgrep._apply_fixes(project_path)
            total_applied += applied
            total_failed += failed
        
        logger.info(f"Auto-fix phase complete: {total_applied} fixes applied, {total_failed} failed")
        return total_applied, total_failed
    
    async def run_sast_pipeline(
        self,
        project_path: str,
        session_id: str,
        db: AsyncSession
    ) -> Tuple[Dict[str, SastReport], Dict[str, SastReport], SastVerification]:
        """
        Run complete SAST pipeline:
        1. Initial scan (before any fixes)
        2. Auto-fix phase
        3. Post-auto-fix scan
        4. (LLM analysis happens elsewhere)
        5. Verification will be done after LLM fixes
        
        Args:
            project_path: Path to the project directory
            session_id: Session ID for database storage
            db: Database session
            
        Returns:
            Tuple of (initial_reports, post_auto_fix_reports, verification)
        """
        if not self.enabled:
            logger.info("SAST scanning is disabled")
            empty_verification = SastVerification(
                resolved_issues=[],
                resolved_count=0,
                remaining_issues=[],
                remaining_count=0,
                new_issues=[],
                new_count=0,
                severity_changes={},
                verification_status="disabled",
                verification_score=1.0,
                verification_notes="SAST scanning is disabled"
            )
            return {}, {}, empty_verification
        
        # Phase 1: Initial scan (before any fixes)
        logger.info("SAST Phase 1: Initial scan")
        initial_reports = await self.run_full_scan(
            project_path, 
            apply_fixes=False, 
            session_id=session_id, 
            db=db
        )
        
        # Phase 2: Auto-fix
        logger.info("SAST Phase 2: Auto-fix")
        fixes_applied, fixes_failed = await self.run_auto_fix_phase(project_path)
        
        # Phase 3: Post-auto-fix scan
        logger.info("SAST Phase 3: Post-auto-fix scan")
        post_auto_fix_reports = await self.run_full_scan(
            project_path,
            apply_fixes=False,
            session_id=session_id,
            db=db
        )
        
        # Generate verification comparing initial vs post-auto-fix
        verification = self._generate_verification(initial_reports, post_auto_fix_reports)
        
        # Save verification result
        await self._save_verification_result(db, session_id, verification, phase="after_auto_fix")
        
        return initial_reports, post_auto_fix_reports, verification
    
    async def run_verification_scan(
        self,
        project_path: str,
        session_id: str,
        db: AsyncSession,
        pre_llm_reports: Dict[str, SastReport]
    ) -> SastVerification:
        """
        Run verification scan after LLM remediation.
        
        Args:
            project_path: Path to the project directory
            session_id: Session ID
            db: Database session
            pre_llm_reports: SAST reports from before LLM analysis
            
        Returns:
            SastVerification comparing pre-LLM vs post-LLM
        """
        logger.info("Running post-LLM verification scan")
        
        # Run final scan
        post_llm_reports = await self.run_full_scan(
            project_path,
            apply_fixes=False,
            session_id=session_id,
            db=db
        )
        
        # Generate verification
        verification = self._generate_verification(pre_llm_reports, post_llm_reports)
        
        # Save verification result
        await self._save_verification_result(db, session_id, verification, phase="after_llm")
        
        return verification
    
    def _generate_verification(
        self,
        before_reports: Dict[str, SastReport],
        after_reports: Dict[str, SastReport]
    ) -> SastVerification:
        """Generate verification comparing before and after reports."""
        
        # Collect all issues
        before_issues = []
        after_issues = []
        
        for tool, report in before_reports.items():
            before_issues.extend(report.issues)
        
        for tool, report in after_reports.items():
            after_issues.extend(report.issues)
        
        # Find resolved, remaining, and new issues
        resolved_issues = []
        remaining_issues = []
        new_issues = []
        
        # Create lookup for after issues
        after_issue_keys = {
            self._issue_key(issue): issue 
            for issue in after_issues
        }
        
        # Check which before issues are resolved or remaining
        for issue in before_issues:
            key = self._issue_key(issue)
            if key in after_issue_keys:
                remaining_issues.append(issue)
            else:
                resolved_issues.append(issue)
        
        # Find new issues (in after but not in before)
        before_issue_keys = {
            self._issue_key(issue) 
            for issue in before_issues
        }
        
        for issue in after_issues:
            key = self._issue_key(issue)
            if key not in before_issue_keys:
                new_issues.append(issue)
        
        # Calculate severity changes
        severity_changes = self._calculate_severity_changes(before_issues, after_issues)
        
        # Determine verification status
        verification_status = self._determine_status(
            len(resolved_issues),
            len(remaining_issues),
            len(new_issues)
        )
        
        # Calculate verification score (0.0 to 1.0)
        total_before = len(before_issues)
        if total_before == 0:
            verification_score = 1.0 if len(new_issues) == 0 else 0.5
        else:
            resolved_ratio = len(resolved_issues) / total_before
            new_penalty = min(len(new_issues) * 0.1, 0.5)  # Penalty for new issues
            verification_score = max(0.0, min(1.0, resolved_ratio - new_penalty))
        
        # Generate notes
        notes = self._generate_verification_notes(
            resolved_issues, remaining_issues, new_issues, verification_score
        )
        
        return SastVerification(
            resolved_issues=resolved_issues,
            resolved_count=len(resolved_issues),
            remaining_issues=remaining_issues,
            remaining_count=len(remaining_issues),
            new_issues=new_issues,
            new_count=len(new_issues),
            severity_changes=severity_changes,
            verification_status=verification_status,
            verification_score=verification_score,
            verification_notes=notes
        )
    
    def _issue_key(self, issue: SastIssue) -> str:
        """Generate a unique key for an issue for comparison."""
        return f"{issue.tool}:{issue.rule_id}:{issue.file_path}:{issue.line_start}"
    
    def _calculate_severity_changes(
        self,
        before: List[SastIssue],
        after: List[SastIssue]
    ) -> Dict[str, Dict[str, int]]:
        """Calculate severity breakdown changes."""
        severities = ["blocker", "critical", "major", "minor", "info"]
        
        before_counts = {s: 0 for s in severities}
        after_counts = {s: 0 for s in severities}
        
        for issue in before:
            if issue.severity in before_counts:
                before_counts[issue.severity] += 1
        
        for issue in after:
            if issue.severity in after_counts:
                after_counts[issue.severity] += 1
        
        changes = {}
        for severity in severities:
            changes[severity] = {
                "before": before_counts[severity],
                "after": after_counts[severity],
                "change": after_counts[severity] - before_counts[severity]
            }
        
        return changes
    
    def _determine_status(
        self,
        resolved_count: int,
        remaining_count: int,
        new_count: int
    ) -> str:
        """Determine verification status."""
        if remaining_count == 0 and new_count == 0:
            return "resolved"
        elif new_count > remaining_count:
            return "degraded"
        elif resolved_count > 0:
            return "partial"
        else:
            return "unresolved"
    
    def _generate_verification_notes(
        self,
        resolved: List[SastIssue],
        remaining: List[SastIssue],
        new: List[SastIssue],
        score: float
    ) -> str:
        """Generate human-readable verification notes."""
        lines = [f"Verification Score: {score:.0%}\n"]
        
        if resolved:
            lines.append(f"✓ Resolved {len(resolved)} issue(s)")
            for issue in resolved[:5]:  # Show first 5
                lines.append(f"  - {issue.tool}: {issue.rule_id} in {issue.file_path}:{issue.line_start}")
            if len(resolved) > 5:
                lines.append(f"  ... and {len(resolved) - 5} more")
        
        if remaining:
            lines.append(f"\n⚠ Remaining {len(remaining)} issue(s)")
            for issue in remaining[:5]:
                lines.append(f"  - {issue.tool}: {issue.rule_id} in {issue.file_path}:{issue.line_start}")
            if len(remaining) > 5:
                lines.append(f"  ... and {len(remaining) - 5} more")
        
        if new:
            lines.append(f"\n✗ New {len(new)} issue(s) introduced")
            for issue in new[:5]:
                lines.append(f"  - {issue.tool}: {issue.rule_id} in {issue.file_path}:{issue.line_start}")
            if len(new) > 5:
                lines.append(f"  ... and {len(new) - 5} more")
        
        return "\n".join(lines)
    
    async def _save_sast_result(
        self,
        db: AsyncSession,
        session_id: str,
        report: SastReport,
        scan_phase: str
    ):
        """Save SAST result to database."""
        try:
            result = SastResult(
                session_id=session_id,
                scan_phase=scan_phase,
                tool=report.tool,
                status=report.status,
                issues=[issue.model_dump() for issue in report.issues],
                total_issues=report.total_issues,
                summary=report.summary,
                auto_fixes_applied=report.auto_fixes_applied,
                auto_fixes_failed=report.auto_fixes_failed,
                error_message=report.error_message,
                raw_output=report.raw_output
            )
            db.add(result)
            await db.commit()
            logger.debug(f"Saved SAST result for session {session_id}")
        except Exception as e:
            logger.error(f"Failed to save SAST result: {e}")
            await db.rollback()
    
    async def _save_verification_result(
        self,
        db: AsyncSession,
        session_id: str,
        verification: SastVerification,
        phase: str
    ):
        """Save verification result to database."""
        try:
            result = SastVerificationResult(
                session_id=session_id,
                verification_status=verification.verification_status,
                verification_score=int(verification.verification_score * 100),
                issues_before=verification.resolved_count + verification.remaining_count,
                issues_after=verification.remaining_count + verification.new_count,
                issues_resolved=verification.resolved_count,
                issues_remaining=verification.remaining_count,
                issues_new=verification.new_count,
                resolved_issues=[issue.issue_id for issue in verification.resolved_issues],
                remaining_issues=[issue.issue_id for issue in verification.remaining_issues],
                new_issues=[issue.issue_id for issue in verification.new_issues],
                severity_before=verification.severity_changes,
                severity_after=verification.severity_changes,  # Will be updated
                verification_notes=verification.verification_notes
            )
            db.add(result)
            await db.commit()
            logger.debug(f"Saved verification result for session {session_id}")
        except Exception as e:
            logger.error(f"Failed to save verification result: {e}")
            await db.rollback()
    
    def format_for_llm(self, reports: Dict[str, SastReport]) -> str:
        """
        Format all SAST reports for LLM prompt context.
        
        This is used to provide SAST context to the LLM for analysis.
        """
        if not reports:
            return "No SAST analysis available."
        
        lines = ["=" * 60]
        lines.append("SAST ANALYSIS RESULTS")
        lines.append("=" * 60)
        lines.append("")
        
        total_issues = sum(r.total_issues for r in reports.values())
        lines.append(f"Total issues found: {total_issues}")
        lines.append("")
        
        for tool, report in reports.items():
            if report.issues:
                lines.append(f"\n--- {tool.upper()} Issues ---\n")
                
                if tool == "clippy":
                    lines.append(self.clippy.format_for_llm(report.issues))
                elif tool == "semgrep":
                    lines.append(self.semgrep.format_for_llm(report.issues))
        
        lines.append("\n" + "=" * 60)
        lines.append("Please consider these SAST findings in your analysis.")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def get_all_issues(self, reports: Dict[str, SastReport]) -> List[SastIssue]:
        """Get all issues from all reports as a flat list."""
        issues = []
        for report in reports.values():
            issues.extend(report.issues)
        return issues


# Global service instance
sast_service = SastService()