from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.response import error_response, success_response
from app.modules.table_session.schema import TableTransferResponse
from app.modules.table_session.service import (
    TableSessionError,
    TableSessionService,
    TableTransferService,
)
from app.modules.user.model import User

router = APIRouter(prefix="/table-transfers", tags=["Table Transfers"])


@router.get("/restaurant/{restaurant_id}/pending", response_model=None)
async def list_pending_transfers(
    restaurant_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Staff: list pending table transfer requests."""
    transfers, total = await TableTransferService.list_pending_transfers(
        db, restaurant_id, skip=skip, limit=limit
    )
    data = [
        TableTransferResponse(
            id=t.id,
            old_table_uuid=t.old_table_id,
            new_table_uuid=t.new_table_id,
            customer_uuid=t.customer_id,
            restaurant_uuid=t.restaurant_id,
            order_uuid=t.order_id,
            status=t.status.upper(),
            resolved_by=t.resolved_by,
            resolved_at=t.resolved_at,
            audit_log=t.audit_log,
            created_at=t.created_at,
        ).model_dump()
        for t in transfers
    ]
    return success_response(
        message="Pending transfers retrieved",
        data={"transfers": data, "total": total, "skip": skip, "limit": limit},
    )


@router.patch("/{transfer_id}/approve", response_model=None)
async def approve_transfer(
    transfer_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        transfer = await TableTransferService.resolve_transfer(
            db, transfer_id, approve=True, resolved_by=current_user.id
        )
        if not transfer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found")
        return success_response(
            message="Transfer approved",
            data={
                "transfer": TableTransferResponse(
                    id=transfer.id,
                    old_table_uuid=transfer.old_table_id,
                    new_table_uuid=transfer.new_table_id,
                    customer_uuid=transfer.customer_id,
                    restaurant_uuid=transfer.restaurant_id,
                    order_uuid=transfer.order_id,
                    status=transfer.status.upper(),
                    resolved_by=transfer.resolved_by,
                    resolved_at=transfer.resolved_at,
                    audit_log=transfer.audit_log,
                    created_at=transfer.created_at,
                ).model_dump()
            },
        )
    except TableSessionError as e:
        return error_response(
            message=e.message,
            error_code=e.code,
            status_code=e.status_code,
        )


@router.patch("/{transfer_id}/reject", response_model=None)
async def reject_transfer(
    transfer_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        transfer = await TableTransferService.resolve_transfer(
            db, transfer_id, approve=False, resolved_by=current_user.id
        )
        if not transfer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found")
        return success_response(
            message="Transfer rejected",
            data={
                "transfer": TableTransferResponse(
                    id=transfer.id,
                    old_table_uuid=transfer.old_table_id,
                    new_table_uuid=transfer.new_table_id,
                    customer_uuid=transfer.customer_id,
                    restaurant_uuid=transfer.restaurant_id,
                    order_uuid=transfer.order_id,
                    status=transfer.status.upper(),
                    resolved_by=transfer.resolved_by,
                    resolved_at=transfer.resolved_at,
                    audit_log=transfer.audit_log,
                    created_at=transfer.created_at,
                ).model_dump()
            },
        )
    except TableSessionError as e:
        return error_response(
            message=e.message,
            error_code=e.code,
            status_code=e.status_code,
        )
