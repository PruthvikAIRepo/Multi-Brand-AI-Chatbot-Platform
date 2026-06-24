from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.auth import (
    LoginRequest, LoginResponse,
    RefreshRequest, RefreshResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.services import auth_service
from app.core.permissions import get_current_user, get_authenticated_user
from app.core.response import api_response
from app.core.request_utils import get_client_ip
from app.core.rate_limiter import check_auth_rate_limit
from app.core.exceptions import RateLimitError
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=dict)
async def login(payload: LoginRequest, http_request: Request, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return JWT tokens."""
    ip = get_client_ip(http_request)
    if await check_auth_rate_limit(ip):
        raise RateLimitError()
    result = await auth_service.authenticate_user(db, payload.email, payload.password, ip_address=ip)
    return api_response(data=result, message="Login successful")


@router.post("/refresh", response_model=dict)
async def refresh_token(request: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Get a new access token using a refresh token."""
    result = await auth_service.refresh_access_token(db, request.refresh_token)
    return api_response(data=result, message="Token refreshed")


@router.post("/change-password", response_model=dict)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Change password for the currently authenticated user.

    Uses the lenient dependency so a user still flagged must_change_password
    can reach this endpoint to clear the gate."""
    await auth_service.change_password(
        db, current_user.id, request.current_password, request.new_password
    )
    return api_response(message="Password changed successfully")


@router.post("/forgot-password", response_model=dict)
async def forgot_password(request: ForgotPasswordRequest, http_request: Request, db: AsyncSession = Depends(get_db)):
    """Request a password reset link. Always returns success to prevent email enumeration."""
    if await check_auth_rate_limit(get_client_ip(http_request)):
        raise RateLimitError()
    raw_token = await auth_service.forgot_password(db, request.email)
    # In production, send email with the raw_token link here
    # For development, we return the token so you can test
    data = None
    from app.config import get_settings
    if get_settings().ENVIRONMENT == "development" and raw_token:
        data = {"reset_token": raw_token}
    return api_response(
        data=data,
        message="If this email is registered, a reset link has been sent",
    )


@router.post("/reset-password", response_model=dict)
async def reset_password(request: ResetPasswordRequest, http_request: Request, db: AsyncSession = Depends(get_db)):
    """Reset password using a valid reset token."""
    if await check_auth_rate_limit(get_client_ip(http_request)):
        raise RateLimitError()
    await auth_service.reset_password(db, request.token, request.new_password)
    return api_response(message="Password reset successfully")


@router.post("/logout", response_model=dict)
async def logout(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Logout — revoke the refresh token."""
    await auth_service.logout(db, request.refresh_token)
    return api_response(message="Logged out successfully")


@router.get("/me", response_model=dict)
async def get_me(current_user: User = Depends(get_authenticated_user)):
    """Get current authenticated user's info.

    Lenient dependency so the frontend can read must_change_password and
    redirect the user to the change-password screen."""
    return api_response(data={
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role.value,
        "is_active": current_user.is_active,
        "must_change_password": current_user.must_change_password,
        "assigned_brands": [
            {"brand_id": str(a.brand_id), "permissions": a.permissions or []}
            for a in current_user.brand_assignments
        ],
    })


class UpdateProfileRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)


@router.put("/me", response_model=dict)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update own profile (full_name)."""
    current_user.full_name = request.full_name
    await db.flush()
    return api_response(data={
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
    }, message="Profile updated")
