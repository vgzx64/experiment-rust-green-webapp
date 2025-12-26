from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from app.database import Base

class CodeBlockType(PyEnum):
    REPLACEABLE = "replaceable"
    NON_REPLACEABLE = "non_replaceable"
    CONDITIONALLY_REPLACEABLE = "conditionally_replaceable"

class Analysis(Base):
    """Analysis entity representing analysis results for a code block."""
    __tablename__ = "analyses"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    code_block_id = Column(String(36), ForeignKey("code_blocks.id"), nullable=False)
    
    # Analysis results
    code_block_type = Column(Enum(CodeBlockType), nullable=False)
    suggested_replacement = Column(Text, nullable=True)  # Safe replacement code
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("Session", back_populates="analyses")
    code_block = relationship("CodeBlock", back_populates="analysis")
    
    def __repr__(self):
        return f"<Analysis(id={self.id}, type={self.code_block_type})>"
