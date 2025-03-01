from fastapi import APIRouter

from .campaigns import router as campaigns_router
from .health import router as health_router
from .models import router as models_router
from .templates import router as templates_router
from .privacy import router as privacy_router
from .auth import router as auth_router
from .integrations import router as integrations_router
from .platforms import router as platforms_router
from .contacts import router as contacts_router
from .policies import router as policies_router
from .graphql import router as graphql_router
from .websocket import router as websocket_router
from .canvas import router as canvas_router
from .api_keys import router as api_keys_router

router = APIRouter()

router.include_router(campaigns_router, tags=["Campaigns"])
router.include_router(models_router, tags=["Models"])
router.include_router(health_router, tags=["System"])
router.include_router(templates_router, tags=["Templates"])
router.include_router(privacy_router, tags=["Privacy"])
router.include_router(auth_router, tags=["Authentication"])
router.include_router(integrations_router, tags=["Integrations"])
router.include_router(platforms_router, tags=["Platforms"])
router.include_router(contacts_router, tags=["Contacts"])
router.include_router(policies_router, tags=["Policies"])
router.include_router(graphql_router, tags=["GraphQL"])
router.include_router(websocket_router, tags=["WebSocket"])
router.include_router(canvas_router, tags=["Canvas"])
router.include_router(api_keys_router, tags=["API Keys"])

__all__ = ["router"]
