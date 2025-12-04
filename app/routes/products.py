"""
Product API routes
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
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.schemas.pagination import PaginationParams, PaginatedResponse
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

router = APIRouter(prefix="/api/v1/products", tags=["products"])

# Configuration for image uploads
UPLOAD_DIR = Path("uploads/products")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png",".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
WEBP_QUALITY = 85  # WebP quality (0-100)
TARGET_IMAGE_SIZE = (800, 800)  # Product images: 800x800px
MAX_OUTPUT_FILE_SIZE = 500 * 1024  # Max output: 500KB


def save_upload_file(upload_file: UploadFile, convert_to_webp: bool = True) -> str:
    """
    Save uploaded file to storage, optionally convert to WebP for better compression
    
    Args:
        upload_file: The uploaded file
        convert_to_webp: Convert to WebP format for smaller size and better quality
        
    Returns:
        str: Full path to the saved file (e.g., /uploads/products/filename.webp)
        
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
            print(f"Image saved: {file_path.name}, Size: {final_size / 1024:.2f} KB ({final_size} bytes)")
            
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
            print(f"Image saved: {file_path.name}, Size: {file_size / 1024:.2f} KB ({file_size} bytes)")
        
        # Return path in format: /uploads/products/filename.webp (matching categories format)
        return f"/uploads/products/{file_path.name}"
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process image: {str(e)}"
        )


@router.get("/")
def list_products(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    category_id: Optional[str] = None,
    available: Optional[bool] = None,
    featured: Optional[bool] = None,
    department: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all products with pagination and optional filtering (with translations)
    """
    query = db.query(Product)
    
    if category_id:
        try:
            cat_uuid = uuid.UUID(category_id)
            query = query.filter(Product.category_id == cat_uuid)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid category_id format"
            )
    
    if available is not None:
        query = query.filter(Product.available == available)
    
    if featured is not None:
        query = query.filter(Product.featured == featured)
    
    if department:
        query = query.filter(Product.department == department)
    
    if search:
        query = query.filter(
            Product.name.ilike(f"%{search}%") | 
            Product.description.ilike(f"%{search}%")
        )
    
    # Apply pagination
    pagination = PaginationParams(page=page, page_size=page_size)
    products, pagination_meta = paginate_query(query, pagination)
    
    # Get user's language and translate
    language = extract_language_from_header(request)
    translated_data = translate_entity_list(
        db=db,
        entities=products,
        language_code=language,
        entity_type="product",
        translatable_fields=["name", "description"]
    )
    
    # Build response with translated data
    products_list = []
    for i, product in enumerate(products):
        products_list.append({
            "id": str(product.id),
            "name": translated_data[i]["name"],
            "slug": product.slug,
            "description": translated_data[i]["description"],
            "price": product.price,
            "cost": product.cost,
            "category_id": str(product.category_id),
            "available": product.available,
            "featured": product.featured,
            "preparation_time": product.preparation_time,
            "department": product.department,
            "printer_tag": product.printer_tag,
            "image": product.image,
            "created_at": product.created_at,
            "updated_at": product.updated_at
        })
    
    return {
        "status": "success",
        "message": "Products retrieved successfully",
        "data": products_list,
        "pagination": pagination_meta.model_dump()
    }


@router.get("/{product_id}")
def get_product(product_id: uuid.UUID, request: Request, db: Session = Depends(get_db)):
    """
    Get a specific product by ID (with translations)
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )
    
    # Get language and translate
    language = extract_language_from_header(request)
    
    translated_name = get_translated_field(
        db=db,
        entity_type="product",
        entity_id=str(product.id),
        field_name="name",
        language_code=language,
        default_value=product.name
    )
    
    translated_description = get_translated_field(
        db=db,
        entity_type="product",
        entity_id=str(product.id),
        field_name="description",
        language_code=language,
        default_value=product.description or ""
    )
    
    return success_response(
        data={
            "id": str(product.id),
            "name": translated_name,
            "slug": product.slug,
            "description": translated_description,
            "price": product.price,
            "cost": product.cost,
            "category_id": str(product.category_id),
            "available": product.available,
            "featured": product.featured,
            "preparation_time": product.preparation_time,
            "department": product.department,
            "printer_tag": product.printer_tag,
            "image": product.image,
            "created_at": product.created_at,
            "updated_at": product.updated_at
        },
        message="Product retrieved successfully"
    )


@router.get("/slug/{slug}")
def get_product_by_slug(slug: str, request: Request, db: Session = Depends(get_db)):
    """
    Get a specific product by slug (with translations)
    """
    product = db.query(Product).filter(Product.slug == slug).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with slug '{slug}' not found"
        )
    
    # Get language and translate
    language = extract_language_from_header(request)
    
    translated_name = get_translated_field(
        db=db,
        entity_type="product",
        entity_id=str(product.id),
        field_name="name",
        language_code=language,
        default_value=product.name
    )
    
    translated_description = get_translated_field(
        db=db,
        entity_type="product",
        entity_id=str(product.id),
        field_name="description",
        language_code=language,
        default_value=product.description or ""
    )
    
    return success_response(
        data={
            "id": str(product.id),
            "name": translated_name,
            "slug": product.slug,
            "description": translated_description,
            "price": product.price,
            "cost": product.cost,
            "category_id": str(product.category_id),
            "available": product.available,
            "featured": product.featured,
            "preparation_time": product.preparation_time,
            "department": product.department,
            "printer_tag": product.printer_tag,
            "image": product.image,
            "created_at": product.created_at,
            "updated_at": product.updated_at
        },
        message="Product retrieved successfully"
    )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_product(
    name: str = Form(...),
    slug: str = Form(...),
    category_id: str = Form(...),
    price: int = Form(...),
    description: Optional[str] = Form(None),
    cost: int = Form(0),
    available: bool = Form(True),
    featured: bool = Form(False),
    preparation_time: int = Form(15),
    department: str = Form("kitchen"),
    printer_tag: Optional[str] = Form(None),
    translations_json: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Create a new product with optional image upload (converts to WebP)
    
    Args:
        name: Product name (required)
        slug: URL-friendly slug (required, unique)
        category_id: Category UUID (required)
        price: Price in cents (required)
        description: Product description (optional)
        cost: Cost in cents (optional, default: 0)
        available: Availability status (optional, default: true)
        featured: Featured status (optional, default: false)
        preparation_time: Prep time in minutes (optional, default: 15)
        department: Department (optional, default: "kitchen")
        printer_tag: Printer tag (optional)
        image: Image file (optional, auto-converts to WebP, max 10MB)
        db: Database session
    """
    # Check if slug already exists
    existing = db.query(Product).filter(Product.slug == slug).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with slug '{slug}' already exists"
        )
    
    # Verify category exists
    from app.models.product import Category
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )
    
    # Handle image upload if provided
    image_path = None
    if image and image.filename:
        image_path = save_upload_file(image, convert_to_webp=True)
    
    # Create product
    db_product = Product(
        name=name,
        slug=slug,
        category_id=category_id,
        price=price,
        description=description,
        cost=cost,
        available=available,
        featured=featured,
        preparation_time=preparation_time,
        department=department,
        printer_tag=printer_tag,
        image=image_path
    )
    
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    # Add translations if provided
    if translations_json:
        try:
            translations = json.loads(translations_json)
            create_entity_translations(
                db=db,
                entity_type="product",
                entity_id=str(db_product.id),
                translations=translations
            )
        except json.JSONDecodeError:
            pass  # Don't fail product creation if translation JSON is invalid
    
    return created_response(
        data={
            "id": str(db_product.id),
            "name": db_product.name,
            "slug": db_product.slug,
            "category_id": str(db_product.category_id),
            "price": db_product.price,
            "description": db_product.description,
            "cost": db_product.cost,
            "available": db_product.available,
            "featured": db_product.featured,
            "preparation_time": db_product.preparation_time,
            "department": db_product.department,
            "printer_tag": db_product.printer_tag,
            "image": db_product.image,
            "created_at": db_product.created_at,
            "updated_at": db_product.updated_at
        },
        message="Product created successfully"
    )


@router.put("/{product_id}")
async def update_product(
    product_id: uuid.UUID,
    name: Optional[str] = Form(None),
    slug: Optional[str] = Form(None),
    category_id: Optional[str] = Form(None),
    price: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    cost: Optional[int] = Form(None),
    available: Optional[bool] = Form(None),
    featured: Optional[bool] = Form(None),
    preparation_time: Optional[int] = Form(None),
    department: Optional[str] = Form(None),
    printer_tag: Optional[str] = Form(None),
    translations_json: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Update an existing product with optional new image (auto-converts to WebP)
    
    Args:
        product_id: Product UUID
        name: Product name (optional)
        slug: URL-friendly slug (optional)
        category_id: Category UUID (optional)
        price: Price in cents (optional)
        description: Product description (optional)
        cost: Cost in cents (optional)
        available: Availability status (optional)
        featured: Featured status (optional)
        preparation_time: Prep time in minutes (optional)
        department: Department (optional)
        printer_tag: Printer tag (optional)
        image: New image file (optional, auto-converts to WebP, max 10MB)
        db: Database session
    """
    db_product = db.query(Product).filter(Product.id == str(product_id)).first()
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )
    
    # Check if slug is being changed and if it already exists
    if slug and slug != db_product.slug:
        existing = db.query(Product).filter(Product.slug == slug).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with slug '{slug}' already exists"
            )
    
    # Verify category exists if being changed
    if category_id:
        from app.models.product import Category
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id {category_id} not found"
            )
    
    # Update fields if provided
    if name is not None:
        db_product.name = name
    if slug is not None:
        db_product.slug = slug
    if category_id is not None:
        db_product.category_id = category_id
    if price is not None:
        db_product.price = price
    if description is not None:
        db_product.description = description
    if cost is not None:
        db_product.cost = cost
    if available is not None:
        db_product.available = available
    if featured is not None:
        db_product.featured = featured
    if preparation_time is not None:
        db_product.preparation_time = preparation_time
    if department is not None:
        db_product.department = department
    if printer_tag is not None:
        db_product.printer_tag = printer_tag
    
    # Handle image upload if provided
    if image and image.filename:
        # Delete old image if exists
        if db_product.image:
            # Handle both old format and new format
            old_image_path = db_product.image.lstrip('/')
            old_image_full_path = Path(old_image_path) if not old_image_path.startswith('uploads/') else Path(old_image_path)
            
            if not str(old_image_full_path).startswith('uploads/'):
                old_image_full_path = Path("uploads") / old_image_path
            
            if old_image_full_path.exists():
                try:
                    os.remove(old_image_full_path)
                except Exception as e:
                    print(f"Failed to delete old image: {e}")
        
        # Save new image (converts to WebP)
        image_path = save_upload_file(image, convert_to_webp=True)
        db_product.image = image_path
    
    db.commit()
    db.refresh(db_product)
    
    # Update translations if provided
    if translations_json:
        try:
            translations = json.loads(translations_json)
            update_entity_translations(
                db=db,
                entity_type="product",
                entity_id=str(product_id),
                translations=translations
            )
        except json.JSONDecodeError:
            pass
    
    return success_response(
        data={
            "id": str(db_product.id),
            "name": db_product.name,
            "slug": db_product.slug,
            "category_id": str(db_product.category_id),
            "price": db_product.price,
            "description": db_product.description,
            "cost": db_product.cost,
            "available": db_product.available,
            "featured": db_product.featured,
            "preparation_time": db_product.preparation_time,
            "department": db_product.department,
            "printer_tag": db_product.printer_tag,
            "image": db_product.image,
            "created_at": db_product.created_at,
            "updated_at": db_product.updated_at
        },
        message="Product updated successfully"
    )


@router.delete("/{product_id}")
def delete_product(product_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Delete a product, its translations, and its associated image file
    """
    db_product = db.query(Product).filter(Product.id == str(product_id)).first()
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )
    
    # Delete translations first
    delete_entity_translations(
        db=db,
        entity_type="product",
        entity_id=str(product_id)
    )
    
    # Delete image file if exists
    if db_product.image:
        # Handle both old format and new format
        image_path = db_product.image.lstrip('/')
        image_full_path = Path(image_path) if not image_path.startswith('uploads/') else Path(image_path)
        
        if not str(image_full_path).startswith('uploads/'):
            image_full_path = Path("uploads") / image_path
        
        if image_full_path.exists():
            try:
                os.remove(image_full_path)
            except Exception as e:
                print(f"Failed to delete image: {e}")
    
    db.delete(db_product)
    db.commit()
    
    return deleted_response(
        message="Product deleted successfully"
    )


@router.patch("/{product_id}/stock", response_model=ProductResponse)
def update_product_stock(
    product_id: uuid.UUID,
    quantity: int = Query(..., description="Stock adjustment (positive or negative)"),
    db: Session = Depends(get_db)
):
    """
    Update product stock quantity
    """
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )
    
    new_stock = db_product.stock + quantity
    if new_stock < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient stock. Current: {db_product.stock}, Requested: {quantity}"
        )
    
    db_product.stock = new_stock
    db.commit()
    db.refresh(db_product)
    return db_product
