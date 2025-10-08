from typing import List

from sqlalchemy.future import select

from db.session import session_dep
from schemas.additional_hardware import AdditionalHardwareCreate, AdditionalHardwareUpdate
from models.additional_hardware import AdditionalHardware


async def create_hardware(db: session_dep, hardware_data: AdditionalHardwareCreate) -> AdditionalHardware:
    db_hardware = AdditionalHardware(**hardware_data.model_dump())
    db.add(db_hardware)
    await db.commit()
    await db.refresh(db_hardware)
    return db_hardware


async def get_hardware_by_audience(db: session_dep, audience_id: int) -> List[AdditionalHardware]:
    result = await db.execute(
        select(AdditionalHardware)
        .where(AdditionalHardware.audience_id == audience_id)
    )
    return result.scalars().all()


async def update_hardware(db: session_dep, hardware_id: int, hardware_data: AdditionalHardwareUpdate) -> AdditionalHardware | None:
    result = await db.execute(
        select(AdditionalHardware).where(AdditionalHardware.id == hardware_id)
    )
    hardware = result.scalars().first()

    if not hardware:
        return None

    update_data = hardware_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(hardware, field, value)

    await db.commit()
    await db.refresh(hardware)
    return hardware


async def delete_hardware(db: session_dep, hardware_id: int) -> bool:
    result = await db.execute(
        select(AdditionalHardware).where(AdditionalHardware.id == hardware_id)
    )
    hardware = result.scalars().first()

    if not hardware:
        return False

    await db.delete(hardware)
    await db.commit()
    return True


async def delete_all_hardware(db: session_dep, audience_id: int) -> bool:
    result = await db.execute(
        select(AdditionalHardware).where(AdditionalHardware.audience_id == audience_id)
    )
    hardware = result.scalars().all()

    if not hardware:
        return False

    for h_ware in hardware:
        await db.delete(h_ware)

    await db.commit()
    return True