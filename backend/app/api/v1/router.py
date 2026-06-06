from fastapi import APIRouter
from app.api.v1 import health

api_router = APIRouter(prefix="/api/v1")

# Health check
api_router.include_router(health.router)

# Future routers will be added here as we build each module:
# api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
# api_router.include_router(brands.router, prefix="/brands", tags=["Brands"])
# api_router.include_router(products.router, tags=["Products"])
# api_router.include_router(faqs.router, tags=["FAQs"])
# etc.
