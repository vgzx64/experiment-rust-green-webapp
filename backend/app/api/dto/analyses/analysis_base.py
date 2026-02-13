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
    
    # Enhanced LLM analysis fields
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None
    risk_level: Optional[str] = None  # "low", "medium", "high", "critical"
    confidence_score: Optional[float] = None
    
    # Detailed descriptions
    vulnerability_description: Optional[str] = None
    exploitation_scenario: Optional[str] = None
    remediation_explanation: Optional[str] = None
    
    # LLM metadata
    llm_metadata: Optional[dict] = None
