"""
Authentication routes for register, login, refresh token, and profile lookup.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import (
    AuthenticationError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.database.repositories.user import UserRepository
from app.database.session import get_db
from app.schemas.auth import (
    RefreshTokenRequest,
    TokenResponse,
    UserLogin,
    UserProfile,
    UserRegister,
)

router = APIRouter()
security = HTTPBearer()
settings = get_settings()


from fastapi import Request

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> UserProfile:
    """Dependency to get currently authenticated user from HttpOnly cookie or Bearer header."""
    # Try cookies first
    token = request.cookies.get("nexus_token")
    
    # Fallback to Authorization Header
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise AuthenticationError("Invalid token type")
        
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(payload["sub"])
        if not user or not user.is_active:
            raise AuthenticationError("User is inactive or not found")
        
        return UserProfile.model_validate(user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )



from fastapi import APIRouter, Depends, HTTPException, status, Response

# ... (rest of code) ...

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserRegister,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Register a new user and return an authentication token pair."""
    user_repo = UserRepository(db)
    
    # Restrict to single user connected to their DB
    user_count = await user_repo.count()
    if user_count >= 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration disabled: This instance of Nexus is configured for a single user only."
        )

    # Check if username or email already exists
    existing_email = await user_repo.get_by_email(payload.email)
    if existing_email:
        raise UserAlreadyExistsError("email")
        
    existing_username = await user_repo.get_by_username(payload.username)
    if existing_username:
        raise UserAlreadyExistsError("username")

    pwd_hash = hash_password(payload.password)
    
    # The only user is admin/owner
    role = "admin"
    
    user = await user_repo.create_user(
        username=payload.username,
        email=payload.email,
        password_hash=pwd_hash,
        role=role,
    )
    
    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id)
    
    # Set secure HttpOnly cookie
    response.set_cookie(
        key="nexus_token",
        value=access_token,
        httponly=True,
        max_age=settings.jwt_access_token_expire_minutes * 60,
        samesite="lax",
        secure=False  # Set to True in production with SSL
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Login an existing user and return access/refresh tokens."""
    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(payload.email)
    
    if not user or not verify_password(payload.password, user.password_hash):
        raise AuthenticationError("Invalid email or password")
        
    if not user.is_active:
        raise AuthenticationError("Account is deactivated")
        
    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id)
    
    # Set secure HttpOnly cookie
    response.set_cookie(
        key="nexus_token",
        value=access_token,
        httponly=True,
        max_age=settings.jwt_access_token_expire_minutes * 60,
        samesite="lax",
        secure=False  # Set to True in production with SSL
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )



@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Refresh an access token using a valid refresh token."""
    try:
        decoded = decode_token(payload.refresh_token)
        if decoded.get("type") != "refresh":
            raise AuthenticationError("Invalid token type")
            
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(decoded["sub"])
        if not user or not user.is_active:
            raise AuthenticationError("User is inactive or not found")
            
        access_token = create_access_token(user.id, user.role)
        new_refresh_token = create_refresh_token(user.id)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.get("/me", response_model=UserProfile)
async def get_profile(
    current_user: UserProfile = Depends(get_current_user),
) -> UserProfile:
    """Get profile details of the currently logged-in user."""
    return current_user
