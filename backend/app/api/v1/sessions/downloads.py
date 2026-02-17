"""Session download endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, inspect
from sqlalchemy.orm import selectinload
import io

from app.database import get_db
from app.models.session import SessionStatus as ModelSessionStatus
from app.models.analysis import Analysis
from app.services.session_service import SessionService
from app.services.patch_generator import patch_generator
from app.services.git_service import git_service

router = APIRouter()


@router.get("/sessions/{session_id}/download/fixed",
            summary="Download fixed source code (ZIP)")
async def download_fixed_files(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Download ZIP of fixed source code files."""
    session_service = SessionService(db)
    session = await session_service.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    # Check if this is a Git-based session
    session_insp = inspect(session)
    orig_location = session_insp.attrs.orig_location.value
    
    if not orig_location:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Download only available for Git-based sessions"
        )
    
    # Check if session is completed
    status_value = session_insp.attrs.status.value.value
    if status_value != ModelSessionStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Session is not completed (status: {status_value})"
        )
    
    # Get analyses with code blocks
    result = await db.execute(
        select(Analysis)
        .where(Analysis.session_id == session_id)
        .options(selectinload(Analysis.code_block))
    )
    analyses = list(result.scalars().all())
    
    # Read original files from the cloned repository
    selected_files = session_insp.attrs.selected_files.value
    
    repo_path = git_service.get_repo_path(session_id)
    
    # Get list of files that were analyzed
    if selected_files:
        files_to_read = selected_files
    else:
        files_to_read = await git_service.list_rust_files(repo_path)
    
    original_files = git_service.read_files(repo_path, files_to_read)
    
    # Generate ZIP
    zip_bytes = patch_generator.generate_fixed_files_zip(session, analyses, original_files)
    
    # Create streaming response
    zip_buffer = io.BytesIO(zip_bytes)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=fixed_code_{session_id[:8]}.zip"
        }
    )


@router.get("/sessions/{session_id}/download/patches",
            summary="Download Git patches (ZIP)")
async def download_patches(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Download ZIP of .patch files."""
    session_service = SessionService(db)
    session = await session_service.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    # Check if this is a Git-based session
    session_insp = inspect(session)
    orig_location = session_insp.attrs.orig_location.value
    
    if not orig_location:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Download only available for Git-based sessions"
        )
    
    # Check if session is completed
    status_value = session_insp.attrs.status.value.value
    if status_value != ModelSessionStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Session is not completed (status: {status_value})"
        )
    
    # Get analyses with code blocks
    result = await db.execute(
        select(Analysis)
        .where(Analysis.session_id == session_id)
        .options(selectinload(Analysis.code_block))
    )
    analyses = list(result.scalars().all())
    
    # Read original files from the cloned repository
    selected_files = session_insp.attrs.selected_files.value
    
    repo_path = git_service.get_repo_path(session_id)
    
    # Get list of files that were analyzed
    if selected_files:
        files_to_read = selected_files
    else:
        files_to_read = await git_service.list_rust_files(repo_path)
    
    original_files = git_service.read_files(repo_path, files_to_read)
    
    # Generate ZIP
    zip_bytes = patch_generator.generate_patches_zip(session, analyses, original_files)
    
    # Create streaming response
    zip_buffer = io.BytesIO(zip_bytes)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=patches_{session_id[:8]}.zip"
        }
    )