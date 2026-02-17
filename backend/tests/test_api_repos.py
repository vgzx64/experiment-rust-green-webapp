"""Tests for Repos API endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app


class TestReposAPI:
    """Test cases for Repos API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    # ==================== GET /repos/refs Tests ====================
    
    def test_get_refs_success(self, client):
        """Test getting refs from a repository."""
        with patch('app.api.v1.repos.git_service') as mock_git:
            mock_git.get_refs = AsyncMock(return_value={
                "branches": ["main", "develop"],
                "tags": ["v1.0.0", "v2.0.0"],
                "default_branch": "main"
            })
            
            response = client.get("/api/v1/repos/refs?git_url=https://github.com/user/repo")
            
            assert response.status_code == 200
            data = response.json()
            assert "branches" in data
            assert "tags" in data
            assert "main" in data["branches"]
    
    def test_get_refs_missing_url(self, client):
        """Test getting refs without URL parameter."""
        response = client.get("/api/v1/repos/refs")
        
        assert response.status_code == 422  # Validation error
    
    def test_get_refs_git_error(self, client):
        """Test getting refs with Git error."""
        from app.services.git_service import GitServiceError
        
        with patch('app.api.v1.repos.git_service') as mock_git:
            mock_git.get_refs = AsyncMock(
                side_effect=GitServiceError("Repository not found")
            )
            
            response = client.get("/api/v1/repos/refs?git_url=https://github.com/user/nonexistent")
            
            assert response.status_code == 400
    
    def test_get_refs_empty_repo(self, client):
        """Test getting refs from empty repository."""
        with patch('app.api.v1.repos.git_service') as mock_git:
            mock_git.get_refs = AsyncMock(return_value={
                "branches": [],
                "tags": [],
                "default_branch": None
            })
            
            response = client.get("/api/v1/repos/refs?git_url=https://github.com/user/empty")
            
            assert response.status_code == 200
            data = response.json()
            assert data["branches"] == []
            assert data["tags"] == []
    
    # ==================== GET /repos/tree Tests ====================
    
    def test_get_tree_success(self, client):
        """Test getting file tree from a repository."""
        with patch('app.api.v1.repos.git_service') as mock_git:
            mock_git.shallow_clone = AsyncMock()
            mock_git.list_rust_files = AsyncMock(return_value=[
                "src/main.rs",
                "src/lib.rs"
            ])
            
            response = client.get(
                "/api/v1/repos/tree?git_url=https://github.com/user/repo&git_ref=main"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "files" in data
    
    def test_get_tree_missing_url(self, client):
        """Test getting tree without URL parameter."""
        response = client.get("/api/v1/repos/tree?git_ref=main")
        
        assert response.status_code == 422  # Validation error
    
    def test_get_tree_missing_ref(self, client):
        """Test getting tree without ref parameter."""
        response = client.get("/api/v1/repos/tree?git_url=https://github.com/user/repo")
        
        assert response.status_code == 422  # Validation error
    
    def test_get_tree_git_error(self, client):
        """Test getting tree with Git error."""
        from app.services.git_service import GitServiceError
        
        with patch('app.api.v1.repos.git_service') as mock_git:
            mock_git.shallow_clone = AsyncMock(
                side_effect=GitServiceError("Clone failed")
            )
            
            response = client.get(
                "/api/v1/repos/tree?git_url=https://github.com/user/repo&git_ref=main"
            )
            
            assert response.status_code == 400
    
    def test_get_tree_rust_files_only(self, client):
        """Test getting tree returns Rust files."""
        with patch('app.api.v1.repos.git_service') as mock_git:
            mock_git.shallow_clone = AsyncMock()
            mock_git.list_rust_files = AsyncMock(return_value=[
                "src/main.rs",
                "src/lib.rs"
            ])
            
            response = client.get(
                "/api/v1/repos/tree?git_url=https://github.com/user/repo&git_ref=main"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert all(f.endswith('.rs') for f in data["files"])


class TestReposAPIEdgeCases:
    """Test edge cases for Repos API."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_get_refs_with_special_characters_in_url(self, client):
        """Test getting refs with URL-encoded special characters."""
        with patch('app.api.v1.repos.git_service') as mock_git:
            mock_git.get_refs = AsyncMock(return_value={
                "branches": ["main"],
                "tags": [],
                "default_branch": "main"
            })
            
            # URL with special characters
            response = client.get(
                "/api/v1/repos/refs?git_url=https%3A%2F%2Fgithub.com%2Fuser%2Frepo"
            )
            
            assert response.status_code == 200
    
    def test_get_tree_large_repository(self, client):
        """Test getting tree from large repository."""
        with patch('app.api.v1.repos.git_service') as mock_git:
            # Simulate large repo with many files
            many_files = [f"src/file_{i}.rs" for i in range(1000)]
            
            mock_git.shallow_clone = AsyncMock()
            mock_git.list_rust_files = AsyncMock(return_value=many_files)
            
            response = client.get(
                "/api/v1/repos/tree?git_url=https://github.com/user/large-repo&git_ref=main"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["files"]) == 1000
    
    def test_get_refs_timeout(self, client):
        """Test handling timeout when getting refs."""
        from app.services.git_service import GitServiceError
        
        with patch('app.api.v1.repos.git_service') as mock_git:
            mock_git.get_refs = AsyncMock(
                side_effect=GitServiceError("Git command timed out")
            )
            
            response = client.get(
                "/api/v1/repos/refs?git_url=https://github.com/user/slow-repo"
            )
            
            assert response.status_code == 400


class TestReposAPIValidation:
    """Test input validation for Repos API."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_invalid_url_format(self, client):
        """Test with invalid URL format."""
        with patch('app.api.v1.repos.git_service') as mock_git:
            from app.services.git_service import GitServiceError
            
            mock_git.get_refs = AsyncMock(
                side_effect=GitServiceError("Invalid URL")
            )
            
            response = client.get("/api/v1/repos/refs?git_url=not-a-valid-url")
            
            assert response.status_code == 400
    
    def test_private_repo_without_auth(self, client):
        """Test accessing private repository without authentication."""
        from app.services.git_service import GitServiceError
        
        with patch('app.api.v1.repos.git_service') as mock_git:
            mock_git.get_refs = AsyncMock(
                side_effect=GitServiceError("Authentication failed")
            )
            
            response = client.get(
                "/api/v1/repos/refs?git_url=https://github.com/user/private-repo"
            )
            
            assert response.status_code == 400
