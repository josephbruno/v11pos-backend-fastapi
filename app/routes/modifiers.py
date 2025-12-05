"""
Modifier API routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.product import Modifier, ModifierOption
from app.schemas.product import (
    ModifierCreate, ModifierResponse,
    ModifierOptionCreate, ModifierOptionResponse
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

router = APIRouter(prefix="/api/v1/modifiers", tags=["modifiers"])


@router.get("/")
def list_modifiers(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all modifiers with full data including options, with pagination and optional filtering
    """
    query = db.query(Modifier)
    
    if category:
        query = query.filter(Modifier.category == category)
    
    # Apply pagination
    pagination = PaginationParams(page=page, page_size=page_size)
    modifiers, pagination_meta = paginate_query(query, pagination)
    
    # Get user's language for translations
    language = extract_language_from_header(request)
    
    # Build full modifier data with options
    modifiers_list = []
    for modifier in modifiers:
        # Translate modifier name
        translated_name = get_translated_field(
            db=db,
            entity_type="modifier",
            entity_id=modifier.id,
            field_name="name",
            language_code=language,
            default_value=modifier.name
        )
        
        # Translate modifier options
        translated_options = []
        for option in modifier.options:
            translated_option_name = get_translated_field(
                db=db,
                entity_type="modifier_option",
                entity_id=option.id,
                field_name="name",
                language_code=language,
                default_value=option.name
            )
            
            translated_options.append({
                "id": option.id,
                "name": translated_option_name,
                "price": option.price,
                "available": option.available,
                "sort_order": option.sort_order,
                "created_at": option.created_at,
                "updated_at": option.updated_at
            })
        
        modifiers_list.append({
            "id": modifier.id,
            "name": translated_name,
            "type": modifier.type,
            "category": modifier.category,
            "required": modifier.required,
            "min_selections": modifier.min_selections,
            "max_selections": modifier.max_selections,
            "options": translated_options,
            "created_at": modifier.created_at,
            "updated_at": modifier.updated_at
        })
    
    return {
        "status": "success",
        "message": "Modifiers retrieved successfully",
        "data": modifiers_list,
        "pagination": pagination_meta.model_dump()
    }


@router.get("/{modifier_id}", response_model=ModifierResponse)
def get_modifier(request: Request, modifier_id: str, db: Session = Depends(get_db)):
    """
    Get a specific modifier by ID
    """
    modifier = db.query(Modifier).filter(Modifier.id == modifier_id).first()
    if not modifier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Modifier with id {modifier_id} not found"
        )
    
    # Apply translations
    language = extract_language_from_header(request)
    translated_name = get_translated_field(db, "modifier", modifier_id, "name", language, modifier.name)
    
    # Convert to dict and update translated fields
    modifier_dict = {
        "id": modifier.id,
        "name": translated_name,
        "category": modifier.category,
        "selection_type": modifier.selection_type,
        "min_selections": modifier.min_selections,
        "max_selections": modifier.max_selections,
        "is_active": modifier.is_active,
        "sort_order": modifier.sort_order,
        "created_at": modifier.created_at,
        "updated_at": modifier.updated_at,
        "options": modifier.options
    }
    
    return modifier_dict


@router.post("/", response_model=ModifierResponse, status_code=status.HTTP_201_CREATED)
def create_modifier(
    modifier: ModifierCreate,
    translations_json: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Create a new modifier
    """
    db_modifier = Modifier(**modifier.model_dump())
    db.add(db_modifier)
    db.commit()
    db.refresh(db_modifier)
    
    # Handle translations if provided
    if translations_json:
        try:
            import json
            translations_data = json.loads(translations_json)
            create_entity_translations(
                db=db,
                entity_type="modifier",
                entity_id=db_modifier.id,
                translations=translations_data
            )
        except json.JSONDecodeError:
            pass  # Silently skip invalid JSON
    
    return db_modifier


@router.delete("/{modifier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_modifier(modifier_id: str, db: Session = Depends(get_db)):
    """
    Delete a modifier
    """
    db_modifier = db.query(Modifier).filter(Modifier.id == modifier_id).first()
    if not db_modifier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Modifier with id {modifier_id} not found"
        )
    
    # Delete translations first
    delete_entity_translations(db=db, entity_type="modifier", entity_id=modifier_id)
    
    db.delete(db_modifier)
    db.commit()
    return None


# Modifier Options endpoints
options_router = APIRouter(prefix="/api/v1/modifier-options", tags=["modifier-options"])


@router.get("/{modifier_id}/options")
def list_modifier_options(
    request: Request,
    modifier_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    List all options for a specific modifier with pagination
    """
    # Verify modifier exists
    modifier = db.query(Modifier).filter(Modifier.id == modifier_id).first()
    if not modifier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Modifier with id {modifier_id} not found"
        )
    
    query = db.query(ModifierOption).filter(
        ModifierOption.modifier_id == modifier_id
    ).order_by(ModifierOption.sort_order)
    
    # Apply pagination
    pagination = PaginationParams(page=page, page_size=page_size)
    options, pagination_meta = paginate_query(query, pagination)
    
    # Apply translations
    language = extract_language_from_header(request)
    translated_options = translate_entity_list(
        db=db,
        entities=options,
        language_code=language,
        entity_type="modifier_option",
        translatable_fields=["name"]
    )
    
    return create_paginated_response(translated_options, pagination_meta, "Modifier options retrieved successfully")


@router.post("/{modifier_id}/options", response_model=ModifierOptionResponse, status_code=status.HTTP_201_CREATED)
def create_modifier_option(
    modifier_id: str,
    option: ModifierOptionCreate,
    translations_json: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Create a new modifier option
    """
    # Verify modifier exists
    modifier = db.query(Modifier).filter(Modifier.id == modifier_id).first()
    if not modifier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Modifier with id {modifier_id} not found"
        )
    
    option_data = option.model_dump()
    option_data['modifier_id'] = modifier_id
    
    db_option = ModifierOption(**option_data)
    db.add(db_option)
    db.commit()
    db.refresh(db_option)
    
    # Handle translations if provided
    if translations_json:
        try:
            import json
            translations_data = json.loads(translations_json)
            create_entity_translations(
                db=db,
                entity_type="modifier_option",
                entity_id=db_option.id,
                translations=translations_data
            )
        except json.JSONDecodeError:
            pass  # Silently skip invalid JSON
    
    return db_option


@options_router.delete("/{option_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_modifier_option(option_id: str, db: Session = Depends(get_db)):
    """
    Delete a modifier option
    """
    db_option = db.query(ModifierOption).filter(ModifierOption.id == option_id).first()
    if not db_option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Modifier option with id {option_id} not found"
        )
    
    # Delete translations first
    delete_entity_translations(db=db, entity_type="modifier_option", entity_id=option_id)
    
    db.delete(db_option)
    db.commit()
    return None
