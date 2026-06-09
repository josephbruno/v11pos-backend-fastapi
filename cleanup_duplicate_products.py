"""One-off cleanup: remove duplicate products per restaurant (same name)."""
import argparse
import asyncio

from app.core.database import AsyncSessionLocal
from app.modules.product.service import ProductService


async def main() -> None:
    parser = argparse.ArgumentParser(description="Remove duplicate products by restaurant + name")
    parser.add_argument(
        "--restaurant-id",
        help="Limit cleanup to one restaurant (default: all restaurants)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report duplicates without deleting",
    )
    args = parser.parse_args()

    async with AsyncSessionLocal() as db:
        result = await ProductService.remove_duplicate_products(
            db,
            restaurant_id=args.restaurant_id,
            dry_run=args.dry_run,
        )
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
