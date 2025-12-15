"""
Restaurant onboarding routes for new restaurant registration
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime, timedelta
import uuid

from app.database import get_db
from app.models.restaurant import Restaurant, RestaurantOwner, Subscription
from app.models.user import User
from app.security import hash_password, create_token_pair
from app.response_formatter import success_response, error_response, created_response
from app.utils import generate_slug

router = APIRouter(prefix="/api/v1/onboarding", tags=["Onboarding"])


class RestaurantRegistration(BaseModel):
    """Restaurant registration request"""
    # Restaurant Info
    restaurant_name: str
    business_type: Optional[str] = "restaurant"
    cuisine_type: Optional[list] = []
    
    # Owner Info
    owner_name: str
    owner_email: EmailStr
    owner_phone: str
    password: str
    
    # Location
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "USA"
    postal_code: Optional[str] = None
    
    # Settings
    timezone: str = "UTC"
    currency: str = "USD"
    language: str = "en"
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class OnboardingStatusResponse(BaseModel):
    """Onboarding status response"""
    restaurant_id: str
    restaurant_name: str
    slug: str
    onboarding_completed: bool
    onboarding_step: int
    subscription_status: str
    trial_ends_at: Optional[datetime]


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_restaurant(
    data: RestaurantRegistration,
    db: Session = Depends(get_db)
):
    """
    Register a new restaurant and create owner account
    
    Steps:
    1. Validate email doesn't exist
    2. Create restaurant
    3. Create owner user
    4. Link owner to restaurant
    5. Create trial subscription
    6. Return access token
    """
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == data.owner_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Generate unique slug
    base_slug = generate_slug(data.restaurant_name)
    slug = base_slug
    counter = 1
    while db.query(Restaurant).filter(Restaurant.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    try:
        # 1. Create Restaurant
        restaurant_id = str(uuid.uuid4())
        trial_end = datetime.utcnow() + timedelta(days=14)
        
        restaurant = Restaurant(
            id=restaurant_id,
            name=data.restaurant_name,
            slug=slug,
            business_name=data.restaurant_name,
            business_type=data.business_type,
            cuisine_type=data.cuisine_type,
            email=data.owner_email,
            phone=data.owner_phone,
            address=data.address,
            city=data.city,
            state=data.state,
            country=data.country,
            postal_code=data.postal_code,
            timezone=data.timezone,
            currency=data.currency,
            language=data.language,
            subscription_plan='trial',
            subscription_status='active',
            trial_ends_at=trial_end,
            max_users=2,
            max_products=50,
            max_orders_per_month=100,
            is_active=True,
            is_verified=False,
            onboarding_completed=False,
            onboarding_step=1
        )
        db.add(restaurant)
        
        # 2. Create Owner User
        user_id = str(uuid.uuid4())
        hashed_password = hash_password(data.password)
        
        owner_user = User(
            id=user_id,
            restaurant_id=restaurant_id,
            name=data.owner_name,
            email=data.owner_email,
            phone=data.owner_phone,
            password=hashed_password,
            role='admin',
            status='active'
        )
        db.add(owner_user)
        
        # 3. Create Restaurant Owner Link
        restaurant_owner = RestaurantOwner(
            id=str(uuid.uuid4()),
            restaurant_id=restaurant_id,
            user_id=user_id,
            role='owner',
            is_active=True
        )
        db.add(restaurant_owner)
        
        # 4. Create Trial Subscription
        subscription = Subscription(
            id=str(uuid.uuid4()),
            restaurant_id=restaurant_id,
            plan='trial',
            plan_name='Trial Plan',
            status='active',
            price_per_month=0,
            billing_cycle='monthly',
            started_at=datetime.utcnow(),
            trial_end=trial_end,
            payment_method='trial'
        )
        db.add(subscription)
        
        db.commit()
        db.refresh(restaurant)
        db.refresh(owner_user)
        
        # 5. Create access token
        token_response = create_token_pair(
            user_id=user_id,
            email=data.owner_email,
            role='admin',
            restaurant_id=restaurant_id,
            restaurant_slug=slug,
            is_platform_admin=False
        )
        
        return created_response(
            data={
                "restaurant": {
                    "id": restaurant.id,
                    "name": restaurant.name,
                    "slug": restaurant.slug,
                    "subscription_plan": restaurant.subscription_plan,
                    "trial_ends_at": restaurant.trial_ends_at.isoformat() if restaurant.trial_ends_at else None
                },
                "user": {
                    "id": owner_user.id,
                    "name": owner_user.name,
                    "email": owner_user.email,
                    "role": owner_user.role
                },
                "tokens": {
                    "access_token": token_response.access_token,
                    "refresh_token": token_response.refresh_token,
                    "token_type": token_response.token_type,
                    "expires_in": token_response.expires_in
                }
            },
            message="Restaurant registered successfully! Welcome to the platform."
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register restaurant: {str(e)}"
        )


@router.post("/verify-email")
async def verify_email(
    email: EmailStr,
    verification_code: str,
    db: Session = Depends(get_db)
):
    """
    Verify restaurant owner's email
    (Implementation depends on email verification system)
    """
    # TODO: Implement email verification logic
    return success_response(
        message="Email verification endpoint - to be implemented"
    )


@router.post("/complete")
async def complete_onboarding(
    restaurant_id: str,
    db: Session = Depends(get_db)
):
    """
    Mark onboarding as completed
    """
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id
    ).first()
    
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found"
        )
    
    restaurant.onboarding_completed = True
    restaurant.onboarding_step = 100  # Completed
    db.commit()
    
    return success_response(
        data={"onboarding_completed": True},
        message="Onboarding completed successfully!"
    )


@router.get("/status/{restaurant_id}")
async def get_onboarding_status(
    restaurant_id: str,
    db: Session = Depends(get_db)
):
    """
    Get onboarding status for a restaurant
    """
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id
    ).first()
    
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found"
        )
    
    return success_response(
        data={
            "restaurant_id": restaurant.id,
            "restaurant_name": restaurant.name,
            "slug": restaurant.slug,
            "onboarding_completed": restaurant.onboarding_completed,
            "onboarding_step": restaurant.onboarding_step,
            "subscription_status": restaurant.subscription_status,
            "subscription_plan": restaurant.subscription_plan,
            "trial_ends_at": restaurant.trial_ends_at.isoformat() if restaurant.trial_ends_at else None,
            "is_verified": restaurant.is_verified
        }
    )
