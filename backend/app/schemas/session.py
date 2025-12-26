from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class SessionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class CodeBlockType(str, Enum):
    REPLACEABLE = "replaceable"
    NON_REPLACEABLE = "non_replaceable"
    CONDITIONALLY_REPLACEABLE = "conditionally_replaceable"

# Request schemas (to be updated when API endpoints are updated)
class SessionCreate(BaseModel):
    code: str = Field(..., description="Rust source code to analyze")

class SessionUpdate(BaseModel):
    status: Optional[SessionStatus] = None
    error_message: Optional[str] = None

# Response schemas (to be updated when API endpoints are updated)
class SessionBase(BaseModel):
    id: str
    status: SessionStatus
    progress: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

class SessionSimple(SessionBase):
    """Simple session response without code."""
    pass

class SessionDetail(SessionBase):
    """Detailed session response with code and analysis."""
    code: str
    error_message: Optional[str] = None
    # TODO: Update to match new Analysis model when APIs are updated
    code_blocks: List[Any] = []

class SessionStatusResponse(BaseModel):
    """Response for status check endpoint."""
    session_id: str
    status: SessionStatus

# Basic schemas matching new models (for internal use)
class CodeBlockSchema(BaseModel):
    id: str
    raw_code: str
    line_start: int
    line_end: int
    file_path: Optional[str] = None
    created_at: datetime

class AnalysisSchema(BaseModel):
    id: str
    session_id: str
    code_block_id: str
    code_block_type: CodeBlockType
    suggested_replacement: Optional[str] = None
    created_at: datetime
