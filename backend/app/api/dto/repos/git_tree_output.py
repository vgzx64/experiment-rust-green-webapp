"""DTO for Git tree (file list) output."""
from typing import List
from pydantic import BaseModel


class GitTreeOutput(BaseModel):
    """Output for GET /repos/tree endpoint."""
    files: List[str]  # List of .rs file paths
    git_ref: str
    total_files: int