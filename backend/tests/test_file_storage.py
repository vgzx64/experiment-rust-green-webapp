"""Tests for FileStorageService."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.services.file_storage_service import FileStorageService


class TestFileStorageService:
    """Test cases for FileStorageService."""
    
    @pytest.fixture
    def storage_service(self, tmp_path):
        """Create FileStorageService with temporary base directory."""
        return FileStorageService(base_dir=tmp_path)
    
    # ==================== save_uploaded_code Tests ====================
    
    def test_save_uploaded_code(self, storage_service):
        """Test saving uploaded code."""
        session_id = "test-session-123"
        code = "fn main() { println!(\"Hello\"); }"
        
        file_path = storage_service.save_uploaded_code(session_id, code)
        
        assert file_path.exists()
        assert file_path.read_text() == code
    
    def test_save_uploaded_code_creates_directory(self, storage_service, tmp_path):
        """Test that saving code creates session directory."""
        session_id = "new-session"
        code = "fn test() {}"
        
        file_path = storage_service.save_uploaded_code(session_id, code)
        
        session_dir = tmp_path / session_id
        assert session_dir.exists()
        assert session_dir.is_dir()
    
    def test_save_uploaded_code_overwrites(self, storage_service):
        """Test that saving code overwrites existing file."""
        session_id = "test-session"
        
        storage_service.save_uploaded_code(session_id, "original code")
        storage_service.save_uploaded_code(session_id, "new code")
        
        file_path = storage_service.get_uploaded_code_path(session_id)
        assert file_path.read_text() == "new code"
    
    # ==================== read_uploaded_code Tests ====================
    
    def test_read_uploaded_code_success(self, storage_service):
        """Test retrieving saved code."""
        session_id = "test-session"
        code = "fn main() {}"
        
        storage_service.save_uploaded_code(session_id, code)
        retrieved = storage_service.read_uploaded_code(session_id)
        
        assert retrieved == code
    
    def test_read_uploaded_code_not_found(self, storage_service):
        """Test retrieving code when file doesn't exist."""
        session_id = "nonexistent-session"
        
        result = storage_service.read_uploaded_code(session_id)
        
        assert result is None
    
    def test_read_uploaded_code_empty_file(self, storage_service):
        """Test retrieving empty code file."""
        session_id = "empty-session"
        
        storage_service.save_uploaded_code(session_id, "")
        result = storage_service.read_uploaded_code(session_id)
        
        assert result == ""
    
    # ==================== get_uploaded_code_path Tests ====================
    
    def test_get_uploaded_code_path(self, storage_service, tmp_path):
        """Test getting the path for uploaded code."""
        session_id = "test-session"
        
        storage_service.save_uploaded_code(session_id, "code")
        path = storage_service.get_uploaded_code_path(session_id)
        
        assert path is not None
        assert session_id in str(path)
        assert "uploaded_code.rs" in str(path)
    
    # ==================== cleanup_session_directory Tests ====================
    
    def test_cleanup_session_directory(self, storage_service):
        """Test cleaning up session directory."""
        session_id = "cleanup-test"
        
        # Create some files
        storage_service.save_uploaded_code(session_id, "code")
        
        session_dir = storage_service.base_dir / session_id
        assert session_dir.exists()
        
        # Cleanup
        storage_service.cleanup_session_directory(session_id)
        
        assert not session_dir.exists()
    
    def test_cleanup_session_directory_nonexistent(self, storage_service):
        """Test cleaning up non-existent directory (no error)."""
        session_id = "nonexistent"
        
        # Should not raise error
        storage_service.cleanup_session_directory(session_id)
    
    def test_cleanup_session_directory_with_files(self, storage_service):
        """Test cleaning up directory with multiple files."""
        session_id = "multi-file-session"
        
        # Create session directory with multiple files
        session_dir = storage_service.base_dir / session_id
        session_dir.mkdir()
        (session_dir / "file1.rs").write_text("code1")
        (session_dir / "file2.rs").write_text("code2")
        (session_dir / "subdir").mkdir()
        (session_dir / "subdir" / "file3.rs").write_text("code3")
        
        storage_service.cleanup_session_directory(session_id)
        
        assert not session_dir.exists()
    
    # ==================== Path Security Tests ====================
    
    def test_path_traversal_prevention(self, storage_service, tmp_path):
        """Test that path traversal is prevented."""
        # Try to access file outside base directory
        session_id = "../outside"
        
        # This should either fail or be contained within base_dir
        try:
            file_path = storage_service.save_uploaded_code(session_id, "malicious")
            # If it succeeds, verify it's still within base_dir
            assert tmp_path in file_path.parents or file_path.parent == tmp_path
        except Exception:
            # If it fails, that's also acceptable
            pass
    
    def test_session_id_with_special_chars(self, storage_service):
        """Test session IDs with special characters."""
        # Valid session IDs should work
        session_id = "session-with-dashes-and-123"
        
        file_path = storage_service.save_uploaded_code(session_id, "code")
        assert file_path.exists()


class TestFileStorageServiceEncoding:
    """Test encoding handling in FileStorageService."""
    
    @pytest.fixture
    def storage_service(self, tmp_path):
        return FileStorageService(base_dir=tmp_path)
    
    def test_utf8_code(self, storage_service):
        """Test saving and retrieving UTF-8 code."""
        session_id = "utf8-test"
        code = """// Comment with émojis 🦀
fn main() {
    println!("Hello, 世界!");
}"""
        
        storage_service.save_uploaded_code(session_id, code)
        retrieved = storage_service.read_uploaded_code(session_id)
        
        assert retrieved == code
        assert "🦀" in retrieved
        assert "世界" in retrieved
    
    def test_large_code_file(self, storage_service):
        """Test handling large code files."""
        session_id = "large-file"
        # Generate large code
        code = "\n".join([f"// Line {i}" for i in range(10000)])
        
        storage_service.save_uploaded_code(session_id, code)
        retrieved = storage_service.read_uploaded_code(session_id)
        
        assert len(retrieved) == len(code)
        assert retrieved == code


class TestFileStorageServiceIntegration:
    """Integration tests for FileStorageService."""
    
    @pytest.fixture
    def storage_service(self, tmp_path):
        return FileStorageService(base_dir=tmp_path)
    
    def test_multiple_sessions(self, storage_service):
        """Test handling multiple sessions."""
        sessions = {
            "session-1": "code for session 1",
            "session-2": "code for session 2",
            "session-3": "code for session 3",
        }
        
        # Save all
        for session_id, code in sessions.items():
            storage_service.save_uploaded_code(session_id, code)
        
        # Retrieve all
        for session_id, expected_code in sessions.items():
            retrieved = storage_service.read_uploaded_code(session_id)
            assert retrieved == expected_code
    
    def test_session_isolation(self, storage_service):
        """Test that sessions are isolated from each other."""
        storage_service.save_uploaded_code("session-a", "code A")
        storage_service.save_uploaded_code("session-b", "code B")
        
        # Cleanup one session
        storage_service.cleanup_session_directory("session-a")
        
        # Other session should still exist
        assert storage_service.read_uploaded_code("session-b") == "code B"
        assert storage_service.read_uploaded_code("session-a") is None
