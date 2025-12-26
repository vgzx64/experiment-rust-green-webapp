"""Base DTO classes and shared types."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum

class BaseDTO(BaseModel):
    """Base DTO with common fields."""
    id: str
    created_at: datetime

class TimestampedDTO(BaseDTO):
    """DTO with update timestamp."""
    updated_at: datetime

class SessionStatus(str, Enum):
    """Session status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class CodeBlockType(str, Enum):
    """Code block type enumeration."""
    REPLACEABLE = "replaceable"
    NON_REPLACEABLE = "non_replaceable"
    CONDITIONALLY_REPLACEABLE = "conditionally_replaceable"
