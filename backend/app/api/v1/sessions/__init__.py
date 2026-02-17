"""Sessions API module - combines CRUD and download routers."""
from fastapi import APIRouter

from app.api.v1.sessions.crud import router as crud_router
from app.api.v1.sessions.downloads import router as downloads_router

# Create combined router
router = APIRouter()

# Include all session routers
router.include_router(crud_router)
router.include_router(downloads_router)