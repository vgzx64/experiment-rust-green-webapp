"""Models for SAST scan results."""
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import uuid

from app.database import Base


class SastSeverity(PyEnum):
    """SAST issue severity levels."""
    BLOCKER = "blocker"
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    INFO = "info"


class SastTool(PyEnum):
    """SAST tool identifiers."""
    CLIPPY = "clippy"
    SEMGREP = "semgrep"
    CARGO_AUDIT = "cargo-audit"


class SastIssue(BaseModel):
    """Represents a single SAST issue finding."""
    
    # Issue identification
    issue_id: str
    rule_id: str
    tool: str  # clippy, semgrep, cargo-audit
    
    # Severity and message
    severity: str  # blocker, critical, major, minor, info
    message: str
    
    # Location
    file_path: str
    line_start: int
    line_end: int
    column_start: Optional[int] = None
    column_end: Optional[int] = None
    
    # Code snippet
    snippet: Optional[str] = None
    
    # Classification
    cwe_id: Optional[str] = None
    category: Optional[str] = None
    
    # Remediation
    remediation_hint: Optional[str] = None
    auto_fixable: bool = False
    fix_suggestion: Optional[str] = None
    
    # Metadata
    raw_output: Optional[Dict[str, Any]] = None


class SastReport(BaseModel):
    """Complete SAST scan report."""
    
    # Scan metadata
    scan_id: str
    tool: str
    status: str  # success, timeout, error, partial
    timestamp: datetime
    
    # Issues
    issues: List[SastIssue]
    total_issues: int
    
    # Summary by severity
    summary: Dict[str, int]  # {severity: count}
    
    # Auto-fix results
    auto_fixes_applied: int = 0
    auto_fixes_failed: int = 0
    
    # Error info
    error_message: Optional[str] = None
    
    # Raw output
    raw_output: Optional[Dict[str, Any]] = None


class SastVerification(BaseModel):
    """Verification results comparing before/after SAST scans."""
    
    # Issues resolved
    resolved_issues: List[SastIssue]
    resolved_count: int
    
    # Issues still present
    remaining_issues: List[SastIssue]
    remaining_count: int
    
    # New issues introduced
    new_issues: List[SastIssue]
    new_count: int
    
    # Severity breakdown
    severity_changes: Dict[str, Dict[str, int]]  # {severity: {before, after, change}}
    
    # Overall status
    verification_status: str  # resolved, partial, unresolved, degraded
    verification_score: float  # 0.0 to 1.0
    
    # Notes
    verification_notes: str


class SastResult(Base):
    """Database model for storing SAST results for a session."""
    __tablename__ = "sast_results"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    
    # Scan phase
    scan_phase = Column(String(20), nullable=False)  # before_auto_fix, after_auto_fix, after_llm
    
    # Tool info
    tool = Column(String(20), nullable=False)  # clippy, semgrep, cargo-audit
    
    # Scan results
    status = Column(String(20), nullable=False)  # success, timeout, error
    issues = Column(JSON, nullable=True)  # List of SastIssue dicts
    total_issues = Column(Integer, default=0)
    summary = Column(JSON, nullable=True)  # {severity: count}
    
    # Auto-fix info
    auto_fixes_applied = Column(Integer, default=0)
    auto_fixes_failed = Column(Integer, default=0)
    
    # Error info
    error_message = Column(Text, nullable=True)
    
    # Raw output
    raw_output = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("Session", back_populates="sast_results")
    
    def __repr__(self):
        return f"<SastResult(id={self.id}, tool={self.tool}, phase={self.scan_phase}, issues={self.total_issues})>"


class SastVerificationResult(Base):
    """Database model for storing SAST verification results."""
    __tablename__ = "sast_verifications"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    analysis_id = Column(String(36), ForeignKey("analyses.id"), nullable=True)
    
    # Verification results
    verification_status = Column(String(20), nullable=False)  # resolved, partial, unresolved, degraded
    verification_score = Column(Integer, nullable=False)  # 0-100 percentage
    
    # Issue counts
    issues_before = Column(Integer, default=0)
    issues_after = Column(Integer, default=0)
    issues_resolved = Column(Integer, default=0)
    issues_remaining = Column(Integer, default=0)
    issues_new = Column(Integer, default=0)
    
    # Detailed results
    resolved_issues = Column(JSON, nullable=True)  # List of resolved issue IDs
    remaining_issues = Column(JSON, nullable=True)  # List of remaining issue IDs
    new_issues = Column(JSON, nullable=True)  # List of new issue IDs
    
    # Severity breakdown
    severity_before = Column(JSON, nullable=True)  # {severity: count}
    severity_after = Column(JSON, nullable=True)  # {severity: count}
    
    # Notes
    verification_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("Session", back_populates="sast_verifications")
    analysis = relationship("Analysis", back_populates="sast_verification")
    
    def __repr__(self):
        return f"<SastVerificationResult(id={self.id}, status={self.verification_status}, score={self.verification_score})>"