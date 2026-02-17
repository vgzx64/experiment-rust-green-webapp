"""Create session input DTO."""
from pydantic import BaseModel, model_validator
from typing import Optional, List


class CreateSessionInput(BaseModel):
    """Input for POST /sessions."""
    orig_location: Optional[str] = None  # Git URL
    code: Optional[str] = None  # Raw code content
    git_ref: Optional[str] = None  # Branch/tag/commit (required if orig_location provided)
    selected_files: Optional[List[str]] = None  # Files to analyze from repo
    
    @model_validator(mode='after')
    def validate_input(self):
        if not self.orig_location and not self.code:
            raise ValueError('Either orig_location or code must be provided')
        if self.orig_location and not self.git_ref:
            raise ValueError('git_ref is required when orig_location is provided')
        return self
