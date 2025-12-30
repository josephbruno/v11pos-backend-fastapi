from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import Optional, List
from app.modules.table.model import Table, TableStatus
from app.modules.table.schema import TableCreate, TableUpdate


class TableService:
    """Service layer for table operations"""
    
    @staticmethod
    async def create_table(db: AsyncSession, table_data: TableCreate) -> Table:
        """
        Create a new table for a restaurant
        
        Args:
            db: Database session
            table_data: Table creation data
            
        Returns:
            Created table
        """
        db_table = Table(
            restaurant_id=table_data.restaurant_id,
            table_number=table_data.table_number,
            table_name=table_data.table_name,
            capacity=table_data.capacity,
            min_capacity=table_data.min_capacity,
            floor=table_data.floor,
            section=table_data.section,
            position_x=table_data.position_x,
            position_y=table_data.position_y,
            image=table_data.image,
            qr_code=table_data.qr_code,
            status=table_data.status or TableStatus.AVAILABLE,
            is_bookable=table_data.is_bookable if table_data.is_bookable is not None else True,
            is_outdoor=table_data.is_outdoor or False,
            is_accessible=table_data.is_accessible if table_data.is_accessible is not None else True,
            has_power_outlet=table_data.has_power_outlet or False,
            minimum_spend=table_data.minimum_spend,
            description=table_data.description,
            notes=table_data.notes
        )
        
        db.add(db_table)
        await db.commit()
        await db.refresh(db_table)
        
        return db_table
    
    @staticmethod
    async def get_table_by_id(db: AsyncSession, table_id: str) -> Optional[Table]:
        """
        Get table by ID
        
        Args:
            db: Database session
            table_id: Table ID
            
        Returns:
            Table if found, None otherwise
        """
        result = await db.execute(
            select(Table).where(Table.id == table_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_table_by_number(
        db: AsyncSession,
        restaurant_id: str,
        table_number: str
    ) -> Optional[Table]:
        """
        Get table by table number within a restaurant
        
        Args:
            db: Database session
            restaurant_id: Restaurant ID
            table_number: Table number
            
        Returns:
            Table if found, None otherwise
        """
        result = await db.execute(
            select(Table).where(
                and_(
                    Table.restaurant_id == restaurant_id,
                    Table.table_number == table_number
                )
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_tables(
        db: AsyncSession,
        restaurant_id: str,
        skip: int = 0,
        limit: int = 100,
        status: Optional[TableStatus] = None,
        floor: Optional[str] = None,
        section: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_bookable: Optional[bool] = None,
        min_capacity: Optional[int] = None
    ) -> tuple[List[Table], int]:
        """
        Get paginated list of tables for a restaurant with optional filtering
        
        Args:
            db: Database session
            restaurant_id: Restaurant ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Filter by table status
            floor: Filter by floor
            section: Filter by section
            is_active: Filter by active status
            is_bookable: Filter by bookable status
            min_capacity: Filter by minimum capacity
            
        Returns:
            Tuple of (list of tables, total count)
        """
        query = select(Table).where(Table.restaurant_id == restaurant_id)
        
        # Apply filters
        if status is not None:
            query = query.where(Table.status == status)
        
        if floor is not None:
            query = query.where(Table.floor == floor)
        
        if section is not None:
            query = query.where(Table.section == section)
        
        if is_active is not None:
            query = query.where(Table.is_active == is_active)
        
        if is_bookable is not None:
            query = query.where(Table.is_bookable == is_bookable)
        
        if min_capacity is not None:
            query = query.where(Table.capacity >= min_capacity)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()
        
        # Apply pagination and ordering
        query = query.order_by(Table.table_number.asc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        tables = list(result.scalars().all())
        
        return tables, total
    
    @staticmethod
    async def get_available_tables(
        db: AsyncSession,
        restaurant_id: str,
        capacity: Optional[int] = None
    ) -> List[Table]:
        """
        Get available tables for a restaurant, optionally filtered by capacity
        
        Args:
            db: Database session
            restaurant_id: Restaurant ID
            capacity: Minimum capacity required
            
        Returns:
            List of available tables
        """
        query = select(Table).where(
            and_(
                Table.restaurant_id == restaurant_id,
                Table.status == TableStatus.AVAILABLE,
                Table.is_active == True
            )
        )
        
        if capacity is not None:
            query = query.where(Table.capacity >= capacity)
        
        query = query.order_by(Table.capacity.asc(), Table.table_number.asc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def update_table(
        db: AsyncSession,
        table_id: str,
        table_data: TableUpdate
    ) -> Optional[Table]:
        """
        Update table
        
        Args:
            db: Database session
            table_id: Table ID
            table_data: Table update data
            
        Returns:
            Updated table if found, None otherwise
        """
        table = await TableService.get_table_by_id(db, table_id)
        
        if not table:
            return None
        
        # Update only provided fields
        update_data = table_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(table, field, value)
        
        await db.commit()
        await db.refresh(table)
        
        return table
    
    @staticmethod
    async def update_table_status(
        db: AsyncSession,
        table_id: str,
        status: TableStatus
    ) -> Optional[Table]:
        """
        Update table status
        
        Args:
            db: Database session
            table_id: Table ID
            status: New table status
            
        Returns:
            Updated table if found, None otherwise
        """
        table = await TableService.get_table_by_id(db, table_id)
        
        if not table:
            return None
        
        table.status = status
        await db.commit()
        await db.refresh(table)
        
        return table
    
    @staticmethod
    async def delete_table(db: AsyncSession, table_id: str) -> bool:
        """
        Delete table (soft delete by setting is_active to False)
        
        Args:
            db: Database session
            table_id: Table ID
            
        Returns:
            True if table was deleted, False if not found
        """
        table = await TableService.get_table_by_id(db, table_id)
        
        if not table:
            return False
        
        table.is_active = False
        await db.commit()
        
        return True
    
    @staticmethod
    async def permanently_delete_table(db: AsyncSession, table_id: str) -> bool:
        """
        Permanently delete table from database
        
        Args:
            db: Database session
            table_id: Table ID
            
        Returns:
            True if table was deleted, False if not found
        """
        table = await TableService.get_table_by_id(db, table_id)
        
        if not table:
            return False
        
        await db.delete(table)
        await db.commit()
        
        return True
    
    @staticmethod
    async def get_table_statistics(
        db: AsyncSession,
        restaurant_id: str
    ) -> dict:
        """
        Get statistics for tables in a restaurant
        
        Args:
            db: Database session
            restaurant_id: Restaurant ID
            
        Returns:
            Dictionary with table statistics
        """
        # Total tables
        total_query = select(func.count()).select_from(Table).where(
            and_(
                Table.restaurant_id == restaurant_id,
                Table.is_active == True
            )
        )
        total_result = await db.execute(total_query)
        total = total_result.scalar_one()
        
        # Available tables
        available_query = select(func.count()).select_from(Table).where(
            and_(
                Table.restaurant_id == restaurant_id,
                Table.status == TableStatus.AVAILABLE,
                Table.is_active == True
            )
        )
        available_result = await db.execute(available_query)
        available = available_result.scalar_one()
        
        # Occupied tables
        occupied_query = select(func.count()).select_from(Table).where(
            and_(
                Table.restaurant_id == restaurant_id,
                Table.status == TableStatus.OCCUPIED,
                Table.is_active == True
            )
        )
        occupied_result = await db.execute(occupied_query)
        occupied = occupied_result.scalar_one()
        
        # Reserved tables
        reserved_query = select(func.count()).select_from(Table).where(
            and_(
                Table.restaurant_id == restaurant_id,
                Table.status == TableStatus.RESERVED,
                Table.is_active == True
            )
        )
        reserved_result = await db.execute(reserved_query)
        reserved = reserved_result.scalar_one()
        
        # Total capacity
        capacity_query = select(func.sum(Table.capacity)).where(
            and_(
                Table.restaurant_id == restaurant_id,
                Table.is_active == True
            )
        )
        capacity_result = await db.execute(capacity_query)
        total_capacity = capacity_result.scalar_one() or 0
        
        return {
            "total_tables": total,
            "available_tables": available,
            "occupied_tables": occupied,
            "reserved_tables": reserved,
            "total_capacity": total_capacity,
            "occupancy_rate": round((occupied / total * 100), 2) if total > 0 else 0
        }
    
    @staticmethod
    async def bulk_update_status(
        db: AsyncSession,
        table_ids: List[str],
        status: TableStatus
    ) -> int:
        """
        Bulk update status for multiple tables
        
        Args:
            db: Database session
            table_ids: List of table IDs
            status: New status
            
        Returns:
            Number of tables updated
        """
        count = 0
        for table_id in table_ids:
            table = await TableService.get_table_by_id(db, table_id)
            if table:
                table.status = status
                count += 1
        
        await db.commit()
        return count
