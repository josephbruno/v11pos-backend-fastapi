# 🎯 Getting Translated Values Through Model APIs

Step-by-step guide to return translated values from your existing product, category, modifier, and combo APIs.

---

## 📋 Overview

Your current APIs return data like this:
```json
{
  "id": "123",
  "name": "Classic Burger",
  "description": "Delicious burger"
}
```

After integration, they will return translated data based on the user's language:
```json
{
  "id": "123",
  "name": "Hamburguesa Clásica",    // ← Translated to Spanish
  "description": "Deliciosa hamburguesa"  // ← Translated to Spanish
}
```

---

## 🔧 Step-by-Step Integration

### Step 1: Add Import to Your Route File

Add these imports at the top of your route file:

```python
# At the top of app/routes/products.py (or categories.py, modifiers.py, combos.py)

from fastapi import Request  # ← Add this
from app.i18n import (
    extract_language_from_header,
    get_translated_field,
    translate_entity_list
)
```

---

## 📦 PRODUCTS API

### Current Code → Modified Code

#### GET Single Product (BY ID)

**Current Code:**
```python
@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a specific product by ID"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )
    return product
```

**Modified Code with Translations:**
```python
@router.get("/{product_id}")  # Remove response_model to customize response
def get_product(
    product_id: uuid.UUID, 
    request: Request,  # ← Add this
    db: Session = Depends(get_db)
):
    """Get a specific product by ID with translations"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )
    
    # Get user's preferred language from Accept-Language header
    language = extract_language_from_header(request)
    
    # Get translated name
    translated_name = get_translated_field(
        db=db,
        entity_type="product",
        entity_id=str(product.id),
        field_name="name",
        language_code=language,
        default_value=product.name
    )
    
    # Get translated description
    translated_description = get_translated_field(
        db=db,
        entity_type="product",
        entity_id=str(product.id),
        field_name="description",
        language_code=language,
        default_value=product.description or ""
    )
    
    # Return response with translated fields
    return success_response(
        data={
            "id": str(product.id),
            "name": translated_name,  # ← Translated
            "slug": product.slug,
            "description": translated_description,  # ← Translated
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
            "updated_at": product.updated_at,
            "_language": language  # For debugging
        },
        message="Product retrieved successfully"
    )
```

#### GET Product by Slug

**Modified Code:**
```python
@router.get("/slug/{slug}")
def get_product_by_slug(
    slug: str, 
    request: Request,  # ← Add this
    db: Session = Depends(get_db)
):
    """Get a specific product by slug with translations"""
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
            "description": translated_description,
            "slug": product.slug,
            "price": product.price,
            # ... other fields ...
        },
        message="Product retrieved successfully"
    )
```

#### LIST Products (More Efficient)

**Current Code:**
```python
@router.get("/")
def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    category_id: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all products with pagination"""
    query = db.query(Product)
    
    # Apply filters...
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    # Apply pagination
    pagination = PaginationParams(page=page, page_size=page_size)
    products, pagination_meta = paginate_query(query, pagination)
    
    return create_paginated_response(products, pagination_meta, "Products retrieved")
```

**Modified Code with Batch Translation:**
```python
@router.get("/")
def list_products(
    request: Request,  # ← Add this
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    category_id: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all products with pagination and translations"""
    query = db.query(Product)
    
    # Apply filters (existing code)
    if category_id:
        try:
            cat_uuid = uuid.UUID(category_id)
            query = query.filter(Product.category_id == cat_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid category_id")
    
    if search:
        query = query.filter(
            Product.name.ilike(f"%{search}%") | 
            Product.description.ilike(f"%{search}%")
        )
    
    # Apply pagination
    pagination = PaginationParams(page=page, page_size=page_size)
    products, pagination_meta = paginate_query(query, pagination)
    
    # Get user's language
    language = extract_language_from_header(request)
    
    # Batch translate all products (EFFICIENT - only 1 extra query!)
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
            "name": translated_data[i]["name"],  # ← Translated
            "slug": product.slug,
            "description": translated_data[i]["description"],  # ← Translated
            "price": product.price,
            "cost": product.cost,
            "category_id": str(product.category_id),
            "available": product.available,
            "featured": product.featured,
            "preparation_time": product.preparation_time,
            "department": product.department,
            "image": product.image,
            "created_at": product.created_at,
            "updated_at": product.updated_at
        })
    
    return {
        "status": "success",
        "message": "Products retrieved successfully",
        "data": products_list,
        "pagination": pagination_meta.model_dump(),
        "language": language  # For debugging
    }
```

---

## 📁 CATEGORIES API

#### GET Single Category

**Modified Code:**
```python
@router.get("/{category_id}")
def get_category(
    category_id: uuid.UUID, 
    request: Request,  # ← Add this
    db: Session = Depends(get_db)
):
    """Get category with translations"""
    category = db.query(Category).filter(Category.id == str(category_id)).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
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
            "name": translated_name,  # ← Translated
            "slug": category.slug,
            "description": translated_description,  # ← Translated
            "active": category.active,
            "sort_order": category.sort_order,
            "image": category.image,
            "created_at": category.created_at,
            "updated_at": category.updated_at
        },
        message="Category fetched successfully"
    )
```

#### LIST Categories

**Modified Code:**
```python
@router.get("/")
def list_categories(
    request: Request,  # ← Add this
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List categories with translations"""
    query = db.query(Category)
    
    if active is not None:
        query = query.filter(Category.active == active)
    
    query = query.order_by(Category.sort_order)
    
    # Apply pagination
    pagination = PaginationParams(page=page, page_size=page_size)
    categories, pagination_meta = paginate_query(query, pagination)
    
    # Get language
    language = extract_language_from_header(request)
    
    # Batch translate
    translated_data = translate_entity_list(
        db=db,
        entities=categories,
        language_code=language,
        entity_type="category",
        translatable_fields=["name", "description"]
    )
    
    # Build response
    categories_list = []
    for i, cat in enumerate(categories):
        categories_list.append({
            "id": str(cat.id),
            "name": translated_data[i]["name"],  # ← Translated
            "slug": cat.slug,
            "description": translated_data[i]["description"],  # ← Translated
            "active": cat.active,
            "sort_order": cat.sort_order,
            "image": cat.image,
            "created_at": cat.created_at,
            "updated_at": cat.updated_at
        })
    
    return {
        "status": "success",
        "message": "Categories retrieved successfully",
        "data": categories_list,
        "pagination": pagination_meta.model_dump(),
        "language": language
    }
```

---

## 🔧 MODIFIERS API

#### GET Single Modifier

**Modified Code:**
```python
@router.get("/{modifier_id}")
def get_modifier(
    modifier_id: str, 
    request: Request,  # ← Add this
    db: Session = Depends(get_db)
):
    """Get modifier with translations"""
    modifier = db.query(Modifier).filter(Modifier.id == modifier_id).first()
    if not modifier:
        raise HTTPException(status_code=404, detail="Modifier not found")
    
    # Get language and translate
    language = extract_language_from_header(request)
    
    translated_name = get_translated_field(
        db=db,
        entity_type="modifier",
        entity_id=modifier.id,
        field_name="name",
        language_code=language,
        default_value=modifier.name
    )
    
    return success_response(
        data={
            "id": modifier.id,
            "name": translated_name,  # ← Translated
            "category": modifier.category,
            "is_required": modifier.is_required,
            "min_selections": modifier.min_selections,
            "max_selections": modifier.max_selections,
            # ... other fields ...
        },
        message="Modifier retrieved successfully"
    )
```

#### LIST Modifiers

**Modified Code:**
```python
@router.get("/")
def list_modifiers(
    request: Request,  # ← Add this
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List modifiers with translations"""
    query = db.query(Modifier)
    
    if category:
        query = query.filter(Modifier.category == category)
    
    # Apply pagination
    pagination = PaginationParams(page=page, page_size=page_size)
    modifiers, pagination_meta = paginate_query(query, pagination)
    
    # Get language
    language = extract_language_from_header(request)
    
    # Batch translate
    translated_data = translate_entity_list(
        db=db,
        entities=modifiers,
        language_code=language,
        entity_type="modifier",
        translatable_fields=["name"]
    )
    
    # Build response
    modifiers_list = []
    for i, mod in enumerate(modifiers):
        modifiers_list.append({
            "id": mod.id,
            "name": translated_data[i]["name"],  # ← Translated
            "category": mod.category,
            "is_required": mod.is_required,
            # ... other fields ...
        })
    
    return create_paginated_response(
        data=modifiers_list,
        pagination=pagination_meta,
        message="Modifiers retrieved successfully"
    )
```

---

## 🎁 COMBO PRODUCTS API

#### GET Single Combo

**Modified Code:**
```python
@router.get("/{combo_id}")
def get_combo(
    combo_id: str, 
    request: Request,  # ← Add this
    db: Session = Depends(get_db)
):
    """Get combo with translations"""
    combo = db.query(ComboProduct).filter(ComboProduct.id == combo_id).first()
    if not combo:
        raise HTTPException(status_code=404, detail="Combo not found")
    
    # Get language and translate
    language = extract_language_from_header(request)
    
    translated_name = get_translated_field(
        db=db,
        entity_type="combo",
        entity_id=combo.id,
        field_name="name",
        language_code=language,
        default_value=combo.name
    )
    
    translated_description = get_translated_field(
        db=db,
        entity_type="combo",
        entity_id=combo.id,
        field_name="description",
        language_code=language,
        default_value=combo.description or ""
    )
    
    return success_response(
        data={
            "id": combo.id,
            "name": translated_name,  # ← Translated
            "slug": combo.slug,
            "description": translated_description,  # ← Translated
            "price": combo.price,
            "available": combo.available,
            # ... other fields ...
        },
        message="Combo retrieved successfully"
    )
```

#### LIST Combos

**Modified Code:**
```python
@router.get("")
def get_combos(
    request: Request,  # ← Add this
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    available: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List combos with translations"""
    query = db.query(ComboProduct)
    
    if available is not None:
        query = query.filter(ComboProduct.available == available)
    
    # Apply pagination
    pagination = PaginationParams(page=page, page_size=page_size)
    combos, pagination_meta = paginate_query(query, pagination)
    
    # Get language
    language = extract_language_from_header(request)
    
    # Batch translate
    translated_data = translate_entity_list(
        db=db,
        entities=combos,
        language_code=language,
        entity_type="combo",
        translatable_fields=["name", "description"]
    )
    
    # Build response
    combos_list = []
    for i, combo in enumerate(combos):
        combos_list.append({
            "id": combo.id,
            "name": translated_data[i]["name"],  # ← Translated
            "slug": combo.slug,
            "description": translated_data[i]["description"],  # ← Translated
            "price": combo.price,
            "available": combo.available,
            # ... other fields ...
        })
    
    return create_paginated_response(
        data=combos_list,
        pagination=pagination_meta,
        message="Combos retrieved successfully"
    )
```

---

## 🧪 Testing Your Changes

### Test Single Product (English)
```bash
curl http://localhost:8000/api/v1/products/{product-id}
```

### Test Single Product (Spanish)
```bash
curl -H "Accept-Language: es" http://localhost:8000/api/v1/products/{product-id}
```

### Test Single Product (French)
```bash
curl -H "Accept-Language: fr" http://localhost:8000/api/v1/products/{product-id}
```

### Test Product List (Spanish)
```bash
curl -H "Accept-Language: es" http://localhost:8000/api/v1/products
```

### Test Categories (Spanish)
```bash
curl -H "Accept-Language: es" http://localhost:8000/api/v1/categories
```

### Test Modifiers (French)
```bash
curl -H "Accept-Language: fr" http://localhost:8000/api/v1/modifiers
```

### Test Combos (Arabic)
```bash
curl -H "Accept-Language: ar" http://localhost:8000/api/v1/combos
```

---

## 📱 Frontend Usage

### JavaScript/React Example

```javascript
// Function to get products in user's language
async function getProducts(language = 'en') {
    const response = await fetch('/api/v1/products', {
        headers: {
            'Accept-Language': language
        }
    });
    
    const result = await response.json();
    return result.data; // Already translated!
}

// Usage
const products = await getProducts('es'); // Get Spanish products
products.forEach(product => {
    console.log(product.name); // "Hamburguesa Clásica"
});
```

### Language Selector

```javascript
// Language selector component
function LanguageSelector({ onLanguageChange }) {
    const languages = [
        { code: 'en', name: 'English' },
        { code: 'es', name: 'Español' },
        { code: 'fr', name: 'Français' },
        { code: 'ar', name: 'العربية' }
    ];
    
    return (
        <select onChange={(e) => onLanguageChange(e.target.value)}>
            {languages.map(lang => (
                <option key={lang.code} value={lang.code}>
                    {lang.name}
                </option>
            ))}
        </select>
    );
}

// When language changes, refetch data
function App() {
    const [language, setLanguage] = useState('en');
    const [products, setProducts] = useState([]);
    
    useEffect(() => {
        getProducts(language).then(setProducts);
    }, [language]);
    
    return (
        <div>
            <LanguageSelector onLanguageChange={setLanguage} />
            <ProductList products={products} />
        </div>
    );
}
```

---

## ⚡ Performance Tips

### 1. Always Use Batch Translation for Lists

**❌ BAD (N+1 queries):**
```python
# Don't do this!
for product in products:
    translated_name = get_translated_field(db, "product", product.id, "name", lang, product.name)
```

**✅ GOOD (2 queries total):**
```python
# Do this instead!
translated_data = translate_entity_list(db, products, lang, "product", ["name", "description"])
```

### 2. Cache Language Detection

If making multiple calls, extract language once:
```python
language = extract_language_from_header(request)
# Use 'language' variable multiple times
```

### 3. Only Translate What You Need

Don't translate fields that users don't see:
```python
# Only translate visible fields
translatable_fields=["name", "description"]  # Not "slug", "id", etc.
```

---

## 📋 Complete Implementation Checklist

For each entity (products, categories, modifiers, combos):

### GET Single Entity
- [ ] Add `request: Request` parameter
- [ ] Add `extract_language_from_header(request)`
- [ ] Add `get_translated_field()` for each translatable field
- [ ] Remove `response_model` if needed
- [ ] Return dictionary with translated values
- [ ] Test with different languages

### GET List of Entities
- [ ] Add `request: Request` parameter
- [ ] Add `extract_language_from_header(request)`
- [ ] Add `translate_entity_list()` for batch translation
- [ ] Build response list with translated values
- [ ] Add language to response for debugging
- [ ] Test with different languages

---

## 🎯 Quick Summary

**What to add to GET endpoints:**

1. **Import**: `from fastapi import Request` and translation helpers
2. **Parameter**: `request: Request` to function signature
3. **Extract Language**: `language = extract_language_from_header(request)`
4. **Translate**: 
   - Single: Use `get_translated_field()`
   - List: Use `translate_entity_list()`
5. **Return**: Dictionary with translated values

**Time per endpoint**: 5-10 minutes
**Performance impact**: Minimal (1-2 extra queries)

---

## ✅ Next Steps

1. Choose one entity to start (e.g., products)
2. Modify the GET endpoints using code above
3. Test with curl commands
4. Verify translations work
5. Repeat for other entities (categories, modifiers, combos)

**Estimated total time**: 1-2 hours for all entities
