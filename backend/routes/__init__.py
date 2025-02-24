from fastapi import APIRouter
from .campaign_routes import router as campaign_router
from .model_routes import router as model_router
from .health_routes import router as health_router

router = APIRouter()

router.include_router(campaign_router, prefix="/api/v1", tags=["Campaigns"])
router.include_router(model_router, prefix="/api/v1", tags=["Models"])
router.include_router(health_router, prefix="/api/v1", tags=["System"])

__all__ = ['router'] 