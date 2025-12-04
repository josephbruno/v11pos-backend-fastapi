"""
Category API routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import os
import json
from pathlib import Path
import shutil
from PIL import Image
import io

from app.database import get_db
from app.models.product import Category
from app.schemas.product import CategoryCreate, CategoryUpdate, CategoryResponse
from app.schemas.pagination import PaginationParams
from app.response_formatter import success_response, created_response, list_response, deleted_response
from app.utils import paginate_query, create_paginated_response
from app.i18n import (
    create_entity_translations,
    update_entity_translations,
    delete_entity_translations,
    extract_language_from_header,
    translate_entity_list,
    get_translated_field
)

router = APIRouter(prefix="/api/v1/categories", tags=["categories"])

# Configuration for image uploads
UPLOAD_DIR = Path("uploads/categories")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png",".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
WEBP_QUALITY = 85  # WebP quality (0-100)
TARGET_IMAGE_SIZE = (600, 400)  # Category images: 600x400px
MAX_OUTPUT_FILE_SIZE = 200 * 1024  # Max output: 200KB


def save_upload_file(upload_file: UploadFile, convert_to_webp: bool = True) -> str:
    """
    Save uploaded file to storage, optionally convert to WebP for better compression
    
    Args:
        upload_file: The uploaded file
        convert_to_webp: Convert to WebP format for smaller size and better quality
        
    Returns:
        str: Full path to the saved file (e.g., /uploads/categories/filename.webp)
        
    Raises:
        HTTPException: If file validation fails
    """
    # Validate file extension
    file_ext = Path(upload_file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{file_ext}' not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Validate file size
    upload_file.file.seek(0, 2)  # Seek to end
    file_size = upload_file.file.tell()
    upload_file.file.seek(0)  # Reset to beginning
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    try:
        # Read image file
        image_data = upload_file.file.read()
        upload_file.file.seek(0)
        
        if convert_to_webp:
            # Convert to WebP for better compression and quality
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB first if needed
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Calculate aspect ratios
            img_aspect = image.width / image.height
            target_aspect = TARGET_IMAGE_SIZE[0] / TARGET_IMAGE_SIZE[1]
            
            if img_aspect > target_aspect:
                # Image is wider - crop sides (center crop)
                new_width = int(image.height * target_aspect)
                left = (image.width - new_width) // 2
                image = image.crop((left, 0, left + new_width, image.height))
            elif img_aspect < target_aspect:
                # Image is taller - crop top/bottom (center crop)
                new_height = int(image.width / target_aspect)
                top = (image.height - new_height) // 2
                image = image.crop((0, top, image.width, top + new_height))
            
            # Now resize to exact target size (stretch/shrink to fill completely)
            image = image.resize(TARGET_IMAGE_SIZE, Image.Resampling.LANCZOS)
            
            # Generate unique filename with .webp extension
            base_name = Path(upload_file.filename).stem
            file_path = UPLOAD_DIR / f"{base_name}.webp"
            counter = 1
            while file_path.exists():
                file_path = UPLOAD_DIR / f"{base_name}_{counter}.webp"
                counter += 1
            
            # Save as WebP with quality adjustment to meet file size requirement
            quality = WEBP_QUALITY
            final_size = 0
            for attempt in range(5):  # Try up to 5 times with decreasing quality
                buffer = io.BytesIO()
                image.save(buffer, 'WEBP', quality=quality, method=6)
                
                if buffer.tell() <= MAX_OUTPUT_FILE_SIZE or quality <= 50:
                    # File size is acceptable or quality is too low to reduce further
                    with open(file_path, 'wb') as f:
                        f.write(buffer.getvalue())
                    final_size = buffer.tell()
                    break
                
                # Reduce quality for next attempt
                quality -= 10
            
            # Set full permissions (read, write, execute for all users)
            os.chmod(file_path, 0o777)
            
            # Log the saved image size
            print(f"Category image saved: {file_path.name}, Size: {final_size / 1024:.2f} KB ({final_size} bytes)")
            
        else:
            # Save original format
            file_path = UPLOAD_DIR / upload_file.filename
            counter = 1
            while file_path.exists():
                name = Path(upload_file.filename).stem
                ext = Path(upload_file.filename).suffix
                file_path = UPLOAD_DIR / f"{name}_{counter}{ext}"
                counter += 1
            
            with open(file_path, "wb") as buffer:
                buffer.write(image_data)
            
            # Set full permissions (read, write, execute for all users)
            os.chmod(file_path, 0o777)
            
            # Log the saved image size
            file_size = len(image_data)
            print(f"Category image saved: {file_path.name}, Size: {file_size / 1024:.2f} KB ({file_size} bytes)")
        
        # Return path in format: /uploads/categories/filename.webp (matching products format)
        return f"/uploads/categories/{file_path.name}"
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process image: {str(e)}"
        )


@router.get("/")
def list_categories(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    List all categories with pagination and optional filtering (with translations)
    """
    query = db.query(Category)
    
    if active is not None:
        query = query.filter(Category.active == active)
    
    query = query.order_by(Category.sort_order)
    
    # Apply pagination
    pagination = PaginationParams(page=page, page_size=page_size)
    categories, pagination_meta = paginate_query(query, pagination)
    
    # Get language and translate
    language = extract_language_from_header(request)
    translated_data = translate_entity_list(
        db=db,
        entities=categories,
        language_code=language,
        entity_type="category",
        translatable_fields=["name", "description"]
    )
    
    # Convert to dict for response with translations
    categories_data = [
        {
            "id": str(cat.id),
            "name": translated_data[i]["name"],
            "slug": cat.slug,
            "description": translated_data[i]["description"],
            "active": cat.active,
            "sort_order": cat.sort_order,
            "image": cat.image,
            "created_at": cat.created_at,
            "updated_at": cat.updated_at
        }
        for i, cat in enumerate(categories)
    ]
    
    return {
        "status": "success",
        "message": "Categories retrieved successfully",
        "data": categories_data,
        "pagination": pagination_meta.model_dump()
    }


@router.get("/{category_id}")
def get_category(category_id: uuid.UUID, request: Request, db: Session = Depends(get_db)):
    """
    Get a specific category by ID (with translations)
    """
    category = db.query(Category).filter(Category.id == str(category_id)).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )
    
    # Get language and translate
    language = extract_language_from_header(request)
    
    translated_name = get_translated_field(
        db=db,
        entity_type="category",
        entity_id=category.id,
        field_name="name",
        language_code=language,
        default_value=category.name
    )
    
    translated_description = get_translated_field(
        db=db,
        entity_type="category",
        entity_id=category.id,
        field_name="description",
        language_code=language,
        default_value=category.description or ""
    )
    
    return success_response(
        data={
            "id": str(category.id),
            "name": translated_name,
            "slug": category.slug,
            "description": translated_description,
            "active": category.active,
            "sort_order": category.sort_order,
            "image": category.image,
            "created_at": category.created_at,
            "updated_at": category.updated_at
        },
        message="Category fetched successfully"
    )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_category(
    name: str = Form(...),
    slug: str = Form(...),
    description: Optional[str] = Form(None),
    active: bool = Form(True),
    sort_order: int = Form(0),
    translations_json: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Create a new category with optional image upload
    
    Args:
        name: Category name (required)
        slug: URL-friendly slug (required)
        description: Category description (optional)
        active: Active status (default: True)
        sort_order: Sort order (default: 0)
        image: Image file (optional, jpg/jpeg/png/gif/webp, max 10MB)
        db: Database session
    """
    # Check if slug already exists
    existing = db.query(Category).filter(Category.slug == slug).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with slug '{slug}' already exists"
        )
    
    # Handle image upload if provided
    image_path = None
    if image and image.filename:
        image_path = save_upload_file(image)
    
    # Create category
    db_category = Category(
        name=name,
        slug=slug,
        description=description,
        active=active,
        sort_order=sort_order,
        image=image_path
    )
    
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    
    # Add translations if provided
    if translations_json:
        try:
            translations = json.loads(translations_json)
            create_entity_translations(
                db=db,
                entity_type="category",
                entity_id=db_category.id,
                translations=translations
            )
        except json.JSONDecodeError:
            pass
    
    return created_response(
        data={
            "id": str(db_category.id),
            "name": db_category.name,
            "slug": db_category.slug,
            "description": db_category.description,
            "active": db_category.active,
            "sort_order": db_category.sort_order,
            "image": db_category.image,
            "created_at": db_category.created_at,
            "updated_at": db_category.updated_at
        },
        message="Category created successfully"
    )


@router.put("/{category_id}")
async def update_category(
    category_id: uuid.UUID,
    name: Optional[str] = Form(None),
    slug: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    active: Optional[bool] = Form(None),
    sort_order: Optional[int] = Form(None),
    translations_json: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Update an existing category with optional image upload
    
    Args:
        category_id: Category UUID
        name: Category name (optional)
        slug: URL-friendly slug (optional)
        description: Category description (optional)
        active: Active status (optional)
        sort_order: Sort order (optional)
        image: New image file (optional, jpg/jpeg/png/gif/webp, max 10MB)
        db: Database session
    """
    db_category = db.query(Category).filter(Category.id == str(category_id)).first()
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )
    
    # Check if slug is being changed and if it already exists
    if slug and slug != db_category.slug:
        existing = db.query(Category).filter(Category.slug == slug).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with slug '{slug}' already exists"
            )
    
    # Update fields if provided
    if name is not None:
        db_category.name = name
    if slug is not None:
        db_category.slug = slug
    if description is not None:
        db_category.description = description
    if active is not None:
        db_category.active = active
    if sort_order is not None:
        db_category.sort_order = sort_order
    
    # Handle image upload if provided
    if image and image.filename:
        # Delete old image if exists
        if db_category.image:
            # Handle both old format (categories/file.jpg) and new format (/uploads/categories/file.jpg)
            old_image_path = db_category.image.lstrip('/')  # Remove leading slash
            old_image_full_path = Path(old_image_path) if not old_image_path.startswith('uploads/') else Path(old_image_path)
            
            # If path doesn't start with uploads/, prepend it
            if not str(old_image_full_path).startswith('uploads/'):
                old_image_full_path = Path("uploads") / old_image_path
            
            if old_image_full_path.exists():
                try:
                    os.remove(old_image_full_path)
                except Exception as e:
                    print(f"Failed to delete old image: {e}")
        
        # Save new image
        image_path = save_upload_file(image)
        db_category.image = image_path
    
    db.commit()
    db.refresh(db_category)
    
    # Update translations if provided
    if translations_json:
        try:
            translations = json.loads(translations_json)
            update_entity_translations(
                db=db,
                entity_type="category",
                entity_id=str(category_id),
                translations=translations
            )
        except json.JSONDecodeError:
            pass
    
    return success_response(
        data={
            "id": str(db_category.id),
            "name": db_category.name,
            "slug": db_category.slug,
            "description": db_category.description,
            "active": db_category.active,
            "sort_order": db_category.sort_order,
            "image": db_category.image,
            "created_at": db_category.created_at,
            "updated_at": db_category.updated_at
        },
        message="Category updated successfully"
    )


@router.delete("/{category_id}")
def delete_category(category_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Delete a category and its translations
    """
    db_category = db.query(Category).filter(Category.id == str(category_id)).first()
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )
    
    # Check if category has products
    if db_category.products:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category with existing products"
        )
    
    # Delete translations first
    delete_entity_translations(
        db=db,
        entity_type="category",
        entity_id=str(category_id)
    )
    
    # Delete image file if exists
    if db_category.image:
        # Handle both old format (categories/file.jpg) and new format (/uploads/categories/file.jpg)
        image_path = db_category.image.lstrip('/')  # Remove leading slash
        image_full_path = Path(image_path) if not image_path.startswith('uploads/') else Path(image_path)
        
        # If path doesn't start with uploads/, prepend it
        if not str(image_full_path).startswith('uploads/'):
            image_full_path = Path("uploads") / image_path
        
        if image_full_path.exists():
            try:
                os.remove(image_full_path)
            except Exception as e:
                print(f"Failed to delete image: {e}")
    
    db.delete(db_category)
    db.commit()
    
    return deleted_response(
        message="Category deleted successfully"
    )
