from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime

from app.database import get_db
from app.models.session import Session
from app.models.code_block import CodeBlock
from app.models.analysis import Analysis
from app.api.dto import (
    CreateSessionInput,
    CreateSessionOutput,
    GetSessionOutput,
    UpdateSessionInput,
    SessionStatusResponse,
    SessionStatus,
    CodeBlockType,
    AnalysisDetail,
    CodeBlockBase,
)
from app.services.session_service import SessionService

router = APIRouter()

@router.post("/sessions", 
             response_model=CreateSessionOutput, 
             status_code=status.HTTP_202_ACCEPTED,
             summary="Create analysis session",
             description="""Submit Rust code or a Git repository URL for security analysis.
             
## Request Body
You must provide **either**:
- `code`: Raw Rust code content (max 10,000 characters)
- `orig_location`: Git repository URL (e.g., https://github.com/user/repo)

## Response
Returns session ID and initial status. Analysis is processed asynchronously.
Check status via `/sessions/{id}/status` endpoint.

## Notes
- Git repository analysis is not yet implemented (returns NotImplementedError)
- Analysis may take several seconds to complete
- Use the session ID to retrieve results""")
async def create_session(
    session_data: CreateSessionInput,
    db: AsyncSession = Depends(get_db)
):
    """Create a new analysis session for Rust code security analysis."""
    try:
        # Create session in database
        session_service = SessionService(db)
        session = await session_service.create_session(
            orig_location=session_data.orig_location,
            code=session_data.code
        )
        
        # Enqueue for processing
        from app.main import get_analysis_queue  # Import here to avoid circular import
        queue = get_analysis_queue()
        await queue.put(session.id)
        
        # Update session status to processing (not queued - we use PENDING/PROCESSING)
        session.status = SessionStatus.PROCESSING
        await db.commit()
        
        return CreateSessionOutput(
            id=session.id,
            status=session.status,
            progress=session.progress,
            created_at=session.created_at,
            updated_at=session.updated_at,
            completed_at=session.completed_at,
            error_message=session.error_message
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )

@router.get("/sessions/{session_id}", 
            response_model=GetSessionOutput,
            summary="Get session with analysis results",
            description="""Retrieve complete session details including analysis results.
            
## Parameters
- `session_id`: UUID of the session (returned from POST /sessions)

## Response
Returns session metadata and analysis results when available.
If analysis is still in progress, the `analyses` array may be empty.

## Error Responses
- `404 Not Found`: Session ID does not exist
- `500 Internal Server Error`: Database or processing error""")
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get complete session details including analysis results."""
    session_service = SessionService(db)
    session = await session_service.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    # Build analysis details from database
    analyses: List[AnalysisDetail] = []
    
    # Query analyses for this session with their code blocks
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    # Get analyses with code_block relationship
    result = await db.execute(
        select(Analysis)
        .where(Analysis.session_id == session_id)
        .options(selectinload(Analysis.code_block))
    )
    db_analyses = result.scalars().all()
    
    for analysis in db_analyses:
        # Build CodeBlockBase from database CodeBlock
        code_block_dto = None
        if analysis.code_block:
            code_block_dto = CodeBlockBase(
                id=analysis.code_block.id,
                created_at=analysis.code_block.created_at,
                raw_code=analysis.code_block.raw_code,
                line_start=analysis.code_block.line_start,
                line_end=analysis.code_block.line_end,
                file_path=analysis.code_block.file_path
            )
        
        # Build suggested_replacement CodeBlockBase if exists
        suggested_replacement_dto = None
        if analysis.suggested_replacement:
            # For now, suggested_replacement is stored as text in database
            # We need to create a minimal CodeBlockBase for it
            # In future, we might store it as proper CodeBlock
            suggested_replacement_dto = CodeBlockBase(
                id=f"{analysis.id}_replacement",
                created_at=analysis.created_at,
                raw_code=analysis.suggested_replacement,
                line_start=0,
                line_end=0,
                file_path=None
            )
        
        analysis_detail = AnalysisDetail(
            id=analysis.id,
            created_at=analysis.created_at,
            session_id=analysis.session_id,
            code_block_id=analysis.code_block_id,
            code_block_type=CodeBlockType(analysis.code_block_type.value),
            suggested_replacement=suggested_replacement_dto,
            code_block=code_block_dto
        )
        analyses.append(analysis_detail)
    
    return GetSessionOutput(
        id=session.id,
        status=SessionStatus(session.status.value),
        progress=session.progress,
        created_at=session.created_at,
        updated_at=session.updated_at,
        completed_at=session.completed_at,
        error_message=session.error_message,
        analyses=analyses
    )

@router.get("/sessions/{session_id}/status", 
            response_model=SessionStatusResponse,
            summary="Get session status",
            description="""Lightweight endpoint for polling analysis progress.
            
## Use Case
Use this endpoint to check analysis progress without loading full session data.
Poll this endpoint periodically after creating a session.

## Parameters
- `session_id`: UUID of the session

## Response
Returns current status and progress percentage (0-100).

## Status Values
- `PENDING`: Session created, not yet processed
- `PROCESSING`: Analysis in progress
- `COMPLETED`: Analysis finished successfully
- `FAILED`: Analysis failed (check error_message in full session)""")
async def get_session_status(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get lightweight session status for progress polling."""
    session_service = SessionService(db)
    session = await session_service.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    return SessionStatusResponse(
        session_id=session.id,
        status=SessionStatus(session.status.value),
        progress=session.progress
    )

@router.patch("/sessions/{session_id}",
              summary="Update session (internal)",
              description="""Internal endpoint for updating session progress and status.
              
## Use Case
Used by the analysis pipeline to update progress, status, and error messages.
Not intended for external API consumers.

## Parameters
- `session_id`: UUID of the session
- `status`: New status (PROCESSING, COMPLETED, FAILED)
- `progress`: Progress percentage (0-100)
- `error_message`: Error description if analysis failed

## Notes
- Automatically sets `completed_at` when status changes to COMPLETED or FAILED
- Updates `updated_at` timestamp""")
async def update_session(
    session_id: str,
    update_data: UpdateSessionInput,
    db: AsyncSession = Depends(get_db)
):
    """Internal endpoint for updating session metadata."""
    session_service = SessionService(db)
    session = await session_service.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    # Update fields
    if update_data.status:
        session.status = update_data.status
    if update_data.progress is not None:
        session.progress = update_data.progress
    if update_data.error_message is not None:
        session.error_message = update_data.error_message
    
    # Update timestamp and commit
    session.updated_at = datetime.utcnow()
    if session.status == SessionStatus.COMPLETED or session.status == SessionStatus.FAILED:
        session.completed_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "Session updated successfully"}
