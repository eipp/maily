from fastapi import Depends, APIRouter
from ..graphql import graphql_router
from ..middleware.security import authenticate

# Create a router instance with prefix for GraphQL endpoint
router = APIRouter(prefix="/graphql")

# Include the GraphQL router with authentication
# Authentication is disabled in this example, but can be added via dependencies
# router.include_router(graphql_router, dependencies=[Depends(authenticate)])
router.include_router(graphql_router)

@router.get("/health")
async def graphql_health_check():
    """GraphQL health check endpoint."""
    return {"status": "ok", "service": "GraphQL API"}
