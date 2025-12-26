"""Session status response DTO."""
from pydantic import BaseModel
from ..base import SessionStatus

class SessionStatusResponse(BaseModel):
    """Response for GET /sessions/{id}/status."""
    session_id: str
    status: SessionStatus
    progress: int
