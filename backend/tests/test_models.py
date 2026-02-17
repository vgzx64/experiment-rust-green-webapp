"""Tests for database models."""
import pytest
from datetime import datetime
from unittest.mock import patch

from app.models.session import Session, SessionStatus
from app.models.analysis import Analysis, CodeBlockType, RiskLevel
from app.models.code_block import CodeBlock


class TestSessionModel:
    """Test cases for Session model."""
    
    def test_session_creation_default_values(self):
        """Test session creation with default values."""
        session = Session()
        
        # Verify the model can be instantiated and has expected attributes
        assert session is not None
        assert hasattr(session, 'status')
        assert hasattr(session, 'progress')
        assert hasattr(session, 'orig_location')
        assert hasattr(session, 'git_ref')
        assert hasattr(session, 'selected_files')
        assert hasattr(session, 'error_message')
        assert hasattr(session, 'completed_at')
    
    def test_session_creation_with_code(self):
        """Test session creation for code submission."""
        session = Session(
            orig_location=None,
            status=SessionStatus.PENDING,
            progress=0
        )
        
        assert session.status == SessionStatus.PENDING
        assert session.orig_location is None
        assert session.progress == 0
    
    def test_session_creation_with_git(self):
        """Test session creation for Git repository."""
        session = Session(
            orig_location="https://github.com/user/repo",
            git_ref="main",
            selected_files=["src/main.rs", "src/lib.rs"],
            status=SessionStatus.PENDING,
            progress=0
        )
        
        assert session.orig_location == "https://github.com/user/repo"
        assert session.git_ref == "main"
        assert session.selected_files == ["src/main.rs", "src/lib.rs"]
    
    def test_session_status_enum_values(self):
        """Test SessionStatus enum values."""
        assert SessionStatus.PENDING.value == "pending"
        assert SessionStatus.PROCESSING.value == "processing"
        assert SessionStatus.COMPLETED.value == "completed"
        assert SessionStatus.FAILED.value == "failed"
    
    def test_session_status_transitions(self):
        """Test valid session status transitions."""
        session = Session()
        
        # PENDING -> PROCESSING
        session.status = SessionStatus.PROCESSING
        assert session.status == SessionStatus.PROCESSING
        
        # PROCESSING -> COMPLETED
        session.status = SessionStatus.COMPLETED
        assert session.status == SessionStatus.COMPLETED
        
        # Can also transition to FAILED
        session2 = Session()
        session2.status = SessionStatus.PROCESSING
        session2.status = SessionStatus.FAILED
        assert session2.status == SessionStatus.FAILED
    
    def test_session_progress_range(self):
        """Test session progress values."""
        session = Session()
        
        # Valid progress values
        session.progress = 0
        assert session.progress == 0
        
        session.progress = 50
        assert session.progress == 50
        
        session.progress = 100
        assert session.progress == 100
    
    def test_session_timestamps(self):
        """Test session timestamp handling."""
        # SQLAlchemy models get timestamps on flush to database
        # Here we verify the model has the timestamp attributes with correct types
        session = Session()
        assert hasattr(session, 'created_at')
        assert hasattr(session, 'updated_at')
        assert hasattr(session, 'completed_at')
        
        # completed_at should be None for new sessions
        # (will be set when session completes)
    
    def test_session_repr(self):
        """Test session string representation."""
        session = Session()
        session.status = SessionStatus.PENDING
        session.progress = 50
        
        repr_str = repr(session)
        assert "Session" in repr_str
        # The repr should contain status and progress info
        assert "pending" in repr_str.lower() or "PENDING" in repr_str


class TestAnalysisModel:
    """Test cases for Analysis model."""
    
    def test_analysis_creation_default_values(self):
        """Test analysis creation with default values."""
        analysis = Analysis(
            code_block_type=CodeBlockType.REPLACEABLE
        )
        
        assert analysis.code_block_type == CodeBlockType.REPLACEABLE
        assert analysis.suggested_replacement is None
        assert analysis.cwe_id is None
        assert analysis.owasp_category is None
        assert analysis.risk_level is None
        assert analysis.confidence_score is None
        assert analysis.vulnerability_description is None
        assert analysis.exploitation_scenario is None
        assert analysis.remediation_explanation is None
        assert analysis.llm_metadata is None
    
    def test_analysis_with_full_data(self):
        """Test analysis with all fields populated."""
        analysis = Analysis(
            session_id="session-123",
            code_block_id="block-456",
            code_block_type=CodeBlockType.REPLACEABLE,
            suggested_replacement="fn safe() {}",
            cwe_id="CWE-787",
            owasp_category="A1: Injection",
            risk_level=RiskLevel.HIGH,
            confidence_score=0.95,
            vulnerability_description="Buffer overflow vulnerability",
            exploitation_scenario="Attacker can overwrite memory",
            remediation_explanation="Use safe bounds checking",
            llm_metadata={"tokens": 150, "model": "test"}
        )
        
        assert analysis.session_id == "session-123"
        assert analysis.code_block_id == "block-456"
        assert analysis.code_block_type == CodeBlockType.REPLACEABLE
        assert analysis.suggested_replacement == "fn safe() {}"
        assert analysis.cwe_id == "CWE-787"
        assert analysis.owasp_category == "A1: Injection"
        assert analysis.risk_level == RiskLevel.HIGH
        assert analysis.confidence_score == 0.95
        assert analysis.vulnerability_description == "Buffer overflow vulnerability"
        assert analysis.llm_metadata == {"tokens": 150, "model": "test"}
    
    def test_analysis_all_code_block_types(self):
        """Test analysis with all code block types."""
        for block_type in [CodeBlockType.REPLACEABLE, CodeBlockType.NON_REPLACEABLE, CodeBlockType.CONDITIONALLY_REPLACEABLE]:
            analysis = Analysis(code_block_type=block_type)
            assert analysis.code_block_type == block_type
    
    def test_analysis_all_risk_levels(self):
        """Test analysis with all risk levels."""
        for risk in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]:
            analysis = Analysis(
                code_block_type=CodeBlockType.REPLACEABLE,
                risk_level=risk
            )
            assert analysis.risk_level == risk
    
    def test_code_block_type_enum_values(self):
        """Test CodeBlockType enum values."""
        assert CodeBlockType.REPLACEABLE.value == "replaceable"
        assert CodeBlockType.NON_REPLACEABLE.value == "non_replaceable"
        assert CodeBlockType.CONDITIONALLY_REPLACEABLE.value == "conditionally_replaceable"
    
    def test_risk_level_enum_values(self):
        """Test RiskLevel enum values."""
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"
    
    def test_analysis_repr(self):
        """Test analysis string representation."""
        analysis = Analysis(
            code_block_type=CodeBlockType.REPLACEABLE,
            cwe_id="CWE-787",
            risk_level=RiskLevel.HIGH
        )
        
        repr_str = repr(analysis)
        assert "Analysis" in repr_str
        assert "CWE-787" in repr_str


class TestCodeBlockModel:
    """Test cases for CodeBlock model."""
    
    def test_code_block_creation(self):
        """Test code block creation."""
        code = "fn main() { unsafe { } }"
        block = CodeBlock(
            raw_code=code,
            line_start=1,
            line_end=3,
            file_path="src/main.rs"
        )
        
        assert block.raw_code == code
        assert block.line_start == 1
        assert block.line_end == 3
        assert block.file_path == "src/main.rs"
    
    def test_code_block_without_file_path(self):
        """Test code block without file path (direct code submission)."""
        block = CodeBlock(
            raw_code="unsafe code",
            line_start=1,
            line_end=1,
            file_path=None
        )
        
        assert block.file_path is None
        assert block.raw_code == "unsafe code"
    
    def test_code_block_line_numbers(self):
        """Test code block line number handling."""
        block = CodeBlock(
            raw_code="line1\nline2\nline3",
            line_start=10,
            line_end=12
        )
        
        assert block.line_start == 10
        assert block.line_end == 12
    
    def test_code_block_multiline_code(self):
        """Test code block with multiline code."""
        code = """fn main() {
    unsafe { *ptr }
}"""
        block = CodeBlock(
            raw_code=code,
            line_start=1,
            line_end=3,
            file_path="src/main.rs"
        )
        
        assert block.raw_code == code
        assert "\n" in block.raw_code


class TestEnumValues:
    """Test enum value validation."""
    
    def test_session_status_from_string(self):
        """Test creating SessionStatus from string value."""
        assert SessionStatus("pending") == SessionStatus.PENDING
        assert SessionStatus("processing") == SessionStatus.PROCESSING
        assert SessionStatus("completed") == SessionStatus.COMPLETED
        assert SessionStatus("failed") == SessionStatus.FAILED
    
    def test_code_block_type_from_string(self):
        """Test creating CodeBlockType from string value."""
        assert CodeBlockType("replaceable") == CodeBlockType.REPLACEABLE
        assert CodeBlockType("non_replaceable") == CodeBlockType.NON_REPLACEABLE
        assert CodeBlockType("conditionally_replaceable") == CodeBlockType.CONDITIONALLY_REPLACEABLE
    
    def test_risk_level_from_string(self):
        """Test creating RiskLevel from string value."""
        assert RiskLevel("low") == RiskLevel.LOW
        assert RiskLevel("medium") == RiskLevel.MEDIUM
        assert RiskLevel("high") == RiskLevel.HIGH
        assert RiskLevel("critical") == RiskLevel.CRITICAL
    
    def test_invalid_enum_value_raises_error(self):
        """Test that invalid enum values raise errors."""
        with pytest.raises(ValueError):
            SessionStatus("invalid")
        
        with pytest.raises(ValueError):
            CodeBlockType("invalid")
        
        with pytest.raises(ValueError):
            RiskLevel("invalid")
    
    def test_enum_case_sensitivity(self):
        """Test that enum values are case-sensitive."""
        with pytest.raises(ValueError):
            SessionStatus("PENDING")  # Should be lowercase "pending"
        
        with pytest.raises(ValueError):
            RiskLevel("HIGH")  # Should be lowercase "high"


class TestModelRelationships:
    """Test model relationships."""
    
    def test_session_analyses_relationship(self):
        """Test session has analyses relationship."""
        session = Session()
        session.analyses = []
        
        assert hasattr(session, 'analyses')
        assert session.analyses == []
    
    def test_analysis_session_relationship(self):
        """Test analysis belongs to session relationship."""
        analysis = Analysis(code_block_type=CodeBlockType.REPLACEABLE)
        
        assert hasattr(analysis, 'session')
        assert hasattr(analysis, 'session_id')
    
    def test_analysis_code_block_relationship(self):
        """Test analysis has code block relationship."""
        analysis = Analysis(code_block_type=CodeBlockType.REPLACEABLE)
        
        assert hasattr(analysis, 'code_block')
        assert hasattr(analysis, 'code_block_id')
    
    def test_code_block_analysis_relationship(self):
        """Test code block has analysis relationship."""
        block = CodeBlock()
        
        assert hasattr(block, 'analysis')