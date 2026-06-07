from fastapi import APIRouter
from app.api.v1 import (
    health, auth, users, brands, products, faqs, routines,
    compliance_rules, recommendation_rules, prompts,
    conversations, logs, leads, embedding_status,
    secrets, bot_protection, notifications,
)

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

# Conversations (brand-scoped, view/flag/delete)
api_router.include_router(conversations.router)

# Logs (system-wide + brand-scoped)
api_router.include_router(logs.router)

# Leads (brand-scoped, encrypted PII)
api_router.include_router(leads.router)

# Embedding Status (brand-scoped)
api_router.include_router(embedding_status.router)

# Secrets (Super Admin only, encrypted)
api_router.include_router(secrets.router)

# Bot Protection (Super Admin only)
api_router.include_router(bot_protection.router)

# Notifications (per user)
api_router.include_router(notifications.router)
