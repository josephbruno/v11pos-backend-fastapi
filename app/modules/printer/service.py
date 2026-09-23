"""
Receipt printer service layer
"""
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import utc_now_naive
from app.modules.printer.model import PrinterPurpose, ReceiptPrinter
from app.modules.printer.schema import ReceiptPrinterCreate, ReceiptPrinterUpdate


class PrinterService:
    """Service for receipt printer configuration"""

    @staticmethod
    async def upsert_printer(db: AsyncSession, data: ReceiptPrinterCreate) -> ReceiptPrinter:
        existing = await PrinterService.get_by_restaurant_and_purpose(
            db, data.restaurant_id, data.purpose
        )
        if existing:
            for field, value in data.model_dump(exclude={"restaurant_id"}).items():
                setattr(existing, field, value)
            await db.commit()
            await db.refresh(existing)
            return existing

        printer = ReceiptPrinter(**data.model_dump())
        db.add(printer)
        await db.commit()
        await db.refresh(printer)
        return printer

    @staticmethod
    async def get_by_id(db: AsyncSession, printer_id: str) -> Optional[ReceiptPrinter]:
        result = await db.execute(
            select(ReceiptPrinter).where(
                ReceiptPrinter.id == printer_id,
                ReceiptPrinter.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_restaurant_and_purpose(
        db: AsyncSession, restaurant_id: str, purpose: PrinterPurpose
    ) -> Optional[ReceiptPrinter]:
        result = await db.execute(
            select(ReceiptPrinter).where(
                ReceiptPrinter.restaurant_id == restaurant_id,
                ReceiptPrinter.purpose == purpose,
                ReceiptPrinter.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_active(
        db: AsyncSession, restaurant_id: str, purpose: PrinterPurpose
    ) -> Optional[ReceiptPrinter]:
        printer = await PrinterService.get_by_restaurant_and_purpose(db, restaurant_id, purpose)
        if printer and printer.is_active:
            return printer
        return None

    @staticmethod
    async def list_by_restaurant(db: AsyncSession, restaurant_id: str) -> List[ReceiptPrinter]:
        result = await db.execute(
            select(ReceiptPrinter).where(
                ReceiptPrinter.restaurant_id == restaurant_id,
                ReceiptPrinter.deleted_at.is_(None),
            ).order_by(ReceiptPrinter.purpose)
        )
        return list(result.scalars().all())

    @staticmethod
    async def delete_printer(db: AsyncSession, printer_id: str) -> bool:
        printer = await PrinterService.get_by_id(db, printer_id)
        if not printer:
            return False
        printer.deleted_at = utc_now_naive()
        await db.commit()
        return True
