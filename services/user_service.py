from core.security import get_password_hash
from models import User
from repositories.user_repo import UserRepository
from schemas.user import UserUpdate, UserOut, UserCreate


class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def get(self, user_id: int) -> UserOut:
        return await self.repo.get(user_id)

    async def get_by_email(self, email: str) -> UserOut:
        return await self.repo.get_by_email(email)

    async def update(self, user_id: int, data: UserUpdate) -> UserOut | None:
        user = await self.repo.get(user_id)
        if not user:
            return None
        user = await self.repo.update(user, data)
        return UserOut.model_validate(user, from_attributes=True)

    async def create(self, data: UserCreate) -> UserOut | None:
        data.password = get_password_hash(data.password)
        user_data = data.model_dump(exclude_unset=True)
        user = User(**user_data)
        user = await self.repo.create(user)
        return user

    async def delete(self, user_id: int) -> bool:
        user = await self.repo.get(user_id)
        if not user:
            return False
        await self.repo.delete(user)
        return True