"""DTO for Git refs (branches and tags) output."""
from typing import List, Optional
from pydantic import BaseModel


class GitRefsOutput(BaseModel):
    """Output for GET /repos/refs endpoint."""
    branches: List[str]
    tags: List[str]
    default_branch: Optional[str] = None