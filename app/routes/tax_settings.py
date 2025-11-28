"""
Tax Rules and Settings API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.settings import TaxRule, Settings
from app.schemas.settings import (
    TaxRuleCreate,
    TaxRuleUpdate,
    TaxRuleResponse,
    SettingsCreate,
    SettingsUpdate,
    SettingsResponse
)
from app.schemas.pagination import PaginationParams
from app.response_formatter import success_response, created_response, list_response, deleted_response, error_response
from app.utils import paginate_query, create_paginated_response


tax_router = APIRouter(prefix="/api/v1/taxes", tags=["Tax Rules"])
settings_router = APIRouter(prefix="/api/v1/settings", tags=["Settings"])


# Tax Rules routes
@tax_router.get("")
def get_tax_rules(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    active: Optional[bool] = None,
    applicable_on: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all tax rules with pagination"""
    query = db.query(TaxRule)
    
    if active is not None:
        query = query.filter(TaxRule.active == active)
    if applicable_on:
        query = query.filter(TaxRule.applicable_on == applicable_on)
    
    query = query.order_by(TaxRule.priority.asc())
    
    # Apply pagination
    pagination = PaginationParams(page=page, page_size=page_size)
    rules, pagination_meta = paginate_query(query, pagination)
    
    return create_paginated_response(rules, pagination_meta, "Tax rules retrieved successfully")


@tax_router.get("/{rule_id}", response_model=TaxRuleResponse)
def get_tax_rule(rule_id: str, db: Session = Depends(get_db)):
    """Get tax rule by ID"""
    rule = db.query(TaxRule).filter(TaxRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Tax rule not found")
    return rule


@tax_router.post("", response_model=TaxRuleResponse, status_code=201)
def create_tax_rule(rule: TaxRuleCreate, db: Session = Depends(get_db)):
    """Create a new tax rule"""
    # Validate min/max amounts
    if rule.min_amount is not None and rule.max_amount is not None:
        if rule.min_amount >= rule.max_amount:
            raise HTTPException(status_code=400, detail="min_amount must be less than max_amount")
    
    db_rule = TaxRule(**rule.model_dump())
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule


@tax_router.put("/{rule_id}", response_model=TaxRuleResponse)
def update_tax_rule(rule_id: str, rule: TaxRuleUpdate, db: Session = Depends(get_db)):
    """Update a tax rule"""
    db_rule = db.query(TaxRule).filter(TaxRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Tax rule not found")
    
    update_data = rule.model_dump(exclude_unset=True)
    
    # Validate min/max amounts if being updated
    min_amount = update_data.get("min_amount", db_rule.min_amount)
    max_amount = update_data.get("max_amount", db_rule.max_amount)
    if min_amount is not None and max_amount is not None:
        if min_amount >= max_amount:
            raise HTTPException(status_code=400, detail="min_amount must be less than max_amount")
    
    for field, value in update_data.items():
        setattr(db_rule, field, value)
    
    db.commit()
    db.refresh(db_rule)
    return db_rule


@tax_router.delete("/{rule_id}", status_code=204)
def delete_tax_rule(rule_id: str, db: Session = Depends(get_db)):
    """Delete a tax rule"""
    db_rule = db.query(TaxRule).filter(TaxRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Tax rule not found")
    
    db.delete(db_rule)
    db.commit()
    return None


@tax_router.post("/calculate")
def calculate_taxes(
    subtotal: int = Query(..., description="Subtotal amount in cents"),
    order_type: str = Query("dine_in", description="Order type: dine_in, takeaway, delivery"),
    db: Session = Depends(get_db)
):
    """
    Calculate taxes for an order based on tax rules
    """
    # Get active tax rules that apply to this order
    tax_rules = db.query(TaxRule).filter(
        TaxRule.active == True
    ).order_by(TaxRule.priority.asc()).all()
    
    applicable_taxes = []
    total_tax = 0
    compounded_base = subtotal
    
    for rule in tax_rules:
        # Check if rule applies to this order type
        if rule.applicable_on not in ['all', order_type]:
            continue
        
        # Check amount range
        if rule.min_amount is not None and subtotal < rule.min_amount:
            continue
        if rule.max_amount is not None and subtotal > rule.max_amount:
            continue
        
        # Calculate tax amount
        base_amount = compounded_base if rule.is_compounded else subtotal
        tax_amount = int((base_amount * rule.rate) / 10000)  # rate is percentage * 100
        
        applicable_taxes.append({
            "tax_name": rule.tax_name,
            "rate": rule.rate / 100,  # Convert back to percentage
            "rate_display": f"{rule.rate / 100}%",
            "base_amount": base_amount,
            "tax_amount": tax_amount,
            "is_compounded": rule.is_compounded
        })
        
        total_tax += tax_amount
        
        # If compounded, add this tax to base for next calculation
        if rule.is_compounded:
            compounded_base += tax_amount
    
    return {
        "subtotal": subtotal,
        "order_type": order_type,
        "taxes": applicable_taxes,
        "total_tax": total_tax,
        "total_with_tax": subtotal + total_tax
    }


# Settings routes (Singleton)
@settings_router.get("", response_model=SettingsResponse)
def get_settings(db: Session = Depends(get_db)):
    """Get system settings"""
    settings = db.query(Settings).first()
    if not settings:
        # Create default settings if none exist
        settings = Settings(
            restaurant_name="Restaurant POS",
            currency="USD",
            timezone="UTC",
            language="en",
            tax_rate=0,  # 0%
            service_charge=0,  # 0%
            enable_tipping=True,
            default_tip_percentages=[1000, 1500, 2000],  # 10%, 15%, 20%
            print_kot_automatically=True,
            auto_print_receipt=False,
            email_notifications=True,
            sms_notifications=False,
            low_stock_alerts=True
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    return settings


@settings_router.put("", response_model=SettingsResponse)
def update_settings(settings: SettingsUpdate, db: Session = Depends(get_db)):
    """Update system settings"""
    db_settings = db.query(Settings).first()
    
    if not db_settings:
        # Create settings if they don't exist
        db_settings = Settings(**settings.model_dump(exclude_unset=True))
        db.add(db_settings)
    else:
        # Update existing settings
        update_data = settings.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_settings, field, value)
    
    db.commit()
    db.refresh(db_settings)
    return db_settings


@settings_router.post("/initialize", response_model=SettingsResponse, status_code=201)
def initialize_settings(settings: SettingsCreate, db: Session = Depends(get_db)):
    """Initialize system settings (should only be called once during setup)"""
    existing = db.query(Settings).first()
    if existing:
        raise HTTPException(status_code=400, detail="Settings already initialized")
    
    db_settings = Settings(**settings.model_dump())
    db.add(db_settings)
    db.commit()
    db.refresh(db_settings)
    return db_settings
