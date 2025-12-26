"""Analysis detail DTO."""
from .analysis_base import AnalysisBase
from ..code_blocks.code_block_base import CodeBlockBase

class AnalysisDetail(AnalysisBase):
    """Analysis with full code block details."""
    code_block: CodeBlockBase  # Full code block, not just ID
