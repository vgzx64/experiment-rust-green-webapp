from sqlalchemy import Column, String, DateTime, Enum as SQLAEnum, Text, Integer
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from app.database import Base

class SessionStatus(PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Session(Base):
    """Session entity representing a code analysis request."""
    __tablename__ = "sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    orig_location = Column(Text, nullable=True)  # Git URL or None for file submission
    status = Column(SQLAEnum(SessionStatus, values_callable=lambda obj: [e.value for e in obj]), default=SessionStatus.PENDING)
    progress = Column(Integer, default=0)  # 0-100 percentage
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Metadata
    error_message = Column(Text, nullable=True)
    
    # Relationships
    analyses = relationship("Analysis", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Session(id={self.id}, status={self.status}, progress={self.progress}%)>"
