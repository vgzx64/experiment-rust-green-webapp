"""Service for generating patches and ZIP files from analysis results."""
import io
import zipfile
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

from app.models.session import Session
from app.models.analysis import Analysis
from app.models.code_block import CodeBlock
from app.services.git_service import git_service

logger = logging.getLogger(__name__)


class PatchGenerator:
    """Generate patches and ZIP files from analysis results."""
    
    def generate_fixed_files_zip(
        self,
        session: Session,
        analyses: List[Analysis],
        original_files: Dict[str, str]
    ) -> bytes:
        """Generate a ZIP file with fixed source code files.
        
        Args:
            session: The analysis session
            analyses: List of analysis results with suggested replacements
            original_files: Dict of file_path -> original content
            
        Returns:
            ZIP file as bytes
        """
        zip_buffer = io.BytesIO()
        
        # Build a map of file_path -> fixed content
        fixed_files: Dict[str, str] = dict(original_files)  # Start with originals
        
        # Apply fixes to each file
        for analysis in analyses:
            if not analysis.suggested_replacement:  # type: ignore
                continue
                
            code_block = analysis.code_block
            if not code_block or not code_block.file_path:  # type: ignore
                continue
            
            file_path = code_block.file_path
            if file_path not in fixed_files:
                continue
            
            # Replace the vulnerable code with the fix
            original_content = fixed_files[file_path]
            fixed_content = self._apply_fix_to_file(
                original_content,
                code_block.raw_code,
                analysis.suggested_replacement,
                code_block.line_start,
                code_block.line_end
            )
            fixed_files[file_path] = fixed_content
        
        # Create ZIP file
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path, content in fixed_files.items():
                # Use forward slashes in ZIP paths
                zip_path = file_path.replace('\\', '/')
                zf.writestr(zip_path, content)
            
            # Add a README
            readme = self._generate_readme(session, analyses, "Fixed Source Code")
            zf.writestr("README.txt", readme)
        
        zip_buffer.seek(0)
        return zip_buffer.getvalue()
    
    def generate_patches_zip(
        self,
        session: Session,
        analyses: List[Analysis],
        original_files: Dict[str, str]
    ) -> bytes:
        """Generate a ZIP file with .patch files.
        
        Args:
            session: The analysis session
            analyses: List of analysis results with suggested replacements
            original_files: Dict of file_path -> original content
            
        Returns:
            ZIP file as bytes
        """
        zip_buffer = io.BytesIO()
        
        # Build a map of file_path -> fixed content
        fixed_files: Dict[str, str] = dict(original_files)
        
        # Apply fixes to each file
        for analysis in analyses:
            if not analysis.suggested_replacement:  # type: ignore
                continue
                
            code_block = analysis.code_block
            if not code_block or not code_block.file_path:  # type: ignore
                continue
            
            file_path = code_block.file_path
            if file_path not in fixed_files:
                continue
            
            # Replace the vulnerable code with the fix
            original_content = fixed_files[file_path]
            fixed_content = self._apply_fix_to_file(
                original_content,
                code_block.raw_code,
                analysis.suggested_replacement,  # type: ignore
                code_block.line_start,
                code_block.line_end
            )
            fixed_files[file_path] = fixed_content
        
        # Create ZIP file with patches
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path, fixed_content in fixed_files.items():
                if file_path not in original_files:
                    continue
                    
                original_content = original_files[file_path]
                if original_content == fixed_content:
                    continue  # No changes, skip patch
                
                # Generate unified diff
                patch = self._generate_unified_diff(
                    file_path,
                    original_content,
                    fixed_content
                )
                
                # Use .patch extension
                zip_path = file_path.replace('\\', '/') + ".patch"
                zf.writestr(zip_path, patch)
            
            # Add a README
            readme = self._generate_readme(session, analyses, "Git Patches")
            zf.writestr("README.txt", readme)
        
        zip_buffer.seek(0)
        return zip_buffer.getvalue()
    
    def _apply_fix_to_file(
        self,
        original_content: str,
        vulnerable_code: str,
        fixed_code: str,
        line_start: int,
        line_end: int
    ) -> str:
        """Apply a fix to a file by replacing the vulnerable code.
        
        Args:
            original_content: Original file content
            vulnerable_code: The vulnerable code snippet
            fixed_code: The fixed code snippet
            line_start: Starting line number (1-indexed)
            line_end: Ending line number (1-indexed)
            
        Returns:
            Fixed file content
        """
        lines = original_content.split('\n')
        
        # Convert to 0-indexed
        start_idx = max(0, line_start - 1)
        end_idx = min(len(lines), line_end)
        
        # Replace the lines
        new_lines = lines[:start_idx] + [fixed_code] + lines[end_idx:]
        
        return '\n'.join(new_lines)
    
    def _generate_unified_diff(
        self,
        file_path: str,
        original_content: str,
        fixed_content: str
    ) -> str:
        """Generate a unified diff patch.
        
        Args:
            file_path: Path to the file
            original_content: Original file content
            fixed_content: Fixed file content
            
        Returns:
            Unified diff string
        """
        import difflib
        
        original_lines = original_content.splitlines(keepends=True)
        fixed_lines = fixed_content.splitlines(keepends=True)
        
        # Generate unified diff
        diff = difflib.unified_diff(
            original_lines,
            fixed_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm=''
        )
        
        # Add timestamp header
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        header = f"# Generated by rust-green on {timestamp}\n"
        header += f"# File: {file_path}\n\n"
        
        return header + ''.join(diff)
    
    def _generate_readme(
        self,
        session: Session,
        analyses: List[Analysis],
        archive_type: str
    ) -> str:
        """Generate a README for the ZIP archive."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        readme = f"""rust-green Analysis Results
{'=' * 40}

Archive Type: {archive_type}
Session ID: {session.id}
Repository: {session.orig_location or 'N/A'}
Branch/Ref: {session.git_ref or 'N/A'}
Generated: {timestamp}

Analysis Summary:
- Total issues found: {len(analyses)}
- Replaceable: {sum(1 for a in analyses if a.code_block_type.value == 'replaceable')}
- Non-replaceable: {sum(1 for a in analyses if a.code_block_type.value == 'non_replaceable')}
- Conditionally replaceable: {sum(1 for a in analyses if a.code_block_type.value == 'conditionally_replaceable')}

"""
        
        if archive_type == "Git Patches":
            readme += """How to apply patches:
---------------------
1. Navigate to your repository root
2. Extract the ZIP file
3. Apply patches using: git apply <patch_file>

Example:
    git apply src/main.rs.patch

Note: Apply patches one at a time and review changes before committing.
"""
        else:
            readme += """How to use fixed files:
----------------------
1. Extract the ZIP file
2. Review the changes in each file
3. Copy the fixed files to your repository
4. Test the changes before committing
"""
        
        return readme


# Global instance
patch_generator = PatchGenerator()