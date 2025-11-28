# 🌍 Translation Integration Guide for CRUD Operations

This guide shows how to handle translations when creating, updating, and deleting entities (products, categories, modifiers, combos).

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Request Schema Enhancement](#request-schema-enhancement)
3. [Create Operations](#create-operations)
4. [Update Operations](#update-operations)
5. [Delete Operations](#delete-operations)
6. [Read Operations with Translations](#read-operations-with-translations)
7. [Complete Examples](#complete-examples)
8. [Frontend Integration](#frontend-integration)

---

## Overview

### Translation Strategy

**Two-tier approach:**
1. **Base Entity** (English) - Stored in main tables (products, categories, etc.)
2. **Translations** - Stored in `translations` table for other languages

**Key Principles:**
- English is the default/base language (stored directly in entity)
- Other languages stored in `translations` table
- Translations are optional during create/update
- When deleting an entity, cascade delete its translations

---

## Request Schema Enhancement

### Option 1: Separate Translations Field (Recommended)

Add translations as an optional field in your schemas:

```python
# app/schemas/product.py

from typing import Optional, Dict
from pydantic import BaseModel

class ProductCreate(BaseModel):
    name: str  # English name (required)
    slug: str
    category_id: str
    price: int
    description: Optional[str] = None
    # ... other fields ...
    
    # New field for translations
    translations: Optional[Dict[str, Dict[str, str]]] = None
    # Format: {"es": {"name": "Nombre", "description": "Descripción"}, "fr": {...}}

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    # ... other fields ...
    
    # Translations to add/update
    translations: Optional[Dict[str, Dict[str, str]]] = None


class CategoryCreate(BaseModel):
    name: str  # English name
    slug: str
    description: Optional[str] = None
    # ... other fields ...
    
    translations: Optional[Dict[str, Dict[str, str]]] = None


class ModifierCreate(BaseModel):
    name: str  # English name
    category: str
    # ... other fields ...
    
    translations: Optional[Dict[str, Dict[str, str]]] = None


class ComboProductCreate(BaseModel):
    name: str  # English name
    slug: str
    description: Optional[str] = None
    # ... other fields ...
    
    translations: Optional[Dict[str, Dict[str, str]]] = None
```

### Option 2: Form Data with JSON (For File Uploads)

When using `Form` with file uploads:

```python
from fastapi import Form
import json

async def create_product(
    name: str = Form(...),
    slug: str = Form(...),
    # ... other fields ...
    translations_json: Optional[str] = Form(None),  # JSON string
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    # Parse translations JSON
    translations = None
    if translations_json:
        translations = json.loads(translations_json)
```

---

## Create Operations

### Helper Function for Creating Translations

Create a reusable helper function:

```python
# app/i18n.py (add to existing file)

import uuid
from sqlalchemy.orm import Session
from typing import Dict
from app.models.translation import Translation

def create_entity_translations(
    db: Session,
    entity_type: str,
    entity_id: str,
    translations: Dict[str, Dict[str, str]]
) -> None:
    """
    Create multiple translations for an entity
    
    Args:
        db: Database session
        entity_type: Type of entity (product, category, modifier, combo)
        entity_id: ID of the entity
        translations: Dict with structure: 
                     {"es": {"name": "...", "description": "..."}, "fr": {...}}
    """
    if not translations:
        return
    
    for language_code, fields in translations.items():
        for field_name, translation_value in fields.items():
            if translation_value:  # Only create if value is not empty
                db_translation = Translation(
                    id=str(uuid.uuid4()),
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field_name=field_name,
                    language_code=language_code,
                    translation_value=translation_value
                )
                db.add(db_translation)
    
    db.commit()
```

### Product Create Example

```python
# app/routes/products.py

from app.i18n import create_entity_translations
import json

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_product(
    name: str = Form(...),
    slug: str = Form(...),
    category_id: str = Form(...),
    price: int = Form(...),
    description: Optional[str] = Form(None),
    # ... other fields ...
    translations_json: Optional[str] = Form(None),  # JSON string for translations
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Create a new product with optional translations
    
    translations_json format:
    {
        "es": {
            "name": "Nombre del Producto",
            "description": "Descripción del producto"
        },
        "fr": {
            "name": "Nom du Produit",
            "description": "Description du produit"
        }
    }
    """
    # Handle image upload (existing code)
    image_path = None
    if image:
        image_path = save_upload_file(image)
    
    # Create product (English/base language)
    db_product = Product(
        id=str(uuid.uuid4()),
        name=name,  # English name
        slug=slug,
        category_id=category_id,
        price=price,
        description=description,  # English description
        # ... other fields ...
        image=image_path
    )
    
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    # Create translations if provided
    if translations_json:
        try:
            translations = json.loads(translations_json)
            create_entity_translations(
                db=db,
                entity_type="product",
                entity_id=db_product.id,
                translations=translations
            )
        except json.JSONDecodeError:
            # Log error but don't fail the product creation
            print(f"Invalid translations JSON: {translations_json}")
    
    return created_response(
        data={
            "id": db_product.id,
            "name": db_product.name,
            "slug": db_product.slug,
            # ... other fields ...
            "translations_created": bool(translations_json)
        },
        message="Product created successfully"
    )
```

### Category Create Example

```python
# app/routes/categories.py

from app.i18n import create_entity_translations
import json

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_category(
    name: str = Form(...),
    slug: str = Form(...),
    description: Optional[str] = Form(None),
    translations_json: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """Create category with translations"""
    # Check duplicate slug
    existing = db.query(Category).filter(Category.slug == slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Slug already exists")
    
    # Handle image
    image_path = None
    if image:
        image_path = save_upload_file(image)
    
    # Create category
    db_category = Category(
        id=str(uuid.uuid4()),
        name=name,
        slug=slug,
        description=description,
        image=image_path,
        # ... other fields ...
    )
    
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    
    # Add translations
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
        data={"id": db_category.id, "name": db_category.name},
        message="Category created successfully"
    )
```

### Modifier Create Example

```python
# app/routes/modifiers.py

from app.i18n import create_entity_translations

@router.post("/", response_model=ModifierResponse, status_code=status.HTTP_201_CREATED)
def create_modifier(modifier: ModifierCreate, db: Session = Depends(get_db)):
    """Create a new modifier with translations"""
    # Create modifier
    db_modifier = Modifier(**modifier.model_dump(exclude={"translations"}))
    db.add(db_modifier)
    db.commit()
    db.refresh(db_modifier)
    
    # Add translations if provided
    if modifier.translations:
        create_entity_translations(
            db=db,
            entity_type="modifier",
            entity_id=db_modifier.id,
            translations=modifier.translations
        )
    
    return db_modifier
```

### Combo Create Example

```python
# app/routes/combos.py

from app.i18n import create_entity_translations

@router.post("", response_model=ComboProductResponse, status_code=201)
def create_combo(combo: ComboProductCreate, db: Session = Depends(get_db)):
    """Create a new combo product with translations"""
    # Validate category, slug, dates (existing code)
    # ...
    
    # Create combo
    db_combo = ComboProduct(**combo.model_dump(exclude={"translations"}))
    db.add(db_combo)
    db.commit()
    db.refresh(db_combo)
    
    # Add translations
    if combo.translations:
        create_entity_translations(
            db=db,
            entity_type="combo",
            entity_id=db_combo.id,
            translations=combo.translations
        )
    
    return db_combo
```

---

## Update Operations

### Helper Function for Updating Translations

```python
# app/i18n.py (add to existing file)

def update_entity_translations(
    db: Session,
    entity_type: str,
    entity_id: str,
    translations: Dict[str, Dict[str, str]]
) -> None:
    """
    Update or create translations for an entity
    
    Args:
        db: Database session
        entity_type: Type of entity
        entity_id: ID of the entity
        translations: Dict with translations to update/create
    """
    if not translations:
        return
    
    for language_code, fields in translations.items():
        for field_name, translation_value in fields.items():
            if translation_value:
                # Check if translation exists
                existing = db.query(Translation).filter(
                    Translation.entity_type == entity_type,
                    Translation.entity_id == entity_id,
                    Translation.field_name == field_name,
                    Translation.language_code == language_code
                ).first()
                
                if existing:
                    # Update existing
                    existing.translation_value = translation_value
                else:
                    # Create new
                    db_translation = Translation(
                        id=str(uuid.uuid4()),
                        entity_type=entity_type,
                        entity_id=entity_id,
                        field_name=field_name,
                        language_code=language_code,
                        translation_value=translation_value
                    )
                    db.add(db_translation)
    
    db.commit()
```

### Product Update Example

```python
# app/routes/products.py

from app.i18n import update_entity_translations
import json

@router.put("/{product_id}")
async def update_product(
    product_id: uuid.UUID,
    name: Optional[str] = Form(None),
    slug: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    translations_json: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    # ... other fields ...
    db: Session = Depends(get_db)
):
    """Update product with translations"""
    # Get existing product
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Update base fields (English)
    if name is not None:
        db_product.name = name
    if slug is not None:
        db_product.slug = slug
    if description is not None:
        db_product.description = description
    # ... update other fields ...
    
    # Handle image update
    if image:
        # Delete old image if exists
        if db_product.image:
            old_image_path = Path(db_product.image.lstrip('/'))
            if old_image_path.exists():
                old_image_path.unlink()
        
        # Save new image
        db_product.image = save_upload_file(image)
    
    db.commit()
    db.refresh(db_product)
    
    # Update translations
    if translations_json:
        try:
            translations = json.loads(translations_json)
            update_entity_translations(
                db=db,
                entity_type="product",
                entity_id=str(db_product.id),
                translations=translations
            )
        except json.JSONDecodeError:
            pass
    
    return success_response(
        data={"id": str(db_product.id), "name": db_product.name},
        message="Product updated successfully"
    )
```

### Category Update Example

```python
# app/routes/categories.py

from app.i18n import update_entity_translations
import json

@router.put("/{category_id}")
async def update_category(
    category_id: uuid.UUID,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    translations_json: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Update category with translations"""
    db_category = db.query(Category).filter(Category.id == str(category_id)).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Update base fields
    if name is not None:
        db_category.name = name
    if description is not None:
        db_category.description = description
    
    db.commit()
    db.refresh(db_category)
    
    # Update translations
    if translations_json:
        try:
            translations = json.loads(translations_json)
            update_entity_translations(
                db=db,
                entity_type="category",
                entity_id=db_category.id,
                translations=translations
            )
        except json.JSONDecodeError:
            pass
    
    return success_response(
        data={"id": db_category.id, "name": db_category.name},
        message="Category updated successfully"
    )
```

### Modifier/Combo Update (Pydantic Schema)

```python
# For routes using Pydantic schemas instead of Form data

@router.put("/{modifier_id}")
def update_modifier(
    modifier_id: str, 
    modifier: ModifierUpdate, 
    db: Session = Depends(get_db)
):
    """Update modifier with translations"""
    db_modifier = db.query(Modifier).filter(Modifier.id == modifier_id).first()
    if not db_modifier:
        raise HTTPException(status_code=404, detail="Modifier not found")
    
    # Extract translations before updating
    translations = modifier.translations if hasattr(modifier, 'translations') else None
    
    # Update base fields
    update_data = modifier.model_dump(exclude_unset=True, exclude={"translations"})
    for field, value in update_data.items():
        setattr(db_modifier, field, value)
    
    db.commit()
    db.refresh(db_modifier)
    
    # Update translations
    if translations:
        update_entity_translations(
            db=db,
            entity_type="modifier",
            entity_id=db_modifier.id,
            translations=translations
        )
    
    return db_modifier
```

---

## Delete Operations

### Helper Function for Deleting Translations

```python
# app/i18n.py (add to existing file)

def delete_entity_translations(
    db: Session,
    entity_type: str,
    entity_id: str
) -> int:
    """
    Delete all translations for an entity
    
    Args:
        db: Database session
        entity_type: Type of entity
        entity_id: ID of the entity
        
    Returns:
        Number of translations deleted
    """
    deleted_count = db.query(Translation).filter(
        Translation.entity_type == entity_type,
        Translation.entity_id == entity_id
    ).delete()
    
    db.commit()
    return deleted_count
```

### Product Delete Example

```python
# app/routes/products.py

from app.i18n import delete_entity_translations

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: uuid.UUID, db: Session = Depends(get_db)):
    """Delete product and its translations"""
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Delete translations first
    delete_entity_translations(
        db=db,
        entity_type="product",
        entity_id=str(db_product.id)
    )
    
    # Delete image if exists
    if db_product.image:
        image_path = Path(db_product.image.lstrip('/'))
        if image_path.exists():
            image_path.unlink()
    
    # Delete product
    db.delete(db_product)
    db.commit()
    
    return None
```

### Category Delete Example

```python
# app/routes/categories.py

from app.i18n import delete_entity_translations

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: uuid.UUID, db: Session = Depends(get_db)):
    """Delete category and its translations"""
    db_category = db.query(Category).filter(Category.id == str(category_id)).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Delete translations
    delete_entity_translations(
        db=db,
        entity_type="category",
        entity_id=db_category.id
    )
    
    # Delete category
    db.delete(db_category)
    db.commit()
    
    return None
```

### Modifier/Combo Delete

```python
# Similar pattern for modifiers and combos

@router.delete("/{modifier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_modifier(modifier_id: str, db: Session = Depends(get_db)):
    """Delete modifier and translations"""
    db_modifier = db.query(Modifier).filter(Modifier.id == modifier_id).first()
    if not db_modifier:
        raise HTTPException(status_code=404, detail="Modifier not found")
    
    # Delete translations
    delete_entity_translations(db=db, entity_type="modifier", entity_id=modifier_id)
    
    # Delete modifier
    db.delete(db_modifier)
    db.commit()
    return None


@router.delete("/{combo_id}", status_code=204)
def delete_combo(combo_id: str, db: Session = Depends(get_db)):
    """Delete combo and translations"""
    db_combo = db.query(ComboProduct).filter(ComboProduct.id == combo_id).first()
    if not db_combo:
        raise HTTPException(status_code=404, detail="Combo not found")
    
    # Delete translations
    delete_entity_translations(db=db, entity_type="combo", entity_id=combo_id)
    
    # Delete combo
    db.delete(db_combo)
    db.commit()
    return None
```

---

## Read Operations with Translations

### Get Single Entity with Translation

```python
# app/routes/products.py

from app.i18n import extract_language_from_header, get_translated_field
from fastapi import Request

@router.get("/{product_id}")
def get_product(
    product_id: uuid.UUID, 
    request: Request,
    db: Session = Depends(get_db)
):
    """Get product with translations based on Accept-Language header"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get user's preferred language
    language = extract_language_from_header(request)
    
    # Get translated fields
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
            "description": translated_description,
            "price": product.price,
            # ... other fields ...
            "language": language
        },
        message="Product retrieved successfully"
    )
```

### List Entities with Translations (Efficient)

```python
# app/routes/products.py

from app.i18n import translate_entity_list, extract_language_from_header
from fastapi import Request

@router.get("/")
def list_products(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List products with translations"""
    query = db.query(Product)
    
    # Apply filters, pagination (existing code)
    pagination = PaginationParams(page=page, page_size=page_size)
    products, pagination_meta = paginate_query(query, pagination)
    
    # Get user's language
    language = extract_language_from_header(request)
    
    # Translate all products efficiently (single query)
    translated_data = translate_entity_list(
        db=db,
        entities=products,
        language_code=language,
        entity_type="product",
        translatable_fields=["name", "description"]
    )
    
    # Build response with translated data
    products_response = []
    for i, product in enumerate(products):
        products_response.append({
            "id": str(product.id),
            "name": translated_data[i]["name"],
            "description": translated_data[i]["description"],
            "price": product.price,
            # ... other fields ...
        })
    
    return {
        "status": "success",
        "message": "Products retrieved successfully",
        "data": products_response,
        "pagination": pagination_meta.model_dump(),
        "language": language
    }
```

---

## Complete Examples

### Complete Product Route with Translations

Here's a complete example showing all operations:

```python
# app/routes/products.py

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
import uuid
import json
from typing import Optional
from pathlib import Path

from app.database import get_db
from app.models.product import Product
from app.i18n import (
    create_entity_translations,
    update_entity_translations,
    delete_entity_translations,
    extract_language_from_header,
    translate_entity_list
)
from app.response_formatter import success_response, created_response

router = APIRouter(prefix="/api/v1/products", tags=["products"])


@router.post("/", status_code=201)
async def create_product(
    name: str = Form(...),
    slug: str = Form(...),
    price: int = Form(...),
    description: Optional[str] = Form(None),
    translations_json: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Create product with translations
    
    translations_json example:
    {"es": {"name": "Producto", "description": "Descripción"}}
    """
    # Create product
    db_product = Product(
        id=str(uuid.uuid4()),
        name=name,
        slug=slug,
        price=price,
        description=description
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    # Add translations
    if translations_json:
        try:
            translations = json.loads(translations_json)
            create_entity_translations(
                db=db,
                entity_type="product",
                entity_id=db_product.id,
                translations=translations
            )
        except json.JSONDecodeError:
            pass
    
    return created_response(
        data={"id": db_product.id, "name": db_product.name},
        message="Product created successfully"
    )


@router.get("/")
def list_products(
    request: Request,
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db)
):
    """List products with translations"""
    products = db.query(Product).limit(10).all()
    language = extract_language_from_header(request)
    
    translated_data = translate_entity_list(
        db=db,
        entities=products,
        language_code=language,
        entity_type="product",
        translatable_fields=["name", "description"]
    )
    
    result = []
    for i, product in enumerate(products):
        result.append({
            "id": product.id,
            "name": translated_data[i]["name"],
            "description": translated_data[i]["description"],
            "price": product.price
        })
    
    return success_response(data=result, message="Products retrieved")


@router.put("/{product_id}")
async def update_product(
    product_id: str,
    name: Optional[str] = Form(None),
    translations_json: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Update product with translations"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if name:
        product.name = name
    
    db.commit()
    
    if translations_json:
        try:
            translations = json.loads(translations_json)
            update_entity_translations(
                db=db,
                entity_type="product",
                entity_id=product_id,
                translations=translations
            )
        except json.JSONDecodeError:
            pass
    
    return success_response(data={"id": product_id}, message="Updated")


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: str, db: Session = Depends(get_db)):
    """Delete product and translations"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    delete_entity_translations(db=db, entity_type="product", entity_id=product_id)
    db.delete(product)
    db.commit()
    return None
```

---

## Frontend Integration

### Creating a Product with Translations (JavaScript)

```javascript
async function createProduct() {
    const formData = new FormData();
    
    // Base fields (English)
    formData.append('name', 'Classic Burger');
    formData.append('slug', 'classic-burger');
    formData.append('price', 1500);
    formData.append('description', 'Delicious beef burger');
    
    // Translations
    const translations = {
        es: {
            name: 'Hamburguesa Clásica',
            description: 'Deliciosa hamburguesa de carne'
        },
        fr: {
            name: 'Hamburger Classique',
            description: 'Délicieux hamburger de bœuf'
        }
    };
    formData.append('translations_json', JSON.stringify(translations));
    
    // Image
    const imageFile = document.getElementById('product-image').files[0];
    if (imageFile) {
        formData.append('image', imageFile);
    }
    
    const response = await fetch('/api/v1/products', {
        method: 'POST',
        body: formData
    });
    
    const result = await response.json();
    console.log('Product created:', result);
}
```

### Updating a Product with Translations

```javascript
async function updateProduct(productId) {
    const formData = new FormData();
    
    // Update name
    formData.append('name', 'Premium Burger');
    
    // Update translations
    const translations = {
        es: {
            name: 'Hamburguesa Premium',
            description: 'Hamburguesa premium con ingredientes selectos'
        }
    };
    formData.append('translations_json', JSON.stringify(translations));
    
    const response = await fetch(`/api/v1/products/${productId}`, {
        method: 'PUT',
        body: formData
    });
    
    const result = await response.json();
    console.log('Product updated:', result);
}
```

### Fetching Products with User's Language

```javascript
async function getProducts(language = 'en') {
    const response = await fetch('/api/v1/products', {
        headers: {
            'Accept-Language': language
        }
    });
    
    const result = await response.json();
    console.log('Products:', result.data);
    
    // Display products
    result.data.forEach(product => {
        console.log(`${product.name}: ${product.description}`);
    });
}

// Usage
getProducts('es');  // Get products in Spanish
getProducts('fr');  // Get products in French
```

---

## Summary Checklist

### ✅ For CREATE Operations:
- [ ] Accept `translations_json` parameter (Form) or `translations` field (Pydantic)
- [ ] Create base entity with English data
- [ ] Call `create_entity_translations()` if translations provided
- [ ] Handle JSON parsing errors gracefully

### ✅ For UPDATE Operations:
- [ ] Accept `translations_json` or `translations` field
- [ ] Update base entity fields
- [ ] Call `update_entity_translations()` if translations provided
- [ ] Existing translations updated, new ones created

### ✅ For DELETE Operations:
- [ ] Call `delete_entity_translations()` before deleting entity
- [ ] Delete associated files (images, etc.)
- [ ] Delete the entity itself

### ✅ For READ Operations:
- [ ] Use `extract_language_from_header()` to get user's language
- [ ] For single entity: use `get_translated_field()`
- [ ] For lists: use `translate_entity_list()` (more efficient)
- [ ] Include language in response for debugging

---

## Best Practices

1. **Always handle JSON parsing errors** - Don't fail entity creation if translations JSON is invalid
2. **Delete translations when deleting entities** - Prevent orphaned translation records
3. **Use batch translation for lists** - `translate_entity_list()` is much faster than individual queries
4. **Test with Accept-Language header** - Ensure translations are returned correctly
5. **Document translation format** - Include JSON examples in API docs
6. **Validate language codes** - Only accept supported languages (en, es, fr, ar)
7. **Keep English as base** - Always store English in main entity tables

---

**Status**: ✅ Ready to implement
**Next Step**: Choose entities to add translations to and update their routes
