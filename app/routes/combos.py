"""
Combo Products API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json

from app.database import get_db
from app.models.product import ComboProduct, ComboItem, Product, Category
from app.schemas.product import (
    ComboProductCreate,
    ComboProductUpdate,
    ComboProductResponse,
    ComboItemCreate,
    ComboItemResponse
)
from app.schemas.pagination import PaginationParams
from app.response_formatter import success_response, created_response, list_response, deleted_response, error_response
from app.utils import paginate_query, create_paginated_response
from app.i18n import (
    create_entity_translations,
    update_entity_translations,
    delete_entity_translations,
    extract_language_from_header,
    translate_entity_list,
    get_translated_field
)


router = APIRouter(prefix="/api/v1/combos", tags=["Combo Products"])
items_router = APIRouter(prefix="/api/v1/combo-items", tags=["Combo Items"])


@router.get("")
def get_combos(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    category_id: Optional[str] = None,
    available: Optional[bool] = None,
    featured: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get all combo products with pagination and optional filtering"""
    query = db.query(ComboProduct)
    
    if category_id:
        query = query.filter(ComboProduct.category_id == category_id)
    if available is not None:
        query = query.filter(ComboProduct.available == available)
    if featured is not None:
        query = query.filter(ComboProduct.featured == featured)
    
    # Filter by validity dates
    now = datetime.utcnow()
    query = query.filter(
        (ComboProduct.valid_from.is_(None) | (ComboProduct.valid_from <= now)) &
        (ComboProduct.valid_until.is_(None) | (ComboProduct.valid_until >= now))
    )
    
    # Apply pagination
    pagination = PaginationParams(page=page, page_size=page_size)
    combos, pagination_meta = paginate_query(query, pagination)
    
    # Apply translations
    language = extract_language_from_header(request)
    translated_combos = translate_entity_list(
        db=db,
        entities=combos,
        language_code=language,
        entity_type="combo",
        translatable_fields=["name", "description"]
    )
    
    return create_paginated_response(translated_combos, pagination_meta, "Combos retrieved successfully")


@router.get("/{combo_id}", response_model=ComboProductResponse)
def get_combo(request: Request, combo_id: str, db: Session = Depends(get_db)):
    """Get combo product by ID"""
    combo = db.query(ComboProduct).filter(ComboProduct.id == combo_id).first()
    if not combo:
        raise HTTPException(status_code=404, detail="Combo product not found")
    
    # Apply translations
    language = extract_language_from_header(request)
    translated_name = get_translated_field(db, "combo", combo_id, "name", language, combo.name)
    translated_description = get_translated_field(db, "combo", combo_id, "description", language, combo.description)
    
    # Convert to dict and update translated fields
    combo_dict = {
        "id": combo.id,
        "name": translated_name,
        "description": translated_description,
        "slug": combo.slug,
        "category_id": combo.category_id,
        "combo_price": combo.combo_price,
        "original_price": combo.original_price,
        "discount_percentage": combo.discount_percentage,
        "available": combo.available,
        "featured": combo.featured,
        "image_url": combo.image_url,
        "valid_from": combo.valid_from,
        "valid_until": combo.valid_until,
        "max_quantity": combo.max_quantity,
        "created_at": combo.created_at,
        "updated_at": combo.updated_at,
        "category": combo.category,
        "items": combo.items
    }
    
    return combo_dict


@router.post("", response_model=ComboProductResponse, status_code=201)
def create_combo(
    combo: ComboProductCreate,
    translations_json: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Create a new combo product"""
    # Verify category exists
    category = db.query(Category).filter(Category.id == combo.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check for duplicate slug
    existing = db.query(ComboProduct).filter(ComboProduct.slug == combo.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Slug already exists")
    
    # Validate date range
    if combo.valid_from and combo.valid_until:
        if combo.valid_from >= combo.valid_until:
            raise HTTPException(status_code=400, detail="valid_from must be before valid_until")
    
    db_combo = ComboProduct(**combo.model_dump())
    db.add(db_combo)
    db.commit()
    db.refresh(db_combo)
    
    # Handle translations if provided
    if translations_json:
        try:
            translations_data = json.loads(translations_json)
            create_entity_translations(
                db=db,
                entity_type="combo",
                entity_id=db_combo.id,
                translations=translations_data
            )
        except json.JSONDecodeError:
            pass  # Silently skip invalid JSON
    
    return db_combo


@router.put("/{combo_id}", response_model=ComboProductResponse)
def update_combo(
    combo_id: str,
    combo: ComboProductUpdate,
    translations_json: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Update a combo product"""
    db_combo = db.query(ComboProduct).filter(ComboProduct.id == combo_id).first()
    if not db_combo:
        raise HTTPException(status_code=404, detail="Combo product not found")
    
    update_data = combo.model_dump(exclude_unset=True)
    
    # Check slug uniqueness if being updated
    if "slug" in update_data:
        existing = db.query(ComboProduct).filter(
            ComboProduct.slug == update_data["slug"],
            ComboProduct.id != combo_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Slug already exists")
    
    # Verify category if being updated
    if "category_id" in update_data:
        category = db.query(Category).filter(Category.id == update_data["category_id"]).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
    
    # Validate date range if being updated
    valid_from = update_data.get("valid_from", db_combo.valid_from)
    valid_until = update_data.get("valid_until", db_combo.valid_until)
    if valid_from and valid_until:
        if valid_from >= valid_until:
            raise HTTPException(status_code=400, detail="valid_from must be before valid_until")
    
    for field, value in update_data.items():
        setattr(db_combo, field, value)
    
    db.commit()
    db.refresh(db_combo)
    
    # Handle translations if provided
    if translations_json:
        try:
            translations_data = json.loads(translations_json)
            update_entity_translations(
                db=db,
                entity_type="combo",
                entity_id=combo_id,
                translations=translations_data
            )
        except json.JSONDecodeError:
            pass  # Silently skip invalid JSON
    
    return db_combo


@router.delete("/{combo_id}", status_code=204)
def delete_combo(combo_id: str, db: Session = Depends(get_db)):
    """Delete a combo product"""
    db_combo = db.query(ComboProduct).filter(ComboProduct.id == combo_id).first()
    if not db_combo:
        raise HTTPException(status_code=404, detail="Combo product not found")
    
    # Delete translations first
    delete_entity_translations(db=db, entity_type="combo", entity_id=combo_id)
    
    db.delete(db_combo)
    db.commit()
    return None


# Combo Items routes
@items_router.get("")
def get_combo_items(
    request: Request,
    combo_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Get all items for a specific combo with pagination"""
    combo = db.query(ComboProduct).filter(ComboProduct.id == combo_id).first()
    if not combo:
        raise HTTPException(status_code=404, detail="Combo product not found")
    
    query = db.query(ComboItem).filter(
        ComboItem.combo_id == combo_id
    ).order_by(ComboItem.sort_order)
    
    # Apply pagination
    pagination = PaginationParams(page=page, page_size=page_size)
    items, pagination_meta = paginate_query(query, pagination)
    
    # Apply translations
    language = extract_language_from_header(request)
    translated_items = translate_entity_list(
        db=db,
        entities=items,
        language_code=language,
        entity_type="combo_item",
        translatable_fields=["custom_name"]
    )
    
    return create_paginated_response(translated_items, pagination_meta, "Combo items retrieved successfully")


@items_router.post("", response_model=ComboItemResponse, status_code=201)
def add_combo_item(
    item: ComboItemCreate,
    translations_json: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Add an item to a combo"""
    # Verify combo exists
    combo = db.query(ComboProduct).filter(ComboProduct.id == item.combo_id).first()
    if not combo:
        raise HTTPException(status_code=404, detail="Combo product not found")
    
    # Verify product exists
    product = db.query(Product).filter(Product.id == item.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check if product is already in combo
    existing = db.query(ComboItem).filter(
        ComboItem.combo_id == item.combo_id,
        ComboItem.product_id == item.product_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Product already in combo")
    
    db_item = ComboItem(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    # Handle translations if provided
    if translations_json:
        try:
            translations_data = json.loads(translations_json)
            create_entity_translations(
                db=db,
                entity_type="combo_item",
                entity_id=db_item.id,
                translations=translations_data
            )
        except json.JSONDecodeError:
            pass  # Silently skip invalid JSON
    
    return db_item


@items_router.delete("/{item_id}", status_code=204)
def remove_combo_item(item_id: str, db: Session = Depends(get_db)):
    """Remove an item from a combo"""
    db_item = db.query(ComboItem).filter(ComboItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Combo item not found")
    
    # Delete translations first
    delete_entity_translations(db=db, entity_type="combo_item", entity_id=item_id)
    
    db.delete(db_item)
    db.commit()
    return None
