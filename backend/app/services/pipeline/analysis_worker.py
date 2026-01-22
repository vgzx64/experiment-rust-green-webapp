import asyncio
import logging
from typing import Optional
import json
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models.session import Session, SessionStatus
from app.models.code_block import CodeBlock
from app.models.analysis import Analysis, CodeBlockType, RiskLevel
from app.services.file_storage_service import FileStorageService
from app.config.llm_config import llm_config

logger = logging.getLogger(__name__)

class AnalysisWorker:
    """Worker that processes analysis jobs from the queue."""
    
    def __init__(self, queue: asyncio.Queue):
        self.queue = queue
        self.running = False
        self.task: Optional[asyncio.Task] = None
        self.file_storage = FileStorageService()
        
        # Initialize LLM service if enabled
        self.use_llm = llm_config.enabled
        self.llm_service = None
        if self.use_llm:
            try:
                from app.services.llm_service import llm_service
                self.llm_service = llm_service
                logger.info("LLM service initialized")
            except ImportError as e:
                logger.warning(f"Failed to import LLM service: {e}")
                self.use_llm = False
            except Exception as e:
                logger.warning(f"Failed to initialize LLM service: {e}")
                self.use_llm = False
        
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
                session.status = SessionStatus.PROCESSING.value  # type: ignore
                session.progress = 10  # type: ignore
                await db.commit()
                
                # Get code for analysis
                code_to_analyze = ""
                
                # Check if session has uploaded code
                if self.file_storage.session_has_uploaded_code(session_id):
                    code_content = self.file_storage.read_uploaded_code(session_id)
                    if code_content:
                        code_to_analyze = code_content
                    logger.info(f"Using uploaded code for session {session_id}, {len(code_to_analyze)} chars")
                elif session.orig_location is not None:
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
                
                llm_available = bool(self.use_llm and self.llm_service)
                if llm_available:
                    analyzed_blocks = await self._generate_llm_analysis(code_to_analyze)
                
                session.progress = 90  # type: ignore
                await db.commit()
                
                # Save results to database
                await self._save_results(db, session, analyzed_blocks, use_llm=llm_available)
                
                # Mark as completed
                session.status = SessionStatus.COMPLETED.value  # type: ignore
                session.progress = 100  # type: ignore
                session.completed_at = datetime.utcnow()  # type: ignore
                await db.commit()
                
                logger.info(f"Session {session_id} analysis completed")
                
            except Exception as e:
                logger.error(f"Failed to process session {session_id}: {e}", exc_info=True)
                # Update session with error
                try:
                    # Try to get session again to update error status
                    from sqlalchemy import select
                    result = await db.execute(
                        select(Session).where(Session.id == session_id)
                    )
                    session_to_update = result.scalar_one_or_none()
                    if session_to_update:
                        session_to_update.status = SessionStatus.FAILED.value  # type: ignore
                        session_to_update.error_message = str(e)  # type: ignore
                        await db.commit()
                except Exception as update_error:
                    logger.error(f"Failed to update session error status: {update_error}")
    
    
    async def _generate_llm_analysis(self, code: str):
        """Generate enhanced analysis using LLM."""
        try:
            if not self.llm_service:
                logger.warning("LLM service not available, falling back to mock analysis")
                return []
            
            logger.info("Starting LLM analysis pipeline")
            llm_results = await self.llm_service.complete_analysis_pipeline(code)
            
            vulnerability_analysis = llm_results.get("vulnerability_analysis", {})
            remediation = llm_results.get("remediation")
            verification = llm_results.get("verification")
            
            # If no vulnerability found, return empty list
            if vulnerability_analysis.get("vulnerability_type") == "None":
                logger.info("LLM analysis found no vulnerabilities")
                return []
            
            # Extract line numbers from LLM analysis
            line_numbers = vulnerability_analysis.get("line_numbers", [1, 1])
            line_start = line_numbers[0] if len(line_numbers) > 0 else 1
            line_end = line_numbers[1] if len(line_numbers) > 1 else line_start
            
            # Map risk level
            risk_level_str = vulnerability_analysis.get("risk_level", "").lower()
            risk_level = None
            if risk_level_str == "low":
                risk_level = RiskLevel.LOW
            elif risk_level_str == "medium":
                risk_level = RiskLevel.MEDIUM
            elif risk_level_str == "high":
                risk_level = RiskLevel.HIGH
            elif risk_level_str == "critical":
                risk_level = RiskLevel.CRITICAL
            
            # Determine analysis type based on remediation
            analysis_type = "non_replaceable"
            if remediation and remediation.get("fixed_code"):
                analysis_type = "replaceable"
            
            return [{
                "raw_code": code,  # In real implementation, extract vulnerable portion
                "line_start": line_start,
                "line_end": line_end,
                "analysis_type": analysis_type,
                "risk_level": risk_level,
                "cwe_id": vulnerability_analysis.get("cwe_id"),
                "owasp_category": vulnerability_analysis.get("owasp_category"),
                "confidence_score": vulnerability_analysis.get("confidence_score"),
                "vulnerability_description": vulnerability_analysis.get("vulnerability_description"),
                "exploitation_scenario": vulnerability_analysis.get("exploitation_scenario"),
                "remediation_explanation": remediation.get("explanation") if remediation else None,
                "verification_result": verification.get("verification_explanation") if verification else None,
                "llm_metadata": {
                    "vulnerability_analysis": vulnerability_analysis.get("llm_metadata", {}),
                    "remediation": remediation.get("llm_metadata", {}) if remediation else {},
                    "verification": verification.get("llm_metadata", {}) if verification else {}
                },
                "suggestions": [remediation.get("fixed_code")] if remediation and remediation.get("fixed_code") else []
            }]
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}", exc_info=True)
            logger.info("Falling back to mock analysis")
            return []
    
    async def _save_results(self, db: AsyncSession, session: Session, analyzed_blocks: list, use_llm: bool = False):
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
            
            # Get suggested replacement (first suggestion if exists)
            suggested_replacement = None
            suggestions = block_data.get("suggestions", [])
            if suggestions:
                suggested_replacement = suggestions[0]
            
            # Create Analysis with enhanced fields if available
            analysis_kwargs = {
                "session_id": session.id,
                "code_block_id": code_block.id,
                "code_block_type": code_block_type,
                "suggested_replacement": suggested_replacement,
            }
            
            # Add enhanced LLM fields if available
            if use_llm:
                analysis_kwargs.update({
                    "cwe_id": block_data.get("cwe_id"),
                    "owasp_category": block_data.get("owasp_category"),
                    "risk_level": block_data.get("risk_level"),
                    "confidence_score": block_data.get("confidence_score"),
                    "vulnerability_description": block_data.get("vulnerability_description"),
                    "exploitation_scenario": block_data.get("exploitation_scenario"),
                    "remediation_explanation": block_data.get("remediation_explanation"),
                    "verification_result": block_data.get("verification_result"),
                    "llm_metadata": block_data.get("llm_metadata"),
                })
            
            analysis = Analysis(**analysis_kwargs)
            db.add(analysis)
        
        await db.commit()
        logger.info(f"Saved {len(analyzed_blocks)} code blocks and analyses")
