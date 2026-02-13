"""Tests for diff_generator service."""
import pytest
from app.services.diff_generator import DiffGenerator, DiffResult


class TestDiffGenerator:
    """Test cases for DiffGenerator class."""
    
    def test_generate_unified_diff_with_changes(self, sample_rust_code, sample_safe_rust_code):
        """Test unified diff generation when code has changes."""
        diff_text = DiffGenerator.generate_unified_diff(
            sample_rust_code,
            sample_safe_rust_code
        )
        
        assert diff_text is not None
        assert isinstance(diff_text, str)
        assert "vulnerable_code" in diff_text
        assert "remediated_code" in diff_text
        # Should contain at least one removal (-) and one addition (+)
        assert "-" in diff_text or "---" in diff_text
        assert "+" in diff_text or "+++" in diff_text
    
    def test_generate_unified_diff_identical_code(self):
        """Test unified diff when code is identical."""
        code = "fn test() -> i32 { 42 }"
        
        diff_text = DiffGenerator.generate_unified_diff(code, code)
        
        assert diff_text == ""
    
    def test_generate_unified_diff_custom_labels(self):
        """Test unified diff with custom file labels."""
        original = "fn old() {}"
        fixed = "fn new() {}"
        
        diff_text = DiffGenerator.generate_unified_diff(
            original,
            fixed,
            original_label="original.rs",
            fixed_label="fixed.rs"
        )
        
        assert "original.rs" in diff_text
        assert "fixed.rs" in diff_text
    
    def test_generate_unified_diff_empty_original(self, sample_safe_rust_code):
        """Test unified diff when original is empty."""
        diff_text = DiffGenerator.generate_unified_diff(
            "",
            sample_safe_rust_code
        )
        
        assert diff_text is not None
        assert "+" in diff_text or "+++" in diff_text
    
    def test_generate_unified_diff_empty_fixed(self, sample_rust_code):
        """Test unified diff when fixed is empty."""
        diff_text = DiffGenerator.generate_unified_diff(
            sample_rust_code,
            ""
        )
        
        assert diff_text is not None
        assert "-" in diff_text or "---" in diff_text
    
    def test_generate_side_by_side_diff(self, sample_rust_code, sample_safe_rust_code):
        """Test side-by-side diff generation."""
        result = DiffGenerator.generate_side_by_side_diff(
            sample_rust_code,
            sample_safe_rust_code
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Check structure of each item
        for item in result:
            assert 'original' in item
            assert 'fixed' in item
            assert 'status' in item
            assert item['status'] in ['unchanged', 'removed', 'added']
    
    def test_generate_side_by_side_diff_identical(self):
        """Test side-by-side diff with identical code."""
        code = "fn test() {}"
        
        result = DiffGenerator.generate_side_by_side_diff(code, code)
        
        assert all(item['status'] == 'unchanged' for item in result)
    
    def test_generate_diff_stats(self, sample_rust_code, sample_safe_rust_code):
        """Test diff statistics calculation."""
        stats = DiffGenerator.generate_diff_stats(
            sample_rust_code,
            sample_safe_rust_code
        )
        
        assert 'lines_added' in stats
        assert 'lines_removed' in stats
        assert 'lines_modified' in stats
        assert isinstance(stats['lines_added'], int)
        assert isinstance(stats['lines_removed'], int)
        assert stats['lines_added'] >= 0
        assert stats['lines_removed'] >= 0
    
    def test_generate_diff_stats_identical(self):
        """Test diff stats with identical code."""
        code = "fn test() {}"
        
        stats = DiffGenerator.generate_diff_stats(code, code)
        
        assert stats['lines_added'] == 0
        assert stats['lines_removed'] == 0
    
    def test_generate_diff_result(self, sample_rust_code, sample_safe_rust_code):
        """Test complete diff result generation."""
        result = DiffGenerator.generate_diff_result(
            sample_rust_code,
            sample_safe_rust_code
        )
        
        assert isinstance(result, DiffResult)
        assert isinstance(result.diff_text, str)
        assert isinstance(result.lines_added, int)
        assert isinstance(result.lines_removed, int)
        assert isinstance(result.lines_modified, int)
        assert isinstance(result.has_changes, bool)
    
    def test_generate_diff_result_no_changes(self):
        """Test diff result when code is identical."""
        code = "fn test() {}"
        
        result = DiffGenerator.generate_diff_result(code, code)
        
        assert result.diff_text == ""
        assert result.has_changes is False
        assert result.lines_added == 0
        assert result.lines_removed == 0
    
    def test_generate_diff_result_with_custom_labels(self):
        """Test diff result with custom labels."""
        original = "fn old() {}"
        fixed = "fn new() {}"
        
        result = DiffGenerator.generate_diff_result(
            original,
            fixed,
            original_label="before.rs",
            fixed_label="after.rs"
        )
        
        assert "before.rs" in result.diff_text
        assert "after.rs" in result.diff_text
    
    def test_multiline_code_diff(self):
        """Test diff with multiline code."""
        original = """fn main() {
    let x = 1;
    let y = 2;
    println!("{}", x + y);
}"""
        
        fixed = """fn main() {
    let x = 1;
    let y = 2;
    let sum = x + y;
    println!("{}", sum);
}"""
        
        result = DiffGenerator.generate_diff_result(original, fixed)
        
        assert result.has_changes is True
        assert result.lines_added > 0
        assert result.lines_removed > 0
    
    def test_generate_diff_with_only_additions(self):
        """Test diff when only adding code."""
        original = "fn main() {}"
        fixed = """fn main() {
    println!("Hello");
}"""
        
        result = DiffGenerator.generate_diff_result(original, fixed)
        
        assert result.has_changes is True
        assert result.lines_added > 0
    
    def test_generate_diff_with_only_removals(self):
        """Test diff when only removing code."""
        original = """fn main() {
    println!("Hello");
    let x = 1;
}"""
        fixed = "fn main() {}"
        
        result = DiffGenerator.generate_diff_result(original, fixed)
        
        assert result.has_changes is True
        assert result.lines_removed > 0
