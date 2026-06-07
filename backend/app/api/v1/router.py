from fastapi import APIRouter
from app.api.v1 import health, auth

api_router = APIRouter(prefix="/api/v1")

# Health check (public)
api_router.include_router(health.router)

# Auth (public — login, refresh, forgot/reset password)
api_router.include_router(auth.router)

# Future routers will be added here as we build each module:
# api_router.include_router(users.router)
# api_router.include_router(brands.router)
# etc.
