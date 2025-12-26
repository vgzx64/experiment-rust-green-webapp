import asyncio
import logging
from typing import Optional
import json
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models.session import Session, SessionStatus
from app.models.code_block import CodeBlock
from app.models.analysis import Analysis, CodeBlockType
from app.services.file_storage_service import FileStorageService

logger = logging.getLogger(__name__)

class AnalysisWorker:
    """Worker that processes analysis jobs from the queue."""
    
    def __init__(self, queue: asyncio.Queue):
        self.queue = queue
        self.running = False
        self.task: Optional[asyncio.Task] = None
        self.file_storage = FileStorageService()
        
    async def start(self):
        """Start the worker."""
        self.running = True
        self.task = asyncio.create_task(self._run())
        logger.info("Analysis worker started")
    
    async def stop(self):
        """Stop the worker."""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Analysis worker stopped")
    
    async def _run(self):
        """Main worker loop."""
        while self.running:
            try:
                # Wait for a job from the queue
                session_id = await self.queue.get()
                logger.info(f"Processing session: {session_id}")
                
                # Process the job
                await self._process_session(session_id)
                
                # Mark task as done
                self.queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in analysis worker: {e}", exc_info=True)
                await asyncio.sleep(1)  # Prevent tight loop on errors
    
    async def _process_session(self, session_id: str):
        """Process a single analysis session."""
        async with AsyncSessionLocal() as db:
            try:
                # Get session from database
                from sqlalchemy import select
                result = await db.execute(
                    select(Session).where(Session.id == session_id)
                )
                session = result.scalar_one_or_none()
                
                if not session:
                    logger.error(f"Session {session_id} not found")
                    return
                
                # Update status to processing
                session.status = SessionStatus.PROCESSING
                session.progress = 10
                await db.commit()
                
                # Get code for analysis
                code_to_analyze = None
                
                # Check if session has uploaded code
                if self.file_storage.session_has_uploaded_code(session_id):
                    code_to_analyze = self.file_storage.read_uploaded_code(session_id)
                    logger.info(f"Using uploaded code for session {session_id}, {len(code_to_analyze)} chars")
                elif session.orig_location:
                    # Git URL - not implemented yet
                    error_msg = f"Git analysis not implemented yet. URL: {session.orig_location}"
                    logger.error(error_msg)
                    raise NotImplementedError(error_msg)
                else:
                    # Should not happen due to validation
                    error_msg = f"Session {session_id} has no code or git URL"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                
                # Generate analysis
                logger.info(f"Generating analysis for session {session_id}")
                analyzed_blocks = self._generate_mock_analysis(code_to_analyze)
                session.progress = 90
                await db.commit()
                
                # Save results to database
                await self._save_results(db, session, analyzed_blocks)
                
                # Mark as completed
                session.status = SessionStatus.COMPLETED
                session.progress = 100
                session.completed_at = datetime.utcnow()
                await db.commit()
                
                logger.info(f"Session {session_id} analysis completed")
                
            except Exception as e:
                logger.error(f"Failed to process session {session_id}: {e}", exc_info=True)
                # Update session with error
                if session:
                    session.status = SessionStatus.FAILED
                    session.error_message = str(e)
                    await db.commit()
    
    def _generate_mock_analysis(self, code: str):
        """Generate mock analysis with unsafe blocks marked as non_replaceable."""
        import re
        from datetime import datetime
        
        # Find unsafe blocks with simple regex
        unsafe_blocks = []
        pattern = r"unsafe\s*\{[^}]*\}"
        
        for i, match in enumerate(re.finditer(pattern, code, re.DOTALL)):
            block_code = match.group()
            line_start = code[:match.start()].count('\n') + 1
            line_end = line_start + block_code.count('\n')
            
            unsafe_blocks.append({
                "raw_code": block_code,
                "line_start": line_start,
                "line_end": line_end,
                "analysis_type": "non_replaceable",  # As requested
                "risk_level": None,  # Not needed per user, but included for schema compatibility
                "suggestions": []  # Empty for non_replaceable
            })
        
        return unsafe_blocks
    
    async def _save_results(self, db: AsyncSession, session: Session, analyzed_blocks: list):
        """Save analysis results to database."""
        logger.info(f"Saving {len(analyzed_blocks)} analyzed blocks for session {session.id}")
        
        for block_data in analyzed_blocks:
            # Create CodeBlock
            code_block = CodeBlock(
                raw_code=block_data["raw_code"],
                line_start=block_data["line_start"],
                line_end=block_data["line_end"],
                file_path=None  # Will be set when we have file structure
            )
            db.add(code_block)
            await db.flush()  # Get the ID
            
            # Map analysis_type string to CodeBlockType enum
            analysis_type_str = block_data.get("analysis_type", "non_replaceable")
            if analysis_type_str == "replaceable":
                code_block_type = CodeBlockType.REPLACEABLE
            elif analysis_type_str == "conditionally_replaceable":
                code_block_type = CodeBlockType.CONDITIONALLY_REPLACEABLE
            else:
                code_block_type = CodeBlockType.NON_REPLACEABLE
            
            # Create Analysis
            analysis = Analysis(
                session_id=session.id,
                code_block_id=code_block.id,
                code_block_type=code_block_type,
                suggested_replacement=None  # No suggestions in mock
            )
            db.add(analysis)
        
        await db.commit()
        logger.info(f"Saved {len(analyzed_blocks)} code blocks and analyses")
