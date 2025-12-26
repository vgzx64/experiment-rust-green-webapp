from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.models.session import Session, SessionStatus
from app.services.file_storage_service import FileStorageService

class SessionService:
    """Service for managing analysis sessions."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.file_storage = FileStorageService()
    
    async def create_session(
        self, 
        orig_location: Optional[str] = None,
        code: Optional[str] = None
    ) -> Session:
        """Create a new analysis session.
        
        Args:
            orig_location: Git URL for repository analysis
            code: Raw Rust code content for direct analysis
            
        Returns:
            Session object
        """
        # Validate input
        if not orig_location and not code:
            raise ValueError("Either orig_location or code must be provided")
        
        # Create session in database
        session = Session(
            orig_location=orig_location,
            status=SessionStatus.PENDING,
            progress=0
        )
        
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        
        # Save uploaded code if provided
        if code:
            self.file_storage.save_uploaded_code(session.id, code)
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        result = await self.db.execute(
            select(Session).where(Session.id == session_id)
        )
        return result.scalar_one_or_none()
    
    async def update_session_status(
        self, 
        session_id: str, 
        status: SessionStatus,
        progress: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> Optional[Session]:
        """Update session status and progress."""
        session = await self.get_session(session_id)
        if not session:
            return None
        
        session.status = status
        if progress is not None:
            session.progress = progress
        if error_message is not None:
            session.error_message = error_message
        
        await self.db.commit()
        await self.db.refresh(session)
        return session
    
    async def list_sessions(
        self, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[SessionStatus] = None
    ) -> list[Session]:
        """List sessions with optional filtering."""
        query = select(Session)
        
        if status:
            query = query.where(Session.status == status)
        
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        # Delete session directory if it exists
        self.file_storage.cleanup_session_directory(session_id)
        
        await self.db.delete(session)
        await self.db.commit()
        return True
