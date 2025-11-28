# 📊 Translation System Architecture

Visual guide showing how translations work across create, update, delete, and read operations.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TRANSLATION SYSTEM                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │   JSON Files  │         │   Database   │                 │
│  │ (Static UI)   │         │  (Entities)  │                 │
│  ├──────────────┤         ├──────────────┤                 │
│  │  en.json     │         │ translations │                 │
│  │  es.json     │         │   table      │                 │
│  │  fr.json     │         └──────┬───────┘                 │
│  │  ar.json     │                │                          │
│  └──────────────┘                │                          │
│        ▲                         ▼                          │
│        │              ┌──────────────────┐                  │
│        │              │  Products Table  │                  │
│        │              │  Categories Table│                  │
│        │              │  Modifiers Table │                  │
│        │              │  Combos Table    │                  │
│        │              └──────────────────┘                  │
│        │                                                     │
│  ┌─────┴────────────────────────────────────────┐          │
│  │         Translation Helper Functions          │          │
│  ├──────────────────────────────────────────────┤          │
│  │  create_entity_translations()                 │          │
│  │  update_entity_translations()                 │          │
│  │  delete_entity_translations()                 │          │
│  │  get_translated_field()                       │          │
│  │  translate_entity_list()                      │          │
│  └──────────────────────────────────────────────┘          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 CREATE Flow

```
Frontend                  Backend                    Database
   │                         │                           │
   │  POST /products         │                           │
   │  + translations_json    │                           │
   ├────────────────────────>│                           │
   │                         │                           │
   │                         │ 1. Create Product         │
   │                         │    (English data)         │
   │                         ├──────────────────────────>│
   │                         │                           │
   │                         │<──────────────────────────┤
   │                         │    Product ID: 123        │
   │                         │                           │
   │                         │ 2. Parse translations     │
   │                         │    JSON                   │
   │                         │                           │
   │                         │ 3. Create translations    │
   │                         │    for each language      │
   │                         ├──────────────────────────>│
   │                         │    INSERT INTO            │
   │                         │    translations ...       │
   │                         │                           │
   │<────────────────────────┤                           │
   │  201 Created            │                           │
   │  Product + translations │                           │
   │                         │                           │
```

**Result**: 
- 1 record in `products` table (English)
- N records in `translations` table (other languages)

---

## 🔄 READ Flow (Single Entity)

```
Frontend                  Backend                    Database
   │                         │                           │
   │  GET /products/123      │                           │
   │  Accept-Language: es    │                           │
   ├────────────────────────>│                           │
   │                         │                           │
   │                         │ 1. Get product            │
   │                         ├──────────────────────────>│
   │                         │    SELECT * FROM          │
   │                         │    products WHERE id=123  │
   │                         │<──────────────────────────┤
   │                         │    Product data (EN)      │
   │                         │                           │
   │                         │ 2. Extract language       │
   │                         │    from header: "es"      │
   │                         │                           │
   │                         │ 3. Get Spanish trans.     │
   │                         ├──────────────────────────>│
   │                         │    SELECT * FROM          │
   │                         │    translations WHERE     │
   │                         │    entity_id=123 AND      │
   │                         │    language_code='es'     │
   │                         │<──────────────────────────┤
   │                         │    Spanish translations   │
   │                         │                           │
   │                         │ 4. Merge data             │
   │                         │    name: "Hamburguesa"    │
   │                         │    desc: "Deliciosa..."   │
   │                         │                           │
   │<────────────────────────┤                           │
   │  200 OK                 │                           │
   │  Product in Spanish     │                           │
   │                         │                           │
```

---

## 🔄 READ Flow (List - Efficient)

```
Frontend                  Backend                    Database
   │                         │                           │
   │  GET /products          │                           │
   │  Accept-Language: es    │                           │
   ├────────────────────────>│                           │
   │                         │                           │
   │                         │ 1. Get all products       │
   │                         ├──────────────────────────>│
   │                         │    SELECT * FROM          │
   │                         │    products LIMIT 10      │
   │                         │<──────────────────────────┤
   │                         │    [10 products]          │
   │                         │                           │
   │                         │ 2. Extract language: es   │
   │                         │                           │
   │                         │ 3. Batch fetch trans.     │
   │                         ├──────────────────────────>│
   │                         │    SELECT * FROM          │
   │                         │    translations WHERE     │
   │                         │    entity_id IN (...)     │
   │                         │    AND language_code='es' │
   │                         │<──────────────────────────┤
   │                         │    All Spanish trans.     │
   │                         │                           │
   │                         │ 4. Map translations       │
   │                         │    to products            │
   │                         │    (in memory)            │
   │                         │                           │
   │<────────────────────────┤                           │
   │  200 OK                 │                           │
   │  10 products in Spanish │                           │
   │  (2 queries total)      │                           │
   │                         │                           │
```

**Performance**: Only 2 queries regardless of list size!

---

## 🔄 UPDATE Flow

```
Frontend                  Backend                    Database
   │                         │                           │
   │  PUT /products/123      │                           │
   │  + translations_json    │                           │
   ├────────────────────────>│                           │
   │                         │                           │
   │                         │ 1. Find product           │
   │                         ├──────────────────────────>│
   │                         │<──────────────────────────┤
   │                         │                           │
   │                         │ 2. Update product         │
   │                         │    (English fields)       │
   │                         ├──────────────────────────>│
   │                         │    UPDATE products...     │
   │                         │                           │
   │                         │ 3. Parse translations     │
   │                         │                           │
   │                         │ 4. For each translation:  │
   │                         │    Check if exists        │
   │                         ├──────────────────────────>│
   │                         │    SELECT FROM            │
   │                         │    translations...        │
   │                         │<──────────────────────────┤
   │                         │                           │
   │                         │    If exists: UPDATE      │
   │                         │    If not: INSERT         │
   │                         ├──────────────────────────>│
   │                         │                           │
   │<────────────────────────┤                           │
   │  200 OK                 │                           │
   │  Updated successfully   │                           │
   │                         │                           │
```

**Smart Update**: Only modifies/creates translations that are sent

---

## 🔄 DELETE Flow

```
Frontend                  Backend                    Database
   │                         │                           │
   │  DELETE /products/123   │                           │
   ├────────────────────────>│                           │
   │                         │                           │
   │                         │ 1. Find product           │
   │                         ├──────────────────────────>│
   │                         │<──────────────────────────┤
   │                         │                           │
   │                         │ 2. Delete translations    │
   │                         ├──────────────────────────>│
   │                         │    DELETE FROM            │
   │                         │    translations WHERE     │
   │                         │    entity_type='product'  │
   │                         │    AND entity_id='123'    │
   │                         │                           │
   │                         │ 3. Delete product         │
   │                         ├──────────────────────────>│
   │                         │    DELETE FROM            │
   │                         │    products WHERE id=123  │
   │                         │                           │
   │<────────────────────────┤                           │
   │  204 No Content         │                           │
   │  Deleted successfully   │                           │
   │                         │                           │
```

**Clean Deletion**: Both product and translations removed

---

## 📊 Database Schema

### Products Table (Example)
```sql
+----------------+------------------+
| Field          | Value            |
+----------------+------------------+
| id             | product-123      |
| name           | Classic Burger   | ← English (base)
| slug           | classic-burger   |
| description    | Delicious...     | ← English (base)
| price          | 1500             |
| category_id    | cat-456          |
+----------------+------------------+
```

### Translations Table
```sql
+-------------+-------------+-------------+---------------+----------------------+
| entity_type | entity_id   | field_name  | language_code | translation_value    |
+-------------+-------------+-------------+---------------+----------------------+
| product     | product-123 | name        | es            | Hamburguesa Clásica  |
| product     | product-123 | description | es            | Deliciosa...         |
| product     | product-123 | name        | fr            | Hamburger Classique  |
| product     | product-123 | description | fr            | Délicieux...         |
| product     | product-123 | name        | ar            | برجر كلاسيكي         |
+-------------+-------------+-------------+---------------+----------------------+
```

---

## 🎯 Language Fallback Strategy

```
User requests language: "fr"
                │
                ▼
    ┌───────────────────────┐
    │ Translation exists?   │
    └───────┬───────────────┘
            │
        Yes │         No
            │          │
            ▼          ▼
    ┌──────────┐  ┌──────────┐
    │ Return   │  │ Try "en" │
    │ French   │  │ (base)   │
    └──────────┘  └────┬─────┘
                       │
                       ▼
               ┌──────────────┐
               │ Return       │
               │ English/     │
               │ Original     │
               └──────────────┘
```

---

## 🚀 Request/Response Example

### CREATE Request
```http
POST /api/v1/products HTTP/1.1
Content-Type: multipart/form-data

name=Classic Burger
slug=classic-burger
price=1500
description=Delicious beef burger with cheese
translations_json={
  "es": {
    "name": "Hamburguesa Clásica",
    "description": "Deliciosa hamburguesa con queso"
  },
  "fr": {
    "name": "Hamburger Classique",
    "description": "Délicieux hamburger au fromage"
  }
}
```

### CREATE Response
```json
{
  "status": "success",
  "message": "Product created successfully",
  "data": {
    "id": "product-123",
    "name": "Classic Burger",
    "slug": "classic-burger",
    "price": 1500,
    "translations_created": true
  }
}
```

### READ Request (Spanish)
```http
GET /api/v1/products/product-123 HTTP/1.1
Accept-Language: es
```

### READ Response (Spanish)
```json
{
  "status": "success",
  "message": "Product retrieved successfully",
  "data": {
    "id": "product-123",
    "name": "Hamburguesa Clásica",
    "description": "Deliciosa hamburguesa con queso",
    "price": 1500,
    "language": "es"
  }
}
```

### READ Request (French)
```http
GET /api/v1/products/product-123 HTTP/1.1
Accept-Language: fr
```

### READ Response (French)
```json
{
  "status": "success",
  "message": "Product retrieved successfully",
  "data": {
    "id": "product-123",
    "name": "Hamburger Classique",
    "description": "Délicieux hamburger au fromage",
    "price": 1500,
    "language": "fr"
  }
}
```

---

## 📈 Performance Comparison

### Without Batch Translation (N+1 Problem)
```
GET /products (10 items)
│
├─ Query 1: SELECT * FROM products (10 rows)
├─ Query 2: SELECT * FROM translations WHERE entity_id='1' AND lang='es'
├─ Query 3: SELECT * FROM translations WHERE entity_id='2' AND lang='es'
├─ Query 4: SELECT * FROM translations WHERE entity_id='3' AND lang='es'
├─ ...
└─ Query 11: SELECT * FROM translations WHERE entity_id='10' AND lang='es'

Total: 11 queries
```

### With Batch Translation (Efficient)
```
GET /products (10 items)
│
├─ Query 1: SELECT * FROM products (10 rows)
└─ Query 2: SELECT * FROM translations 
            WHERE entity_id IN ('1','2',...,'10') 
            AND lang='es'

Total: 2 queries  ✅
```

---

## 🎨 Entity Type Mapping

```
┌─────────────────────────────────────────────┐
│           Entity Type Mapping                │
├─────────────┬───────────────┬───────────────┤
│ Model       │ entity_type   │ Translatable  │
├─────────────┼───────────────┼───────────────┤
│ Product     │ "product"     │ name, desc    │
│ Category    │ "category"    │ name, desc    │
│ Modifier    │ "modifier"    │ name          │
│ ModOption   │ "mod_option"  │ name          │
│ ComboProduct│ "combo"       │ name, desc    │
│ ComboItem   │ "combo_item"  │ name          │
└─────────────┴───────────────┴───────────────┘
```

---

## ✅ Implementation Summary

| Operation | Helper Function | When Called |
|-----------|----------------|-------------|
| **CREATE** | `create_entity_translations()` | After entity created |
| **UPDATE** | `update_entity_translations()` | After entity updated |
| **DELETE** | `delete_entity_translations()` | Before entity deleted |
| **GET (single)** | `get_translated_field()` | When reading one entity |
| **GET (list)** | `translate_entity_list()` | When reading multiple |

---

**Key Takeaway**: The translation system is completely additive. No changes to existing data structures, just additional translation records that enhance the base English data.
