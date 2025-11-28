"""
Customer API routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.customer import Customer, CustomerTag, LoyaltyTransaction
from app.models.user import User
from app.schemas.customer import (
    CustomerCreate, CustomerUpdate, CustomerResponse,
    CustomerTagCreate, CustomerTagUpdate, CustomerTagResponse,
    LoyaltyTransactionResponse
)
from app.schemas.pagination import PaginationParams
from datetime import datetime
from app.response_formatter import success_response, created_response, list_response, deleted_response, error_response
from app.utils import paginate_query, create_paginated_response

router = APIRouter(prefix="/api/v1/customers", tags=["customers"])


@router.get("/")
def list_customers(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = None,
    is_blacklisted: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    List all customers with pagination and optional filtering
    """
    query = db.query(Customer)
    
    if search:
        query = query.filter(
            Customer.name.ilike(f"%{search}%") |
            Customer.phone.ilike(f"%{search}%") |
            Customer.email.ilike(f"%{search}%")
        )
    
    if is_blacklisted is not None:
        query = query.filter(Customer.is_blacklisted == is_blacklisted)
    
    query = query.order_by(Customer.created_at.desc())
    
    # Apply pagination
    pagination = PaginationParams(page=page, page_size=page_size)
    customers, pagination_meta = paginate_query(query, pagination)
    
    return create_paginated_response(customers, pagination_meta, "Customers retrieved successfully")


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    """
    Get a specific customer by ID
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with id {customer_id} not found"
        )
    return customer


@router.get("/phone/{phone}", response_model=CustomerResponse)
def get_customer_by_phone(phone: str, db: Session = Depends(get_db)):
    """
    Get a specific customer by phone number
    """
    customer = db.query(Customer).filter(Customer.phone == phone).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with phone {phone} not found"
        )
    return customer


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    """
    Create a new customer
    """
    # Check if phone already exists
    existing = db.query(Customer).filter(Customer.phone == customer.phone).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Customer with phone '{customer.phone}' already exists"
        )
    
    # Check if email already exists (if provided)
    if customer.email:
        existing_email = db.query(Customer).filter(Customer.email == customer.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Customer with email '{customer.email}' already exists"
            )
    
    db_customer = Customer(**customer.model_dump())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer


@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: str,
    customer: CustomerUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing customer
    """
    db_customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not db_customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with id {customer_id} not found"
        )
    
    # Check if phone is being changed and if it already exists
    if customer.phone and customer.phone != db_customer.phone:
        existing = db.query(Customer).filter(Customer.phone == customer.phone).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Customer with phone '{customer.phone}' already exists"
            )
    
    # Update only provided fields
    update_data = customer.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_customer, field, value)
    
    db.commit()
    db.refresh(db_customer)
    return db_customer


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(customer_id: str, db: Session = Depends(get_db)):
    """
    Delete a customer
    """
    db_customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not db_customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with id {customer_id} not found"
        )
    
    db.delete(db_customer)
    db.commit()
    return None


@router.post("/{customer_id}/loyalty/adjust", response_model=LoyaltyTransactionResponse)
def adjust_customer_loyalty_points(
    customer_id: str,
    points: int = Query(...),
    operation: str = Query(..., regex="^(add|subtract)$"),
    reason: str = Query(..., min_length=1),
    created_by: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Adjust customer loyalty points (manual adjustment)
    """
    # Verify customer exists
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with id {customer_id} not found"
        )
    
    # Verify user if provided
    if created_by:
        user = db.query(User).filter(User.id == created_by).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {created_by} not found"
            )
    
    # Calculate points change
    points_change = points if operation == "add" else -points
    
    # Check if adjustment would result in negative balance
    new_balance = customer.loyalty_points + points_change
    if new_balance < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Adjustment would result in negative points balance"
        )
    
    # Create transaction
    transaction = LoyaltyTransaction(
        customer_id=customer_id,
        points=points_change,
        operation='adjust',
        reason=reason,
        balance_before=customer.loyalty_points,
        balance_after=new_balance,
        created_by=created_by,
        created_at=datetime.utcnow()
    )
    
    # Update customer points
    customer.loyalty_points = new_balance
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    return transaction


# Customer Tags endpoints
tags_router = APIRouter(prefix="/api/v1/customers/tags", tags=["customer-tags"])


@tags_router.get("/")
def list_customer_tags(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    List all customer tags with pagination
    """
    query = db.query(CustomerTag).order_by(CustomerTag.priority.desc())
    
    # Apply pagination
    pagination = PaginationParams(page=page, page_size=page_size)
    tags, pagination_meta = paginate_query(query, pagination)
    
    return create_paginated_response(tags, pagination_meta, "Customer tags retrieved successfully")


@tags_router.get("/{tag_id}", response_model=CustomerTagResponse)
def get_customer_tag(tag_id: str, db: Session = Depends(get_db)):
    """
    Get a specific customer tag by ID
    """
    tag = db.query(CustomerTag).filter(CustomerTag.id == tag_id).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer tag with id {tag_id} not found"
        )
    return tag


@tags_router.post("/", response_model=CustomerTagResponse, status_code=status.HTTP_201_CREATED)
def create_customer_tag(tag: CustomerTagCreate, db: Session = Depends(get_db)):
    """
    Create a new customer tag
    """
    # Check if name already exists
    existing = db.query(CustomerTag).filter(CustomerTag.name == tag.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Customer tag with name '{tag.name}' already exists"
        )
    
    db_tag = CustomerTag(**tag.model_dump())
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag


@tags_router.put("/{tag_id}", response_model=CustomerTagResponse)
def update_customer_tag(
    tag_id: str,
    tag: CustomerTagUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing customer tag
    """
    db_tag = db.query(CustomerTag).filter(CustomerTag.id == tag_id).first()
    if not db_tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer tag with id {tag_id} not found"
        )
    
    # Update only provided fields
    update_data = tag.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_tag, field, value)
    
    db.commit()
    db.refresh(db_tag)
    return db_tag


@tags_router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer_tag(tag_id: str, db: Session = Depends(get_db)):
    """
    Delete a customer tag
    """
    db_tag = db.query(CustomerTag).filter(CustomerTag.id == tag_id).first()
    if not db_tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer tag with id {tag_id} not found"
        )
    
    db.delete(db_tag)
    db.commit()
    return None
