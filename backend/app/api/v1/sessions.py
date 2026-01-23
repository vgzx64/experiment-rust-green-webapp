from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.session import SessionStatus as ModelSessionStatus
from app.models.analysis import Analysis
from app.api.dto import (
    CreateSessionInput,
    CreateSessionOutput,
    GetSessionOutput,
    UpdateSessionInput,
    SessionStatusResponse,
    SessionListOutput,
    SessionStatus as DTOSessionStatus,
    CodeBlockType,
    AnalysisDetail,
    CodeBlockBase,
)
from app.services.session_service import SessionService

router = APIRouter()

@router.get("/sessions", 
            response_model=List[SessionListOutput],
            summary="List analysis sessions",
            description="""List all analysis sessions with optional filtering.
            
## Parameters
- `skip`: Number of sessions to skip (for pagination)
- `limit`: Maximum number of sessions to return (default: 100, max: 1000)
- `status_filter`: Filter by session status (PENDING, PROCESSING, COMPLETED, FAILED)

## Response
Returns a list of session summaries including basic metadata.
Use the session ID from the response to get detailed session information.

## Notes
- Sessions are returned in reverse chronological order (newest first)
- For detailed analysis results, use GET /sessions/{id}
- Large result sets should use pagination with skip/limit parameters""")
async def list_sessions(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[DTOSessionStatus] = None,
    db: AsyncSession = Depends(get_db)
):
    """List analysis sessions with optional filtering."""
    # Validate limit
    if limit > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit cannot exceed 1000"
        )
    
    session_service = SessionService(db)
    
    # Convert DTO status to model status if provided
    model_status = None
    if status_filter:
        model_status = ModelSessionStatus(status_filter.value)
    
    # Get sessions from database
    sessions = await session_service.list_sessions(
        skip=skip,
        limit=limit,
        status=model_status
    )
    
    # Convert to DTOs with analysis counts
    from sqlalchemy import select, func
    session_outputs = []
    
    for session in sessions:
        # Get analysis count for this session
        result = await db.execute(
            select(func.count(Analysis.id)).where(Analysis.session_id == session.id)
        )
        analysis_count = result.scalar() or 0
        
        # Use SQLAlchemy inspect to get actual attribute values with proper typing
        from sqlalchemy import inspect
        session_insp = inspect(session)
        
        session_id = session_insp.attrs.id.value
        status_value = DTOSessionStatus(session_insp.attrs.status.value.value)
        progress_value = session_insp.attrs.progress.value
        created_at_value = session_insp.attrs.created_at.value
        updated_at_value = session_insp.attrs.updated_at.value
        completed_at_value = session_insp.attrs.completed_at.value
        error_message_value = session_insp.attrs.error_message.value
        
        session_output = SessionListOutput(
            id=session_id,
            status=status_value,
            progress=progress_value,
            created_at=created_at_value,
            updated_at=updated_at_value,
            completed_at=completed_at_value,
            error_message=error_message_value,
            analysis_count=analysis_count
        )
        session_outputs.append(session_output)
    
    return session_outputs

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
        
        # Use SQLAlchemy inspect to get actual attribute values with proper typing
        from sqlalchemy import inspect
        insp = inspect(session)
        
        # Get attribute values using inspect which returns the actual Python values
        session_id = insp.attrs.id.value
        status_value = insp.attrs.status.value.value  # status is an enum, need .value
        progress_value = insp.attrs.progress.value
        created_at_value = insp.attrs.created_at.value
        updated_at_value = insp.attrs.updated_at.value
        completed_at_value = insp.attrs.completed_at.value
        error_message_value = insp.attrs.error_message.value
        
        return CreateSessionOutput(
            id=session_id,
            status=status_value,
            progress=progress_value,
            created_at=created_at_value,
            updated_at=updated_at_value,
            completed_at=completed_at_value,
            error_message=error_message_value
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
        # Use SQLAlchemy inspect to get actual attribute values with proper typing
        from sqlalchemy import inspect
        analysis_insp = inspect(analysis)
        
        # Build CodeBlockBase from database CodeBlock
        if analysis.code_block is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Analysis {analysis_insp.attrs.id.value} has no associated code block"
            )
        
        code_block_insp = inspect(analysis.code_block)
        code_block_dto = CodeBlockBase(
            id=code_block_insp.attrs.id.value,
            created_at=code_block_insp.attrs.created_at.value,
            raw_code=code_block_insp.attrs.raw_code.value,
            line_start=code_block_insp.attrs.line_start.value,
            line_end=code_block_insp.attrs.line_end.value,
            file_path=code_block_insp.attrs.file_path.value if code_block_insp.attrs.file_path.value else None
        )
        
        # Build suggested_replacement CodeBlockBase if exists
        suggested_replacement_dto = None
        if analysis_insp.attrs.suggested_replacement.value is not None:
            # For now, suggested_replacement is stored as text in database
            # We need to create a minimal CodeBlockBase for it
            # In future, we might store it as proper CodeBlock
            suggested_replacement_dto = CodeBlockBase(
                id=f"{analysis_insp.attrs.id.value}_replacement",
                created_at=analysis_insp.attrs.created_at.value,
                raw_code=analysis_insp.attrs.suggested_replacement.value,
                line_start=0,
                line_end=0,
                file_path=None
            )
        
        # Get risk level as string if exists
        risk_level_str = None
        if analysis_insp.attrs.risk_level.value is not None:
            risk_level_str = analysis_insp.attrs.risk_level.value.value
        
        analysis_detail = AnalysisDetail(
            id=analysis_insp.attrs.id.value,
            created_at=analysis_insp.attrs.created_at.value,
            session_id=analysis_insp.attrs.session_id.value,
            code_block_id=analysis_insp.attrs.code_block_id.value,
            code_block_type=CodeBlockType(analysis_insp.attrs.code_block_type.value.value),
            suggested_replacement=suggested_replacement_dto,
            code_block=code_block_dto,
            # Enhanced fields
            cwe_id=analysis_insp.attrs.cwe_id.value,
            owasp_category=analysis_insp.attrs.owasp_category.value,
            risk_level=risk_level_str,
            confidence_score=analysis_insp.attrs.confidence_score.value,
            vulnerability_description=analysis_insp.attrs.vulnerability_description.value,
            exploitation_scenario=analysis_insp.attrs.exploitation_scenario.value,
            remediation_explanation=analysis_insp.attrs.remediation_explanation.value,
            verification_result=analysis_insp.attrs.verification_result.value,
            llm_metadata=analysis_insp.attrs.llm_metadata.value
        )
        analyses.append(analysis_detail)
    
    # Use SQLAlchemy inspect to get actual attribute values with proper typing
    from sqlalchemy import inspect
    session_insp = inspect(session)
    
    session_id = session_insp.attrs.id.value
    status_value = DTOSessionStatus(session_insp.attrs.status.value.value)
    progress_value = session_insp.attrs.progress.value
    created_at_value = session_insp.attrs.created_at.value
    updated_at_value = session_insp.attrs.updated_at.value
    completed_at_value = session_insp.attrs.completed_at.value
    error_message_value = session_insp.attrs.error_message.value
    
    return GetSessionOutput(
        id=session_id,
        status=status_value,
        progress=progress_value,
        created_at=created_at_value,
        updated_at=updated_at_value,
        completed_at=completed_at_value,
        error_message=error_message_value,
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
    
    # Use SQLAlchemy inspect to get actual attribute values with proper typing
    from sqlalchemy import inspect
    session_insp = inspect(session)
    
    session_id_value = session_insp.attrs.id.value
    status_value = DTOSessionStatus(session_insp.attrs.status.value.value)
    progress_value = session_insp.attrs.progress.value
    
    return SessionStatusResponse(
        session_id=session_id_value,
        status=status_value,
        progress=progress_value
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
    
    # Update fields - using direct assignment which works at runtime
    # Pylance has incorrect type stubs for SQLAlchemy, but this is correct
    if update_data.status:
        # Use setattr to avoid direct assignment type errors
        setattr(session, 'status', update_data.status.value)
    
    if update_data.progress is not None:
        setattr(session, 'progress', update_data.progress)
    
    if update_data.error_message is not None:
        setattr(session, 'error_message', update_data.error_message)
    
    # Update timestamp and commit
    setattr(session, 'updated_at', datetime.utcnow())
    
    # Check if status changed to COMPLETED or FAILED
    # Get the status value that was just set
    new_status = update_data.status.value if update_data.status else None
    if new_status and (new_status == ModelSessionStatus.COMPLETED.value or new_status == ModelSessionStatus.FAILED.value):
        setattr(session, 'completed_at', datetime.utcnow())
    
    await db.commit()
    
    return {"message": "Session updated successfully"}
