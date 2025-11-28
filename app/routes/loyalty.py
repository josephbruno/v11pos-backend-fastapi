"""
Loyalty Program API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models.customer import LoyaltyRule, LoyaltyTransaction, Customer
from app.models.order import Order
from app.models.user import User
from app.schemas.customer import (
    LoyaltyRuleCreate,
    LoyaltyRuleUpdate,
    LoyaltyRuleResponse,
    LoyaltyTransactionResponse
)
from app.schemas.pagination import PaginationParams
from app.response_formatter import success_response, created_response, list_response, deleted_response, error_response
from app.utils import paginate_query, create_paginated_response


rules_router = APIRouter(prefix="/api/v1/loyalty/rules", tags=["Loyalty Rules"])
transactions_router = APIRouter(prefix="/api/v1/loyalty/transactions", tags=["Loyalty Transactions"])


# Loyalty Rules routes
@rules_router.get("")
def get_loyalty_rules(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get all loyalty rules with pagination"""
    query = db.query(LoyaltyRule)
    
    if active is not None:
        query = query.filter(LoyaltyRule.active == active)
    
    query = query.order_by(LoyaltyRule.priority.desc())
    
    # Apply pagination
    pagination = PaginationParams(page=page, page_size=page_size)
    rules, pagination_meta = paginate_query(query, pagination)
    
    return create_paginated_response(rules, pagination_meta, "Loyalty rules retrieved successfully")


@rules_router.get("/{rule_id}", response_model=LoyaltyRuleResponse)
def get_loyalty_rule(rule_id: str, db: Session = Depends(get_db)):
    """Get loyalty rule by ID"""
    rule = db.query(LoyaltyRule).filter(LoyaltyRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Loyalty rule not found")
    return rule


@rules_router.post("", response_model=LoyaltyRuleResponse, status_code=201)
def create_loyalty_rule(rule: LoyaltyRuleCreate, db: Session = Depends(get_db)):
    """Create a new loyalty rule"""
    db_rule = LoyaltyRule(**rule.model_dump())
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule


@rules_router.put("/{rule_id}", response_model=LoyaltyRuleResponse)
def update_loyalty_rule(rule_id: str, rule: LoyaltyRuleUpdate, db: Session = Depends(get_db)):
    """Update a loyalty rule"""
    db_rule = db.query(LoyaltyRule).filter(LoyaltyRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Loyalty rule not found")
    
    update_data = rule.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_rule, field, value)
    
    db.commit()
    db.refresh(db_rule)
    return db_rule


@rules_router.delete("/{rule_id}", status_code=204)
def delete_loyalty_rule(rule_id: str, db: Session = Depends(get_db)):
    """Delete a loyalty rule"""
    db_rule = db.query(LoyaltyRule).filter(LoyaltyRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Loyalty rule not found")
    
    db.delete(db_rule)
    db.commit()
    return None


# Loyalty Transactions routes
@transactions_router.get("")
def get_loyalty_transactions(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    customer_id: Optional[str] = None,
    operation: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get loyalty transactions with pagination and optional filtering"""
    query = db.query(LoyaltyTransaction)
    
    if customer_id:
        query = query.filter(LoyaltyTransaction.customer_id == customer_id)
    if operation:
        query = query.filter(LoyaltyTransaction.operation == operation)
    
    query = query.order_by(LoyaltyTransaction.created_at.desc())
    
    # Apply pagination
    pagination = PaginationParams(page=page, page_size=page_size)
    transactions, pagination_meta = paginate_query(query, pagination)
    
    return create_paginated_response(transactions, pagination_meta, "Loyalty transactions retrieved successfully")


@transactions_router.get("/{transaction_id}", response_model=LoyaltyTransactionResponse)
def get_loyalty_transaction(transaction_id: str, db: Session = Depends(get_db)):
    """Get loyalty transaction by ID"""
    transaction = db.query(LoyaltyTransaction).filter(LoyaltyTransaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Loyalty transaction not found")
    return transaction


@transactions_router.post("/earn", response_model=LoyaltyTransactionResponse, status_code=201)
def earn_loyalty_points(
    customer_id: str,
    order_id: str,
    db: Session = Depends(get_db)
):
    """Award loyalty points for an order"""
    # Verify customer exists
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Verify order exists
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check if points already awarded for this order
    existing = db.query(LoyaltyTransaction).filter(
        LoyaltyTransaction.order_id == order_id,
        LoyaltyTransaction.operation == 'earn'
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Points already awarded for this order")
    
    # Get active loyalty rule
    rule = db.query(LoyaltyRule).filter(LoyaltyRule.active == True).order_by(
        LoyaltyRule.priority.desc()
    ).first()
    
    if not rule:
        raise HTTPException(status_code=400, detail="No active loyalty rule found")
    
    # Calculate points (earn_rate is percentage * 100, e.g., 1.00% = 100)
    # order.total is in cents
    points_to_earn = int((order.total / 100) * (rule.earn_rate / 100))
    
    if points_to_earn <= 0:
        raise HTTPException(status_code=400, detail="Order amount too small to earn points")
    
    # Calculate expiry date if rule has expiry days
    expires_at = None
    if rule.expiry_days:
        expires_at = datetime.utcnow() + timedelta(days=rule.expiry_days)
    
    # Create transaction
    transaction = LoyaltyTransaction(
        customer_id=customer_id,
        order_id=order_id,
        points=points_to_earn,
        operation='earn',
        reason=f"Order #{order.order_number}",
        balance_before=customer.loyalty_points,
        balance_after=customer.loyalty_points + points_to_earn,
        expires_at=expires_at
    )
    
    # Update customer points
    customer.loyalty_points += points_to_earn
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@transactions_router.post("/redeem", response_model=LoyaltyTransactionResponse, status_code=201)
def redeem_loyalty_points(
    customer_id: str,
    points: int = Query(..., gt=0),
    order_id: Optional[str] = None,
    reason: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Redeem loyalty points"""
    # Verify customer exists
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Get active loyalty rule
    rule = db.query(LoyaltyRule).filter(LoyaltyRule.active == True).order_by(
        LoyaltyRule.priority.desc()
    ).first()
    
    if not rule:
        raise HTTPException(status_code=400, detail="No active loyalty rule found")
    
    # Check minimum redeem points
    if points < rule.min_redeem_points:
        raise HTTPException(
            status_code=400,
            detail=f"Minimum {rule.min_redeem_points} points required for redemption"
        )
    
    # Check if customer has enough points
    if customer.loyalty_points < points:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient points. Customer has {customer.loyalty_points} points"
        )
    
    # Verify order if provided
    if order_id:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
    
    # Create transaction
    transaction = LoyaltyTransaction(
        customer_id=customer_id,
        order_id=order_id,
        points=-points,  # Negative for redemption
        operation='redeem',
        reason=reason or f"Redeemed {points} points",
        balance_before=customer.loyalty_points,
        balance_after=customer.loyalty_points - points
    )
    
    # Update customer points
    customer.loyalty_points -= points
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@transactions_router.post("/adjust", response_model=LoyaltyTransactionResponse, status_code=201)
def adjust_loyalty_points(
    customer_id: str,
    points: int = Query(...),  # Can be positive or negative
    reason: str = Query(..., min_length=1),
    created_by: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Manual adjustment of loyalty points (admin only)"""
    # Verify customer exists
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Verify user if provided
    if created_by:
        user = db.query(User).filter(User.id == created_by).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
    
    # Check if adjustment would result in negative balance
    new_balance = customer.loyalty_points + points
    if new_balance < 0:
        raise HTTPException(
            status_code=400,
            detail="Adjustment would result in negative points balance"
        )
    
    # Create transaction
    transaction = LoyaltyTransaction(
        customer_id=customer_id,
        points=points,
        operation='adjust',
        reason=reason,
        balance_before=customer.loyalty_points,
        balance_after=new_balance,
        created_by=created_by
    )
    
    # Update customer points
    customer.loyalty_points = new_balance
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction
