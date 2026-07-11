from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
import jwt
from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.repositories.user import UserRepository
from app.services.auth import AuthService
from app.services.ai import AIService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

async def get_auth_service(user_repo: UserRepository = Depends(get_user_repository)) -> AuthService:
    return AuthService(user_repo)

# AI Service Singleton-like instance
_ai_service_instance = None

def get_ai_service() -> AIService:
    global _ai_service_instance
    if _ai_service_instance is None:
        _ai_service_instance = AIService()
    return _ai_service_instance

async def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    user_repo: UserRepository = Depends(get_user_repository)
) -> User:
    # 1. Fallback: Check cookies for browser requests (HTMX uses cookies)
    if not token:
        token = request.cookies.get("access_token")
        if token and token.startswith("Bearer "):
            token = token[7:]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        token_type = payload.get("type")
        if user_id is None or token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials."
            )
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
        
    user = await user_repo.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user."
        )
    return current_user

async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have enough privileges."
        )
    return current_user

async def get_current_qa_lead(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if current_user.role not in ["qa_lead", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have enough privileges."
        )
    return current_user

async def get_current_qa_engineer(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if current_user.role not in ["qa_engineer", "qa_lead", "admin", "user"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have enough privileges."
        )
    return current_user
