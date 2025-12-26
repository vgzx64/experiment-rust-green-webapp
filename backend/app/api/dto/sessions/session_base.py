"""Session base DTO."""
from ..base import TimestampedDTO, SessionStatus
from datetime import datetime
from typing import Optional

class SessionBase(TimestampedDTO):
    """Session DTO."""
    status: SessionStatus
    progress: int
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
