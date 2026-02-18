"""Session CRUD endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.session import SessionStatus as ModelSessionStatus
from app.models.analysis import Analysis
from app.models.sast_result import SastResult
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
from app.services.diff_generator import DiffGenerator

router = APIRouter()


@router.get("/sessions", 
            response_model=List[SessionListOutput],
            summary="List analysis sessions")
async def list_sessions(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[DTOSessionStatus] = None,
    db: AsyncSession = Depends(get_db)
):
    """List analysis sessions with optional filtering."""
    if limit > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit cannot exceed 1000"
        )
    
    session_service = SessionService(db)
    
    model_status = None
    if status_filter:
        model_status = ModelSessionStatus(status_filter.value)
    
    sessions = await session_service.list_sessions(
        skip=skip,
        limit=limit,
        status=model_status
    )
    
    session_outputs = []
    
    for session in sessions:
        result = await db.execute(
            select(func.count(Analysis.id)).where(Analysis.session_id == session.id)
        )
        analysis_count = result.scalar() or 0
        
        from sqlalchemy import inspect
        session_insp = inspect(session)
        
        session_output = SessionListOutput(
            id=session_insp.attrs.id.value,
            status=DTOSessionStatus(session_insp.attrs.status.value.value),
            progress=session_insp.attrs.progress.value,
            created_at=session_insp.attrs.created_at.value,
            updated_at=session_insp.attrs.updated_at.value,
            completed_at=session_insp.attrs.completed_at.value,
            error_message=session_insp.attrs.error_message.value,
            analysis_count=analysis_count
        )
        session_outputs.append(session_output)
    
    return session_outputs


@router.post("/sessions", 
             response_model=CreateSessionOutput, 
             status_code=status.HTTP_202_ACCEPTED,
             summary="Create analysis session")
async def create_session(
    session_data: CreateSessionInput,
    db: AsyncSession = Depends(get_db)
):
    """Create a new analysis session for Rust code security analysis."""
    try:
        session_service = SessionService(db)
        session = await session_service.create_session(
            orig_location=session_data.orig_location,
            code=session_data.code,
            git_ref=session_data.git_ref,
            selected_files=session_data.selected_files
        )
        
        from app.main import get_analysis_queue
        queue = get_analysis_queue()
        await queue.put(session.id)
        
        from sqlalchemy import inspect
        insp = inspect(session)
        
        return CreateSessionOutput(
            id=insp.attrs.id.value,
            status=insp.attrs.status.value.value,
            progress=insp.attrs.progress.value,
            created_at=insp.attrs.created_at.value,
            updated_at=insp.attrs.updated_at.value,
            completed_at=insp.attrs.completed_at.value,
            error_message=insp.attrs.error_message.value
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
            summary="Get session with analysis results")
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
    
    analyses: List[AnalysisDetail] = []
    
    result = await db.execute(
        select(Analysis)
        .where(Analysis.session_id == session_id)
        .options(selectinload(Analysis.code_block))
    )
    db_analyses = result.scalars().all()
    
    for analysis in db_analyses:
        analysis_detail = _build_analysis_detail(analysis)
        analyses.append(analysis_detail)
    
    # Fetch SAST results for this session
    sast_result = await db.execute(
        select(SastResult).where(SastResult.session_id == session_id)
    )
    db_sast = sast_result.scalars().all()
    sast_data = [
        {
            "tool": r.tool,
            "scan_phase": r.scan_phase,
            "status": r.status,
            "total_issues": r.total_issues,
            "summary": r.summary,
            "issues": r.issues,
            "auto_fixes_applied": r.auto_fixes_applied,
            "auto_fixes_failed": r.auto_fixes_failed,
            "error_message": r.error_message,
            "created_at": r.created_at.isoformat() if r.created_at is not None else None,
        }
        for r in db_sast
    ]
    
    from sqlalchemy import inspect
    session_insp = inspect(session)
    
    return GetSessionOutput(
        id=session_insp.attrs.id.value,
        status=DTOSessionStatus(session_insp.attrs.status.value.value),
        progress=session_insp.attrs.progress.value,
        created_at=session_insp.attrs.created_at.value,
        updated_at=session_insp.attrs.updated_at.value,
        completed_at=session_insp.attrs.completed_at.value,
        error_message=session_insp.attrs.error_message.value,
        analyses=analyses,
        sast_results=sast_data
    )


@router.get("/sessions/{session_id}/status", 
            response_model=SessionStatusResponse,
            summary="Get session status")
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
    
    from sqlalchemy import inspect
    session_insp = inspect(session)
    
    return SessionStatusResponse(
        session_id=session_insp.attrs.id.value,
        status=DTOSessionStatus(session_insp.attrs.status.value.value),
        progress=session_insp.attrs.progress.value
    )


@router.patch("/sessions/{session_id}",
              summary="Update session (internal)")
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
    
    if update_data.status:
        setattr(session, 'status', update_data.status.value)
    
    if update_data.progress is not None:
        setattr(session, 'progress', update_data.progress)
    
    if update_data.error_message is not None:
        setattr(session, 'error_message', update_data.error_message)
    
    setattr(session, 'updated_at', datetime.utcnow())
    
    new_status = update_data.status.value if update_data.status else None
    if new_status and (new_status == ModelSessionStatus.COMPLETED.value or new_status == ModelSessionStatus.FAILED.value):
        setattr(session, 'completed_at', datetime.utcnow())
    
    await db.commit()
    
    return {"message": "Session updated successfully"}


def _build_analysis_detail(analysis) -> AnalysisDetail:
    """Build AnalysisDetail DTO from database Analysis model."""
    from sqlalchemy import inspect
    analysis_insp = inspect(analysis)
    
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
    
    suggested_replacement_dto = None
    diff_text = None
    if analysis_insp.attrs.suggested_replacement.value is not None:
        suggested_replacement_dto = CodeBlockBase(
            id=f"{analysis_insp.attrs.id.value}_replacement",
            created_at=analysis_insp.attrs.created_at.value,
            raw_code=analysis_insp.attrs.suggested_replacement.value,
            line_start=0,
            line_end=0,
            file_path=None
        )
        
        original_code = code_block_insp.attrs.raw_code.value
        fixed_code = analysis_insp.attrs.suggested_replacement.value
        diff_text = DiffGenerator.generate_unified_diff(
            original_code,
            fixed_code,
            original_label="vulnerable_code",
            fixed_label="remediated_code"
        )
    
    risk_level_str = None
    if analysis_insp.attrs.risk_level.value is not None:
        risk_level_str = analysis_insp.attrs.risk_level.value.value
    
    return AnalysisDetail(
        id=analysis_insp.attrs.id.value,
        created_at=analysis_insp.attrs.created_at.value,
        session_id=analysis_insp.attrs.session_id.value,
        code_block_id=analysis_insp.attrs.code_block_id.value,
        code_block_type=CodeBlockType(analysis_insp.attrs.code_block_type.value.value),
        suggested_replacement=suggested_replacement_dto,
        code_block=code_block_dto,
        cwe_id=analysis_insp.attrs.cwe_id.value,
        owasp_category=analysis_insp.attrs.owasp_category.value,
        risk_level=risk_level_str,
        confidence_score=analysis_insp.attrs.confidence_score.value,
        vulnerability_description=analysis_insp.attrs.vulnerability_description.value,
        exploitation_scenario=analysis_insp.attrs.exploitation_scenario.value,
        remediation_explanation=analysis_insp.attrs.remediation_explanation.value,
        diff=diff_text,
        llm_metadata=analysis_insp.attrs.llm_metadata.value
    )