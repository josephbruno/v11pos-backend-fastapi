"""
User and Staff Management API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from passlib.context import CryptContext

from app.database import get_db
from app.models.user import User, ShiftSchedule, StaffPerformance
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    ShiftScheduleCreate,
    ShiftScheduleUpdate,
    ShiftScheduleResponse,
    StaffPerformanceResponse
)
from app.schemas.pagination import PaginationParams
from app.response_formatter import success_response, created_response, list_response, deleted_response, error_response
from app.utils import paginate_query, create_paginated_response


users_router = APIRouter(prefix="/api/v1/users", tags=["Users"])
shifts_router = APIRouter(prefix="/api/v1/shifts", tags=["Shift Schedules"])
performance_router = APIRouter(prefix="/api/v1/staff-performance", tags=["Staff Performance"])
roles_router = APIRouter(prefix="/api/v1/users/roles", tags=["User Roles"])

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# User routes
@users_router.get("")
def get_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    role: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all users with pagination and optional filtering"""
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    if status:
        query = query.filter(User.status == status)
    if search:
        query = query.filter(
            (User.name.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%")) |
            (User.phone.ilike(f"%{search}%"))
        )
    
    # Apply pagination
    pagination = PaginationParams(page=page, page_size=page_size)
    users, pagination_meta = paginate_query(query, pagination)
    
    return create_paginated_response(users, pagination_meta, "Users retrieved successfully")


@users_router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db)):
    """Get user by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@users_router.get("/email/{email}", response_model=UserResponse)
def get_user_by_email(email: str, db: Session = Depends(get_db)):
    """Get user by email"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@users_router.post("", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    # Check for duplicate email
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = pwd_context.hash(user.password)
    
    user_data = user.model_dump()
    user_data["password"] = hashed_password
    
    db_user = User(**user_data)
    db.add(db_user)
    
    # Create staff performance record
    performance = StaffPerformance(user_id=db_user.id)
    db.add(performance)
    
    db.commit()
    db.refresh(db_user)
    return db_user


@users_router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: str, user: UserUpdate, db: Session = Depends(get_db)):
    """Update a user"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user.model_dump(exclude_unset=True)
    
    # Check email uniqueness if being updated
    if "email" in update_data:
        existing = db.query(User).filter(
            User.email == update_data["email"],
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password if being updated
    if "password" in update_data:
        update_data["password"] = pwd_context.hash(update_data["password"])
    
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user


@users_router.delete("/{user_id}", status_code=204)
def delete_user(user_id: str, db: Session = Depends(get_db)):
    """Delete a user"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(db_user)
    db.commit()
    return None


# Shift Schedule routes
@shifts_router.get("")
def get_shifts(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    user_id: Optional[str] = None,
    day: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get all shift schedules with pagination and optional filtering"""
    query = db.query(ShiftSchedule)
    
    if user_id:
        query = query.filter(ShiftSchedule.user_id == user_id)
    if day:
        query = query.filter(ShiftSchedule.day == day)
    if is_active is not None:
        query = query.filter(ShiftSchedule.is_active == is_active)
    
    # Apply pagination
    pagination = PaginationParams(page=page, page_size=page_size)
    shifts, pagination_meta = paginate_query(query, pagination)
    
    return create_paginated_response(shifts, pagination_meta, "Shifts retrieved successfully")


@shifts_router.get("/{shift_id}", response_model=ShiftScheduleResponse)
def get_shift(shift_id: str, db: Session = Depends(get_db)):
    """Get shift schedule by ID"""
    shift = db.query(ShiftSchedule).filter(ShiftSchedule.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift schedule not found")
    return shift


@shifts_router.post("", response_model=ShiftScheduleResponse, status_code=201)
def create_shift(shift: ShiftScheduleCreate, db: Session = Depends(get_db)):
    """Create a new shift schedule"""
    # Verify user exists
    user = db.query(User).filter(User.id == shift.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate time format (HH:MM)
    import re
    time_pattern = r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$'
    if not re.match(time_pattern, shift.start_time):
        raise HTTPException(status_code=400, detail="Invalid start_time format. Use HH:MM")
    if not re.match(time_pattern, shift.end_time):
        raise HTTPException(status_code=400, detail="Invalid end_time format. Use HH:MM")
    
    # Check for overlapping shifts
    existing = db.query(ShiftSchedule).filter(
        ShiftSchedule.user_id == shift.user_id,
        ShiftSchedule.day == shift.day,
        ShiftSchedule.is_active == True
    ).all()
    
    for existing_shift in existing:
        # Simple overlap check (assumes no shifts cross midnight)
        if not (shift.end_time <= existing_shift.start_time or 
                shift.start_time >= existing_shift.end_time):
            raise HTTPException(
                status_code=400,
                detail=f"Shift overlaps with existing shift on {shift.day}"
            )
    
    db_shift = ShiftSchedule(**shift.model_dump())
    db.add(db_shift)
    db.commit()
    db.refresh(db_shift)
    return db_shift


@shifts_router.put("/{shift_id}", response_model=ShiftScheduleResponse)
def update_shift(shift_id: str, shift: ShiftScheduleUpdate, db: Session = Depends(get_db)):
    """Update a shift schedule"""
    db_shift = db.query(ShiftSchedule).filter(ShiftSchedule.id == shift_id).first()
    if not db_shift:
        raise HTTPException(status_code=404, detail="Shift schedule not found")
    
    update_data = shift.model_dump(exclude_unset=True)
    
    # Validate time format if being updated
    import re
    time_pattern = r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$'
    if "start_time" in update_data and not re.match(time_pattern, update_data["start_time"]):
        raise HTTPException(status_code=400, detail="Invalid start_time format. Use HH:MM")
    if "end_time" in update_data and not re.match(time_pattern, update_data["end_time"]):
        raise HTTPException(status_code=400, detail="Invalid end_time format. Use HH:MM")
    
    for field, value in update_data.items():
        setattr(db_shift, field, value)
    
    db.commit()
    db.refresh(db_shift)
    return db_shift


@shifts_router.delete("/{shift_id}", status_code=204)
def delete_shift(shift_id: str, db: Session = Depends(get_db)):
    """Delete a shift schedule"""
    db_shift = db.query(ShiftSchedule).filter(ShiftSchedule.id == shift_id).first()
    if not db_shift:
        raise HTTPException(status_code=404, detail="Shift schedule not found")
    
    db.delete(db_shift)
    db.commit()
    return None


# Staff Performance routes
@performance_router.get("")
def get_all_performance(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Get all staff performance records with pagination"""
    query = db.query(StaffPerformance)
    
    # Apply pagination
    pagination = PaginationParams(page=page, page_size=page_size)
    performances, pagination_meta = paginate_query(query, pagination)
    
    return create_paginated_response(performances, pagination_meta, "Performance records retrieved successfully")


@performance_router.get("/{user_id}", response_model=StaffPerformanceResponse)
def get_staff_performance(user_id: str, db: Session = Depends(get_db)):
    """Get staff performance by user ID"""
    performance = db.query(StaffPerformance).filter(StaffPerformance.user_id == user_id).first()
    if not performance:
        # Create default performance record if it doesn't exist
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        performance = StaffPerformance(user_id=user_id)
        db.add(performance)
        db.commit()
        db.refresh(performance)
    
    return performance


@performance_router.post("/{user_id}/recalculate", response_model=StaffPerformanceResponse)
def recalculate_performance(user_id: str, db: Session = Depends(get_db)):
    """Recalculate staff performance metrics from orders"""
    from app.models.order import Order
    from datetime import datetime
    
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get or create performance record
    performance = db.query(StaffPerformance).filter(StaffPerformance.user_id == user_id).first()
    if not performance:
        performance = StaffPerformance(user_id=user_id)
        db.add(performance)
    
    # Get all completed orders created by this user
    orders = db.query(Order).filter(
        Order.created_by == user_id,
        Order.status == 'completed'
    ).all()
    
    if orders:
        total_orders = len(orders)
        total_revenue = sum(order.total for order in orders)
        avg_order_value = total_revenue // total_orders if total_orders > 0 else 0
        
        performance.orders_handled = total_orders
        performance.total_revenue = total_revenue
        performance.avg_order_value = avg_order_value
        performance.last_calculated = datetime.utcnow()
    
    db.commit()
    db.refresh(performance)
    return performance


# User Roles endpoints
# Define available roles and permissions
PREDEFINED_ROLES = {
    "admin": {
        "name": "Administrator",
        "permissions": ["all"],
        "description": "Full system access"
    },
    "manager": {
        "name": "Manager",
        "permissions": [
            "view_orders", "create_orders", "update_orders", "cancel_orders",
            "view_products", "create_products", "update_products", "delete_products",
            "view_customers", "create_customers", "update_customers",
            "view_reports", "view_analytics",
            "manage_staff_shifts", "view_staff_performance"
        ],
        "description": "Manager with full operational access"
    },
    "cashier": {
        "name": "Cashier",
        "permissions": [
            "view_orders", "create_orders", "update_orders",
            "view_products",
            "view_customers", "create_customers",
            "process_payments"
        ],
        "description": "POS operator for order processing"
    },
    "waiter": {
        "name": "Waiter/Server",
        "permissions": [
            "view_orders", "create_orders", "update_orders",
            "view_products",
            "view_customers"
        ],
        "description": "Waiter/server for taking orders"
    },
    "kitchen": {
        "name": "Kitchen Staff",
        "permissions": [
            "view_orders", "update_kot_status",
            "view_products"
        ],
        "description": "Kitchen staff for order preparation"
    },
    "delivery": {
        "name": "Delivery Staff",
        "permissions": [
            "view_orders", "update_order_status",
            "view_customers"
        ],
        "description": "Delivery personnel"
    }
}


@roles_router.get("")
def get_all_roles():
    """
    Get all available roles and their permissions
    """
    return {
        "predefined_roles": [
            {
                "role_id": role_id,
                "name": role_data["name"],
                "permissions": role_data["permissions"],
                "description": role_data["description"],
                "is_custom": False
            }
            for role_id, role_data in PREDEFINED_ROLES.items()
        ],
        "custom_roles": [],  # TODO: Implement custom roles in database
        "available_permissions": [
            "all",
            "view_orders",
            "create_orders",
            "update_orders",
            "cancel_orders",
            "process_payments",
            "view_products",
            "create_products",
            "update_products",
            "delete_products",
            "view_categories",
            "manage_categories",
            "view_customers",
            "create_customers",
            "update_customers",
            "delete_customers",
            "manage_loyalty",
            "view_users",
            "create_users",
            "update_users",
            "delete_users",
            "manage_staff_shifts",
            "view_staff_performance",
            "view_reports",
            "view_analytics",
            "manage_settings",
            "manage_tax_rules",
            "update_kot_status",
            "update_order_status"
        ]
    }


@roles_router.post("")
def create_custom_role(
    role_name: str = Query(..., min_length=1),
    permissions: List[str] = Query(...),
    description: Optional[str] = None
):
    """
    Create a new custom role
    Note: This is a placeholder. Custom roles should be stored in database.
    """
    # TODO: Implement custom roles storage in database
    # For now, return a success response
    
    # Validate permissions
    valid_permissions = [
        "all", "view_orders", "create_orders", "update_orders", "cancel_orders",
        "process_payments", "view_products", "create_products", "update_products",
        "delete_products", "view_categories", "manage_categories", "view_customers",
        "create_customers", "update_customers", "delete_customers", "manage_loyalty",
        "view_users", "create_users", "update_users", "delete_users",
        "manage_staff_shifts", "view_staff_performance", "view_reports",
        "view_analytics", "manage_settings", "manage_tax_rules",
        "update_kot_status", "update_order_status"
    ]
    
    invalid_perms = [p for p in permissions if p not in valid_permissions]
    if invalid_perms:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid permissions: {', '.join(invalid_perms)}"
        )
    
    return {
        "message": "Custom role creation not fully implemented. This is a placeholder endpoint.",
        "role_data": {
            "role_name": role_name,
            "permissions": permissions,
            "description": description,
            "is_custom": True
        },
        "note": "To fully implement, create a Role model and store in database"
    }
