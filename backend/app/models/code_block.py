from sqlalchemy import Column, String, Text, Integer, DateTime
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.database import Base

class CodeBlock(Base):
    """CodeBlock entity representing an unsafe code segment."""
    __tablename__ = "code_blocks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Code content
    raw_code = Column(Text, nullable=False)
    
    # Location information
    file_path = Column(Text, nullable=True)
    line_start = Column(Integer, nullable=False)
    line_end = Column(Integer, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    analysis = relationship("Analysis", back_populates="code_block", uselist=False)
    
    def __repr__(self):
        return f"<CodeBlock(id={self.id}, lines={self.line_start}-{self.line_end})>"
