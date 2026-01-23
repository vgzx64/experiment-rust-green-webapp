"""Session list output DTO."""
from ..base import TimestampedDTO, SessionStatus
from datetime import datetime
from typing import Optional

class SessionListOutput(TimestampedDTO):
    """Output for GET /sessions (list of sessions)."""
    status: SessionStatus
    progress: int
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    # Add analysis count for quick overview
    analysis_count: int = 0
