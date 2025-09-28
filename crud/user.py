from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.user import User
from schemas.user import UserCreate, UserUpdate
from core.security import get_password_hash


async def update_user(db: AsyncSession, orm_model: User, schema: UserUpdate):
    update_data = schema.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["password"] = get_password_hash(update_data["password"])
    for field, value in update_data.items():
        setattr(orm_model, field, value)
    db.add(orm_model)
    await db.commit()
    await db.refresh(orm_model)
    return orm_model


async def get_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()


async def create_user(db: AsyncSession, schema: UserCreate):
    user = User(
        name=schema.name,
        surname=schema.surname,
        email=schema.email,
        telegram_id=schema.telegram_id,
        telegram_id_confirmed=schema.telegram_id_confirmed,
        password=get_password_hash(schema.password),
        photo=schema.photo,
        is_superuser=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def delete_user(db: AsyncSession, user_id: int):
    obj = await get_user(db, user_id)
    if obj:
        await db.delete(obj)
        await db.commit()
    return obj