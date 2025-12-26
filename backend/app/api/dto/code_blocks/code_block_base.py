"""CodeBlock base DTO."""
from ..base import BaseDTO
from typing import Optional

class CodeBlockBase(BaseDTO):
    """CodeBlock DTO."""
    raw_code: str
    line_start: int
    line_end: int
    file_path: Optional[str] = None
