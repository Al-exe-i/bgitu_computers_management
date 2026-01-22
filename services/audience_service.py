from fastapi import HTTPException
from core.exceptions import HTTP404
from models import Hardware, Audience
from repositories.audience_repo import AudienceRepository
from repositories.hardware_repo import HardwareRepository
from schemas.audience import AudienceCreate, AudienceUpdate
from websocket.routes import manager


class AudienceService:
    def __init__(self, repo: AudienceRepository, hardware_repo: HardwareRepository):
        self.repo = repo
        self.hardware_repo = hardware_repo

    async def get_list(self):
        return await self.repo.get_all()

    async def get_one(self, audience_id: int):
        audience = await self.repo.get_by_id(audience_id)
        if not audience:
            raise HTTP404("Audience not found")
        return audience

    async def create_audience(self, schema: AudienceCreate):
        if await self.repo.get_by_id(schema.id):
            raise HTTPException(status_code=409, detail="Audience already exists")
        audience_data = schema.model_dump(exclude={'hardware'})

        hardware_orm_list = [
            Hardware(**hw.model_dump()) for hw in schema.hardware
        ]

        audience_orm = Audience(
            **audience_data,
            hardware=hardware_orm_list
        )

        return await self.repo.create(audience_orm)

    async def update_audience(self, audience_id: int, schema: AudienceUpdate):
        # 1. Проверяем существование
        current_audience = await self.repo.get_by_id(audience_id)
        if not current_audience:
            raise HTTPException(status_code=404, detail="Audience not found")

        # 2. Обновляем поля самой аудитории
        update_data = schema.model_dump(exclude_unset=True, exclude={'hardware'})

        # Если есть поля для обновления
        if update_data:
            for key, value in update_data.items():
                setattr(current_audience, key, value)
            await self.repo.session.commit()

        # 3. Синхронизируем сетку оборудования (если она пришла)
        if schema.hardware is not None:
            await self._sync_grid(audience_id, schema.hardware)

        # 4. Уведомляем всех через WebSocket, что аудитория изменилась
        await manager.broadcast({"audience_updated": audience_id})

        await self.repo.session.refresh(current_audience)
        return current_audience

    async def _sync_grid(self, audience_id: int, incoming_hardware_list: list):
        """
        Умная синхронизация:
        1. Если пришел ID, тогда обновляем координаты (перемещение).
        2. Если ID нет, то создаем новое.
        3. Если в БД есть ID, которого нет во входящем списке, то удаляем.
        """
        # Получаем всё текущее оборудование из БД
        existing_hw_list = await self.hardware_repo.get_by_audience_id(audience_id)

        # Создаем словарь: { id_оборудования: объект_БД }
        existing_map: dict[int, Hardware] = {hw.id: hw for hw in existing_hw_list}

        # Сюда будем складывать ID, которые мы обработали (обновили или создали)
        processed_ids = set()

        for item in incoming_hardware_list:
            # Первый случай: Перемещение существующего (пришел ID и он есть в базе)
            if item.id is not None and item.id in existing_map:
                db_item = existing_map[item.id]

                # Обновляем координаты и состояние
                db_item.x = item.x
                db_item.y = item.y
                db_item.type = item.type
                # Если с фронта приходят state/inv_number, обновляем и их
                if item.state is not None:
                    db_item.state = item.state

                processed_ids.add(item.id)

            # Второй случай: Создание нового (ID нет или он фейковый/не найден)
            else:
                new_hw = Hardware(
                    **item.model_dump(exclude={'id'}),  # Исключаем ID, пусть БД генерирует новый
                    audience_id=audience_id
                )
                await self.hardware_repo.create(new_hw)

        # Третий случай: Удаление (то, что было в БД, но не пришло с фронта)
        for hw_id, hw in existing_map.items():
            if hw_id not in processed_ids:
                # Это оборудование удалили с сетки, тогда удаляем из БД (каскадно удалятся файлы)
                await self.hardware_repo.delete(hw_id)

        await self.repo.session.commit()

    async def delete_audience(self, audience_id: int):
        await self.get_one(audience_id)
        await self.repo.delete(audience_id)



