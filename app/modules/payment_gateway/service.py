from __future__ import annotations

from typing import Optional

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.payment_gateway.model import PaymentGateway, PaymentGatewayProvider
from app.modules.payment_gateway.schema import PaymentGatewayCreate, PaymentGatewayUpdate
from app.modules.restaurant.model import Restaurant


class PaymentGatewayService:
    @staticmethod
    async def restaurant_exists(db: AsyncSession, restaurant_id: str) -> bool:
        result = await db.execute(select(Restaurant.id).where(Restaurant.id == restaurant_id))
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def get_by_id(db: AsyncSession, gateway_id: str) -> Optional[PaymentGateway]:
        result = await db.execute(select(PaymentGateway).where(PaymentGateway.id == gateway_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_provider(
        db: AsyncSession,
        restaurant_id: str,
        provider: PaymentGatewayProvider,
    ) -> Optional[PaymentGateway]:
        result = await db.execute(
            select(PaymentGateway).where(
                and_(
                    PaymentGateway.restaurant_id == restaurant_id,
                    PaymentGateway.provider == provider,
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_restaurant(
        db: AsyncSession,
        restaurant_id: str,
        skip: int = 0,
        limit: int = 100,
        provider: Optional[PaymentGatewayProvider] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[PaymentGateway], int]:
        query = select(PaymentGateway).where(PaymentGateway.restaurant_id == restaurant_id)

        if provider is not None:
            query = query.where(PaymentGateway.provider == provider)
        if is_active is not None:
            query = query.where(PaymentGateway.is_active == is_active)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        query = (
            query.order_by(PaymentGateway.is_default.desc(), PaymentGateway.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all()), total

    @staticmethod
    async def create_gateway(
        db: AsyncSession,
        data: PaymentGatewayCreate,
        created_by: Optional[str] = None,
    ) -> Optional[PaymentGateway]:
        if not await PaymentGatewayService.restaurant_exists(db, data.restaurant_id):
            return None

        if data.is_default:
            await PaymentGatewayService._clear_default(db, data.restaurant_id)

        gateway = PaymentGateway(
            **data.model_dump(),
            created_by=created_by,
            updated_by=created_by,
        )
        db.add(gateway)

        await db.commit()
        await db.refresh(gateway)
        return gateway

    @staticmethod
    async def update_gateway(
        db: AsyncSession,
        gateway_id: str,
        data: PaymentGatewayUpdate,
        updated_by: Optional[str] = None,
    ) -> Optional[PaymentGateway]:
        gateway = await PaymentGatewayService.get_by_id(db, gateway_id)
        if not gateway:
            return None

        patch = data.model_dump(exclude_unset=True)
        will_be_default = patch.get("is_default") is True

        for key, value in patch.items():
            setattr(gateway, key, value)
        gateway.updated_by = updated_by

        if will_be_default:
            await PaymentGatewayService._clear_default(db, gateway.restaurant_id, except_gateway_id=gateway.id)

        await db.commit()
        await db.refresh(gateway)
        return gateway

    @staticmethod
    async def delete_gateway(db: AsyncSession, gateway_id: str) -> bool:
        gateway = await PaymentGatewayService.get_by_id(db, gateway_id)
        if not gateway:
            return False

        await db.delete(gateway)
        await db.commit()
        return True

    @staticmethod
    async def set_default(
        db: AsyncSession,
        gateway_id: str,
        updated_by: Optional[str] = None,
    ) -> Optional[PaymentGateway]:
        gateway = await PaymentGatewayService.get_by_id(db, gateway_id)
        if not gateway:
            return None

        await PaymentGatewayService._clear_default(db, gateway.restaurant_id, except_gateway_id=gateway.id)
        gateway.is_default = True
        gateway.updated_by = updated_by
        await db.commit()
        await db.refresh(gateway)
        return gateway

    @staticmethod
    async def _clear_default(
        db: AsyncSession,
        restaurant_id: str,
        except_gateway_id: Optional[str] = None,
    ) -> None:
        statement = (
            update(PaymentGateway)
            .where(PaymentGateway.restaurant_id == restaurant_id)
            .values(is_default=False)
        )
        if except_gateway_id:
            statement = statement.where(PaymentGateway.id != except_gateway_id)
        await db.execute(statement)
