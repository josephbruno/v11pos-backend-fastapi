# 🎯 Translation CRUD Cheat Sheet

Quick copy-paste examples for adding translations to your routes.

---

## 📥 Import Required Functions

```python
from app.i18n import (
    create_entity_translations,      # For CREATE
    update_entity_translations,      # For UPDATE
    delete_entity_translations,      # For DELETE
    extract_language_from_header,    # For READ
    translate_entity_list           # For LIST
)
import json  # For parsing translations_json
from fastapi import Request  # For language detection
```

---

## ✨ CREATE - Add Translations

### Step 1: Add Parameter to Endpoint

```python
@router.post("/")
async def create_product(
    name: str = Form(...),
    # ... other fields ...
    translations_json: Optional[str] = Form(None),  # ← Add this
    db: Session = Depends(get_db)
):
```

### Step 2: Create Entity + Translations

```python
    # Create entity (existing code)
    db_product = Product(id=str(uuid.uuid4()), name=name, ...)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    # Add translations (new code)
    if translations_json:
        try:
            translations = json.loads(translations_json)
            create_entity_translations(
                db=db,
                entity_type="product",  # or "category", "modifier", "combo"
                entity_id=db_product.id,
                translations=translations
            )
        except json.JSONDecodeError:
            pass  # Don't fail if translation JSON is invalid
```

---

## 🔄 UPDATE - Update Translations

### Step 1: Add Parameter

```python
@router.put("/{product_id}")
async def update_product(
    product_id: str,
    name: Optional[str] = Form(None),
    translations_json: Optional[str] = Form(None),  # ← Add this
    db: Session = Depends(get_db)
):
```

### Step 2: Update Entity + Translations

```python
    # Update entity (existing code)
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Not found")
    
    if name:
        db_product.name = name
    db.commit()
    
    # Update translations (new code)
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
```

---

## 🗑️ DELETE - Remove Translations

### Just Add One Line Before Deleting

```python
@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: str, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Not found")
    
    # Delete translations (new code - add this line)
    delete_entity_translations(db=db, entity_type="product", entity_id=product_id)
    
    # Delete entity (existing code)
    db.delete(db_product)
    db.commit()
    return None
```

---

## 📖 READ - Get with Translations

### Single Entity

```python
@router.get("/{product_id}")
def get_product(
    product_id: str,
    request: Request,  # ← Add this
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Not found")
    
    # Get user's language
    language = extract_language_from_header(request)
    
    # Get translated fields
    translated_name = get_translated_field(
        db=db,
        entity_type="product",
        entity_id=product.id,
        field_name="name",
        language_code=language,
        default_value=product.name
    )
    
    return {
        "id": product.id,
        "name": translated_name,  # ← Use translated value
        "price": product.price
    }
```

### List Entities (More Efficient)

```python
@router.get("/")
def list_products(
    request: Request,  # ← Add this
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db)
):
    # Get products (existing code)
    products = db.query(Product).limit(10).all()
    
    # Get user's language
    language = extract_language_from_header(request)
    
    # Translate all at once (efficient - single query)
    translated_data = translate_entity_list(
        db=db,
        entities=products,
        language_code=language,
        entity_type="product",
        translatable_fields=["name", "description"]
    )
    
    # Build response with translated data
    result = []
    for i, product in enumerate(products):
        result.append({
            "id": product.id,
            "name": translated_data[i]["name"],
            "description": translated_data[i]["description"],
            "price": product.price
        })
    
    return {"data": result}
```

---

## 🌐 Frontend - Send Translations

### JavaScript Example

```javascript
// Create with translations
const formData = new FormData();
formData.append('name', 'Classic Burger');
formData.append('price', 1500);

// Add translations
const translations = {
    es: {
        name: 'Hamburguesa Clásica',
        description: 'Deliciosa hamburguesa'
    },
    fr: {
        name: 'Hamburger Classique'
    }
};
formData.append('translations_json', JSON.stringify(translations));

await fetch('/api/v1/products', {
    method: 'POST',
    body: formData
});
```

### Fetch with Language

```javascript
// Get products in Spanish
const response = await fetch('/api/v1/products', {
    headers: {
        'Accept-Language': 'es'
    }
});
```

---

## 📝 Entity Types Reference

Use these exact strings for `entity_type`:

| Entity | entity_type value |
|--------|-------------------|
| Product | `"product"` |
| Category | `"category"` |
| Modifier | `"modifier"` |
| Modifier Option | `"modifier_option"` |
| Combo Product | `"combo"` |
| Combo Item | `"combo_item"` |

---

## 🔧 Translatable Fields

Common fields that can be translated:

- `"name"` - Entity name
- `"description"` - Entity description
- `"label"` - Labels, titles
- `"instructions"` - Instructions, notes

---

## ✅ Implementation Checklist

For each entity (product, category, modifier, combo):

- [ ] **CREATE**: Add `translations_json` parameter
- [ ] **CREATE**: Call `create_entity_translations()`
- [ ] **UPDATE**: Add `translations_json` parameter
- [ ] **UPDATE**: Call `update_entity_translations()`
- [ ] **DELETE**: Call `delete_entity_translations()` before deleting
- [ ] **GET**: Add `Request` parameter
- [ ] **GET**: Use `extract_language_from_header()`
- [ ] **GET**: Use `get_translated_field()` or `translate_entity_list()`
- [ ] **TEST**: Verify with curl/Postman

---

## 🧪 Quick Test Commands

```bash
# Create product with translations
curl -X POST http://localhost:8000/api/v1/products \
  -F 'name=Burger' \
  -F 'slug=burger' \
  -F 'price=1500' \
  -F 'translations_json={"es":{"name":"Hamburguesa"}}'

# Get product in Spanish
curl -H "Accept-Language: es" \
  http://localhost:8000/api/v1/products/{product_id}

# Update translations
curl -X PUT http://localhost:8000/api/v1/products/{product_id} \
  -F 'translations_json={"es":{"name":"Nueva Hamburguesa"}}'

# Delete (translations auto-deleted)
curl -X DELETE http://localhost:8000/api/v1/products/{product_id}
```

---

## 🎨 Translation JSON Format

```json
{
  "es": {
    "name": "Producto en Español",
    "description": "Descripción en español"
  },
  "fr": {
    "name": "Produit en Français",
    "description": "Description en français"
  },
  "ar": {
    "name": "منتج بالعربية",
    "description": "وصف بالعربية"
  }
}
```

---

**Quick Tip**: Copy the code snippets above and replace:
- `"product"` with your entity type
- `Product` with your model class
- Field names as needed

**Status**: ✅ Ready to implement
