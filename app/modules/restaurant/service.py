from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from datetime import datetime, timedelta
import secrets
import uuid

from app.modules.restaurant.model import (
    Restaurant,
    RestaurantOwner,
    SubscriptionPlan,
    Subscription,
    Invoice,
    RestaurantInvitation,
    SubscriptionPlanType,
    SubscriptionStatus,
    InvoiceStatus
)
from app.modules.restaurant.schema import (
    RestaurantCreate,
    RestaurantUpdate,
    SubscriptionPlanCreate,
    SubscriptionPlanUpdate,
    SubscriptionCreate,
    SubscriptionUpdate,
    InvoiceCreate,
    RestaurantInvitationCreate
)


class RestaurantService:
    """Service layer for restaurant operations"""
    
    @staticmethod
    async def create_restaurant(
        db: AsyncSession,
        restaurant_data: RestaurantCreate,
        owner_user_id: str
    ) -> Restaurant:
        """
        Create a new restaurant and link owner
        
        Args:
            db: Database session
            restaurant_data: Restaurant creation data
            owner_user_id: User ID of the owner
            
        Returns:
            Created restaurant
        """
        # Create restaurant
        restaurant = Restaurant(
            id=str(uuid.uuid4()),
            name=restaurant_data.name,
            slug=restaurant_data.slug,
            business_name=restaurant_data.business_name,
            business_type=restaurant_data.business_type,
            cuisine_type=restaurant_data.cuisine_type,
            description=restaurant_data.description,
            email=restaurant_data.email,
            phone=restaurant_data.phone,
            alternate_phone=restaurant_data.alternate_phone,
            address=restaurant_data.address,
            city=restaurant_data.city,
            state=restaurant_data.state,
            country=restaurant_data.country,
            postal_code=restaurant_data.postal_code,
            gstin=restaurant_data.gstin,
            fssai_license=restaurant_data.fssai_license,
            pan_number=restaurant_data.pan_number,
            timezone=restaurant_data.timezone,
            currency=restaurant_data.currency,
            language=restaurant_data.language,
            enable_gst=restaurant_data.enable_gst,
            cgst_rate=restaurant_data.cgst_rate,
            sgst_rate=restaurant_data.sgst_rate,
            igst_rate=restaurant_data.igst_rate,
            service_charge_percentage=restaurant_data.service_charge_percentage,
            trial_ends_at=datetime.utcnow() + timedelta(days=14)
        )
        
        db.add(restaurant)
        await db.flush()
        
        # Create owner relationship
        owner = RestaurantOwner(
            id=str(uuid.uuid4()),
            restaurant_id=restaurant.id,
            user_id=owner_user_id,
            role='owner'
        )
        db.add(owner)
        
        await db.commit()
        await db.refresh(restaurant)
        
        return restaurant
    
    @staticmethod
    async def get_restaurant_by_id(db: AsyncSession, restaurant_id: str) -> Optional[Restaurant]:
        """Get restaurant by ID"""
        result = await db.execute(
            select(Restaurant).where(
                and_(
                    Restaurant.id == restaurant_id,
                    Restaurant.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_restaurant_by_slug(db: AsyncSession, slug: str) -> Optional[Restaurant]:
        """Get restaurant by slug"""
        result = await db.execute(
            select(Restaurant).where(
                and_(
                    Restaurant.slug == slug,
                    Restaurant.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_restaurants(
        db: AsyncSession,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Restaurant]:
        """Get all restaurants owned by a user"""
        result = await db.execute(
            select(Restaurant)
            .join(RestaurantOwner)
            .where(
                and_(
                    RestaurantOwner.user_id == user_id,
                    RestaurantOwner.is_active == True,
                    Restaurant.deleted_at.is_(None)
                )
            )
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def update_restaurant(
        db: AsyncSession,
        restaurant_id: str,
        restaurant_data: RestaurantUpdate
    ) -> Optional[Restaurant]:
        """Update restaurant"""
        result = await db.execute(
            select(Restaurant).where(Restaurant.id == restaurant_id)
        )
        restaurant = result.scalar_one_or_none()
        
        if not restaurant:
            return None
        
        update_data = restaurant_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(restaurant, field, value)
        
        await db.commit()
        await db.refresh(restaurant)
        
        return restaurant
    
    @staticmethod
    async def delete_restaurant(db: AsyncSession, restaurant_id: str) -> bool:
        """Soft delete restaurant"""
        result = await db.execute(
            select(Restaurant).where(Restaurant.id == restaurant_id)
        )
        restaurant = result.scalar_one_or_none()
        
        if not restaurant:
            return False
        
        restaurant.deleted_at = datetime.utcnow()
        restaurant.is_active = False
        
        await db.commit()
        return True
    
    @staticmethod
    async def check_usage_limits(db: AsyncSession, restaurant_id: str, resource_type: str) -> bool:
        """
        Check if restaurant can add more resources
        
        Args:
            db: Database session
            restaurant_id: Restaurant ID
            resource_type: Type of resource (users, products, orders)
            
        Returns:
            True if within limits, False otherwise
        """
        restaurant = await RestaurantService.get_restaurant_by_id(db, restaurant_id)
        if not restaurant:
            return False
        
        if resource_type == "users":
            return restaurant.current_users < restaurant.max_users
        elif resource_type == "products":
            return restaurant.current_products < restaurant.max_products
        elif resource_type == "orders":
            return restaurant.current_orders_this_month < restaurant.max_orders_per_month
        
        return False
    
    @staticmethod
    async def increment_usage(
        db: AsyncSession,
        restaurant_id: str,
        resource_type: str,
        amount: int = 1
    ) -> bool:
        """Increment usage counter"""
        restaurant = await RestaurantService.get_restaurant_by_id(db, restaurant_id)
        if not restaurant:
            return False
        
        if resource_type == "users":
            restaurant.current_users += amount
        elif resource_type == "products":
            restaurant.current_products += amount
        elif resource_type == "orders":
            restaurant.current_orders_this_month += amount
        
        await db.commit()
        return True


class SubscriptionPlanService:
    """Service layer for subscription plan operations"""
    
    @staticmethod
    async def create_plan(db: AsyncSession, plan_data: SubscriptionPlanCreate) -> SubscriptionPlan:
        """Create a new subscription plan"""
        plan = SubscriptionPlan(
            id=str(uuid.uuid4()),
            **plan_data.model_dump()
        )
        
        db.add(plan)
        await db.commit()
        await db.refresh(plan)
        
        return plan
    
    @staticmethod
    async def get_plan_by_name(db: AsyncSession, name: str) -> Optional[SubscriptionPlan]:
        """Get plan by name"""
        result = await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.name == name)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_active_plans(db: AsyncSession) -> List[SubscriptionPlan]:
        """Get all active public plans"""
        result = await db.execute(
            select(SubscriptionPlan)
            .where(
                and_(
                    SubscriptionPlan.is_active == True,
                    SubscriptionPlan.is_public == True
                )
            )
            .order_by(SubscriptionPlan.sort_order)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def update_plan(
        db: AsyncSession,
        plan_id: str,
        plan_data: SubscriptionPlanUpdate
    ) -> Optional[SubscriptionPlan]:
        """Update subscription plan"""
        result = await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            return None
        
        update_data = plan_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(plan, field, value)
        
        await db.commit()
        await db.refresh(plan)
        
        return plan


class SubscriptionService:
    """Service layer for subscription operations"""
    
    @staticmethod
    async def create_subscription(
        db: AsyncSession,
        subscription_data: SubscriptionCreate
    ) -> Subscription:
        """Create a new subscription"""
        # Get plan details
        plan = await SubscriptionPlanService.get_plan_by_name(db, subscription_data.plan.value)
        
        if not plan:
            raise ValueError(f"Plan {subscription_data.plan} not found")
        
        # Calculate period
        now = datetime.utcnow()
        trial_end = now + timedelta(days=plan.trial_days)
        
        subscription = Subscription(
            id=str(uuid.uuid4()),
            restaurant_id=subscription_data.restaurant_id,
            plan=subscription_data.plan,
            plan_name=subscription_data.plan_name,
            status=SubscriptionStatus.ACTIVE,
            price_per_month=plan.price_monthly,
            price_per_year=plan.price_yearly,
            billing_cycle=subscription_data.billing_cycle,
            started_at=now,
            current_period_start=now,
            current_period_end=trial_end if subscription_data.plan == SubscriptionPlanType.TRIAL else now + timedelta(days=30),
            trial_end=trial_end if subscription_data.plan == SubscriptionPlanType.TRIAL else None,
            payment_method=subscription_data.payment_method
        )
        
        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)
        
        return subscription
    
    @staticmethod
    async def get_active_subscription(
        db: AsyncSession,
        restaurant_id: str
    ) -> Optional[Subscription]:
        """Get active subscription for restaurant"""
        result = await db.execute(
            select(Subscription)
            .where(
                and_(
                    Subscription.restaurant_id == restaurant_id,
                    Subscription.status == SubscriptionStatus.ACTIVE
                )
            )
            .order_by(Subscription.created_at.desc())
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def cancel_subscription(
        db: AsyncSession,
        subscription_id: str,
        user_id: str,
        reason: Optional[str] = None,
        immediate: bool = False
    ) -> Optional[Subscription]:
        """Cancel a subscription"""
        result = await db.execute(
            select(Subscription).where(Subscription.id == subscription_id)
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            return None
        
        if immediate:
            subscription.status = SubscriptionStatus.CANCELLED
            subscription.cancelled_at = datetime.utcnow()
            subscription.ended_at = datetime.utcnow()
        else:
            subscription.cancel_at_period_end = True
        
        subscription.cancellation_reason = reason
        subscription.cancelled_by = user_id
        
        await db.commit()
        await db.refresh(subscription)
        
        return subscription


class InvoiceService:
    """Service layer for invoice operations"""
    
    @staticmethod
    async def create_invoice(db: AsyncSession, invoice_data: InvoiceCreate) -> Invoice:
        """Create a new invoice"""
        # Generate invoice number
        count = await db.execute(select(func.count(Invoice.id)))
        invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m')}-{count.scalar() + 1:05d}"
        
        invoice = Invoice(
            id=str(uuid.uuid4()),
            invoice_number=invoice_number,
            **invoice_data.model_dump()
        )
        
        db.add(invoice)
        await db.commit()
        await db.refresh(invoice)
        
        return invoice
    
    @staticmethod
    async def get_restaurant_invoices(
        db: AsyncSession,
        restaurant_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Invoice]:
        """Get all invoices for a restaurant"""
        result = await db.execute(
            select(Invoice)
            .where(Invoice.restaurant_id == restaurant_id)
            .order_by(Invoice.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def mark_invoice_paid(
        db: AsyncSession,
        invoice_id: str,
        payment_method: str,
        payment_gateway_charge_id: Optional[str] = None
    ) -> Optional[Invoice]:
        """Mark invoice as paid"""
        result = await db.execute(
            select(Invoice).where(Invoice.id == invoice_id)
        )
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            return None
        
        invoice.status = InvoiceStatus.PAID
        invoice.paid_at = datetime.utcnow()
        invoice.payment_method = payment_method
        invoice.payment_gateway_charge_id = payment_gateway_charge_id
        
        await db.commit()
        await db.refresh(invoice)
        
        return invoice


class RestaurantInvitationService:
    """Service layer for restaurant invitation operations"""
    
    @staticmethod
    async def create_invitation(
        db: AsyncSession,
        restaurant_id: str,
        invitation_data: RestaurantInvitationCreate,
        invited_by_user_id: str
    ) -> RestaurantInvitation:
        """Create a new restaurant invitation"""
        # Generate unique token
        token = secrets.token_urlsafe(32)
        
        invitation = RestaurantInvitation(
            id=str(uuid.uuid4()),
            restaurant_id=restaurant_id,
            email=invitation_data.email,
            name=invitation_data.name,
            role=invitation_data.role,
            token=token,
            invited_by=invited_by_user_id,
            message=invitation_data.message,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        
        db.add(invitation)
        await db.commit()
        await db.refresh(invitation)
        
        return invitation
    
    @staticmethod
    async def get_invitation_by_token(
        db: AsyncSession,
        token: str
    ) -> Optional[RestaurantInvitation]:
        """Get invitation by token"""
        result = await db.execute(
            select(RestaurantInvitation).where(RestaurantInvitation.token == token)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def accept_invitation(
        db: AsyncSession,
        token: str,
        user_id: str
    ) -> Optional[RestaurantInvitation]:
        """Accept a restaurant invitation"""
        invitation = await RestaurantInvitationService.get_invitation_by_token(db, token)
        
        if not invitation:
            return None
        
        if invitation.status != 'pending':
            return None
        
        if invitation.expires_at < datetime.utcnow():
            invitation.status = 'expired'
            await db.commit()
            return None
        
        # Update invitation
        invitation.status = 'accepted'
        invitation.accepted_at = datetime.utcnow()
        invitation.accepted_by = user_id
        
        # Create restaurant owner relationship
        owner = RestaurantOwner(
            id=str(uuid.uuid4()),
            restaurant_id=invitation.restaurant_id,
            user_id=user_id,
            role=invitation.role,
            invited_by=invitation.invited_by
        )
        db.add(owner)
        
        await db.commit()
        await db.refresh(invitation)
        
        return invitation
