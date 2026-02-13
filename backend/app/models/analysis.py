from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from app.database import Base

class CodeBlockType(PyEnum):
    REPLACEABLE = "replaceable"
    NON_REPLACEABLE = "non_replaceable"
    CONDITIONALLY_REPLACEABLE = "conditionally_replaceable"


class RiskLevel(PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Analysis(Base):
    """Analysis entity representing analysis results for a code block."""
    __tablename__ = "analyses"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    code_block_id = Column(String(36), ForeignKey("code_blocks.id"), nullable=False)
    
    # Analysis results
    code_block_type = Column(Enum(CodeBlockType), nullable=False)
    suggested_replacement = Column(Text, nullable=True)  # Safe replacement code
    
    # Enhanced LLM analysis fields
    cwe_id = Column(String(20), nullable=True)  # e.g., "CWE-787"
    owasp_category = Column(String(50), nullable=True)  # e.g., "A1: Injection"
    risk_level = Column(Enum(RiskLevel), nullable=True)
    confidence_score = Column(Float, nullable=True)  # 0.0-1.0
    
    # Detailed descriptions
    vulnerability_description = Column(Text, nullable=True)
    exploitation_scenario = Column(Text, nullable=True)
    remediation_explanation = Column(Text, nullable=True)
    
    # LLM metadata
    llm_metadata = Column(JSON, nullable=True)  # Raw LLM response, tokens used, etc.
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("Session", back_populates="analyses")
    code_block = relationship("CodeBlock", back_populates="analysis")
    
    def __repr__(self):
        return f"<Analysis(id={self.id}, type={self.code_block_type}, cwe={self.cwe_id}, risk={self.risk_level})>"
