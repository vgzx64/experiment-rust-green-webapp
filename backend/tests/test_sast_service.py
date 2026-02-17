"""Tests for SAST services."""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from app.models.sast_result import (
    SastIssue, SastReport, SastVerification,
    SastSeverity, SastTool
)
from app.services.clippy_service import ClippyService
from app.services.semgrep_service import SemgrepService
from app.services.sast_service import SastService


class TestSastModels:
    """Test SAST model classes."""
    
    def test_sast_issue_creation(self):
        """Test creating a SastIssue."""
        issue = SastIssue(
            issue_id="test-123",
            rule_id="clippy::unwrap_used",
            tool="clippy",
            severity="major",
            message="Used unwrap() which can panic",
            file_path="src/main.rs",
            line_start=10,
            line_end=10
        )
        
        assert issue.issue_id == "test-123"
        assert issue.rule_id == "clippy::unwrap_used"
        assert issue.tool == "clippy"
        assert issue.severity == "major"
        assert issue.file_path == "src/main.rs"
        assert issue.line_start == 10
        assert issue.auto_fixable == False
    
    def test_sast_issue_with_fix(self):
        """Test creating a SastIssue with fix suggestion."""
        issue = SastIssue(
            issue_id="test-456",
            rule_id="semgrep:unsafe-unwrap",
            tool="semgrep",
            severity="critical",
            message="Unsafe unwrap detected",
            file_path="src/lib.rs",
            line_start=20,
            line_end=20,
            auto_fixable=True,
            fix_suggestion="if let Some(x) = opt { ... }"
        )
        
        assert issue.auto_fixable == True
        assert issue.fix_suggestion == "if let Some(x) = opt { ... }"
    
    def test_sast_report_creation(self):
        """Test creating a SastReport."""
        issues = [
            SastIssue(
                issue_id="1",
                rule_id="rule1",
                tool="clippy",
                severity="major",
                message="Issue 1",
                file_path="a.rs",
                line_start=1,
                line_end=1
            ),
            SastIssue(
                issue_id="2",
                rule_id="rule2",
                tool="clippy",
                severity="minor",
                message="Issue 2",
                file_path="b.rs",
                line_start=2,
                line_end=2
            )
        ]
        
        report = SastReport(
            scan_id="scan-123",
            tool="clippy",
            status="success",
            timestamp=datetime.utcnow(),
            issues=issues,
            total_issues=2,
            summary={"major": 1, "minor": 1}
        )
        
        assert report.scan_id == "scan-123"
        assert report.total_issues == 2
        assert report.summary["major"] == 1
    
    def test_sast_verification_creation(self):
        """Test creating a SastVerification."""
        resolved = [
            SastIssue(
                issue_id="1",
                rule_id="rule1",
                tool="clippy",
                severity="major",
                message="Fixed",
                file_path="a.rs",
                line_start=1,
                line_end=1
            )
        ]
        
        verification = SastVerification(
            resolved_issues=resolved,
            resolved_count=1,
            remaining_issues=[],
            remaining_count=0,
            new_issues=[],
            new_count=0,
            severity_changes={"major": {"before": 1, "after": 0, "change": -1}},
            verification_status="resolved",
            verification_score=1.0,
            verification_notes="All issues resolved"
        )
        
        assert verification.verification_status == "resolved"
        assert verification.verification_score == 1.0
        assert verification.resolved_count == 1


class TestClippyService:
    """Test Clippy service."""
    
    @pytest.fixture
    def clippy_service(self):
        """Create Clippy service instance."""
        return ClippyService()
    
    def test_map_severity(self, clippy_service):
        """Test severity mapping."""
        assert clippy_service._map_severity("error") == SastSeverity.MAJOR.value
        assert clippy_service._map_severity("warning") == SastSeverity.MINOR.value
        assert clippy_service._map_severity("note") == SastSeverity.INFO.value
    
    def test_is_auto_fixable(self, clippy_service):
        """Test auto-fixable rule detection."""
        assert clippy_service._is_auto_fixable("clippy::needless_return") == True
        assert clippy_service._is_auto_fixable("clippy::redundant_clone") == True
        assert clippy_service._is_auto_fixable("clippy::unknown_rule") == False
    
    def test_build_summary(self, clippy_service):
        """Test summary building."""
        issues = [
            SastIssue(
                issue_id="1",
                rule_id="r1",
                tool="clippy",
                severity="major",
                message="m1",
                file_path="a.rs",
                line_start=1,
                line_end=1
            ),
            SastIssue(
                issue_id="2",
                rule_id="r2",
                tool="clippy",
                severity="major",
                message="m2",
                file_path="b.rs",
                line_start=2,
                line_end=2
            ),
            SastIssue(
                issue_id="3",
                rule_id="r3",
                tool="clippy",
                severity="minor",
                message="m3",
                file_path="c.rs",
                line_start=3,
                line_end=3
            )
        ]
        
        summary = clippy_service._build_summary(issues)
        
        assert summary["major"] == 2
        assert summary["minor"] == 1
        assert summary["critical"] == 0
    
    def test_format_for_llm(self, clippy_service):
        """Test LLM formatting."""
        issues = [
            SastIssue(
                issue_id="1",
                rule_id="clippy::unwrap_used",
                tool="clippy",
                severity="major",
                message="Called unwrap() on an Option",
                file_path="src/main.rs",
                line_start=10,
                line_end=10
            )
        ]
        
        formatted = clippy_service.format_for_llm(issues)
        
        assert "clippy::unwrap_used" in formatted
        assert "src/main.rs:10" in formatted
        assert "Called unwrap()" in formatted
    
    def test_format_for_llm_empty(self, clippy_service):
        """Test LLM formatting with no issues."""
        formatted = clippy_service.format_for_llm([])
        assert "No Clippy issues" in formatted


class TestSemgrepService:
    """Test Semgrep service."""
    
    @pytest.fixture
    def semgrep_service(self):
        """Create Semgrep service instance."""
        return SemgrepService()
    
    def test_map_severity(self, semgrep_service):
        """Test severity mapping."""
        assert semgrep_service._map_severity("ERROR") == SastSeverity.CRITICAL.value
        assert semgrep_service._map_severity("WARNING") == SastSeverity.MAJOR.value
        assert semgrep_service._map_severity("INFO") == SastSeverity.INFO.value
    
    def test_parse_semgrep_result(self, semgrep_service):
        """Test parsing Semgrep JSON result."""
        result = {
            "check_id": "rust.security.unsafe-unwrap",
            "path": "/project/src/main.rs",
            "start": {"line": 10, "col": 5},
            "end": {"line": 10, "col": 20},
            "extra": {
                "severity": "ERROR",
                "message": "Unsafe unwrap detected",
                "metadata": {
                    "cwe": ["CWE-476"],
                    "category": "security"
                }
            }
        }
        
        issue = semgrep_service._parse_semgrep_result(result, "/project")
        
        assert issue is not None
        assert issue.rule_id == "rust.security.unsafe-unwrap"
        assert issue.severity == SastSeverity.CRITICAL.value
        assert issue.line_start == 10
        assert issue.cwe_id == "CWE-476"
    
    def test_format_for_llm(self, semgrep_service):
        """Test LLM formatting."""
        issues = [
            SastIssue(
                issue_id="1",
                rule_id="rust.security.buffer-overflow",
                tool="semgrep",
                severity="critical",
                message="Potential buffer overflow",
                file_path="src/unsafe.rs",
                line_start=42,
                line_end=42,
                cwe_id="CWE-787"
            )
        ]
        
        formatted = semgrep_service.format_for_llm(issues)
        
        assert "buffer-overflow" in formatted
        assert "CWE-787" in formatted
        assert "src/unsafe.rs:42" in formatted


class TestSastService:
    """Test unified SAST service."""
    
    @pytest.fixture
    def sast_service(self):
        """Create SAST service instance."""
        return SastService()
    
    def test_issue_key(self, sast_service):
        """Test issue key generation."""
        issue = SastIssue(
            issue_id="1",
            rule_id="rule1",
            tool="clippy",
            severity="major",
            message="test",
            file_path="src/main.rs",
            line_start=10,
            line_end=10
        )
        
        key = sast_service._issue_key(issue)
        
        assert key == "clippy:rule1:src/main.rs:10"
    
    def test_determine_status(self, sast_service):
        """Test verification status determination."""
        # All resolved
        assert sast_service._determine_status(5, 0, 0) == "resolved"
        
        # Partial resolution
        assert sast_service._determine_status(3, 2, 0) == "partial"
        
        # No resolution
        assert sast_service._determine_status(0, 5, 0) == "unresolved"
        
        # Degraded (new issues)
        assert sast_service._determine_status(2, 3, 5) == "degraded"
    
    def test_calculate_severity_changes(self, sast_service):
        """Test severity change calculation."""
        before = [
            SastIssue(issue_id="1", rule_id="r1", tool="clippy", severity="critical", message="", file_path="a.rs", line_start=1, line_end=1),
            SastIssue(issue_id="2", rule_id="r2", tool="clippy", severity="major", message="", file_path="b.rs", line_start=2, line_end=2),
        ]
        
        after = [
            SastIssue(issue_id="2", rule_id="r2", tool="clippy", severity="major", message="", file_path="b.rs", line_start=2, line_end=2),
            SastIssue(issue_id="3", rule_id="r3", tool="clippy", severity="minor", message="", file_path="c.rs", line_start=3, line_end=3),
        ]
        
        changes = sast_service._calculate_severity_changes(before, after)
        
        assert changes["critical"]["before"] == 1
        assert changes["critical"]["after"] == 0
        assert changes["critical"]["change"] == -1
        assert changes["minor"]["before"] == 0
        assert changes["minor"]["after"] == 1
    
    def test_generate_verification_notes(self, sast_service):
        """Test verification notes generation."""
        resolved = [
            SastIssue(issue_id="1", rule_id="r1", tool="clippy", severity="major", message="Fixed", file_path="a.rs", line_start=1, line_end=1)
        ]
        remaining = [
            SastIssue(issue_id="2", rule_id="r2", tool="semgrep", severity="minor", message="Still here", file_path="b.rs", line_start=2, line_end=2)
        ]
        new = [
            SastIssue(issue_id="3", rule_id="r3", tool="clippy", severity="info", message="New issue", file_path="c.rs", line_start=3, line_end=3)
        ]
        
        notes = sast_service._generate_verification_notes(resolved, remaining, new, 0.5)
        
        assert "Resolved 1" in notes
        assert "Remaining 1" in notes
        assert "New 1" in notes
        assert "50%" in notes
    
    def test_format_for_llm(self, sast_service):
        """Test unified LLM formatting."""
        reports = {
            "clippy": SastReport(
                scan_id="1",
                tool="clippy",
                status="success",
                timestamp=datetime.utcnow(),
                issues=[
                    SastIssue(
                        issue_id="1",
                        rule_id="clippy::unwrap",
                        tool="clippy",
                        severity="major",
                        message="Unwrap used",
                        file_path="a.rs",
                        line_start=1,
                        line_end=1
                    )
                ],
                total_issues=1,
                summary={"major": 1}
            ),
            "semgrep": SastReport(
                scan_id="2",
                tool="semgrep",
                status="success",
                timestamp=datetime.utcnow(),
                issues=[
                    SastIssue(
                        issue_id="2",
                        rule_id="semgrep:overflow",
                        tool="semgrep",
                        severity="critical",
                        message="Buffer overflow",
                        file_path="b.rs",
                        line_start=2,
                        line_end=2
                    )
                ],
                total_issues=1,
                summary={"critical": 1}
            )
        }
        
        formatted = sast_service.format_for_llm(reports)
        
        assert "SAST ANALYSIS RESULTS" in formatted
        assert "Total issues found: 2" in formatted
        assert "CLIPPY" in formatted
        assert "SEMGREP" in formatted
    
    def test_get_all_issues(self, sast_service):
        """Test getting all issues from reports."""
        reports = {
            "clippy": SastReport(
                scan_id="1",
                tool="clippy",
                status="success",
                timestamp=datetime.utcnow(),
                issues=[
                    SastIssue(issue_id="1", rule_id="r1", tool="clippy", severity="major", message="", file_path="a.rs", line_start=1, line_end=1)
                ],
                total_issues=1,
                summary={}
            ),
            "semgrep": SastReport(
                scan_id="2",
                tool="semgrep",
                status="success",
                timestamp=datetime.utcnow(),
                issues=[
                    SastIssue(issue_id="2", rule_id="r2", tool="semgrep", severity="critical", message="", file_path="b.rs", line_start=2, line_end=2)
                ],
                total_issues=1,
                summary={}
            )
        }
        
        all_issues = sast_service.get_all_issues(reports)
        
        assert len(all_issues) == 2
        assert all_issues[0].tool == "clippy"
        assert all_issues[1].tool == "semgrep"


class TestSastVerification:
    """Test SAST verification logic."""
    
    @pytest.fixture
    def sast_service(self):
        """Create SAST service instance."""
        return SastService()
    
    def test_generate_verification_all_resolved(self, sast_service):
        """Test verification when all issues are resolved."""
        before_reports = {
            "clippy": SastReport(
                scan_id="1",
                tool="clippy",
                status="success",
                timestamp=datetime.utcnow(),
                issues=[
                    SastIssue(issue_id="1", rule_id="r1", tool="clippy", severity="major", message="", file_path="a.rs", line_start=1, line_end=1)
                ],
                total_issues=1,
                summary={}
            )
        }
        
        after_reports = {
            "clippy": SastReport(
                scan_id="2",
                tool="clippy",
                status="success",
                timestamp=datetime.utcnow(),
                issues=[],
                total_issues=0,
                summary={}
            )
        }
        
        verification = sast_service._generate_verification(before_reports, after_reports)
        
        assert verification.verification_status == "resolved"
        assert verification.resolved_count == 1
        assert verification.remaining_count == 0
        assert verification.new_count == 0
        assert verification.verification_score == 1.0
    
    def test_generate_verification_partial(self, sast_service):
        """Test verification when some issues remain."""
        before_reports = {
            "clippy": SastReport(
                scan_id="1",
                tool="clippy",
                status="success",
                timestamp=datetime.utcnow(),
                issues=[
                    SastIssue(issue_id="1", rule_id="r1", tool="clippy", severity="major", message="", file_path="a.rs", line_start=1, line_end=1),
                    SastIssue(issue_id="2", rule_id="r2", tool="clippy", severity="minor", message="", file_path="b.rs", line_start=2, line_end=2)
                ],
                total_issues=2,
                summary={}
            )
        }
        
        after_reports = {
            "clippy": SastReport(
                scan_id="2",
                tool="clippy",
                status="success",
                timestamp=datetime.utcnow(),
                issues=[
                    SastIssue(issue_id="2", rule_id="r2", tool="clippy", severity="minor", message="", file_path="b.rs", line_start=2, line_end=2)
                ],
                total_issues=1,
                summary={}
            )
        }
        
        verification = sast_service._generate_verification(before_reports, after_reports)
        
        assert verification.verification_status == "partial"
        assert verification.resolved_count == 1
        assert verification.remaining_count == 1
        assert verification.verification_score == 0.5
    
    def test_generate_verification_degraded(self, sast_service):
        """Test verification when new issues are introduced."""
        before_reports = {
            "clippy": SastReport(
                scan_id="1",
                tool="clippy",
                status="success",
                timestamp=datetime.utcnow(),
                issues=[
                    SastIssue(issue_id="1", rule_id="r1", tool="clippy", severity="major", message="", file_path="a.rs", line_start=1, line_end=1)
                ],
                total_issues=1,
                summary={}
            )
        }
        
        after_reports = {
            "clippy": SastReport(
                scan_id="2",
                tool="clippy",
                status="success",
                timestamp=datetime.utcnow(),
                issues=[
                    SastIssue(issue_id="1", rule_id="r1", tool="clippy", severity="major", message="", file_path="a.rs", line_start=1, line_end=1),
                    SastIssue(issue_id="2", rule_id="r2", tool="clippy", severity="critical", message="", file_path="b.rs", line_start=2, line_end=2),
                    SastIssue(issue_id="3", rule_id="r3", tool="clippy", severity="critical", message="", file_path="c.rs", line_start=3, line_end=3)
                ],
                total_issues=3,
                summary={}
            )
        }
        
        verification = sast_service._generate_verification(before_reports, after_reports)
        
        assert verification.verification_status == "degraded"
        assert verification.new_count == 2