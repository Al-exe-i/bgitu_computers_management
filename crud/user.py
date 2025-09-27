from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.user import User
from schemas.user import UserCreate, UserUpdate
from core.security import get_password_hash


async def update_user(db: AsyncSession, db_obj: User, obj_in: UserUpdate):
    update_data = obj_in.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["password"] = get_password_hash(update_data["password"])
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def get_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()


async def create_user(db: AsyncSession, obj_in: UserCreate):
    db_obj = User(
        name=obj_in.name,
        surname=obj_in.surname,
        email=obj_in.email,
        telegram_id=obj_in.telegram_id,
        telegram_id_confirmed=obj_in.telegram_id_confirmed,
        password=get_password_hash(obj_in.password),
        photo=obj_in.photo,
        is_superuser=False,
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def delete_user(db: AsyncSession, user_id: int):
    obj = await get_user(db, user_id)
    if obj:
        await db.delete(obj)
        await db.commit()
    return obj