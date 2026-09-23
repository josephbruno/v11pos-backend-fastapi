"""
Receipt printer API routes
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.response import error_response, success_response
from app.modules.printer.model import PrinterPurpose
from app.modules.printer.schema import (
    ReceiptPrinterActiveResponse,
    ReceiptPrinterCreate,
    ReceiptPrinterResponse,
)
from app.modules.printer.service import PrinterService
from app.modules.user.model import User

router = APIRouter(prefix="/printers", tags=["Printers"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def upsert_printer(
    payload: ReceiptPrinterCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create or update the printer registered for a restaurant/purpose"""
    try:
        printer = await PrinterService.upsert_printer(db, payload)
        return success_response(
            message="Printer saved successfully",
            data=ReceiptPrinterResponse.from_model(printer).model_dump(),
            status_code=status.HTTP_201_CREATED,
        )
    except Exception as e:
        return error_response(
            message="Failed to save printer",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


@router.get("/restaurant/{restaurant_id}")
async def list_printers(
    restaurant_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List printers registered for a restaurant (token masked)"""
    try:
        printers = await PrinterService.list_by_restaurant(db, restaurant_id)
        return success_response(
            message="Printers retrieved successfully",
            data=[ReceiptPrinterResponse.from_model(p).model_dump() for p in printers],
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve printers",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


@router.get("/restaurant/{restaurant_id}/active/{purpose}")
async def get_active_printer(
    restaurant_id: str,
    purpose: PrinterPurpose,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the active printer config for a restaurant/purpose, including the
    real printer_token. Used right before printing, when the frontend needs
    to call the local print-bridge (printer_url) directly.
    """
    try:
        printer = await PrinterService.get_active(db, restaurant_id, purpose)
        if not printer:
            return error_response(
                message="No active printer configured",
                error_code="NOT_FOUND",
                error_details=f"No active {purpose.value} printer for restaurant {restaurant_id}",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return success_response(
            message="Active printer retrieved successfully",
            data=ReceiptPrinterActiveResponse.model_validate(printer).model_dump(),
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve active printer",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


@router.delete("/{printer_id}")
async def delete_printer(
    printer_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a registered printer"""
    try:
        deleted = await PrinterService.delete_printer(db, printer_id)
        if not deleted:
            return error_response(
                message="Printer not found",
                error_code="NOT_FOUND",
                error_details=f"Printer with ID {printer_id} not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return success_response(
            message="Printer deleted successfully",
            data={"id": printer_id},
        )
    except Exception as e:
        return error_response(
            message="Failed to delete printer",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )
