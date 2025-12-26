from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from contextlib import asynccontextmanager
import logging

from app.database import engine, Base
from app.services.session_service import SessionService
from app.services.pipeline.analysis_worker import AnalysisWorker
from app.api.v1 import sessions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global message queue for analysis jobs
analysis_queue = asyncio.Queue()
analysis_worker = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup
    logger.info("Starting up Rust-Green Backend...")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")
    
    # Start analysis worker
    global analysis_worker
    analysis_worker = AnalysisWorker(analysis_queue)
    asyncio.create_task(analysis_worker.start())
    logger.info("Analysis worker started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    if analysis_worker:
        await analysis_worker.stop()
    logger.info("Analysis worker stopped")

# Create FastAPI app
app = FastAPI(
    title="Rust-Green Backend API",
    description="""Backend API for the Rust code safety analysis platform.
    
## Overview
This API provides endpoints for submitting Rust code for security analysis,
tracking analysis sessions, and retrieving results.

## Key Features
- Submit Rust code or Git repository URLs for analysis
- Track analysis progress in real-time
- Retrieve detailed analysis reports with unsafe code blocks
- Asynchronous processing with job queue

## API Documentation
- Interactive documentation available at `/docs` (Swagger UI)
- Alternative documentation at `/redoc`
- OpenAPI schema at `/openapi.json`
""",
    version="0.1.0",
    contact={
        "name": "Rust-Green Team",
        "url": "https://github.com/rust-green",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(sessions.router, prefix="/api/v1", tags=["sessions"])

@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {
        "message": "Rust-Green Backend API",
        "version": "0.1.0",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": "2023-10-01T10:00:00Z"}

# Export the queue for use in other modules
def get_analysis_queue():
    return analysis_queue
