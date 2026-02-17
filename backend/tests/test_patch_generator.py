"""Tests for PatchGenerator service."""
import pytest
import zipfile
import io
from unittest.mock import MagicMock
from datetime import datetime

from app.services.patch_generator import PatchGenerator
from app.models.session import Session, SessionStatus
from app.models.analysis import Analysis, CodeBlockType, RiskLevel
from app.models.code_block import CodeBlock


class TestPatchGenerator:
    """Test cases for PatchGenerator."""
    
    @pytest.fixture
    def patch_generator(self):
        """Create PatchGenerator instance."""
        return PatchGenerator()
    
    @pytest.fixture
    def mock_session(self):
        """Create mock session."""
        session = Session()
        session.id = "test-session-id"
        session.orig_location = "https://github.com/user/repo"
        session.git_ref = "main"
        session.status = SessionStatus.COMPLETED
        return session
    
    @pytest.fixture
    def mock_code_block(self):
        """Create mock code block."""
        block = CodeBlock()
        block.id = "block-123"
        block.raw_code = "unsafe { *ptr }"
        block.line_start = 10
        block.line_end = 12
        block.file_path = "src/main.rs"
        return block
    
    @pytest.fixture
    def mock_analysis(self, mock_code_block):
        """Create mock analysis with suggested replacement."""
        analysis = Analysis()
        analysis.id = "analysis-123"
        analysis.code_block_type = CodeBlockType.REPLACEABLE
        analysis.suggested_replacement = "safe_deref(ptr)"
        analysis.cwe_id = "CWE-787"
        analysis.risk_level = RiskLevel.HIGH
        analysis.code_block = mock_code_block
        return analysis
    
    @pytest.fixture
    def original_files(self):
        """Sample original files."""
        return {
            "src/main.rs": """fn main() {
    let ptr: *const i32 = &42;
    unsafe { *ptr }
    println!("Done");
}""",
            "src/lib.rs": "pub fn helper() {}"
        }
    
    # ==================== generate_fixed_files_zip Tests ====================
    
    def test_generate_fixed_files_zip_basic(self, patch_generator, mock_session, mock_analysis, original_files):
        """Test basic ZIP generation with fixed files."""
        zip_bytes = patch_generator.generate_fixed_files_zip(
            mock_session,
            [mock_analysis],
            original_files
        )
        
        assert isinstance(zip_bytes, bytes)
        assert len(zip_bytes) > 0
        
        # Verify ZIP structure
        zip_buffer = io.BytesIO(zip_bytes)
        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            names = zf.namelist()
            assert "src/main.rs" in names
            assert "src/lib.rs" in names
            assert "README.txt" in names
    
    def test_generate_fixed_files_zip_contains_readme(self, patch_generator, mock_session, mock_analysis, original_files):
        """Test that ZIP contains README with metadata."""
        zip_bytes = patch_generator.generate_fixed_files_zip(
            mock_session,
            [mock_analysis],
            original_files
        )
        
        zip_buffer = io.BytesIO(zip_bytes)
        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            readme = zf.read("README.txt").decode('utf-8')
            
            assert "rust-green" in readme
            assert "test-session-id" in readme
            assert "https://github.com/user/repo" in readme
    
    def test_generate_fixed_files_zip_no_analyses(self, patch_generator, mock_session, original_files):
        """Test ZIP generation with no analyses."""
        zip_bytes = patch_generator.generate_fixed_files_zip(
            mock_session,
            [],
            original_files
        )
        
        zip_buffer = io.BytesIO(zip_bytes)
        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            # Should still contain original files
            assert "src/main.rs" in zf.namelist()
    
    def test_generate_fixed_files_zip_no_replacement(self, patch_generator, mock_session, mock_code_block, original_files):
        """Test ZIP generation when analysis has no suggested replacement."""
        analysis = Analysis()
        analysis.code_block_type = CodeBlockType.NON_REPLACEABLE
        analysis.suggested_replacement = None  # No replacement
        analysis.code_block = mock_code_block
        
        zip_bytes = patch_generator.generate_fixed_files_zip(
            mock_session,
            [analysis],
            original_files
        )
        
        # Should still generate valid ZIP
        assert isinstance(zip_bytes, bytes)
        assert len(zip_bytes) > 0
    
    # ==================== generate_patches_zip Tests ====================
    
    def test_generate_patches_zip_basic(self, patch_generator, mock_session, mock_analysis, original_files):
        """Test basic patch ZIP generation."""
        zip_bytes = patch_generator.generate_patches_zip(
            mock_session,
            [mock_analysis],
            original_files
        )
        
        assert isinstance(zip_bytes, bytes)
        assert len(zip_bytes) > 0
        
        # Verify ZIP structure
        zip_buffer = io.BytesIO(zip_bytes)
        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            names = zf.namelist()
            assert "src/main.rs.patch" in names
            assert "README.txt" in names
    
    def test_generate_patches_zip_patch_format(self, patch_generator, mock_session, mock_analysis, original_files):
        """Test that patches are in unified diff format."""
        zip_bytes = patch_generator.generate_patches_zip(
            mock_session,
            [mock_analysis],
            original_files
        )
        
        zip_buffer = io.BytesIO(zip_bytes)
        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            patch_content = zf.read("src/main.rs.patch").decode('utf-8')
            
            # Unified diff markers
            assert "---" in patch_content or "a/src/main.rs" in patch_content
            assert "+++" in patch_content or "b/src/main.rs" in patch_content
    
    def test_generate_patches_zip_no_changes(self, patch_generator, mock_session, original_files):
        """Test patch ZIP when no changes needed."""
        zip_bytes = patch_generator.generate_patches_zip(
            mock_session,
            [],
            original_files
        )
        
        zip_buffer = io.BytesIO(zip_bytes)
        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            # Should only have README
            names = zf.namelist()
            assert "README.txt" in names
            # No patch files since no changes
            assert not any(n.endswith('.patch') for n in names)
    
    # ==================== _apply_fix_to_file Tests ====================
    
    def test_apply_fix_to_file_basic(self, patch_generator):
        """Test applying fix to file content."""
        original = """line 1
line 2
line 3
line 4
line 5"""
        
        result = patch_generator._apply_fix_to_file(
            original,
            "line 2\nline 3",
            "fixed line",
            2,  # line_start (1-indexed)
            3   # line_end
        )
        
        lines = result.split('\n')
        assert lines[0] == "line 1"
        assert lines[1] == "fixed line"
        assert lines[2] == "line 4"
    
    def test_apply_fix_to_file_first_line(self, patch_generator):
        """Test applying fix to first line."""
        original = "line 1\nline 2\nline 3"
        
        result = patch_generator._apply_fix_to_file(
            original,
            "line 1",
            "fixed first",
            1, 1
        )
        
        assert result.startswith("fixed first")
    
    def test_apply_fix_to_file_last_line(self, patch_generator):
        """Test applying fix to last line."""
        original = "line 1\nline 2\nline 3"
        
        result = patch_generator._apply_fix_to_file(
            original,
            "line 3",
            "fixed last",
            3, 3
        )
        
        assert result.endswith("fixed last")
    
    def test_apply_fix_to_file_multiline_replacement(self, patch_generator):
        """Test replacing with multiline code."""
        original = "line 1\nline 2\nline 3"
        
        result = patch_generator._apply_fix_to_file(
            original,
            "line 2",
            "new line 2a\nnew line 2b",
            2, 2
        )
        
        assert "new line 2a" in result
        assert "new line 2b" in result
    
    # ==================== _generate_unified_diff Tests ====================
    
    def test_generate_unified_diff_basic(self, patch_generator):
        """Test unified diff generation."""
        original = "line 1\nline 2\nline 3"
        fixed = "line 1\nline 2 modified\nline 3"
        
        diff = patch_generator._generate_unified_diff(
            "test.rs",
            original,
            fixed
        )
        
        assert "test.rs" in diff
        assert "-line 2" in diff or "-line 2" in diff
        assert "+line 2 modified" in diff or "+line 2 modified" in diff
    
    def test_generate_unified_diff_header(self, patch_generator):
        """Test unified diff header format."""
        original = "code"
        fixed = "fixed code"
        
        diff = patch_generator._generate_unified_diff("test.rs", original, fixed)
        
        assert "a/test.rs" in diff
        assert "b/test.rs" in diff
        assert "Generated by rust-green" in diff
    
    def test_generate_unified_diff_identical(self, patch_generator):
        """Test diff for identical content."""
        content = "line 1\nline 2"
        
        diff = patch_generator._generate_unified_diff("test.rs", content, content)
        
        # Diff should contain headers but no actual changes
        assert "test.rs" in diff
        # No removal lines (except header ---)
        lines = diff.split('\n')
        removal_lines = [l for l in lines if l.startswith('-') and not l.startswith('---')]
        assert len(removal_lines) == 0
    
    # ==================== _generate_readme Tests ====================
    
    def test_generate_readme_fixed_files(self, patch_generator, mock_session, mock_analysis):
        """Test README for fixed files archive."""
        readme = patch_generator._generate_readme(
            mock_session,
            [mock_analysis],
            "Fixed Source Code"
        )
        
        assert "Fixed Source Code" in readme
        assert "test-session-id" in readme
        assert "Total issues found: 1" in readme
    
    def test_generate_readme_patches(self, patch_generator, mock_session, mock_analysis):
        """Test README for patches archive."""
        readme = patch_generator._generate_readme(
            mock_session,
            [mock_analysis],
            "Git Patches"
        )
        
        assert "Git Patches" in readme
        assert "git apply" in readme
    
    def test_generate_readme_statistics(self, patch_generator, mock_session):
        """Test README contains correct statistics."""
        # Create analyses with different types
        analyses = []
        
        for _ in range(3):
            a = Analysis()
            a.code_block_type = CodeBlockType.REPLACEABLE
            analyses.append(a)
        
        for _ in range(2):
            a = Analysis()
            a.code_block_type = CodeBlockType.NON_REPLACEABLE
            analyses.append(a)
        
        a = Analysis()
        a.code_block_type = CodeBlockType.CONDITIONALLY_REPLACEABLE
        analyses.append(a)
        
        readme = patch_generator._generate_readme(mock_session, analyses, "Test")
        
        assert "Total issues found: 6" in readme
        assert "Replaceable: 3" in readme
        assert "Non-replaceable: 2" in readme
        assert "Conditionally replaceable: 1" in readme


class TestPatchGeneratorEdgeCases:
    """Test edge cases in PatchGenerator."""
    
    @pytest.fixture
    def patch_generator(self):
        return PatchGenerator()
    
    def test_empty_original_files(self, patch_generator):
        """Test with empty original files dict."""
        session = Session()
        session.id = "test"
        
        zip_bytes = patch_generator.generate_fixed_files_zip(session, [], {})
        
        # Should still generate valid ZIP with README
        zip_buffer = io.BytesIO(zip_bytes)
        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            assert "README.txt" in zf.namelist()
    
    def test_analysis_without_file_path(self, patch_generator):
        """Test analysis without file path (direct code submission)."""
        session = Session()
        session.id = "test"
        
        block = CodeBlock()
        block.raw_code = "unsafe code"
        block.line_start = 1
        block.line_end = 1
        block.file_path = None  # No file path
        
        analysis = Analysis()
        analysis.code_block_type = CodeBlockType.REPLACEABLE
        analysis.suggested_replacement = "safe code"
        analysis.code_block = block
        
        original_files = {"code.rs": "unsafe code"}
        
        # Should handle gracefully - generate valid ZIP
        zip_bytes = patch_generator.generate_fixed_files_zip(
            session, [analysis], original_files
        )
        
        # Verify it's a valid ZIP file
        assert isinstance(zip_bytes, bytes)
        assert len(zip_bytes) > 0
        
        zip_buffer = io.BytesIO(zip_bytes)
        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            # Should contain README
            assert "README.txt" in zf.namelist()
            # Should contain the original file
            assert "code.rs" in zf.namelist()
            # Original file should be unchanged since file_path is None
            content = zf.read("code.rs").decode('utf-8')
            assert content == "unsafe code"
    
    def test_file_not_in_original_files(self, patch_generator):
        """Test when analysis references file not in original files."""
        session = Session()
        session.id = "test"
        
        block = CodeBlock()
        block.raw_code = "code"
        block.line_start = 1
        block.line_end = 1
        block.file_path = "missing.rs"  # File not in original_files
        
        analysis = Analysis()
        analysis.code_block_type = CodeBlockType.REPLACEABLE
        analysis.suggested_replacement = "fixed"
        analysis.code_block = block
        
        original_files = {"other.rs": "other code"}
        
        # Should handle gracefully - generate valid ZIP without crashing
        zip_bytes = patch_generator.generate_fixed_files_zip(
            session, [analysis], original_files
        )
        
        # Verify it's a valid ZIP file
        assert isinstance(zip_bytes, bytes)
        assert len(zip_bytes) > 0
        
        zip_buffer = io.BytesIO(zip_bytes)
        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            # Should contain README
            assert "README.txt" in zf.namelist()
            # Should contain the original file (unchanged)
            assert "other.rs" in zf.namelist()
            content = zf.read("other.rs").decode('utf-8')
            assert content == "other code"
    
    def test_windows_path_handling(self, patch_generator):
        """Test that Windows paths are converted to forward slashes in ZIP."""
        session = Session()
        session.id = "test"
        
        block = CodeBlock()
        block.raw_code = "code"
        block.line_start = 1
        block.line_end = 1
        block.file_path = "src\\main.rs"  # Windows path
        
        analysis = Analysis()
        analysis.code_block_type = CodeBlockType.REPLACEABLE
        analysis.suggested_replacement = "fixed"
        analysis.code_block = block
        
        original_files = {"src\\main.rs": "code"}
        
        zip_bytes = patch_generator.generate_fixed_files_zip(
            session, [analysis], original_files
        )
        
        # Verify it's a valid ZIP file
        assert isinstance(zip_bytes, bytes)
        assert len(zip_bytes) > 0
        
        zip_buffer = io.BytesIO(zip_bytes)
        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            names = zf.namelist()
            # Should contain README
            assert "README.txt" in names
            # All paths should use forward slashes (no backslashes)
            for name in names:
                if name != "README.txt":
                    assert "\\" not in name, f"Path {name} contains backslash"
                    # Should be a valid forward-slash path
                    assert "/" in name or name.endswith(".rs")
