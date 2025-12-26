"""Analysis base DTO."""
from ..base import BaseDTO, CodeBlockType
from ..code_blocks.code_block_base import CodeBlockBase
from typing import Optional

class AnalysisBase(BaseDTO):
    """Analysis DTO."""
    session_id: str
    code_block_id: str
    code_block_type: CodeBlockType
    suggested_replacement: Optional[CodeBlockBase] = None  # CodeBlock DTO, not string
