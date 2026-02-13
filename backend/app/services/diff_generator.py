"""
Diff generator service for creating diffs between vulnerable and remediated code.
"""
import difflib
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class DiffResult:
    """Result of a diff operation."""
    diff_text: str
    lines_added: int
    lines_removed: int
    lines_modified: int
    has_changes: bool


class DiffGenerator:
    """Service for generating diffs between original and remediated code."""
    
    @staticmethod
    def generate_unified_diff(
        original_code: str,
        fixed_code: str,
        original_label: str = "vulnerable_code",
        fixed_label: str = "remediated_code",
        context_lines: int = 3
    ) -> str:
        """
        Generate a unified diff between original and fixed code.
        
        Args:
            original_code: The original vulnerable code
            fixed_code: The remediated/safe code
            original_label: Label for original file in diff header
            fixed_label: Label for fixed file in diff header
            context_lines: Number of context lines to show
            
        Returns:
            Unified diff string
        """
        original_lines = original_code.splitlines(keepends=True)
        fixed_lines = fixed_code.splitlines(keepends=True)
        
        # Use unified_diff from difflib
        diff = difflib.unified_diff(
            original_lines,
            fixed_lines,
            fromfile=original_label,
            tofile=fixed_label,
            lineterm='',
            n=context_lines
        )
        
        return ''.join(diff)
    
    @staticmethod
    def generate_side_by_side_diff(
        original_code: str,
        fixed_code: str,
        width: int = 80
    ) -> List[Dict[str, str]]:
        """
        Generate a side-by-side diff representation.
        
        Args:
            original_code: The original vulnerable code
            fixed_code: The remediated/safe code
            width: Maximum width for each side
            
        Returns:
            List of dictionaries with 'original' and 'fixed' keys
        """
        original_lines = original_code.splitlines()
        fixed_lines = fixed_code.splitlines()
        
        # Use ndiff to get differences
        diff = list(difflib.ndiff(original_lines, fixed_lines))
        
        result = []
        for line in diff:
            if line.startswith('  '):  # Unchanged
                result.append({
                    'original': line[2:],
                    'fixed': line[2:],
                    'status': 'unchanged'
                })
            elif line.startswith('- '):  # Removed
                result.append({
                    'original': line[2:],
                    'fixed': '',
                    'status': 'removed'
                })
            elif line.startswith('+ '):  # Added
                result.append({
                    'original': '',
                    'fixed': line[2:],
                    'status': 'added'
                })
        
        return result
    
    @staticmethod
    def generate_diff_stats(original_code: str, fixed_code: str) -> Dict[str, int]:
        """
        Calculate statistics about the differences.
        
        Args:
            original_code: The original vulnerable code
            fixed_code: The remediated/safe code
            
        Returns:
            Dictionary with lines_added, lines_removed, lines_modified
        """
        original_lines = original_code.splitlines()
        fixed_lines = fixed_code.splitlines()
        
        diff = list(difflib.ndiff(original_lines, fixed_lines))
        
        lines_added = sum(1 for line in diff if line.startswith('+ '))
        lines_removed = sum(1 for line in diff if line.startswith('- '))
        lines_modified = min(lines_added, lines_removed)  # Approximation
        
        return {
            "lines_added": lines_added,
            "lines_removed": lines_removed,
            "lines_modified": lines_modified
        }
    
    @staticmethod
    def generate_diff_result(
        original_code: str,
        fixed_code: str,
        original_label: str = "vulnerable_code",
        fixed_label: str = "remediated_code"
    ) -> DiffResult:
        """
        Generate a complete diff result with statistics.
        
        Args:
            original_code: The original vulnerable code
            fixed_code: The remediated/safe code
            original_label: Label for original file
            fixed_label: Label for fixed file
            
        Returns:
            DiffResult object with diff and statistics
        """
        diff_text = DiffGenerator.generate_unified_diff(
            original_code,
            fixed_code,
            original_label,
            fixed_label
        )
        
        stats = DiffGenerator.generate_diff_stats(original_code, fixed_code)
        
        return DiffResult(
            diff_text=diff_text,
            lines_added=stats["lines_added"],
            lines_removed=stats["lines_removed"],
            lines_modified=stats["lines_modified"],
            has_changes=bool(diff_text)
        )
    
# Global instance
diff_generator = DiffGenerator()
