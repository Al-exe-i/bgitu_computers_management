from collections import defaultdict
from typing import Any

from sqlalchemy import select, func, cast, Integer, Float, Boolean
from sqlalchemy.ext.asyncio import AsyncSession

from models.hardware import Hardware, HardwareType
from models.audience import Audience
from models.office import Office
from schemas.analytics import HardwareAnalyticsFilters


class HardwareAnalyticsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _base_stmt(self):
        return (
            select(
                Hardware,
                Audience.id.label("audience_id"),
                Audience.floor.label("floor"),
                Office.id.label("office_id"),
                Office.address.label("office_address"),
            )
            .join(Audience, Hardware.audience_id == Audience.id)
            .join(Office, Audience.office_id == Office.id)
        )

    @staticmethod
    def _apply_range(stmt, expr, rng):
        if rng is None:
            return stmt
        if rng.gte is not None:
            stmt = stmt.where(expr >= rng.gte)
        if rng.lte is not None:
            stmt = stmt.where(expr <= rng.lte)
        return stmt

    def _apply_filters(self, stmt, filters: HardwareAnalyticsFilters):
        if filters.office_ids:
            stmt = stmt.where(Office.id.in_(filters.office_ids))

        if filters.floors:
            stmt = stmt.where(Audience.floor.in_(filters.floors))

        if filters.audience_ids:
            stmt = stmt.where(Audience.id.in_(filters.audience_ids))

        if filters.states:
            stmt = stmt.where(Hardware.state.in_(filters.states))

        if filters.types:
            stmt = stmt.where(Hardware.type.in_(filters.types))

        # JSONB numeric / boolean filters
        cpu_frequency_expr = cast(Hardware.specs["cpu_frequency_ghz"].astext, Float)
        cpu_cores_expr = cast(Hardware.specs["cpu_cores"].astext, Integer)
        ram_amount_expr = cast(Hardware.specs["ram_amount"].astext, Integer)
        storage_amount_expr = cast(Hardware.specs["storage_amount"].astext, Integer)
        purchase_year_expr = cast(Hardware.specs["purchase_year"].astext, Integer)
        ports_count_expr = cast(Hardware.specs["ports_count"].astext, Integer)
        managed_expr = cast(Hardware.specs["managed"].astext, Boolean)

        stmt = self._apply_range(stmt, cpu_frequency_expr, filters.cpu_frequency_ghz)
        stmt = self._apply_range(stmt, cpu_cores_expr, filters.cpu_cores)
        stmt = self._apply_range(stmt, ram_amount_expr, filters.ram_amount)
        stmt = self._apply_range(stmt, storage_amount_expr, filters.storage_amount)
        stmt = self._apply_range(stmt, purchase_year_expr, filters.purchase_year)
        stmt = self._apply_range(stmt, ports_count_expr, filters.ports_count)

        if filters.managed is not None:
            stmt = stmt.where(managed_expr == filters.managed)

        return stmt

    async def list(self, filters: HardwareAnalyticsFilters):
        stmt = self._apply_filters(self._base_stmt(), filters)
        stmt = stmt.order_by(Office.id, Audience.floor, Audience.id, Hardware.id)
        stmt = stmt.limit(filters.limit).offset(filters.offset)

        result = await self.db.execute(stmt)
        return result.all()

    async def count_total(self, filters: HardwareAnalyticsFilters) -> int:
        stmt = (
            select(func.count(Hardware.id))
            .select_from(Hardware)
            .join(Audience, Hardware.audience_id == Audience.id)
            .join(Office, Audience.office_id == Office.id)
        )
        stmt = self._apply_filters(stmt, filters)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def summary(self, filters: HardwareAnalyticsFilters) -> dict[str, Any]:
        stmt = (
            select(Hardware.type, Hardware.state, func.count(Hardware.id))
            .select_from(Hardware)
            .join(Audience, Hardware.audience_id == Audience.id)
            .join(Office, Audience.office_id == Office.id)
            .group_by(Hardware.type, Hardware.state)
        )
        stmt = self._apply_filters(stmt, filters)

        result = await self.db.execute(stmt)
        rows = result.all()

        total = 0
        working = 0
        broken = 0
        by_type: dict[str, int] = defaultdict(int)

        for hw_type, state, cnt in rows:
            total += cnt
            by_type[hw_type.value] += cnt
            if state:
                working += cnt
            else:
                broken += cnt

        return {
            "total": total,
            "working": working,
            "broken": broken,
            "by_type": dict(by_type),
        }

    async def filter_options(self) -> dict[str, Any]:
        offices_stmt = select(Office.id, Office.address).order_by(Office.id)
        floors_stmt = select(Audience.floor).distinct().order_by(Audience.floor)
        audiences_stmt = select(Audience.id).order_by(Audience.id)

        offices = (await self.db.execute(offices_stmt)).all()
        floors = (await self.db.execute(floors_stmt)).all()
        audiences = (await self.db.execute(audiences_stmt)).all()

        return {
            "offices": [{"value": oid, "label": address} for oid, address in offices],
            "floors": [{"value": floor, "label": str(floor)} for (floor,) in floors],
            "audiences": [{"value": aid, "label": str(aid)} for (aid,) in audiences],
            "states": [
                {"value": True, "label": "Исправен"},
                {"value": False, "label": "Неисправен"},
            ],
            "types": [
                {"value": t.value, "label": t.value}
                for t in HardwareType
            ],
        }