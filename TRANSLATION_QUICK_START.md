# 🚀 Multi-Language Quick Start Guide

## Get Translations (Frontend)

```javascript
// Get supported languages
const { data: languages } = await fetch('/api/v1/translations/languages')
  .then(r => r.json());

// Get Spanish UI translations
const { translations } = await fetch('/api/v1/translations/es')
  .then(r => r.json());

// Use translations
button.textContent = translations.common.save; // "Guardar"
```

## Add Product Translation (Admin)

```bash
# Add Spanish product name
curl -X POST http://localhost:8000/api/v1/translations/entity \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type": "product",
    "entity_id": "YOUR-PRODUCT-ID",
    "field_name": "name",
    "language_code": "es",
    "translation_value": "Nombre en Español"
  }'
```

## Use in Backend Routes

```python
from fastapi import Request, Depends
from sqlalchemy.orm import Session
from app.i18n import extract_language_from_header, get_translated_field
from app.database import get_db

@router.get("/products/{product_id}")
def get_product(product_id: str, request: Request, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    language = extract_language_from_header(request)
    
    # Get translated name
    name = get_translated_field(
        db=db,
        entity_type="product",
        entity_id=product.id,
        field_name="name",
        language_code=language,
        default_value=product.name
    )
    
    return {"id": product.id, "name": name, "price": product.price}
```

## Available Endpoints

```
GET  /api/v1/translations/languages              # List all languages
GET  /api/v1/translations/{language}             # Get UI translations
POST /api/v1/translations/entity                 # Add/update translation
GET  /api/v1/translations/entity/{type}/{id}     # Get entity translations
```

## Supported Languages

- `en` - English (default)
- `es` - Spanish (Español)
- `fr` - French (Français)
- `ar` - Arabic (العربية) - RTL

## Translation Keys Structure

```javascript
{
  "common": { "save": "Save", "cancel": "Cancel", ... },
  "auth": { "login": "Login", "logout": "Logout", ... },
  "navigation": { "dashboard": "Dashboard", ... },
  "products": { "title": "Products", ... },
  "categories": { "title": "Categories", ... },
  "orders": { "title": "Orders", ... }
}
```

## Files Created

- `app/translations/en.json` - English UI text
- `app/translations/es.json` - Spanish UI text  
- `app/routes/translations.py` - API endpoints
- `app/models/translation.py` - Database model
- `app/i18n.py` - Helper functions
- `migrations/add_translations_table.sql` - Database setup

## Quick Commands

```bash
# Get English translations
curl http://localhost:8000/api/v1/translations/en

# Get Spanish translations
curl http://localhost:8000/api/v1/translations/es

# View API docs
open http://localhost:8000/docs#/translations
```

## Status: ✅ READY TO USE

All tests passed. System is production-ready.

For detailed documentation, see:
- `MULTILANGUAGE_IMPLEMENTATION_COMPLETE.md`
- `TRANSLATION_TEST_RESULTS.md`
