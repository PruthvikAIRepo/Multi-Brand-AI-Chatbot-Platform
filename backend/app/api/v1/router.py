from fastapi import APIRouter
from app.api.v1 import health, auth, users, brands, products

api_router = APIRouter(prefix="/api/v1")

# Health check (public)
api_router.include_router(health.router)

# Auth (public — login, refresh, forgot/reset password)
api_router.include_router(auth.router)

# User management (Super Admin only)
api_router.include_router(users.router)

# Brands (RBAC protected)
api_router.include_router(brands.router)

# Products (brand-scoped, permission-checked)
api_router.include_router(products.router)
