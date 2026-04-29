from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List
from app.modules.customer.model import Customer, CustomerAddress
from app.modules.customer.schema import (
    CustomerCreate,
    CustomerUpdate,
    CustomerAddressCreate,
    CustomerAddressUpdate,
)


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
            notes=customer_data.notes,
            is_active=customer_data.is_active
        )
        
        db.add(db_customer)
        await db.commit()
        await db.refresh(db_customer)

        # Backward-compatible: if legacy address fields were provided, also create a default address record
        await CustomerService.ensure_customer_default_address_from_legacy_fields(db, db_customer)

        # Reload with addresses eager-loaded (avoid async lazy-load issues in response serialization)
        customer = await CustomerService.get_customer_by_id(db, db_customer.id)
        return customer or db_customer
    
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
            select(Customer)
            .options(selectinload(Customer.addresses))
            .where(Customer.id == customer_id)
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
            select(Customer)
            .options(selectinload(Customer.addresses))
            .where(Customer.email == email)
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
            select(Customer)
            .options(selectinload(Customer.addresses))
            .where(Customer.phone == phone)
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
        query = select(Customer).options(selectinload(Customer.addresses))
        
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
    async def get_customer_address_by_id(
        db: AsyncSession, customer_id: str, address_id: str
    ) -> Optional[CustomerAddress]:
        result = await db.execute(
            select(CustomerAddress).where(
                CustomerAddress.customer_id == customer_id,
                CustomerAddress.id == address_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_customer_addresses(
        db: AsyncSession, customer_id: str, include_inactive: bool = False
    ) -> List[CustomerAddress]:
        query = select(CustomerAddress).where(CustomerAddress.customer_id == customer_id)
        if not include_inactive:
            query = query.where(CustomerAddress.is_active == True)
        query = query.order_by(CustomerAddress.is_default.desc(), CustomerAddress.created_at.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def _unset_other_default_addresses(db: AsyncSession, customer_id: str, keep_address_id: str) -> None:
        result = await db.execute(
            select(CustomerAddress).where(
                CustomerAddress.customer_id == customer_id,
                CustomerAddress.id != keep_address_id,
                CustomerAddress.is_default == True,
            )
        )
        others = list(result.scalars().all())
        for addr in others:
            addr.is_default = False

    @staticmethod
    async def add_customer_address(
        db: AsyncSession,
        customer_id: str,
        payload: CustomerAddressCreate,
    ) -> CustomerAddress:
        address = CustomerAddress(
            customer_id=customer_id,
            label=payload.label,
            address=payload.address,
            city=payload.city,
            state=payload.state,
            postal_code=payload.postal_code,
            country=payload.country,
            latitude=payload.latitude,
            longitude=payload.longitude,
            is_default=payload.is_default,
            is_active=payload.is_active,
        )
        db.add(address)
        await db.flush()

        if address.is_default:
            await CustomerService._unset_other_default_addresses(db, customer_id, address.id)

        await db.commit()
        await db.refresh(address)
        return address

    @staticmethod
    async def update_customer_address(
        db: AsyncSession,
        customer_id: str,
        address_id: str,
        payload: CustomerAddressUpdate,
    ) -> Optional[CustomerAddress]:
        address = await CustomerService.get_customer_address_by_id(db, customer_id, address_id)
        if not address:
            return None

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(address, field, value)

        if update_data.get("is_default") is True:
            await CustomerService._unset_other_default_addresses(db, customer_id, address.id)

        await db.commit()
        await db.refresh(address)
        return address

    @staticmethod
    async def delete_customer_address(db: AsyncSession, customer_id: str, address_id: str) -> bool:
        address = await CustomerService.get_customer_address_by_id(db, customer_id, address_id)
        if not address:
            return False
        await db.delete(address)
        await db.commit()
        return True

    @staticmethod
    async def ensure_customer_default_address_from_legacy_fields(db: AsyncSession, customer: Customer) -> None:
        """
        If the customer has legacy address fields but no addresses, create a default address entry.
        Keeps the legacy fields intact for backward compatibility.
        """
        if customer.addresses:
            return
        if not (customer.address or customer.city or customer.state or customer.postal_code or customer.country):
            return

        address = CustomerAddress(
            customer_id=customer.id,
            label="Primary",
            address=customer.address,
            city=customer.city,
            state=customer.state,
            postal_code=customer.postal_code,
            country=customer.country,
            latitude=customer.latitude,
            longitude=customer.longitude,
            is_default=True,
            is_active=True,
        )
        db.add(address)
        await db.commit()
    
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
        # Reload with addresses eager-loaded (avoid async lazy-load issues in response serialization)
        updated = await CustomerService.get_customer_by_id(db, customer_id)
        return updated
    
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
