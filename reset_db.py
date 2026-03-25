import asyncio
import sys
import os
from sqlalchemy import text

# Add current dir to sys.path
sys.path.append(os.getcwd())

from app.core.database import engine, Base

# Import all models
from app.modules.user.model import User
from app.modules.auth.model import LoginLog
from app.modules.restaurant.model import (
    Restaurant,
    RestaurantOwner,
    SubscriptionPlan,
    Subscription,
    Invoice,
    RestaurantInvitation
)
from app.modules.product.model import (
    Category,
    Product,
    Modifier,
    ModifierOption,
    ProductModifier,
    ComboProduct,
    ComboItem,
    InventoryTransaction,
    CategoryTranslation,
    ProductTranslation,
    ModifierTranslation,
    ModifierOptionTranslation,
    ComboProductTranslation
)

async def reset():
    async with engine.begin() as conn:
        print("Dropping all tables...")
        await conn.run_sync(Base.metadata.drop_all)
        print("Dropping alembic_version...")
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
        print("Tables dropped.")

if __name__ == "__main__":
    asyncio.run(reset())
