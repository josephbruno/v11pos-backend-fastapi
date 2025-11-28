# 🚀 Translation API - Quick Test Commands

## 🔄 Restart Server First

```bash
# Restart Docker container
docker restart restaurant_pos_api

# Or restart using docker-compose
cd /home/brunodoss/docs/pos/pos/pos-fastapi
docker-compose restart api
```

---

## 🧪 Test Commands

### 1️⃣ Products API

```bash
# GET all products (Spanish)
curl -X GET "http://localhost:8001/api/v1/products/" \
  -H "Accept-Language: es"

# GET single product (French)
curl -X GET "http://localhost:8001/api/v1/products/{product_id}" \
  -H "Accept-Language: fr"

# CREATE product with translations
curl -X POST "http://localhost:8001/api/v1/products/" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "name=Burger" \
  -d "description=Delicious burger" \
  -d "price=9.99" \
  -d "category_id=cat123" \
  -d "available=true" \
  -d 'translations_json={"es":{"name":"Hamburguesa","description":"Hamburguesa deliciosa"},"fr":{"name":"Burger","description":"Burger délicieux"}}'

# UPDATE product with translations
curl -X PUT "http://localhost:8001/api/v1/products/{product_id}" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "name=Cheeseburger" \
  -d 'translations_json={"es":{"name":"Hamburguesa con Queso"}}'
```

### 2️⃣ Categories API

```bash
# GET all categories (Spanish)
curl -X GET "http://localhost:8001/api/v1/categories/" \
  -H "Accept-Language: es"

# GET single category (Arabic)
curl -X GET "http://localhost:8001/api/v1/categories/{category_id}" \
  -H "Accept-Language: ar"

# CREATE category with translations
curl -X POST "http://localhost:8001/api/v1/categories/" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "name=Drinks" \
  -d "description=Beverages" \
  -d "icon=drink" \
  -d 'translations_json={"es":{"name":"Bebidas","description":"Bebidas"},"fr":{"name":"Boissons","description":"Boissons"}}'
```

### 3️⃣ Modifiers API

```bash
# GET all modifiers (Spanish)
curl -X GET "http://localhost:8001/api/v1/modifiers/" \
  -H "Accept-Language: es"

# GET single modifier (French)
curl -X GET "http://localhost:8001/api/v1/modifiers/{modifier_id}" \
  -H "Accept-Language: fr"

# CREATE modifier with translations
curl -X POST "http://localhost:8001/api/v1/modifiers/" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "name=Size" \
  -d "selection_type=single" \
  -d "is_active=true" \
  -d 'translations_json={"es":{"name":"Tamaño"},"fr":{"name":"Taille"}}'

# GET modifier options (Spanish)
curl -X GET "http://localhost:8001/api/v1/modifiers/{modifier_id}/options" \
  -H "Accept-Language: es"
```

### 4️⃣ Combos API

```bash
# GET all combos (Spanish)
curl -X GET "http://localhost:8001/api/v1/combos" \
  -H "Accept-Language: es"

# GET single combo (French)
curl -X GET "http://localhost:8001/api/v1/combos/{combo_id}" \
  -H "Accept-Language: fr"

# CREATE combo with translations
curl -X POST "http://localhost:8001/api/v1/combos" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "name=Lunch Special" \
  -d "description=Great lunch deal" \
  -d "slug=lunch-special" \
  -d "category_id=cat123" \
  -d "combo_price=15.99" \
  -d "original_price=20.00" \
  -d "available=true" \
  -d 'translations_json={"es":{"name":"Especial de Almuerzo","description":"Gran oferta de almuerzo"}}'

# GET combo items (Spanish)
curl -X GET "http://localhost:8001/api/v1/combo-items?combo_id={combo_id}" \
  -H "Accept-Language: es"
```

---

## 📝 Translation JSON Format

Use this format for `translations_json` parameter:

```json
{
  "es": {
    "name": "Spanish Name",
    "description": "Spanish Description"
  },
  "fr": {
    "name": "French Name",
    "description": "French Description"
  },
  "ar": {
    "name": "Arabic Name",
    "description": "Arabic Description"
  }
}
```

**URL-encoded for curl:**
```
translations_json={"es":{"name":"Spanish Name"},"fr":{"name":"French Name"}}
```

---

## 🌐 Supported Languages

| Code | Language | Direction |
|------|----------|-----------|
| `en` | English | LTR |
| `es` | Spanish | LTR |
| `fr` | French | LTR |
| `ar` | Arabic | RTL |

---

## 📊 Entity Types & Fields

| Entity | Fields | Endpoint |
|--------|--------|----------|
| Product | name, description | /api/v1/products |
| Category | name, description | /api/v1/categories |
| Modifier | name | /api/v1/modifiers |
| Modifier Option | name | /api/v1/modifiers/{id}/options |
| Combo | name, description | /api/v1/combos |
| Combo Item | custom_name | /api/v1/combo-items |

---

## ✅ Testing Checklist

- [ ] Test GET endpoints with different `Accept-Language` headers
- [ ] Test POST endpoints with `translations_json` parameter
- [ ] Test PUT endpoints with `translations_json` parameter
- [ ] Test DELETE endpoints (verify translations are also deleted)
- [ ] Verify fallback to English when translation not found
- [ ] Test with missing `Accept-Language` header (should default to English)
- [ ] Test with invalid `translations_json` (should not break the API)

---

## 🎯 Expected Behavior

### ✅ Correct Behavior

1. **GET with Accept-Language: es** → Returns Spanish translations
2. **GET with Accept-Language: en** → Returns English values
3. **GET without Accept-Language** → Returns English values (default)
4. **POST with translations_json** → Creates entity + translations
5. **PUT with translations_json** → Updates entity + translations
6. **DELETE** → Deletes entity + all translations
7. **Invalid translations_json** → Creates/updates entity without translations (no error)

### ❌ Things to Watch For

- Missing translations → Should fallback to English
- Invalid JSON → Should silently skip (not break the API)
- Missing Accept-Language header → Should default to English
- Deleting entity → Should also delete all translations

---

## 🔍 Check Translations in Database

```bash
# Connect to MySQL
docker exec -it restaurant_pos_db mysql -u root -p

# Switch to database
USE restaurant_pos;

# View all translations
SELECT * FROM translations;

# View translations for specific entity
SELECT * FROM translations 
WHERE entity_type = 'product' 
AND entity_id = 'product123';

# View translations for specific language
SELECT * FROM translations 
WHERE language_code = 'es';
```

---

## 📋 Full Test Workflow

1. **Create a product with translations**
   ```bash
   curl -X POST "http://localhost:8001/api/v1/products/" \
     -d "name=Test Product" \
     -d "description=Test Description" \
     -d "price=10.00" \
     -d "category_id=cat123" \
     -d "available=true" \
     -d 'translations_json={"es":{"name":"Producto de Prueba","description":"Descripción de Prueba"}}'
   ```
   **Expected:** Product created with English and Spanish translations

2. **Get product in Spanish**
   ```bash
   curl -X GET "http://localhost:8001/api/v1/products/{product_id}" \
     -H "Accept-Language: es"
   ```
   **Expected:** Returns "Producto de Prueba" instead of "Test Product"

3. **Get product in French (no translation)**
   ```bash
   curl -X GET "http://localhost:8001/api/v1/products/{product_id}" \
     -H "Accept-Language: fr"
   ```
   **Expected:** Fallback to English → Returns "Test Product"

4. **Update product translations**
   ```bash
   curl -X PUT "http://localhost:8001/api/v1/products/{product_id}" \
     -d 'translations_json={"fr":{"name":"Produit de Test"}}'
   ```
   **Expected:** Adds French translation

5. **Get product in French again**
   ```bash
   curl -X GET "http://localhost:8001/api/v1/products/{product_id}" \
     -H "Accept-Language: fr"
   ```
   **Expected:** Now returns "Produit de Test"

6. **Delete product**
   ```bash
   curl -X DELETE "http://localhost:8001/api/v1/products/{product_id}"
   ```
   **Expected:** Product deleted + all translations deleted

---

## 🎉 Success Indicators

✅ API responds to requests
✅ Translations returned based on Accept-Language header
✅ Fallback to English when translation missing
✅ Creating/updating with translations works
✅ Deleting entity also deletes translations
✅ Invalid JSON doesn't break the API

---

**Ready to test!** 🚀
