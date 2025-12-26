"""File storage service for managing session code files."""
from pathlib import Path
import shutil
from typing import Optional

class FileStorageService:
    """Service for managing filesystem operations for session code storage."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize with base directory.
        
        Args:
            base_dir: Base directory for session storage. Defaults to 
                     /home/dev/Code/rust-green-webapp/sessions
        """
        if base_dir is None:
            self.base_dir = Path("/home/dev/Code/rust-green-webapp/sessions")
        else:
            self.base_dir = Path(base_dir)
        
        # Ensure base directory exists
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def get_session_directory(self, session_id: str) -> Path:
        """Get filesystem directory for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Path to session directory (creates if doesn't exist)
        """
        session_dir = self.base_dir / session_id / "repo"
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir
    
    def save_uploaded_code(self, session_id: str, code: str) -> Path:
        """Save uploaded Rust code to session directory.
        
        Args:
            session_id: Session ID
            code: Rust code content
            
        Returns:
            Path to saved code file
        """
        session_dir = self.get_session_directory(session_id)
        code_file = session_dir / "uploaded_code.rs"
        code_file.write_text(code)
        return code_file
    
    def read_uploaded_code(self, session_id: str) -> Optional[str]:
        """Read uploaded Rust code from session directory.
        
        Args:
            session_id: Session ID
            
        Returns:
            Code content if exists, None otherwise
        """
        code_file = self.base_dir / session_id / "repo" / "uploaded_code.rs"
        if code_file.exists():
            return code_file.read_text()
        return None
    
    def session_has_uploaded_code(self, session_id: str) -> bool:
        """Check if session has uploaded code.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if uploaded code exists
        """
        code_file = self.base_dir / session_id / "repo" / "uploaded_code.rs"
        return code_file.exists()
    
    def get_uploaded_code_path(self, session_id: str) -> Optional[Path]:
        """Get path to uploaded code file.
        
        Args:
            session_id: Session ID
            
        Returns:
            Path to code file if exists, None otherwise
        """
        code_file = self.base_dir / session_id / "repo" / "uploaded_code.rs"
        if code_file.exists():
            return code_file
        return None
    
    def cleanup_session_directory(self, session_id: str):
        """Delete session directory.
        
        Args:
            session_id: Session ID
        """
        session_dir = self.base_dir / session_id
        if session_dir.exists():
            shutil.rmtree(session_dir)
    
    def list_session_files(self, session_id: str) -> list[Path]:
        """List all files in session directory.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of file paths
        """
        session_dir = self.base_dir / session_id / "repo"
        if not session_dir.exists():
            return []
        
        return list(session_dir.rglob("*"))
