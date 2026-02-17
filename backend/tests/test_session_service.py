"""Tests for SessionService."""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session, SessionStatus
from app.services.session_service import SessionService


class TestSessionService:
    """Test cases for SessionService."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock(spec=AsyncSession)
    
    @pytest.fixture
    def mock_file_storage(self):
        """Create mock file storage service."""
        with patch('app.services.session_service.FileStorageService') as mock:
            yield mock.return_value
    
    @pytest.fixture
    def session_service(self, mock_db, mock_file_storage):
        """Create session service with mocked dependencies."""
        return SessionService(mock_db)
    
    # ==================== create_session Tests ====================
    
    @pytest.mark.asyncio
    async def test_create_session_with_code(self, session_service, mock_db):
        """Test creating session with code submission."""
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        session = await session_service.create_session(code="fn main() {}")
        
        assert session is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_session_with_git_url(self, session_service, mock_db):
        """Test creating session with Git URL."""
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        session = await session_service.create_session(
            orig_location="https://github.com/user/repo",
            git_ref="main",
            selected_files=["src/main.rs"]
        )
        
        assert session is not None
        mock_db.add.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_session_requires_code_or_url(self, session_service):
        """Test that session requires either code or URL."""
        with pytest.raises(ValueError, match="Either orig_location or code must be provided"):
            await session_service.create_session()
    
    @pytest.mark.asyncio
    async def test_create_session_git_requires_ref(self, session_service):
        """Test that Git session requires git_ref."""
        with pytest.raises(ValueError, match="git_ref is required"):
            await session_service.create_session(
                orig_location="https://github.com/user/repo"
            )
    
    @pytest.mark.asyncio
    async def test_create_session_default_status(self, session_service, mock_db):
        """Test that new session has PENDING status."""
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        session = await session_service.create_session(code="fn main() {}")
        
        assert session.status == SessionStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_create_session_default_progress(self, session_service, mock_db):
        """Test that new session has 0 progress."""
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        session = await session_service.create_session(code="fn main() {}")
        
        assert session.progress == 0
    
    # ==================== get_session Tests ====================
    
    @pytest.mark.asyncio
    async def test_get_session_found(self, session_service, mock_db):
        """Test getting an existing session."""
        mock_session = Session()
        mock_session.id = "test-session-id"
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        session = await session_service.get_session("test-session-id")
        
        assert session is not None
        assert session.id == "test-session-id"
    
    @pytest.mark.asyncio
    async def test_get_session_not_found(self, session_service, mock_db):
        """Test getting a non-existent session."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        session = await session_service.get_session("non-existent-id")
        
        assert session is None
    
    # ==================== update_session_status Tests ====================
    
    @pytest.mark.asyncio
    async def test_update_session_status(self, session_service, mock_db):
        """Test updating session status."""
        mock_session = Session()
        mock_session.id = "test-id"
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        result = await session_service.update_session_status(
            "test-id",
            SessionStatus.PROCESSING,
            progress=50
        )
        
        assert result is not None
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_session_status_with_error(self, session_service, mock_db):
        """Test updating session with error message."""
        mock_session = Session()
        mock_session.id = "test-id"
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        result = await session_service.update_session_status(
            "test-id",
            SessionStatus.FAILED,
            error_message="Analysis failed"
        )
        
        assert result is not None
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_session_status_not_found(self, session_service, mock_db):
        """Test updating non-existent session."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        result = await session_service.update_session_status(
            "non-existent-id",
            SessionStatus.COMPLETED
        )
        
        assert result is None
    
    # ==================== list_sessions Tests ====================
    
    @pytest.mark.asyncio
    async def test_list_sessions(self, session_service, mock_db):
        """Test listing sessions."""
        mock_sessions = [Session(), Session()]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_sessions
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        sessions = await session_service.list_sessions()
        
        assert len(sessions) == 2
    
    @pytest.mark.asyncio
    async def test_list_sessions_with_pagination(self, session_service, mock_db):
        """Test listing sessions with pagination."""
        mock_sessions = [Session()]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_sessions
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        sessions = await session_service.list_sessions(skip=10, limit=5)
        
        assert len(sessions) == 1
    
    @pytest.mark.asyncio
    async def test_list_sessions_with_status_filter(self, session_service, mock_db):
        """Test listing sessions with status filter."""
        mock_sessions = [Session()]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_sessions
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        sessions = await session_service.list_sessions(
            status=SessionStatus.COMPLETED
        )
        
        assert len(sessions) == 1
    
    @pytest.mark.asyncio
    async def test_list_sessions_empty(self, session_service, mock_db):
        """Test listing sessions when none exist."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        sessions = await session_service.list_sessions()
        
        assert len(sessions) == 0
    
    # ==================== delete_session Tests ====================
    
    @pytest.mark.asyncio
    async def test_delete_session(self, session_service, mock_db):
        """Test deleting a session."""
        mock_session = Session()
        mock_session.id = "test-id"
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()
        
        result = await session_service.delete_session("test-id")
        
        assert result is True
        mock_db.delete.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_session_not_found(self, session_service, mock_db):
        """Test deleting non-existent session."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        result = await session_service.delete_session("non-existent-id")
        
        assert result is False


class TestSessionServiceFileStorage:
    """Test file storage integration in SessionService."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock(spec=AsyncSession)
    
    @pytest.mark.asyncio
    async def test_create_session_saves_code(self, mock_db):
        """Test that creating session saves code to file storage."""
        with patch('app.services.session_service.FileStorageService') as mock_storage_class:
            mock_storage = mock_storage_class.return_value
            mock_storage.save_uploaded_code = MagicMock()
            
            mock_db.add = MagicMock()
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()
            
            service = SessionService(mock_db)
            await service.create_session(code="fn main() {}")
            
            mock_storage.save_uploaded_code.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_session_cleans_up_directory(self, mock_db):
        """Test that deleting session cleans up file directory."""
        with patch('app.services.session_service.FileStorageService') as mock_storage_class:
            mock_storage = mock_storage_class.return_value
            mock_storage.cleanup_session_directory = MagicMock()
            
            mock_session = Session()
            mock_session.id = "test-id"
            
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_session
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.delete = AsyncMock()
            mock_db.commit = AsyncMock()
            
            service = SessionService(mock_db)
            await service.delete_session("test-id")
            
            mock_storage.cleanup_session_directory.assert_called_once_with("test-id")