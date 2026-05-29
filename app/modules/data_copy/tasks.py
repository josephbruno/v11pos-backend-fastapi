from __future__ import annotations

import asyncio

from app.core.celery_app import celery_app
from app.core.database import AsyncSessionLocal, close_db
from app.modules.data_copy.service import DataCopyService

# Ensure relationship targets are registered when the worker runs without app.main.
from app.modules.auth import model as _auth_model  # noqa: F401
from app.modules.cart import model as _cart_model  # noqa: F401
from app.modules.customer import model as _customer_model  # noqa: F401
from app.modules.customer_auth import model as _customer_auth_model  # noqa: F401
from app.modules.data_copy import model as _data_copy_model  # noqa: F401
from app.modules.data_import import model as _data_import_model  # noqa: F401
from app.modules.homebanner import model as _homebanner_model  # noqa: F401
from app.modules.inventory import model as _inventory_model  # noqa: F401
from app.modules.kds import model as _kds_model  # noqa: F401
from app.modules.order import model as _order_model  # noqa: F401
from app.modules.payment import model as _payment_model  # noqa: F401
from app.modules.payment_gateway import model as _payment_gateway_model  # noqa: F401
from app.modules.product import model as _product_model  # noqa: F401
from app.modules.reports import model as _reports_model  # noqa: F401
from app.modules.restaurant import model as _restaurant_model  # noqa: F401
from app.modules.row_management import model as _row_management_model  # noqa: F401
from app.modules.staff import model as _staff_model  # noqa: F401
from app.modules.table import model as _table_model  # noqa: F401
from app.modules.user import model as _user_model  # noqa: F401


@celery_app.task(name="data_copy.run", queue="data_copy", bind=True)
def run_data_copy(self, copy_id: str) -> dict:
    """Run a single restaurant data-copy operation in the Celery worker."""
    return asyncio.run(_run_data_copy(copy_id, self.request.id))


async def _run_data_copy(copy_id: str, task_id: str | None) -> dict:
    async with AsyncSessionLocal() as db:
        operation = await DataCopyService.get_copy_by_id(db, copy_id)
        if operation:
            operation.copy_metadata = {
                **(operation.copy_metadata or {}),
                "celery_task_id": task_id,
            }
            await db.commit()

        status = await DataCopyService.process_copy_operation(db, copy_id)

    await close_db()
    return {"copy_id": copy_id, "status": status}
