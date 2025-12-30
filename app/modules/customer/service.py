from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional, List
from app.modules.customer.model import Customer
from app.modules.customer.schema import CustomerCreate, CustomerUpdate


class CustomerService:
    """Service layer for customer operations"""
    
    @staticmethod
    async def create_customer(db: AsyncSession, customer_data: CustomerCreate) -> Customer:
        """
        Create a new customer
        
        Args:
            db: Database session
            customer_data: Customer creation data
            
        Returns:
            Created customer
        """
        db_customer = Customer(
            name=customer_data.name,
            email=customer_data.email,
            phone=customer_data.phone,
            address=customer_data.address,
            city=customer_data.city,
            state=customer_data.state,
            postal_code=customer_data.postal_code,
            country=customer_data.country,
            latitude=customer_data.latitude,
            longitude=customer_data.longitude,
            notes=customer_data.notes
        )
        
        db.add(db_customer)
        await db.commit()
        await db.refresh(db_customer)
        
        return db_customer
    
    @staticmethod
    async def get_customer_by_id(db: AsyncSession, customer_id: str) -> Optional[Customer]:
        """
        Get customer by ID
        
        Args:
            db: Database session
            customer_id: Customer ID
            
        Returns:
            Customer if found, None otherwise
        """
        result = await db.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_customer_by_email(db: AsyncSession, email: str) -> Optional[Customer]:
        """
        Get customer by email
        
        Args:
            db: Database session
            email: Customer email
            
        Returns:
            Customer if found, None otherwise
        """
        result = await db.execute(
            select(Customer).where(Customer.email == email)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_customer_by_phone(db: AsyncSession, phone: str) -> Optional[Customer]:
        """
        Get customer by phone
        
        Args:
            db: Database session
            phone: Customer phone number
            
        Returns:
            Customer if found, None otherwise
        """
        result = await db.execute(
            select(Customer).where(Customer.phone == phone)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_customers(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> tuple[List[Customer], int]:
        """
        Get paginated list of customers with optional filtering
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            search: Search term for name, email, or phone
            is_active: Filter by active status
            
        Returns:
            Tuple of (list of customers, total count)
        """
        query = select(Customer)
        
        # Apply filters
        if is_active is not None:
            query = query.where(Customer.is_active == is_active)
        
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Customer.name.ilike(search_pattern),
                    Customer.email.ilike(search_pattern),
                    Customer.phone.ilike(search_pattern)
                )
            )
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()
        
        # Apply pagination and ordering
        query = query.order_by(Customer.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        customers = list(result.scalars().all())
        
        return customers, total
    
    @staticmethod
    async def update_customer(
        db: AsyncSession,
        customer_id: str,
        customer_data: CustomerUpdate
    ) -> Optional[Customer]:
        """
        Update customer
        
        Args:
            db: Database session
            customer_id: Customer ID
            customer_data: Customer update data
            
        Returns:
            Updated customer if found, None otherwise
        """
        customer = await CustomerService.get_customer_by_id(db, customer_id)
        
        if not customer:
            return None
        
        # Update only provided fields
        update_data = customer_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(customer, field, value)
        
        await db.commit()
        await db.refresh(customer)
        
        return customer
    
    @staticmethod
    async def delete_customer(db: AsyncSession, customer_id: str) -> bool:
        """
        Delete customer (soft delete by setting is_active to False)
        
        Args:
            db: Database session
            customer_id: Customer ID
            
        Returns:
            True if customer was deleted, False if not found
        """
        customer = await CustomerService.get_customer_by_id(db, customer_id)
        
        if not customer:
            return False
        
        customer.is_active = False
        await db.commit()
        
        return True
    
    @staticmethod
    async def permanently_delete_customer(db: AsyncSession, customer_id: str) -> bool:
        """
        Permanently delete customer from database
        
        Args:
            db: Database session
            customer_id: Customer ID
            
        Returns:
            True if customer was deleted, False if not found
        """
        customer = await CustomerService.get_customer_by_id(db, customer_id)
        
        if not customer:
            return False
        
        await db.delete(customer)
        await db.commit()
        
        return True
    
    @staticmethod
    async def search_customers_by_location(
        db: AsyncSession,
        latitude: float,
        longitude: float,
        radius_km: float = 10.0,
        limit: int = 100
    ) -> List[Customer]:
        """
        Search customers by proximity to a location
        Note: This is a simple implementation. For production, consider using PostGIS for proper geospatial queries.
        
        Args:
            db: Database session
            latitude: Center latitude
            longitude: Center longitude
            radius_km: Search radius in kilometers
            limit: Maximum number of results
            
        Returns:
            List of customers within the specified radius
        """
        # Simple bounding box calculation (approximate)
        # For production, use PostGIS or similar geospatial extension
        lat_range = radius_km / 111.0  # 1 degree latitude ≈ 111 km
        lon_range = radius_km / (111.0 * abs(float(func.cos(func.radians(latitude)))))
        
        query = select(Customer).where(
            Customer.latitude.between(latitude - lat_range, latitude + lat_range),
            Customer.longitude.between(longitude - lon_range, longitude + lon_range),
            Customer.is_active == True
        ).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
