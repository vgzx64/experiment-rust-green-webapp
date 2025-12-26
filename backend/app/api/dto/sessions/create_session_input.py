"""Create session input DTO."""
from pydantic import BaseModel, model_validator
from typing import Optional

class CreateSessionInput(BaseModel):
    """Input for POST /sessions."""
    orig_location: Optional[str] = None  # Git URL
    code: Optional[str] = None  # Raw code content
    
    @model_validator(mode='after')
    def validate_at_least_one_provided(self):
        if not self.orig_location and not self.code:
            raise ValueError('Either orig_location or code must be provided')
        return self
