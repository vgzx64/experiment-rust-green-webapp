"""Tests for GitService."""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from app.services.git_service import GitService, GitServiceError


class TestGitService:
    """Test cases for GitService."""
    
    @pytest.fixture
    def git_service(self, tmp_path):
        """Create GitService with temporary directory."""
        return GitService(base_dir=tmp_path)
    
    @pytest.fixture
    def mock_subprocess(self):
        """Mock asyncio.create_subprocess_exec."""
        with patch('asyncio.create_subprocess_exec') as mock:
            yield mock
    
    def _create_mock_process(self, stdout="", stderr="", returncode=0):
        """Create a mock subprocess process."""
        process = MagicMock()
        process.communicate = AsyncMock(return_value=(
            stdout.encode('utf-8'),
            stderr.encode('utf-8')
        ))
        process.returncode = returncode
        return process
    
    # ==================== get_refs Tests ====================
    
    @pytest.mark.asyncio
    async def test_get_refs_success(self, git_service, mock_subprocess):
        """Test getting refs from a repository."""
        stdout = """abc123\trefs/heads/main
def456\trefs/heads/develop
ghi789\trefs/tags/v1.0.0
jkl012\trefs/tags/v2.0.0"""
        
        mock_subprocess.return_value = self._create_mock_process(stdout=stdout)
        
        result = await git_service.get_refs("https://github.com/user/repo")
        
        assert "branches" in result
        assert "tags" in result
        assert "main" in result["branches"]
        assert "develop" in result["branches"]
        assert "v1.0.0" in result["tags"]
        assert "v2.0.0" in result["tags"]
        assert result["default_branch"] == "main"
    
    @pytest.mark.asyncio
    async def test_get_refs_master_default(self, git_service, mock_subprocess):
        """Test that master is detected as default branch."""
        stdout = """abc123\trefs/heads/master
def456\trefs/heads/feature"""
        
        mock_subprocess.return_value = self._create_mock_process(stdout=stdout)
        
        result = await git_service.get_refs("https://github.com/user/repo")
        
        assert result["default_branch"] == "master"
    
    @pytest.mark.asyncio
    async def test_get_refs_empty_repo(self, git_service, mock_subprocess):
        """Test getting refs from empty repository."""
        mock_subprocess.return_value = self._create_mock_process(stdout="")
        
        result = await git_service.get_refs("https://github.com/user/empty")
        
        assert result["branches"] == []
        assert result["tags"] == []
        assert result["default_branch"] is None
    
    @pytest.mark.asyncio
    async def test_get_refs_git_error(self, git_service, mock_subprocess):
        """Test handling git errors."""
        mock_subprocess.return_value = self._create_mock_process(
            stderr="Repository not found",
            returncode=128
        )
        
        with pytest.raises(GitServiceError):
            await git_service.get_refs("https://github.com/user/nonexistent")
    
    # ==================== shallow_clone Tests ====================
    
    @pytest.mark.asyncio
    async def test_shallow_clone_success(self, git_service, mock_subprocess, tmp_path):
        """Test successful shallow clone."""
        mock_subprocess.return_value = self._create_mock_process()
        
        target_dir = tmp_path / "test-repo"
        result = await git_service.shallow_clone(
            "https://github.com/user/repo",
            target_dir,
            "main"
        )
        
        assert result == target_dir
    
    @pytest.mark.asyncio
    async def test_shallow_clone_creates_parent_dir(self, git_service, mock_subprocess, tmp_path):
        """Test that clone creates parent directories."""
        mock_subprocess.return_value = self._create_mock_process()
        
        target_dir = tmp_path / "nested" / "path" / "repo"
        result = await git_service.shallow_clone(
            "https://github.com/user/repo",
            target_dir,
            "main"
        )
        
        assert result == target_dir
    
    @pytest.mark.asyncio
    async def test_shallow_clone_failure(self, git_service, mock_subprocess, tmp_path):
        """Test handling clone failure."""
        mock_subprocess.return_value = self._create_mock_process(
            stderr="Authentication failed",
            returncode=128
        )
        
        target_dir = tmp_path / "test-repo"
        
        with pytest.raises(GitServiceError):
            await git_service.shallow_clone(
                "https://github.com/user/private",
                target_dir,
                "main"
            )
    
    # ==================== list_rust_files Tests ====================
    
    @pytest.mark.asyncio
    async def test_list_rust_files(self, git_service, mock_subprocess, tmp_path):
        """Test listing Rust files."""
        stdout = """src/main.rs
src/lib.rs
src/utils.rs"""
        
        mock_subprocess.return_value = self._create_mock_process(stdout=stdout)
        
        result = await git_service.list_rust_files(tmp_path / "repo")
        
        assert len(result) == 3
        assert "src/main.rs" in result
        assert "src/lib.rs" in result
    
    @pytest.mark.asyncio
    async def test_list_rust_files_empty(self, git_service, mock_subprocess, tmp_path):
        """Test listing Rust files in empty repo."""
        mock_subprocess.return_value = self._create_mock_process(stdout="")
        
        result = await git_service.list_rust_files(tmp_path / "repo")
        
        assert result == []
    
    # ==================== read_file Tests ====================
    
    def test_read_file_success(self, git_service, tmp_path):
        """Test reading a file from repository."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        
        file_path = repo_path / "src" / "main.rs"
        file_path.parent.mkdir(parents=True)
        file_path.write_text("fn main() {}")
        
        content = git_service.read_file(repo_path, "src/main.rs")
        
        assert content == "fn main() {}"
    
    def test_read_file_not_found(self, git_service, tmp_path):
        """Test reading non-existent file."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        
        with pytest.raises(GitServiceError, match="File not found"):
            git_service.read_file(repo_path, "nonexistent.rs")
    
    def test_read_file_path_traversal(self, git_service, tmp_path):
        """Test path traversal security."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        
        # Create a file outside the repo
        outside_file = tmp_path / "secret.txt"
        outside_file.write_text("secret")
        
        with pytest.raises(GitServiceError, match="outside repository"):
            git_service.read_file(repo_path, "../secret.txt")
    
    # ==================== read_files Tests ====================
    
    def test_read_files_multiple(self, git_service, tmp_path):
        """Test reading multiple files."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        
        # Create files
        (repo_path / "main.rs").write_text("fn main() {}")
        (repo_path / "lib.rs").write_text("fn lib() {}")
        
        result = git_service.read_files(repo_path, ["main.rs", "lib.rs"])
        
        assert len(result) == 2
        assert result["main.rs"] == "fn main() {}"
        assert result["lib.rs"] == "fn lib() {}"
    
    def test_read_files_partial_failure(self, git_service, tmp_path):
        """Test reading files with some missing."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        
        (repo_path / "main.rs").write_text("fn main() {}")
        
        result = git_service.read_files(repo_path, ["main.rs", "missing.rs"])
        
        assert len(result) == 1
        assert "main.rs" in result
        assert "missing.rs" not in result
    
    # ==================== _is_commit_hash Tests ====================
    
    def test_is_commit_hash_full(self, git_service):
        """Test detecting full commit hash."""
        assert git_service._is_commit_hash("abc123def456789012345678901234567890abcd") is True
    
    def test_is_commit_hash_short(self, git_service):
        """Test detecting short commit hash."""
        assert git_service._is_commit_hash("abc1234") is True
        assert git_service._is_commit_hash("abcdef12") is True
    
    def test_is_commit_hash_branch_name(self, git_service):
        """Test that branch names are not commit hashes."""
        assert git_service._is_commit_hash("main") is False
        assert git_service._is_commit_hash("feature/branch") is False
    
    def test_is_commit_hash_tag(self, git_service):
        """Test that tags are not commit hashes."""
        assert git_service._is_commit_hash("v1.0.0") is False
    
    # ==================== get_repo_path Tests ====================
    
    def test_get_repo_path(self, git_service, tmp_path):
        """Test getting repository path for session."""
        result = git_service.get_repo_path("session-123")
        
        assert "session-123" in str(result)
        assert "repo" in str(result)
    
    # ==================== cleanup_repo Tests ====================
    
    def test_cleanup_repo_existing(self, git_service, tmp_path):
        """Test cleaning up existing repository."""
        repo_path = tmp_path / "test-repo"
        repo_path.mkdir()
        (repo_path / "main.rs").write_text("fn main() {}")
        
        git_service.cleanup_repo(repo_path)
        
        assert not repo_path.exists()
    
    def test_cleanup_repo_nonexistent(self, git_service, tmp_path):
        """Test cleaning up non-existent repository (no error)."""
        repo_path = tmp_path / "nonexistent"
        
        # Should not raise error
        git_service.cleanup_repo(repo_path)


class TestGitServiceTimeout:
    """Test timeout handling in GitService."""
    
    @pytest.fixture
    def git_service(self, tmp_path):
        """Create GitService with temporary directory."""
        return GitService(base_dir=tmp_path)
    
    @pytest.mark.asyncio
    async def test_command_timeout(self, git_service):
        """Test handling command timeout."""
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            process = MagicMock()
            process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
            mock_subprocess.return_value = process
            
            with pytest.raises(GitServiceError, match="timed out"):
                await git_service.get_refs("https://github.com/user/repo")
    
    @pytest.mark.asyncio
    async def test_git_not_found(self, git_service):
        """Test handling git not installed."""
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_subprocess.side_effect = FileNotFoundError()
            
            with pytest.raises(GitServiceError, match="Git executable not found"):
                await git_service.get_refs("https://github.com/user/repo")


class TestGitServiceEdgeCases:
    """Test edge cases in GitService."""
    
    @pytest.fixture
    def git_service(self, tmp_path):
        """Create GitService with temporary directory."""
        return GitService(base_dir=tmp_path)
    
    @pytest.mark.asyncio
    async def test_get_refs_with_annotated_tags(self, git_service):
        """Test that annotated tag references are filtered."""
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            stdout = """abc123\trefs/heads/main
def456\trefs/tags/v1.0.0
def456\trefs/tags/v1.0.0^{}"""
            
            process = MagicMock()
            process.communicate = AsyncMock(return_value=(
                stdout.encode('utf-8'),
                b""
            ))
            process.returncode = 0
            mock_subprocess.return_value = process
            
            result = await git_service.get_refs("https://github.com/user/repo")
            
            # Should only have one v1.0.0 entry (not the ^{} reference)
            assert result["tags"].count("v1.0.0") == 1
    
    @pytest.mark.asyncio
    async def test_get_refs_sorted_output(self, git_service):
        """Test that branches and tags are sorted."""
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            stdout = """c\trefs/heads/z-branch
a\trefs/heads/a-branch
b\trefs/heads/m-branch
z\trefs/tags/v3.0.0
x\trefs/tags/v1.0.0
y\trefs/tags/v2.0.0"""
            
            process = MagicMock()
            process.communicate = AsyncMock(return_value=(
                stdout.encode('utf-8'),
                b""
            ))
            process.returncode = 0
            mock_subprocess.return_value = process
            
            result = await git_service.get_refs("https://github.com/user/repo")
            
            # Branches should be sorted alphabetically
            assert result["branches"] == ["a-branch", "m-branch", "z-branch"]
            
            # Tags should be sorted in reverse (most recent first)
            assert result["tags"] == ["v3.0.0", "v2.0.0", "v1.0.0"]
    
    def test_read_file_utf8_handling(self, git_service, tmp_path):
        """Test UTF-8 file reading with error handling."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        
        # Create file with UTF-8 content
        file_path = repo_path / "main.rs"
        file_path.write_text("// Comment with émojis 🦀", encoding='utf-8')
        
        content = git_service.read_file(repo_path, "main.rs")
        
        assert "🦀" in content