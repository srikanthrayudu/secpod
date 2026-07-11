from uuid import UUID
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.repositories.base import BaseRepository

class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).filter(User.email == email))
        return result.scalars().first()

    async def get_users_paged(
        self,
        *,
        skip: int = 0,
        limit: int = 10,
        search: str | None = None,
        role: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> tuple[list[User], int]:
        # Formulate query
        query = select(User)
        count_query = select(func.count(User.id))

        # Filter by role
        if role:
            query = query.filter(User.role == role)
            count_query = count_query.filter(User.role == role)

        # Filter by search term
        if search:
            search_filter = or_(
                User.email.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%"),
                User.bio.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
            count_query = count_query.filter(search_filter)

        # Sort order
        sort_col = getattr(User, sort_by, User.created_at)
        if sort_order == "desc":
            query = query.order_by(sort_col.desc())
        else:
            query = query.order_by(sort_col.asc())

        # Total Count
        count_res = await self.db.execute(count_query)
        total = count_res.scalar() or 0

        # Execute page fetch
        query = query.offset(skip).limit(limit)
        res = await self.db.execute(query)
        users = list(res.scalars().all())

        return users, total
