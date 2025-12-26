"""DTO (Data Transfer Object) module."""
from .base import (
    BaseDTO,
    TimestampedDTO,
    SessionStatus,
    CodeBlockType,
)

# Export all DTOs for easy access
from .sessions import (
    SessionBase,
    CreateSessionInput,
    CreateSessionOutput,
    GetSessionOutput,
    UpdateSessionInput,
    SessionStatusResponse,
)

from .code_blocks import (
    CodeBlockBase,
)

from .analyses import (
    AnalysisBase,
    AnalysisDetail,
)

__all__ = [
    # Base
    "BaseDTO",
    "TimestampedDTO",
    "SessionStatus",
    "CodeBlockType",
    
    # Sessions
    "SessionBase",
    "CreateSessionInput",
    "CreateSessionOutput",
    "GetSessionOutput",
    "UpdateSessionInput",
    "SessionStatusResponse",
    
    # CodeBlocks
    "CodeBlockBase",
    
    # Analyses
    "AnalysisBase",
    "AnalysisDetail",
]
