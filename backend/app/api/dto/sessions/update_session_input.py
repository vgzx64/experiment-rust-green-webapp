"""Update session input DTO."""
from pydantic import BaseModel
from typing import Optional
from ..base import SessionStatus

class UpdateSessionInput(BaseModel):
    """Input for PATCH /sessions/{id}."""
    status: Optional[SessionStatus] = None
    progress: Optional[int] = None
    error_message: Optional[str] = None
