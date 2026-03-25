# 🌍 Multi-Language Support - Product Module

## ✅ Status: Fully Implemented

Multi-language support has been successfully added to the Product Catalog module, allowing products, categories, modifiers, and combos to be displayed in multiple languages.

---

## 🎯 Supported Languages

- **en** - English (default)
- **ta** - Tamil
- **hi** - Hindi
- **fr** - French
- **Extendable** - Easy to add more languages

---

## 📊 Translation Tables

### 5 Translation Tables Created:

1. **category_translations** - Category name & description
2. **product_translations** - Product name & description
3. **modifier_translations** - Modifier name
4. **modifier_option_translations** - Modifier option name
5. **combo_product_translations** - Combo product name & description

### Table Structure Example (product_translations):
```sql
+---------------------+--------------+
| Field               | Type         |
+---------------------+--------------+
| id                  | varchar(36)  | PK
| product_id          | varchar(36)  | FK → products.id
| language_code       | varchar(5)   | en, ta, hi, fr
| name                | varchar(255) |
| description         | varchar(1000)|
| created_at          | datetime     |
| updated_at          | datetime     |
+---------------------+--------------+

UNIQUE INDEX: (product_id, language_code)
```

---

## 🔧 How It Works

### 1. Main Tables (Language-Neutral)
Main tables store default content (usually English):
- `categories` - Default name & description
- `products` - Default name & description
- `modifiers` - Default name
- `modifier_options` - Default name
- `combo_products` - Default name & description

### 2. Translation Tables
Translation tables store localized content:
- One row per language per entity
- Unique constraint on (entity_id, language_code)
- Cascade delete when parent is deleted

### 3. ORM Relationships
Models have `translations` relationship:
```python
# In Product model
translations = relationship(
    "ProductTranslation",
    cascade="all, delete-orphan",
    lazy="selectin"
)
```

---

## 🌐 API Usage

### Using Accept-Language Header

```bash
# Get products in Tamil
curl http://localhost:8000/products/restaurant/rest-id \
  -H "Accept-Language: ta"

# Get products in Hindi
curl http://localhost:8000/products/restaurant/rest-id \
  -H "Accept-Language: hi"

# Get products in French
curl http://localhost:8000/products/restaurant/rest-id \
  -H "Accept-Language: fr"

# Default to English if not specified
curl http://localhost:8000/products/restaurant/rest-id
```

### Language Code Extraction
The system automatically:
1. Parses `Accept-Language` header
2. Extracts language code (e.g., "ta" from "ta-IN")
3. Falls back to "en" if unsupported

---

## 📝 Creating Translations

### 1. Create Product with Default Language
```bash
curl -X POST http://localhost:8000/products \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "restaurant_id": "rest-uuid",
    "name": "Cappuccino",
    "description": "Classic Italian coffee",
    "price": 15000,
    "category_id": "cat-uuid",
    ...
  }'
```

### 2. Add Tamil Translation
```bash
curl -X POST http://localhost:8000/products/translations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "product_id": "product-uuid",
    "language_code": "ta",
    "name": "காப்புசினோ",
    "description": "பாரம்பரிய இத்தாலிய காபி"
  }'
```

### 3. Add Hindi Translation
```bash
curl -X POST http://localhost:8000/products/translations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "product_id": "product-uuid",
    "language_code": "hi",
    "name": "कैप्पुचीनो",
    "description": "क्लासिक इतालवी कॉफी"
  }'
```

---

## 🛠️ Helper Functions

### 1. Get Language from Header
```python
from app.core.i18n import get_language_from_header

@router.get("/products")
async def get_products(
    language: str = Depends(get_language_from_header)
):
    # language will be "en", "ta", "hi", or "fr"
    pass
```

### 2. Get Translated Field
```python
from app.core.i18n import get_translated_field

# Get product name in Tamil
name = get_translated_field(product, 'name', 'ta')

# Get category description in Hindi
desc = get_translated_field(category, 'description', 'hi')
```

### 3. Apply Translations to Entity
```python
from app.core.i18n import apply_translations

# Get product with Tamil translations applied
product_dict = apply_translations(product, 'ta')
```

### 4. Get All Translations
```python
from app.core.i18n import get_translation_dict

# Get all translations for a product
translations = get_translation_dict(product)
# Returns: {
#   "en": {"name": "Cappuccino", "description": "..."},
#   "ta": {"name": "காப்புசினோ", "description": "..."},
#   "hi": {"name": "कैप्पुचीनो", "description": "..."}
# }
```

---

## 📋 Translation Schemas

### Category Translation
```python
{
  "category_id": "uuid",
  "language_code": "ta",
  "name": "பானங்கள்",
  "description": "சூடான மற்றும் குளிர் பானங்கள்"
}
```

### Product Translation
```python
{
  "product_id": "uuid",
  "language_code": "hi",
  "name": "कैप्पुचीनो",
  "description": "क्लासिक इतालवी कॉफी"
}
```

### Modifier Translation
```python
{
  "modifier_id": "uuid",
  "language_code": "ta",
  "name": "அளவு"  # Size
}
```

### Modifier Option Translation
```python
{
  "modifier_option_id": "uuid",
  "language_code": "ta",
  "name": "பெரிய"  # Large
}
```

### Combo Product Translation
```python
{
  "combo_product_id": "uuid",
  "language_code": "hi",
  "name": "नाश्ता कॉम्बो",
  "description": "कॉफी + सैंडविच"
}
```

---

## 🎯 Use Cases

### 1. Multi-Lingual Menu Display
```python
# Customer app in Tamil
GET /products/restaurant/rest-id
Header: Accept-Language: ta

Response:
{
  "name": "காப்புசினோ",
  "description": "பாரம்பரிய இத்தாலிய காபி",
  "price": 15000
}
```

### 2. Admin Panel - Add Translations
```python
# Admin adds translations for all products
POST /products/{id}/translations
{
  "language_code": "ta",
  "name": "தமிழ் பெயர்",
  "description": "தமிழ் விளக்கம்"
}
```

### 3. Dynamic Language Switching
```javascript
// Frontend can switch languages dynamically
const fetchProducts = async (lang) => {
  const response = await fetch('/products/restaurant/rest-id', {
    headers: {
      'Accept-Language': lang
    }
  });
  return response.json();
};

// Switch to Tamil
fetchProducts('ta');

// Switch to Hindi
fetchProducts('hi');
```

---

## 🔍 Database Queries

### Get Product with Translations
```sql
SELECT 
  p.*,
  pt.language_code,
  pt.name as translated_name,
  pt.description as translated_description
FROM products p
LEFT JOIN product_translations pt ON p.id = pt.product_id
WHERE p.id = 'product-uuid';
```

### Get All Products in Tamil
```sql
SELECT 
  p.id,
  p.price,
  COALESCE(pt.name, p.name) as name,
  COALESCE(pt.description, p.description) as description
FROM products p
LEFT JOIN product_translations pt 
  ON p.id = pt.product_id 
  AND pt.language_code = 'ta'
WHERE p.restaurant_id = 'rest-uuid';
```

---

## ⚡ Performance Considerations

### 1. Eager Loading
Translations are loaded with `lazy="selectin"`:
```python
translations = relationship(
    "ProductTranslation",
    cascade="all, delete-orphan",
    lazy="selectin"  # Loads in separate query
)
```

### 2. Indexing
All translation tables have indexes on:
- `entity_id` - Fast lookup by parent
- `language_code` - Fast filtering by language
- Unique constraint on `(entity_id, language_code)`

### 3. Caching Strategy
Consider caching translations:
```python
# Cache key: product:{id}:lang:{code}
cache_key = f"product:{product_id}:lang:{lang_code}"
```

---

## 🚀 Benefits

### For Customers
- ✅ View menu in their preferred language
- ✅ Better understanding of products
- ✅ Improved user experience
- ✅ Increased accessibility

### For Restaurant Owners
- ✅ Reach wider audience
- ✅ Support multiple regions
- ✅ Localized marketing
- ✅ Competitive advantage

### For Developers
- ✅ Clean separation of concerns
- ✅ Easy to add new languages
- ✅ Flexible translation management
- ✅ No impact on existing code

---

## 📊 Summary

**Feature**: Multi-Language Support ✅
**Tables Created**: 5 translation tables
**Languages Supported**: en, ta, hi, fr (extendable)
**Translatable Entities**: 5 (Category, Product, Modifier, ModifierOption, ComboProduct)
**API Integration**: Accept-Language header
**Status**: Production Ready 🚀

**All products can now be displayed in multiple languages!**
