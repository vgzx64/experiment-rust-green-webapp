"""API endpoints for Git repository operations."""
from fastapi import APIRouter, HTTPException, status, Query
import logging
import tempfile
import shutil
from pathlib import Path

from app.api.dto.repos import GitRefsOutput, GitTreeOutput
from app.services.git_service import git_service, GitServiceError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/repos/refs",
    response_model=GitRefsOutput,
    summary="Get repository branches and tags",
    description="""Get all branches and tags from a Git repository without cloning.
    
## Use Case
Use this endpoint to let users browse available branches and tags before selecting
which version of the code to analyze.

## Parameters
- `git_url`: Git repository URL (e.g., https://github.com/user/repo)

## Response
Returns lists of branches and tags, plus the detected default branch.

## Notes
- Uses `git ls-remote` - no cloning required, fast operation
- Supports GitHub, GitLab, Bitbucket, and any public Git repository
- Private repositories require authentication in the URL
"""
)
async def get_git_refs(
    git_url: str = Query(..., description="Git repository URL")
):
    """Get branches and tags from a remote Git repository."""
    try:
        refs = await git_service.get_refs(git_url)
        return GitRefsOutput(
            branches=refs["branches"],
            tags=refs["tags"],
            default_branch=refs["default_branch"]
        )
    except GitServiceError as e:
        logger.error(f"Failed to get refs for {git_url}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to access repository: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error getting refs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


@router.get(
    "/repos/tree",
    response_model=GitTreeOutput,
    summary="Get repository file tree",
    description="""List Rust files in a repository at a specific branch/tag/commit.

## Use Case
Use this endpoint to let users select which Rust files to analyze after choosing
a branch/tag/commit.

## Parameters
- `git_url`: Git repository URL
- `git_ref`: Branch name, tag, or commit hash

## Response
Returns list of `.rs` file paths in the repository.

## Notes
- Uses shallow clone (`--depth 1`) for efficiency
- Only returns `.rs` files (Rust source files)
- The clone is temporary and cleaned up after the request
"""
)
async def get_git_tree(
    git_url: str = Query(..., description="Git repository URL"),
    git_ref: str = Query(..., description="Branch, tag, or commit hash")
):
    """List Rust files in a repository at a specific ref."""
    temp_dir = None
    
    try:
        # Create temporary directory for clone
        temp_dir = tempfile.mkdtemp(prefix="rust_green_repo_")
        repo_path = Path(temp_dir) / "repo"
        
        # Shallow clone the repository
        await git_service.shallow_clone(git_url, repo_path, git_ref)
        
        # List Rust files
        files = await git_service.list_rust_files(repo_path)
        
        return GitTreeOutput(
            files=files,
            git_ref=git_ref,
            total_files=len(files)
        )
        
    except GitServiceError as e:
        logger.error(f"Failed to get tree for {git_url} at {git_ref}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to access repository: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error getting tree: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
    finally:
        # Cleanup temporary directory
        if temp_dir:
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp dir: {e}")
