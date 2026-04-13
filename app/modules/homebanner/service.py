"""
Home banner service layer
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.homebanner.model import HomeBanner
from app.modules.homebanner.schema import HomeBannerCreate, HomeBannerUpdate


class DuplicateError(Exception):
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(message)


class HomeBannerService:
    """Service for home banner operations"""

    @staticmethod
    async def create_banner(db: AsyncSession, banner_data: HomeBannerCreate) -> HomeBanner:
        stmt = select(HomeBanner).where(
            HomeBanner.restaurant_id == banner_data.restaurant_id,
            func.lower(HomeBanner.title) == func.lower(banner_data.title),
            HomeBanner.deleted_at.is_(None),
        )
        if await db.scalar(stmt):
            raise DuplicateError("Home banner with this title already exists in this restaurant", field="title")

        banner = HomeBanner(**banner_data.model_dump())
        db.add(banner)
        await db.commit()
        await db.refresh(banner)
        return banner

    @staticmethod
    async def get_banner_by_id(db: AsyncSession, banner_id: str) -> Optional[HomeBanner]:
        result = await db.execute(
            select(HomeBanner).where(
                HomeBanner.id == banner_id,
                HomeBanner.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_banners_by_restaurant(
        db: AsyncSession,
        restaurant_id: str,
        active_only: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> List[HomeBanner]:
        query = select(HomeBanner).where(
            HomeBanner.restaurant_id == restaurant_id,
            HomeBanner.deleted_at.is_(None),
        )
        if active_only:
            query = query.where(HomeBanner.active == True)

        query = query.order_by(HomeBanner.sort_order, HomeBanner.title).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def update_banner(
        db: AsyncSession,
        banner_id: str,
        banner_data: HomeBannerUpdate,
    ) -> Optional[HomeBanner]:
        banner = await HomeBannerService.get_banner_by_id(db, banner_id)
        if not banner:
            return None

        if banner_data.title:
            stmt = select(HomeBanner).where(
                HomeBanner.restaurant_id == banner.restaurant_id,
                HomeBanner.id != banner_id,
                func.lower(HomeBanner.title) == func.lower(banner_data.title),
                HomeBanner.deleted_at.is_(None),
            )
            if await db.scalar(stmt):
                raise DuplicateError("Home banner with this title already exists in this restaurant", field="title")

        update_data = banner_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(banner, field, value)

        if (
            "mobile_image" in update_data or "desktop_image" in update_data
        ) and not banner.mobile_image and not banner.desktop_image:
            raise ValueError("At least one of mobile_image or desktop_image is required")

        await db.commit()
        await db.refresh(banner)
        return banner

    @staticmethod
    async def delete_banner(db: AsyncSession, banner_id: str) -> bool:
        banner = await HomeBannerService.get_banner_by_id(db, banner_id)
        if not banner:
            return False

        banner.deleted_at = datetime.utcnow()
        await db.commit()
        return True
