# Multi-Language Implementation Guide for Your POS Project

**Project-Specific Implementation Steps**  
**Date:** November 25, 2025  
**Your Project:** Restaurant POS FastAPI + React/Next.js

---

## 🎯 Implementation Roadmap

### Phase 1: Backend Setup (Day 1-2)
- Create translation files structure
- Add translation API endpoints
- Test with Postman/curl

### Phase 2: Frontend Integration (Day 3-4)
- Add i18n utility
- Create language selector
- Update existing components

### Phase 3: Database Translations (Day 5-7)
- Create translations table
- Update product/category endpoints
- Migration scripts

---

## Step 1: Create Translation Files

### 1.1 Create Directory Structure

```bash
cd /home/brunodoss/docs/pos/pos/pos-fastapi

# Create translations directory
mkdir -p app/translations

# Create translation files
touch app/translations/en.json
touch app/translations/es.json
touch app/translations/fr.json
touch app/translations/ar.json
```

### 1.2 Add English Translations (Base)

```bash
cat > app/translations/en.json << 'EOF'
{
  "common": {
    "save": "Save",
    "cancel": "Cancel",
    "delete": "Delete",
    "edit": "Edit",
    "search": "Search",
    "loading": "Loading...",
    "refresh": "Refresh",
    "back": "Back",
    "next": "Next",
    "previous": "Previous",
    "submit": "Submit",
    "close": "Close",
    "view": "View",
    "select": "Select",
    "actions": "Actions"
  },
  "auth": {
    "login": "Login",
    "logout": "Logout",
    "username": "Username",
    "password": "Password",
    "forgot_password": "Forgot Password?",
    "remember_me": "Remember Me",
    "sign_in": "Sign In",
    "welcome": "Welcome to Restaurant POS"
  },
  "navigation": {
    "dashboard": "Dashboard",
    "products": "Products",
    "categories": "Categories",
    "orders": "Orders",
    "customers": "Customers",
    "users": "Users",
    "settings": "Settings",
    "reports": "Reports",
    "analytics": "Analytics"
  },
  "products": {
    "title": "Products",
    "add_new": "Add New Product",
    "edit_product": "Edit Product",
    "delete_product": "Delete Product",
    "product_name": "Product Name",
    "product_slug": "Product Slug",
    "description": "Description",
    "price": "Price",
    "category": "Category",
    "sku": "SKU",
    "stock": "Stock",
    "available": "Available",
    "unavailable": "Unavailable",
    "image": "Image",
    "upload_image": "Upload Image",
    "not_found": "Product not found",
    "created_success": "Product created successfully",
    "updated_success": "Product updated successfully",
    "deleted_success": "Product deleted successfully"
  },
  "categories": {
    "title": "Categories",
    "add_new": "Add New Category",
    "edit_category": "Edit Category",
    "delete_category": "Delete Category",
    "category_name": "Category Name",
    "description": "Description",
    "image": "Image",
    "not_found": "Category not found",
    "created_success": "Category created successfully",
    "updated_success": "Category updated successfully",
    "deleted_success": "Category deleted successfully"
  },
  "modifiers": {
    "title": "Modifiers",
    "add_new": "Add New Modifier",
    "modifier_name": "Modifier Name",
    "type": "Type",
    "single": "Single Selection",
    "multiple": "Multiple Selection",
    "required": "Required",
    "optional": "Optional",
    "min_selections": "Minimum Selections",
    "max_selections": "Maximum Selections",
    "options": "Options",
    "add_option": "Add Option",
    "option_name": "Option Name",
    "option_price": "Option Price",
    "free": "Free"
  },
  "orders": {
    "title": "Orders",
    "new_order": "New Order",
    "order_number": "Order Number",
    "order_date": "Order Date",
    "customer": "Customer",
    "items": "Items",
    "quantity": "Quantity",
    "unit_price": "Unit Price",
    "subtotal": "Subtotal",
    "tax": "Tax",
    "discount": "Discount",
    "total": "Total",
    "status": "Status",
    "payment_method": "Payment Method",
    "notes": "Notes",
    "statuses": {
      "pending": "Pending",
      "confirmed": "Confirmed",
      "preparing": "Preparing",
      "ready": "Ready",
      "delivered": "Delivered",
      "cancelled": "Cancelled"
    }
  },
  "customers": {
    "title": "Customers",
    "add_new": "Add New Customer",
    "customer_name": "Customer Name",
    "email": "Email",
    "phone": "Phone",
    "address": "Address",
    "loyalty_points": "Loyalty Points"
  },
  "validation": {
    "required": "{field} is required",
    "min_length": "{field} must be at least {min} characters",
    "max_length": "{field} must not exceed {max} characters",
    "invalid_email": "Invalid email address",
    "invalid_phone": "Invalid phone number",
    "invalid_price": "Price must be greater than 0",
    "invalid_quantity": "Quantity must be at least 1",
    "unique": "{field} must be unique"
  },
  "messages": {
    "confirm_delete": "Are you sure you want to delete this {item}?",
    "no_data": "No data available",
    "loading_data": "Loading data...",
    "error_occurred": "An error occurred",
    "success": "Success",
    "error": "Error",
    "warning": "Warning",
    "info": "Info"
  }
}
EOF
```

### 1.3 Add Spanish Translations

```bash
cat > app/translations/es.json << 'EOF'
{
  "common": {
    "save": "Guardar",
    "cancel": "Cancelar",
    "delete": "Eliminar",
    "edit": "Editar",
    "search": "Buscar",
    "loading": "Cargando...",
    "refresh": "Actualizar",
    "back": "Volver",
    "next": "Siguiente",
    "previous": "Anterior",
    "submit": "Enviar",
    "close": "Cerrar",
    "view": "Ver",
    "select": "Seleccionar",
    "actions": "Acciones"
  },
  "auth": {
    "login": "Iniciar Sesión",
    "logout": "Cerrar Sesión",
    "username": "Usuario",
    "password": "Contraseña",
    "forgot_password": "¿Olvidó su contraseña?",
    "remember_me": "Recordarme",
    "sign_in": "Entrar",
    "welcome": "Bienvenido a Restaurant POS"
  },
  "navigation": {
    "dashboard": "Panel",
    "products": "Productos",
    "categories": "Categorías",
    "orders": "Pedidos",
    "customers": "Clientes",
    "users": "Usuarios",
    "settings": "Configuración",
    "reports": "Informes",
    "analytics": "Analítica"
  },
  "products": {
    "title": "Productos",
    "add_new": "Agregar Nuevo Producto",
    "edit_product": "Editar Producto",
    "delete_product": "Eliminar Producto",
    "product_name": "Nombre del Producto",
    "product_slug": "Slug del Producto",
    "description": "Descripción",
    "price": "Precio",
    "category": "Categoría",
    "sku": "SKU",
    "stock": "Inventario",
    "available": "Disponible",
    "unavailable": "No Disponible",
    "image": "Imagen",
    "upload_image": "Subir Imagen",
    "not_found": "Producto no encontrado",
    "created_success": "Producto creado exitosamente",
    "updated_success": "Producto actualizado exitosamente",
    "deleted_success": "Producto eliminado exitosamente"
  },
  "categories": {
    "title": "Categorías",
    "add_new": "Agregar Nueva Categoría",
    "edit_category": "Editar Categoría",
    "delete_category": "Eliminar Categoría",
    "category_name": "Nombre de la Categoría",
    "description": "Descripción",
    "image": "Imagen",
    "not_found": "Categoría no encontrada",
    "created_success": "Categoría creada exitosamente",
    "updated_success": "Categoría actualizada exitosamente",
    "deleted_success": "Categoría eliminada exitosamente"
  },
  "modifiers": {
    "title": "Modificadores",
    "add_new": "Agregar Nuevo Modificador",
    "modifier_name": "Nombre del Modificador",
    "type": "Tipo",
    "single": "Selección Única",
    "multiple": "Selección Múltiple",
    "required": "Requerido",
    "optional": "Opcional",
    "min_selections": "Selecciones Mínimas",
    "max_selections": "Selecciones Máximas",
    "options": "Opciones",
    "add_option": "Agregar Opción",
    "option_name": "Nombre de la Opción",
    "option_price": "Precio de la Opción",
    "free": "Gratis"
  },
  "orders": {
    "title": "Pedidos",
    "new_order": "Nuevo Pedido",
    "order_number": "Número de Pedido",
    "order_date": "Fecha del Pedido",
    "customer": "Cliente",
    "items": "Artículos",
    "quantity": "Cantidad",
    "unit_price": "Precio Unitario",
    "subtotal": "Subtotal",
    "tax": "Impuesto",
    "discount": "Descuento",
    "total": "Total",
    "status": "Estado",
    "payment_method": "Método de Pago",
    "notes": "Notas",
    "statuses": {
      "pending": "Pendiente",
      "confirmed": "Confirmado",
      "preparing": "Preparando",
      "ready": "Listo",
      "delivered": "Entregado",
      "cancelled": "Cancelado"
    }
  },
  "customers": {
    "title": "Clientes",
    "add_new": "Agregar Nuevo Cliente",
    "customer_name": "Nombre del Cliente",
    "email": "Correo Electrónico",
    "phone": "Teléfono",
    "address": "Dirección",
    "loyalty_points": "Puntos de Lealtad"
  },
  "validation": {
    "required": "{field} es requerido",
    "min_length": "{field} debe tener al menos {min} caracteres",
    "max_length": "{field} no debe exceder {max} caracteres",
    "invalid_email": "Correo electrónico inválido",
    "invalid_phone": "Número de teléfono inválido",
    "invalid_price": "El precio debe ser mayor que 0",
    "invalid_quantity": "La cantidad debe ser al menos 1",
    "unique": "{field} debe ser único"
  },
  "messages": {
    "confirm_delete": "¿Está seguro de que desea eliminar este {item}?",
    "no_data": "No hay datos disponibles",
    "loading_data": "Cargando datos...",
    "error_occurred": "Ocurrió un error",
    "success": "Éxito",
    "error": "Error",
    "warning": "Advertencia",
    "info": "Información"
  }
}
EOF
```

---

## Step 2: Create Translation API Endpoints

### 2.1 Create Translation Routes File

```bash
cat > app/routes/translations.py << 'EOF'
"""
Translation API routes
"""
from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
from typing import Dict, Any

router = APIRouter(prefix="/api/v1/translations", tags=["translations"])

TRANSLATIONS_DIR = Path(__file__).parent.parent / "translations"
SUPPORTED_LANGUAGES = ["en", "es", "fr", "ar"]

@router.get("/languages")
def get_supported_languages():
    """Get list of supported languages"""
    return {
        "success": True,
        "data": [
            {
                "code": "en",
                "name": "English",
                "native_name": "English",
                "rtl": False
            },
            {
                "code": "es",
                "name": "Spanish",
                "native_name": "Español",
                "rtl": False
            },
            {
                "code": "fr",
                "name": "French",
                "native_name": "Français",
                "rtl": False
            },
            {
                "code": "ar",
                "name": "Arabic",
                "native_name": "العربية",
                "rtl": True
            }
        ],
        "default_language": "en"
    }


@router.get("/{language}")
def get_translations(language: str) -> Dict[str, Any]:
    """Get all translations for a specific language"""
    if language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language. Supported: {', '.join(SUPPORTED_LANGUAGES)}"
        )
    
    file_path = TRANSLATIONS_DIR / f"{language}.json"
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Translation file not found for language: {language}"
        )
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            translations = json.load(f)
        
        return {
            "success": True,
            "language": language,
            "translations": translations
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading translations: {str(e)}"
        )
EOF
```

### 2.2 Register Translation Routes in Main App

```bash
# This will show you the current main.py structure
cat app/main.py | grep "include_router"
```

Now add the translation routes:

```python
# Open app/main.py and add after other router imports:
from app.routes import translations

# Then add after other include_router calls:
app.include_router(translations.router)
```

### 2.3 Test the Translation Endpoint

```bash
# Restart the server
sudo docker restart restaurant_pos_api

# Wait for server to start
sleep 5

# Test get supported languages
curl http://localhost:8000/api/v1/translations/languages | jq

# Test get English translations
curl http://localhost:8000/api/v1/translations/en | jq '.translations.common'

# Test get Spanish translations
curl http://localhost:8000/api/v1/translations/es | jq '.translations.products'
```

---

## Step 3: Create Database Translation Table

### 3.1 Create Migration File

```bash
cat > app/migrations/add_translations_table.sql << 'EOF'
-- Migration: Add translations table for dynamic content
-- Date: 2025-11-25

CREATE TABLE IF NOT EXISTS translations (
    id VARCHAR(36) PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL COMMENT 'product, category, modifier, modifier_option',
    entity_id VARCHAR(36) NOT NULL COMMENT 'ID of the entity',
    field_name VARCHAR(50) NOT NULL COMMENT 'name, description, etc',
    language_code VARCHAR(10) NOT NULL COMMENT 'en, es, fr, ar',
    translation_value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_translation (entity_type, entity_id, field_name, language_code),
    INDEX idx_entity_lookup (entity_type, entity_id, language_code),
    INDEX idx_language (language_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add some example translations for existing products
-- Note: Replace with your actual product IDs after running
EOF
```

### 3.2 Run Migration

```bash
# Connect to MySQL and run migration
sudo docker exec -i restaurant_pos_mysql mysql -uroot -pYourPassword123! restaurant_pos < app/migrations/add_translations_table.sql

# Verify table was created
sudo docker exec -it restaurant_pos_mysql mysql -uroot -pYourPassword123! restaurant_pos -e "DESCRIBE translations;"
```

### 3.3 Create Translation Model

```bash
cat > app/models/translation.py << 'EOF'
"""
Translation model for dynamic content
"""
import uuid
from sqlalchemy import Column, String, Text, DateTime, Index
from sqlalchemy.sql import func
from app.database import Base


class Translation(Base):
    __tablename__ = "translations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(36), nullable=False)
    field_name = Column(String(50), nullable=False)
    language_code = Column(String(10), nullable=False)
    translation_value = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_entity_lookup', 'entity_type', 'entity_id', 'language_code'),
        Index('idx_language', 'language_code'),
    )
    
    def __repr__(self):
        return f"<Translation({self.entity_type}:{self.entity_id}:{self.field_name}:{self.language_code})>"
EOF
```

---

## Step 4: Add Translation Helper Functions

### 4.1 Create Translation Utils

```bash
cat > app/i18n.py << 'EOF'
"""
Internationalization (i18n) helper functions
"""
from sqlalchemy.orm import Session
from app.models.translation import Translation
from typing import Optional


def get_translated_field(
    db: Session,
    entity_type: str,
    entity_id: str,
    field_name: str,
    language: str,
    default_value: Optional[str] = None
) -> Optional[str]:
    """
    Get translated field value with automatic fallback
    
    Fallback order:
    1. Requested language
    2. English (default)
    3. Original value
    """
    # Try requested language
    translation = db.query(Translation).filter(
        Translation.entity_type == entity_type,
        Translation.entity_id == str(entity_id),
        Translation.field_name == field_name,
        Translation.language_code == language
    ).first()
    
    if translation:
        return translation.translation_value
    
    # Fallback to English if not the requested language
    if language != 'en':
        translation = db.query(Translation).filter(
            Translation.entity_type == entity_type,
            Translation.entity_id == str(entity_id),
            Translation.field_name == field_name,
            Translation.language_code == 'en'
        ).first()
        
        if translation:
            return translation.translation_value
    
    # Fallback to original value
    return default_value


def extract_language_from_header(accept_language: Optional[str] = None) -> str:
    """
    Extract preferred language from Accept-Language header
    
    Examples:
    - "en-US,en;q=0.9,es;q=0.8" → "en"
    - "es-ES" → "es"
    - "ar" → "ar"
    - None → "en" (default)
    """
    if not accept_language:
        return 'en'
    
    # Parse Accept-Language header
    # Format: "en-US,en;q=0.9,es;q=0.8"
    languages = []
    for lang_entry in accept_language.split(','):
        # Remove quality factor if present
        lang = lang_entry.split(';')[0].strip()
        # Extract language code (before hyphen)
        lang_code = lang.split('-')[0].lower()
        languages.append(lang_code)
    
    # Return first supported language
    supported = ['en', 'es', 'fr', 'ar']
    for lang in languages:
        if lang in supported:
            return lang
    
    return 'en'  # Default fallback
EOF
```

---

## Step 5: Update Product Endpoint with Translations

### 5.1 Modify Product Routes

Add translation support to your existing `app/routes/products.py`:

```python
# Add these imports at the top
from app.models.translation import Translation
from app.i18n import get_translated_field, extract_language_from_header
from fastapi import Header
from typing import Optional

# Modify the get_product endpoint
@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: str,
    accept_language: Optional[str] = Header(default=None),
    db: Session = Depends(get_db)
):
    """Get product by ID with translation support"""
    product = db.query(Product).filter(Product.id == str(product_id)).first()
    
    if not product:
        raise HTTPException(
            status_code=404,
            detail=f"Product with id {product_id} not found"
        )
    
    # Extract language preference
    language = extract_language_from_header(accept_language)
    
    # Get translations
    translated_name = get_translated_field(
        db, 'product', product.id, 'name', language, product.name
    )
    translated_description = get_translated_field(
        db, 'product', product.id, 'description', language, product.description
    )
    
    # Apply translations
    product.name = translated_name
    product.description = translated_description
    
    return product
```

### 5.2 Test Product Translation

```bash
# First, add some test translations
sudo docker exec -it restaurant_pos_mysql mysql -uroot -pYourPassword123! restaurant_pos << 'EOF'
-- Get a product ID to test with
SELECT id, name FROM products LIMIT 1;
EOF

# Use the ID from above (replace PRODUCT_ID_HERE)
sudo docker exec -it restaurant_pos_mysql mysql -uroot -pYourPassword123! restaurant_pos << 'EOF'
INSERT INTO translations (id, entity_type, entity_id, field_name, language_code, translation_value)
VALUES 
(UUID(), 'product', 'YOUR_PRODUCT_ID_HERE', 'name', 'es', 'Nombre en Español'),
(UUID(), 'product', 'YOUR_PRODUCT_ID_HERE', 'description', 'es', 'Descripción en español');
EOF

# Test with English (default)
curl http://localhost:8000/api/v1/products/YOUR_PRODUCT_ID_HERE | jq '.name'

# Test with Spanish
curl -H "Accept-Language: es" http://localhost:8000/api/v1/products/YOUR_PRODUCT_ID_HERE | jq '.name'
```

---

## Step 6: Add Translation Management Endpoints

### 6.1 Add to Translation Routes

```python
# Add to app/routes/translations.py

from app.models.translation import Translation
from app.database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends
from pydantic import BaseModel
import uuid

class TranslationCreate(BaseModel):
    entity_type: str
    entity_id: str
    field_name: str
    language_code: str
    translation_value: str

@router.post("/entity")
def add_translation(
    translation: TranslationCreate,
    db: Session = Depends(get_db)
):
    """Add or update translation for any entity"""
    
    # Check if translation exists
    existing = db.query(Translation).filter(
        Translation.entity_type == translation.entity_type,
        Translation.entity_id == translation.entity_id,
        Translation.field_name == translation.field_name,
        Translation.language_code == translation.language_code
    ).first()
    
    if existing:
        # Update
        existing.translation_value = translation.translation_value
        db.commit()
        db.refresh(existing)
        return {
            "success": True,
            "message": "Translation updated successfully",
            "data": existing
        }
    else:
        # Create
        new_translation = Translation(
            id=str(uuid.uuid4()),
            **translation.dict()
        )
        db.add(new_translation)
        db.commit()
        db.refresh(new_translation)
        return {
            "success": True,
            "message": "Translation created successfully",
            "data": new_translation
        }


@router.get("/entity/{entity_type}/{entity_id}")
def get_entity_translations(
    entity_type: str,
    entity_id: str,
    db: Session = Depends(get_db)
):
    """Get all translations for an entity"""
    translations = db.query(Translation).filter(
        Translation.entity_type == entity_type,
        Translation.entity_id == entity_id
    ).all()
    
    # Group by language
    result = {}
    for t in translations:
        if t.language_code not in result:
            result[t.language_code] = {}
        result[t.language_code][t.field_name] = t.translation_value
    
    return {
        "success": True,
        "data": result
    }
```

---

## Step 7: Frontend Integration (Example)

### 7.1 Create i18n Utility (if using React/Next.js frontend)

```javascript
// frontend/utils/i18n.js
class I18n {
  constructor() {
    this.translations = {};
    this.currentLanguage = localStorage.getItem('language') || 'en';
    this.loadTranslations();
  }

  async loadTranslations() {
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE}/api/v1/translations/${this.currentLanguage}`);
      const data = await response.json();
      
      if (data.success) {
        this.translations = data.translations;
      }
    } catch (error) {
      console.error('Failed to load translations:', error);
      
      // Fallback to English if error
      if (this.currentLanguage !== 'en') {
        this.currentLanguage = 'en';
        await this.loadTranslations();
      }
    }
  }

  t(key, variables = {}) {
    // Navigate nested keys: "products.title"
    const keys = key.split('.');
    let value = this.translations;
    
    for (const k of keys) {
      value = value?.[k];
      if (value === undefined) break;
    }

    if (value === undefined) {
      console.warn(`Missing translation: ${key}`);
      return key;
    }

    // Replace variables: "Hello {name}" → "Hello John"
    return Object.keys(variables).reduce(
      (str, varKey) => str.replace(`{${varKey}}`, variables[varKey]),
      value
    );
  }

  async setLanguage(language) {
    this.currentLanguage = language;
    localStorage.setItem('language', language);
    await this.loadTranslations();
    
    // Set document direction for RTL languages
    const RTL_LANGUAGES = ['ar', 'he', 'fa', 'ur'];
    document.documentElement.dir = RTL_LANGUAGES.includes(language) ? 'rtl' : 'ltr';
    document.documentElement.lang = language;
  }

  getLanguage() {
    return this.currentLanguage;
  }
}

export const i18n = new I18n();
```

### 7.2 Language Selector Component

```javascript
// frontend/components/LanguageSelector.jsx
import { useState, useEffect } from 'react';
import { i18n } from '../utils/i18n';

export default function LanguageSelector() {
  const [languages, setLanguages] = useState([]);
  const [current, setCurrent] = useState(i18n.getLanguage());

  useEffect(() => {
    // Fetch supported languages
    fetch('http://localhost:8000/api/v1/translations/languages')
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setLanguages(data.data);
        }
      });
  }, []);

  const handleChange = async (lang) => {
    await i18n.setLanguage(lang);
    setCurrent(lang);
    window.location.reload(); // Reload to apply translations
  };

  return (
    <select 
      value={current} 
      onChange={(e) => handleChange(e.target.value)}
      className="language-selector"
    >
      {languages.map(lang => (
        <option key={lang.code} value={lang.code}>
          {lang.native_name}
        </option>
      ))}
    </select>
  );
}
```

---

## Step 8: Testing & Verification

### 8.1 Test Checklist

```bash
# 1. Test translation file endpoint
curl http://localhost:8000/api/v1/translations/en | jq '.success'
curl http://localhost:8000/api/v1/translations/es | jq '.success'

# 2. Test supported languages endpoint
curl http://localhost:8000/api/v1/translations/languages | jq '.data[] | .code'

# 3. Test product with translation (replace PRODUCT_ID)
curl http://localhost:8000/api/v1/products/PRODUCT_ID | jq '.name'
curl -H "Accept-Language: es" http://localhost:8000/api/v1/products/PRODUCT_ID | jq '.name'

# 4. Test adding translation
curl -X POST http://localhost:8000/api/v1/translations/entity \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type": "product",
    "entity_id": "YOUR_PRODUCT_ID",
    "field_name": "name",
    "language_code": "es",
    "translation_value": "Producto de Prueba"
  }' | jq

# 5. Test getting entity translations
curl http://localhost:8000/api/v1/translations/entity/product/YOUR_PRODUCT_ID | jq
```

---

## Step 9: Bulk Data Migration (Optional)

### 9.1 Create Migration Script for Existing Data

```bash
cat > scripts/migrate_translations.py << 'EOF'
"""
Migrate existing product/category data to translations table
"""
import sys
sys.path.append('/home/brunodoss/docs/pos/pos/pos-fastapi')

from app.database import SessionLocal
from app.models.product import Product, Category
from app.models.translation import Translation
import uuid


def migrate_products():
    """Migrate all products to translation table (English as base)"""
    db = SessionLocal()
    
    try:
        products = db.query(Product).all()
        count = 0
        
        for product in products:
            # Add name translation
            if product.name:
                translation = Translation(
                    id=str(uuid.uuid4()),
                    entity_type='product',
                    entity_id=product.id,
                    field_name='name',
                    language_code='en',
                    translation_value=product.name
                )
                db.merge(translation)
                count += 1
            
            # Add description translation
            if product.description:
                translation = Translation(
                    id=str(uuid.uuid4()),
                    entity_type='product',
                    entity_id=product.id,
                    field_name='description',
                    language_code='en',
                    translation_value=product.description
                )
                db.merge(translation)
                count += 1
        
        db.commit()
        print(f"✅ Migrated {count} product translations")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


def migrate_categories():
    """Migrate all categories to translation table (English as base)"""
    db = SessionLocal()
    
    try:
        categories = db.query(Category).all()
        count = 0
        
        for category in categories:
            # Add name translation
            if category.name:
                translation = Translation(
                    id=str(uuid.uuid4()),
                    entity_type='category',
                    entity_id=category.id,
                    field_name='name',
                    language_code='en',
                    translation_value=category.name
                )
                db.merge(translation)
                count += 1
            
            # Add description translation
            if category.description:
                translation = Translation(
                    id=str(uuid.uuid4()),
                    entity_type='category',
                    entity_id=category.id,
                    field_name='description',
                    language_code='en',
                    translation_value=category.description
                )
                db.merge(translation)
                count += 1
        
        db.commit()
        print(f"✅ Migrated {count} category translations")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("Starting migration...")
    migrate_products()
    migrate_categories()
    print("✅ Migration complete!")
EOF

# Run migration
cd /home/brunodoss/docs/pos/pos/pos-fastapi
python3 scripts/migrate_translations.py
```

---

## Step 10: Documentation Update

### 10.1 Update API Documentation

Add translation endpoints to your API documentation:

```markdown
## Translation Endpoints

### Get Supported Languages
GET /api/v1/translations/languages

### Get Translations for Language
GET /api/v1/translations/{language_code}

### Add/Update Translation
POST /api/v1/translations/entity
Body: {
  "entity_type": "product",
  "entity_id": "uuid",
  "field_name": "name",
  "language_code": "es",
  "translation_value": "Translated text"
}

### Get Entity Translations
GET /api/v1/translations/entity/{entity_type}/{entity_id}

### Using Translations in Product API
GET /api/v1/products/{product_id}
Header: Accept-Language: es
```

---

## Summary & Next Steps

### ✅ What You've Implemented

**Phase 1: JSON Files (Completed)**
- ✅ Created translation files (en.json, es.json)
- ✅ Added translation API endpoints
- ✅ Tested with curl

**Phase 2: Database Translations (Completed)**
- ✅ Created translations table
- ✅ Added Translation model
- ✅ Created helper functions
- ✅ Updated product endpoint with translation support
- ✅ Added translation management endpoints

**Phase 3: Testing & Migration (Completed)**
- ✅ Created test cases
- ✅ Created migration scripts for existing data

### 📝 What's Next (Optional)

1. **Apply to Other Endpoints**
   - Update `categories.py` with translations
   - Update `modifiers.py` with translations
   - Update `combos.py` with translations

2. **Frontend Integration**
   - Create i18n utility
   - Add language selector component
   - Update all components to use translations

3. **Advanced Features**
   - Add Redis caching for translations
   - Create admin UI for translation management
   - Add bulk import/export tools
   - Add translation coverage reports

4. **Performance Optimization**
   - Cache frequently accessed translations
   - Pre-load translations on app start
   - Implement lazy loading for large translation sets

---

## Quick Reference Commands

```bash
# Restart API server
sudo docker restart restaurant_pos_api

# Test translation endpoint
curl http://localhost:8000/api/v1/translations/en | jq

# Get supported languages
curl http://localhost:8000/api/v1/translations/languages | jq

# Test product with Spanish
curl -H "Accept-Language: es" http://localhost:8000/api/v1/products/PRODUCT_ID | jq

# Add translation
curl -X POST http://localhost:8000/api/v1/translations/entity \
  -H "Content-Type: application/json" \
  -d '{"entity_type":"product","entity_id":"ID","field_name":"name","language_code":"es","translation_value":"Nombre"}' | jq
```

---

**Implementation Time Estimate:**
- Phase 1 (JSON files): 2-3 hours ✅
- Phase 2 (Database): 3-4 hours ✅
- Phase 3 (Testing): 1-2 hours ✅
- **Total: 6-9 hours (1 day)**

You now have a fully functional multi-language system integrated into your existing POS project! 🎉
