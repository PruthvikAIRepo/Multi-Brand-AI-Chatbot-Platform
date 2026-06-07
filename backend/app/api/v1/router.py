from fastapi import APIRouter
from app.api.v1 import health, auth, users, brands, products, faqs, routines, compliance_rules, recommendation_rules, prompts

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

# FAQs (brand-scoped, permission-checked)
api_router.include_router(faqs.router)

# Routines (brand-scoped, permission-checked)
api_router.include_router(routines.router)

# Compliance Rules (brand-scoped, permission-checked)
api_router.include_router(compliance_rules.router)

# Recommendation Rules (brand-scoped, permission-checked, with rule testing)
api_router.include_router(recommendation_rules.router)

# Prompt Management (brand-scoped, draft/publish/versioning)
api_router.include_router(prompts.router)
