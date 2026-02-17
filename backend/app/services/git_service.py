"""Git service for repository operations using async subprocess."""
import asyncio
import logging
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class GitServiceError(Exception):
    """Exception raised for Git operation errors."""
    pass


class GitService:
    """Service for Git repository operations using async subprocess calls."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize Git service with base directory for cloning.
        
        Args:
            base_dir: Base directory for cloned repositories. 
                     Defaults to /home/dev/Code/rust-green-webapp/sessions
        """
        if base_dir is None:
            self.base_dir = Path("/home/dev/Code/rust-green-webapp/sessions")
        else:
            self.base_dir = Path(base_dir)
        
        # Ensure base directory exists
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    async def _run_git_command(
        self, 
        args: List[str], 
        cwd: Optional[Path] = None,
        timeout: int = 300  # 5 minutes default timeout
    ) -> tuple[str, str]:
        """Execute a git command asynchronously.
        
        Args:
            args: Git command arguments (e.g., ['clone', '--depth', '1', ...])
            cwd: Working directory for the command
            timeout: Timeout in seconds
            
        Returns:
            Tuple of (stdout, stderr)
            
        Raises:
            GitServiceError: If command fails or times out
        """
        try:
            process = await asyncio.create_subprocess_exec(
                "git", *args,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=timeout
            )
            
            stdout_str = stdout.decode('utf-8', errors='replace').strip()
            stderr_str = stderr.decode('utf-8', errors='replace').strip()
            
            if process.returncode != 0:
                error_msg = stderr_str or stdout_str or "Unknown git error"
                logger.error(f"Git command failed: git {' '.join(args)}")
                logger.error(f"Error: {error_msg}")
                raise GitServiceError(f"Git command failed: {error_msg}")
            
            return stdout_str, stderr_str
            
        except asyncio.TimeoutError:
            logger.error(f"Git command timed out after {timeout}s")
            raise GitServiceError(f"Git command timed out after {timeout}s")
        except FileNotFoundError:
            logger.error("Git executable not found")
            raise GitServiceError("Git executable not found. Please install git.")
    
    async def get_refs(self, git_url: str) -> Dict[str, Any]:
        """Get branches and tags from a remote repository without cloning.
        
        Uses 'git ls-remote' which is fast and doesn't require cloning.
        
        Args:
            git_url: Git repository URL
            
        Returns:
            Dict with 'branches', 'tags', and 'default_branch' keys
        """
        logger.info(f"Fetching refs for: {git_url}")
        
        stdout, _ = await self._run_git_command(
            ["ls-remote", "--heads", "--tags", git_url],
            timeout=60  # 1 minute for ls-remote
        )
        
        branches = []
        tags = []
        default_branch = None
        
        for line in stdout.split('\n'):
            if not line.strip():
                continue
            
            # Parse line: "<commit_hash>\t<ref_path>"
            parts = line.split('\t')
            if len(parts) != 2:
                continue
            
            commit_hash, ref = parts
            
            if ref.startswith('refs/heads/'):
                branch_name = ref.replace('refs/heads/', '')
                branches.append(branch_name)
                
                # Detect default branch (main, master, or develop)
                if branch_name in ('main', 'master'):
                    default_branch = branch_name
                elif default_branch is None and branch_name == 'develop':
                    default_branch = branch_name
                    
            elif ref.startswith('refs/tags/'):
                tag_name = ref.replace('refs/tags/', '')
                # Skip annotated tag references (^{})
                if not tag_name.endswith('^{}'):
                    tags.append(tag_name)
        
        # Sort branches and tags
        branches.sort()
        tags.sort(reverse=True)  # Most recent tags first
        
        # Fallback default branch
        if default_branch is None and branches:
            default_branch = branches[0]
        
        logger.info(f"Found {len(branches)} branches, {len(tags)} tags")
        
        return {
            "branches": branches,
            "tags": tags,
            "default_branch": default_branch
        }
    
    async def shallow_clone(
        self, 
        git_url: str, 
        target_dir: Path, 
        git_ref: str
    ) -> Path:
        """Clone a repository with minimal history (shallow clone).
        
        Uses --depth 1 --single-branch for fastest possible clone.
        
        Args:
            git_url: Git repository URL
            target_dir: Directory to clone into
            git_ref: Branch, tag, or commit hash to checkout
            
        Returns:
            Path to cloned repository
            
        Raises:
            GitServiceError: If clone fails
        """
        logger.info(f"Shallow cloning {git_url} (ref: {git_ref}) to {target_dir}")
        
        # Ensure parent directory exists
        target_dir.parent.mkdir(parents=True, exist_ok=True)
        
        # Try shallow clone with branch/tag
        try:
            await self._run_git_command([
                "clone",
                "--depth", "1",
                "--single-branch",
                "--branch", git_ref,
                git_url,
                str(target_dir)
            ], timeout=300)  # 5 minutes for clone
            logger.info(f"Successfully cloned repository to {target_dir}")
            return target_dir
            
        except GitServiceError as e:
            # If ref is a commit hash, shallow clone won't work directly
            # We need to clone first, then fetch and checkout
            if self._is_commit_hash(git_ref):
                logger.info(f"Ref appears to be commit hash, trying alternate approach")
                return await self._clone_and_checkout_commit(git_url, target_dir, git_ref)
            raise
    
    async def _clone_and_checkout_commit(
        self, 
        git_url: str, 
        target_dir: Path, 
        commit_hash: str
    ) -> Path:
        """Clone repository and checkout a specific commit.
        
        Used when git_ref is a commit hash (shallow clone doesn't support direct commit checkout).
        
        Args:
            git_url: Git repository URL
            target_dir: Directory to clone into
            commit_hash: Commit hash to checkout
            
        Returns:
            Path to cloned repository
        """
        # Shallow clone with depth 1 (will fetch default branch)
        await self._run_git_command([
            "clone",
            "--depth", "1",
            git_url,
            str(target_dir)
        ], timeout=300)
        
        # Fetch the specific commit
        await self._run_git_command([
            "fetch", "--depth", "1", "origin", commit_hash
        ], cwd=target_dir, timeout=120)
        
        # Checkout the commit
        await self._run_git_command([
            "checkout", commit_hash
        ], cwd=target_dir, timeout=30)
        
        logger.info(f"Successfully checked out commit {commit_hash}")
        return target_dir
    
    def _is_commit_hash(self, ref: str) -> bool:
        """Check if a ref looks like a commit hash.
        
        Args:
            ref: Git reference string
            
        Returns:
            True if ref appears to be a commit hash
        """
        # Commit hashes are 40-char hex strings (full) or 7+ char (short)
        return bool(re.match(r'^[0-9a-fA-F]{7,40}$', ref))
    
    async def list_rust_files(self, repo_path: Path) -> List[str]:
        """List all Rust (.rs) files in a repository.
        
        Args:
            repo_path: Path to cloned repository
            
        Returns:
            List of relative file paths
        """
        logger.info(f"Listing Rust files in {repo_path}")
        
        stdout, _ = await self._run_git_command(
            ["ls-files", "*.rs"],
            cwd=repo_path,
            timeout=30
        )
        
        files = [f for f in stdout.split('\n') if f.strip()]
        logger.info(f"Found {len(files)} Rust files")
        
        return files
    
    async def list_all_files(self, repo_path: Path) -> List[str]:
        """List all tracked files in a repository.
        
        Args:
            repo_path: Path to cloned repository
            
        Returns:
            List of relative file paths
        """
        stdout, _ = await self._run_git_command(
            ["ls-files"],
            cwd=repo_path,
            timeout=30
        )
        
        return [f for f in stdout.split('\n') if f.strip()]
    
    def read_file(self, repo_path: Path, file_path: str) -> str:
        """Read a file from the repository.
        
        Args:
            repo_path: Path to cloned repository
            file_path: Relative path to file
            
        Returns:
            File content as string
        """
        full_path = repo_path / file_path
        
        if not full_path.exists():
            raise GitServiceError(f"File not found: {file_path}")
        
        # Security check: ensure file is within repo
        try:
            full_path.resolve().relative_to(repo_path.resolve())
        except ValueError:
            raise GitServiceError(f"File path outside repository: {file_path}")
        
        return full_path.read_text(encoding='utf-8', errors='replace')
    
    def read_files(self, repo_path: Path, file_paths: List[str]) -> Dict[str, str]:
        """Read multiple files from the repository.
        
        Args:
            repo_path: Path to cloned repository
            file_paths: List of relative file paths
            
        Returns:
            Dict mapping file paths to their contents
        """
        contents = {}
        
        for file_path in file_paths:
            try:
                contents[file_path] = self.read_file(repo_path, file_path)
            except GitServiceError as e:
                logger.warning(f"Failed to read {file_path}: {e}")
                # Continue with other files
        
        return contents
    
    def cleanup_repo(self, repo_path: Path) -> None:
        """Remove a cloned repository directory.
        
        Args:
            repo_path: Path to repository to remove
        """
        if repo_path.exists():
            logger.info(f"Cleaning up repository: {repo_path}")
            shutil.rmtree(repo_path)
    
    def get_repo_path(self, session_id: str) -> Path:
        """Get the path where a session's repository should be cloned.
        
        Args:
            session_id: Session ID
            
        Returns:
            Path to repository directory
        """
        return self.base_dir / session_id / "repo"


# Global Git service instance
git_service = GitService()