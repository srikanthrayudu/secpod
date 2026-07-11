from uuid import UUID
from fastapi import HTTPException, status
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserUpdate
from app.utils.logger import logger

class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register_user(self, user_in: UserCreate) -> User:
        logger.info(f"Registering user: {user_in.email}")
        existing_user = await self.user_repo.get_by_email(user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists."
            )
        
        # Hash user password
        hashed_password = get_password_hash(user_in.password)
        
        user_data = user_in.model_dump(exclude={"password"})
        user_data["hashed_password"] = hashed_password
        
        # If first user, make admin (standard shortcut for development setups)
        users, count = await self.user_repo.get_users_paged(limit=1)
        if count == 0:
            user_data["role"] = "admin"
            user_data["is_verified"] = True
            
        return await self.user_repo.create(user_data)

    async def authenticate_user(self, email: str, password: str) -> User:
        logger.info(f"Authenticating user: {email}")
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password."
            )
        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password."
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated."
            )
        return user

    async def get_user_profile(self, user_id: UUID) -> User:
        user = await self.user_repo.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )
        return user

    async def update_user_profile(self, user_id: UUID, update_data: UserUpdate) -> User:
        user = await self.user_repo.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )
        
        data = update_data.model_dump(exclude_unset=True)
        if "password" in data and data["password"]:
            data["hashed_password"] = get_password_hash(data["password"])
            del data["password"]

        return await self.user_repo.update(user, data)
