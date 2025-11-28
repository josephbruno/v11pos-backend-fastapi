# Multi-Currency & Multi-Language Implementation Guidelines

Comprehensive guide for implementing internationalization (i18n) and multi-currency support in your Restaurant POS system.

**Document Version:** 1.0  
**Date:** November 25, 2025  
**Status:** Design Guidelines (No Code Changes)

---

## Table of Contents
1. [Current Architecture Analysis](#current-architecture-analysis)
2. [Multi-Currency Strategy](#multi-currency-strategy)
3. [Multi-Language Strategy](#multi-language-strategy)
4. [Database Schema Recommendations](#database-schema-recommendations)
5. [API Design Patterns](#api-design-patterns)
6. [Frontend Implementation](#frontend-implementation)
7. [Migration Strategy](#migration-strategy)
8. [Testing Considerations](#testing-considerations)

---

## Current Architecture Analysis

### Existing System Overview

**Current Price Storage:**
- All prices stored in **cents (integers)** in database
- Products: `price` field (e.g., 1299 = $12.99)
- Modifiers: `price` field (e.g., 150 = $1.50)
- Orders: `total_amount`, `subtotal`, `tax_amount` in cents
- **Assumption:** USD only, single currency

**Current Text Fields:**
- Product names, descriptions (single language)
- Category names, descriptions (single language)
- Modifier names, option names (single language)
- No language code tracking
- No translation tables

**Authentication & User Settings:**
- User table exists but no locale/currency preferences
- No timezone handling visible
- No language preference per user

---

## Multi-Currency Strategy

### 1. Recommended Approach: Store in Base Currency

**Design Pattern:**
```
Database Storage → Base Currency (e.g., USD cents)
API Response → Client's Preferred Currency (converted)
Display → Localized Format
```

**Advantages:**
- ✅ No schema changes to existing price fields
- ✅ Single source of truth for pricing
- ✅ Easier accounting and reporting
- ✅ Exchange rates managed centrally

**Disadvantages:**
- ❌ Requires real-time or cached exchange rates
- ❌ Conversion overhead on API responses
- ❌ Rounding considerations

---

### 2. Database Schema Additions

#### Add Currency Configuration Table
```sql
CREATE TABLE currencies (
    id VARCHAR(36) PRIMARY KEY,
    code VARCHAR(3) NOT NULL UNIQUE,  -- ISO 4217 (USD, EUR, GBP, INR, etc.)
    name VARCHAR(100) NOT NULL,       -- US Dollar, Euro, etc.
    symbol VARCHAR(10) NOT NULL,      -- $, €, £, ₹, etc.
    decimal_places INT DEFAULT 2,     -- 2 for most, 0 for JPY, 3 for KWD
    is_active BOOLEAN DEFAULT TRUE,
    is_base BOOLEAN DEFAULT FALSE,    -- Base currency (USD)
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Example data
INSERT INTO currencies (id, code, name, symbol, decimal_places, is_base) VALUES
(UUID(), 'USD', 'US Dollar', '$', 2, TRUE),
(UUID(), 'EUR', 'Euro', '€', 2, FALSE),
(UUID(), 'GBP', 'British Pound', '£', 2, FALSE),
(UUID(), 'INR', 'Indian Rupee', '₹', 2, FALSE),
(UUID(), 'JPY', 'Japanese Yen', '¥', 0, FALSE);
```

#### Add Exchange Rates Table
```sql
CREATE TABLE exchange_rates (
    id VARCHAR(36) PRIMARY KEY,
    from_currency VARCHAR(3) NOT NULL,  -- Base currency (USD)
    to_currency VARCHAR(3) NOT NULL,    -- Target currency
    rate DECIMAL(18, 6) NOT NULL,       -- Exchange rate (e.g., 0.85 for USD->EUR)
    effective_date TIMESTAMP NOT NULL,   -- When rate becomes effective
    source VARCHAR(50),                  -- API source (e.g., 'openexchangerates')
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE KEY (from_currency, to_currency, effective_date),
    INDEX idx_currency_date (to_currency, effective_date DESC)
);

-- Example data
INSERT INTO exchange_rates (id, from_currency, to_currency, rate, effective_date) VALUES
(UUID(), 'USD', 'EUR', 0.85, NOW()),
(UUID(), 'USD', 'GBP', 0.73, NOW()),
(UUID(), 'USD', 'INR', 83.12, NOW()),
(UUID(), 'USD', 'JPY', 110.50, NOW());
```

#### Add User Currency Preference
```sql
ALTER TABLE users 
ADD COLUMN preferred_currency VARCHAR(3) DEFAULT 'USD',
ADD COLUMN preferred_language VARCHAR(10) DEFAULT 'en',
ADD COLUMN timezone VARCHAR(50) DEFAULT 'UTC';

-- Index for faster lookups
CREATE INDEX idx_user_preferences ON users(preferred_currency, preferred_language);
```

#### Add Business/Store Settings
```sql
CREATE TABLE store_settings (
    id VARCHAR(36) PRIMARY KEY,
    key_name VARCHAR(100) NOT NULL UNIQUE,
    value TEXT,
    data_type VARCHAR(20) DEFAULT 'string',  -- string, json, boolean, number
    category VARCHAR(50),                    -- currency, language, general
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Example settings
INSERT INTO store_settings (id, key_name, value, category) VALUES
(UUID(), 'default_currency', 'USD', 'currency'),
(UUID(), 'supported_currencies', '["USD","EUR","GBP","INR","JPY"]', 'currency'),
(UUID(), 'default_language', 'en', 'language'),
(UUID(), 'supported_languages', '["en","es","fr","de","ar","hi"]', 'language'),
(UUID(), 'auto_currency_update', 'true', 'currency'),
(UUID(), 'currency_update_frequency', '3600', 'currency');  -- seconds
```

---

### 3. Currency Conversion Logic

#### API Request Flow
```
1. Client Request → Include currency preference in header/query
   GET /api/v1/products?currency=EUR
   Header: X-Currency: EUR
   
2. Backend Processing:
   a. Fetch products with prices in base currency (USD cents)
   b. Get latest exchange rate for target currency
   c. Convert prices: (price_in_cents / 100) * exchange_rate * 100
   d. Round according to currency rules
   
3. API Response → Return prices in requested currency
   {
     "price": 1099,           // €10.99 (if converted from $12.99)
     "currency": "EUR",
     "original_price": 1299,  // Optional: USD cents
     "exchange_rate": 0.85    // Optional: for transparency
   }
```

#### Conversion Helper Functions (Pseudo-code)
```python
# In app/utils.py or app/currency.py

def get_exchange_rate(from_currency: str, to_currency: str) -> Decimal:
    """Get latest exchange rate, with caching"""
    if from_currency == to_currency:
        return Decimal(1.0)
    
    # Try cache first (Redis recommended)
    cache_key = f"exchange_rate:{from_currency}:{to_currency}"
    rate = cache.get(cache_key)
    
    if rate:
        return Decimal(rate)
    
    # Fetch from database
    rate = db.query(ExchangeRate)\
        .filter(
            ExchangeRate.from_currency == from_currency,
            ExchangeRate.to_currency == to_currency
        )\
        .order_by(ExchangeRate.effective_date.desc())\
        .first()
    
    if rate:
        cache.set(cache_key, str(rate.rate), ttl=3600)  # 1 hour cache
        return rate.rate
    
    # Fallback to external API
    return fetch_rate_from_external_api(from_currency, to_currency)


def convert_price(
    amount_cents: int,
    from_currency: str,
    to_currency: str,
    decimal_places: int = 2
) -> int:
    """Convert price from base currency to target currency"""
    if from_currency == to_currency:
        return amount_cents
    
    rate = get_exchange_rate(from_currency, to_currency)
    
    # Convert to decimal, multiply by rate, round
    amount_decimal = Decimal(amount_cents) / 100
    converted = amount_decimal * rate
    
    # Round to appropriate decimal places
    converted = converted.quantize(
        Decimal(10) ** -decimal_places,
        rounding=ROUND_HALF_UP
    )
    
    # Convert back to cents/smallest unit
    return int(converted * (10 ** decimal_places))


def format_price(
    amount_cents: int,
    currency_code: str,
    locale: str = 'en_US'
) -> str:
    """Format price for display with currency symbol"""
    currency = get_currency_by_code(currency_code)
    amount = amount_cents / (10 ** currency.decimal_places)
    
    # Use babel or locale formatting
    return babel.numbers.format_currency(
        amount,
        currency_code,
        locale=locale
    )
```

---

### 4. Currency API Endpoints Design

#### Get Supported Currencies
```http
GET /api/v1/currencies
Response:
[
  {
    "code": "USD",
    "name": "US Dollar",
    "symbol": "$",
    "decimal_places": 2,
    "is_base": true
  },
  {
    "code": "EUR",
    "name": "Euro",
    "symbol": "€",
    "decimal_places": 2,
    "is_base": false
  }
]
```

#### Get Current Exchange Rates
```http
GET /api/v1/exchange-rates?base=USD
Response:
{
  "base": "USD",
  "date": "2025-11-25T10:30:00Z",
  "rates": {
    "EUR": 0.85,
    "GBP": 0.73,
    "INR": 83.12,
    "JPY": 110.50
  }
}
```

#### Product API with Currency Support
```http
GET /api/v1/products/product-id?currency=EUR
Response:
{
  "id": "product-id",
  "name": "Buffalo Wings",
  "price": 1099,              // Converted to EUR cents
  "currency": "EUR",
  "price_display": "€10.99",
  "original_price": 1299,     // USD cents (optional)
  "original_currency": "USD"
}
```

---

### 5. Exchange Rate Management

#### Manual Update Endpoint
```http
POST /api/v1/exchange-rates
Authorization: Bearer <admin_token>
Body:
{
  "from_currency": "USD",
  "to_currency": "EUR",
  "rate": 0.85,
  "effective_date": "2025-11-25T00:00:00Z",
  "source": "manual"
}
```

#### Automatic Updates (Recommended)

**Option A: Scheduled Task (Celery/Background Job)**
```python
# In app/tasks.py or background jobs
@celery.task
def update_exchange_rates():
    """Update exchange rates every hour"""
    base_currency = get_base_currency()  # USD
    supported_currencies = get_supported_currencies()
    
    for currency in supported_currencies:
        if currency.code == base_currency:
            continue
        
        rate = fetch_from_external_api(base_currency, currency.code)
        
        # Save to database
        new_rate = ExchangeRate(
            from_currency=base_currency,
            to_currency=currency.code,
            rate=rate,
            effective_date=datetime.utcnow(),
            source='openexchangerates'
        )
        db.add(new_rate)
    
    db.commit()
```

**Option B: External API Integration**

Recommended Services:
1. **Open Exchange Rates** (https://openexchangerates.org)
   - Free tier: 1000 requests/month
   - Paid: Real-time rates
   
2. **Fixer.io** (https://fixer.io)
   - Free tier: 100 requests/month
   
3. **ExchangeRate-API** (https://exchangerate-api.com)
   - Free tier: 1500 requests/month

Example Integration:
```python
import requests

def fetch_rates_from_openexchangerates(app_id: str, base: str = 'USD'):
    """Fetch latest exchange rates"""
    url = f"https://openexchangerates.org/api/latest.json?app_id={app_id}&base={base}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        return data['rates']
    
    raise Exception("Failed to fetch exchange rates")
```

---

### 6. Rounding & Precision Rules

Different currencies have different rounding conventions:

```python
CURRENCY_ROUNDING_RULES = {
    'USD': {
        'decimal_places': 2,
        'smallest_unit': 1,      # 1 cent
        'round_to': 0.01
    },
    'EUR': {
        'decimal_places': 2,
        'smallest_unit': 1,
        'round_to': 0.01
    },
    'JPY': {
        'decimal_places': 0,
        'smallest_unit': 1,      # 1 yen (no cents)
        'round_to': 1
    },
    'KWD': {
        'decimal_places': 3,     # Kuwaiti Dinar uses 3 decimals
        'smallest_unit': 1,
        'round_to': 0.001
    },
    'CHF': {
        'decimal_places': 2,
        'smallest_unit': 5,      # Swiss Franc rounds to 0.05
        'round_to': 0.05
    }
}

def apply_currency_rounding(amount: Decimal, currency_code: str) -> Decimal:
    """Apply currency-specific rounding rules"""
    rules = CURRENCY_ROUNDING_RULES.get(currency_code, {'round_to': 0.01})
    round_to = Decimal(str(rules['round_to']))
    
    return (amount / round_to).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * round_to
```

---

## Multi-Language Strategy

### 1. Recommended Approach: Separate Translation Tables

**Design Pattern:**
```
Main Table → ID + Non-translatable fields
Translation Table → Foreign Key + Language Code + Translated fields
API → Return translations based on Accept-Language header
```

**Advantages:**
- ✅ Clean separation of concerns
- ✅ Easy to add new languages
- ✅ Can add translations without schema changes
- ✅ Supports fallback languages

---

### 2. Database Schema for Translations

#### Language Configuration Table
```sql
CREATE TABLE languages (
    id VARCHAR(36) PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE,  -- ISO 639-1 (en, es, fr, de, ar, hi, etc.)
    name VARCHAR(100) NOT NULL,        -- English, Spanish, French, etc.
    native_name VARCHAR(100),          -- English, Español, Français, etc.
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    is_rtl BOOLEAN DEFAULT FALSE,      -- Right-to-left (Arabic, Hebrew)
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Example data
INSERT INTO languages (id, code, name, native_name, is_default, is_rtl) VALUES
(UUID(), 'en', 'English', 'English', TRUE, FALSE),
(UUID(), 'es', 'Spanish', 'Español', FALSE, FALSE),
(UUID(), 'fr', 'French', 'Français', FALSE, FALSE),
(UUID(), 'de', 'German', 'Deutsch', FALSE, FALSE),
(UUID(), 'ar', 'Arabic', 'العربية', FALSE, TRUE),
(UUID(), 'hi', 'Hindi', 'हिन्दी', FALSE, FALSE),
(UUID(), 'zh', 'Chinese', '中文', FALSE, FALSE),
(UUID(), 'ja', 'Japanese', '日本語', FALSE, FALSE);
```

#### Product Translations Table
```sql
CREATE TABLE product_translations (
    id VARCHAR(36) PRIMARY KEY,
    product_id VARCHAR(36) NOT NULL,
    language_code VARCHAR(10) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (language_code) REFERENCES languages(code),
    UNIQUE KEY (product_id, language_code)
);

-- Example data
INSERT INTO product_translations (id, product_id, language_code, name, description) VALUES
(UUID(), 'prod-123', 'en', 'Buffalo Wings', 'Crispy chicken wings with buffalo sauce'),
(UUID(), 'prod-123', 'es', 'Alitas de Búfalo', 'Alitas de pollo crujientes con salsa búfalo'),
(UUID(), 'prod-123', 'fr', 'Ailes de Buffle', 'Ailes de poulet croustillantes avec sauce buffalo'),
(UUID(), 'prod-123', 'ar', 'أجنحة بافالو', 'أجنحة دجاج مقرمشة مع صلصة بافالو');
```

#### Category Translations Table
```sql
CREATE TABLE category_translations (
    id VARCHAR(36) PRIMARY KEY,
    category_id VARCHAR(36) NOT NULL,
    language_code VARCHAR(10) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
    FOREIGN KEY (language_code) REFERENCES languages(code),
    UNIQUE KEY (category_id, language_code)
);
```

#### Modifier Translations Table
```sql
CREATE TABLE modifier_translations (
    id VARCHAR(36) PRIMARY KEY,
    modifier_id VARCHAR(36) NOT NULL,
    language_code VARCHAR(10) NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (modifier_id) REFERENCES modifiers(id) ON DELETE CASCADE,
    FOREIGN KEY (language_code) REFERENCES languages(code),
    UNIQUE KEY (modifier_id, language_code)
);
```

#### Modifier Option Translations Table
```sql
CREATE TABLE modifier_option_translations (
    id VARCHAR(36) PRIMARY KEY,
    modifier_option_id VARCHAR(36) NOT NULL,
    language_code VARCHAR(10) NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (modifier_option_id) REFERENCES modifier_options(id) ON DELETE CASCADE,
    FOREIGN KEY (language_code) REFERENCES languages(code),
    UNIQUE KEY (modifier_option_id, language_code)
);
```

#### System Translations (UI text, messages)
```sql
CREATE TABLE system_translations (
    id VARCHAR(36) PRIMARY KEY,
    translation_key VARCHAR(200) NOT NULL,  -- e.g., 'button.save', 'error.not_found'
    language_code VARCHAR(10) NOT NULL,
    translation_value TEXT NOT NULL,
    category VARCHAR(50),                   -- ui, error, message, email
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE KEY (translation_key, language_code),
    INDEX idx_key_lang (translation_key, language_code)
);

-- Example data
INSERT INTO system_translations (id, translation_key, language_code, translation_value, category) VALUES
(UUID(), 'button.save', 'en', 'Save', 'ui'),
(UUID(), 'button.save', 'es', 'Guardar', 'ui'),
(UUID(), 'button.save', 'fr', 'Enregistrer', 'ui'),
(UUID(), 'button.cancel', 'en', 'Cancel', 'ui'),
(UUID(), 'button.cancel', 'es', 'Cancelar', 'ui'),
(UUID(), 'error.not_found', 'en', 'Resource not found', 'error'),
(UUID(), 'error.not_found', 'es', 'Recurso no encontrado', 'error');
```

---

### 3. API Design for Multi-Language

#### Language Detection Strategy
```http
Priority Order:
1. Query parameter: ?lang=es
2. Header: Accept-Language: es-ES,es;q=0.9,en;q=0.8
3. User preference from JWT/session
4. Default language (en)
```

#### Product API with Language Support
```http
GET /api/v1/products?lang=es
or
GET /api/v1/products
Accept-Language: es

Response:
{
  "id": "prod-123",
  "name": "Alitas de Búfalo",           // Spanish translation
  "description": "Alitas de pollo...",  // Spanish translation
  "price": 1299,
  "translations": {                     // Optional: all translations
    "en": {
      "name": "Buffalo Wings",
      "description": "Crispy chicken..."
    },
    "fr": {
      "name": "Ailes de Buffle",
      "description": "Ailes de poulet..."
    }
  }
}
```

#### Translation Management Endpoints
```http
# Get all translations for a product
GET /api/v1/products/{product_id}/translations

# Add/Update translation
POST /api/v1/products/{product_id}/translations
Body:
{
  "language_code": "es",
  "name": "Alitas de Búfalo",
  "description": "Alitas de pollo crujientes"
}

# Delete translation
DELETE /api/v1/products/{product_id}/translations/{language_code}
```

---

### 4. Translation Helper Functions (Pseudo-code)

```python
# In app/utils.py or app/i18n.py

def get_preferred_language(request) -> str:
    """Extract preferred language from request"""
    # 1. Check query parameter
    if 'lang' in request.query_params:
        return request.query_params['lang']
    
    # 2. Check header
    accept_lang = request.headers.get('Accept-Language')
    if accept_lang:
        # Parse Accept-Language header (en-US,en;q=0.9,es;q=0.8)
        languages = parse_accept_language(accept_lang)
        for lang in languages:
            if is_supported_language(lang):
                return lang
    
    # 3. Check user preference (from JWT)
    user = get_current_user(request)
    if user and user.preferred_language:
        return user.preferred_language
    
    # 4. Default
    return 'en'


def get_product_with_translation(product_id: str, language: str):
    """Fetch product with translation"""
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        return None
    
    # Try to get translation
    translation = db.query(ProductTranslation)\
        .filter(
            ProductTranslation.product_id == product_id,
            ProductTranslation.language_code == language
        ).first()
    
    if translation:
        product.name = translation.name
        product.description = translation.description
    else:
        # Fallback to default language (en)
        default_translation = db.query(ProductTranslation)\
            .filter(
                ProductTranslation.product_id == product_id,
                ProductTranslation.language_code == 'en'
            ).first()
        
        if default_translation:
            product.name = default_translation.name
            product.description = default_translation.description
    
    return product


def translate_text(key: str, language: str, **kwargs) -> str:
    """Get system translation by key"""
    translation = db.query(SystemTranslation)\
        .filter(
            SystemTranslation.translation_key == key,
            SystemTranslation.language_code == language
        ).first()
    
    if translation:
        text = translation.translation_value
    else:
        # Fallback to English
        fallback = db.query(SystemTranslation)\
            .filter(
                SystemTranslation.translation_key == key,
                SystemTranslation.language_code == 'en'
            ).first()
        
        text = fallback.translation_value if fallback else key
    
    # Support for placeholders: translate('welcome.user', name='John')
    return text.format(**kwargs) if kwargs else text
```

---

### 5. Schema Modifications (Recommended)

#### Keep Original Fields as Default Language
```sql
-- products table (existing)
-- Keep 'name' and 'description' as default language (English)
-- These serve as fallback if translation not available

-- When querying:
-- 1. Try to get translation for requested language
-- 2. If not found, use original fields
-- 3. If original fields empty, try English translation
```

#### Migration Strategy
```sql
-- Step 1: Create translation tables
CREATE TABLE product_translations (...);

-- Step 2: Migrate existing data to translation table
INSERT INTO product_translations (id, product_id, language_code, name, description)
SELECT UUID(), id, 'en', name, description
FROM products
WHERE name IS NOT NULL;

-- Step 3: Keep original fields for backward compatibility
-- Don't delete 'name' and 'description' from products table
-- They serve as fallback
```

---

## API Design Patterns

### 1. Request Headers

#### Currency Selection
```http
GET /api/v1/products
X-Currency: EUR
X-Currency-Display: symbol  # Options: symbol, code, name
```

#### Language Selection
```http
GET /api/v1/products
Accept-Language: es-ES,es;q=0.9,en;q=0.8
X-Language: es
```

#### Combined
```http
GET /api/v1/products
X-Currency: EUR
Accept-Language: es
```

---

### 2. Response Format

#### Product Response with Currency & Language
```json
{
  "id": "prod-123",
  "name": "Alitas de Búfalo",
  "description": "Alitas de pollo crujientes con salsa búfalo",
  "price": 1099,
  "price_formatted": "10,99 €",
  "currency": "EUR",
  "language": "es",
  "sku": "WINGS-001",
  "stock": 50,
  "image_url": "/uploads/products/wings.webp",
  "category": {
    "id": "cat-123",
    "name": "Aperitivos"
  },
  "meta": {
    "original_price": 1299,
    "original_currency": "USD",
    "exchange_rate": 0.85,
    "available_languages": ["en", "es", "fr", "de"],
    "available_currencies": ["USD", "EUR", "GBP"]
  }
}
```

#### Order Response with Currency
```json
{
  "id": "order-123",
  "order_number": "ORD-2025-001",
  "subtotal": 2499,
  "tax_amount": 250,
  "total_amount": 2749,
  "currency": "EUR",
  "currency_symbol": "€",
  "subtotal_formatted": "24,99 €",
  "tax_formatted": "2,50 €",
  "total_formatted": "27,49 €",
  "items": [
    {
      "product_name": "Alitas de Búfalo",
      "quantity": 2,
      "unit_price": 1099,
      "unit_price_formatted": "10,99 €",
      "total": 2198,
      "total_formatted": "21,98 €"
    }
  ]
}
```

---

### 3. Pagination with i18n

```json
{
  "success": true,
  "message": "Productos recuperados exitosamente",
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_items": 45,
    "total_pages": 5,
    "has_next": true,
    "has_prev": false
  },
  "meta": {
    "currency": "EUR",
    "language": "es"
  }
}
```

---

## Frontend Implementation

### 1. React/Next.js Example

#### Currency Selector Component
```jsx
// components/CurrencySelector.jsx
import { useState, useEffect } from 'react';

export default function CurrencySelector({ onCurrencyChange }) {
  const [currencies, setCurrencies] = useState([]);
  const [selected, setSelected] = useState('USD');

  useEffect(() => {
    // Fetch supported currencies
    fetch('/api/v1/currencies')
      .then(res => res.json())
      .then(data => setCurrencies(data));
    
    // Get from localStorage or user preference
    const saved = localStorage.getItem('preferred_currency');
    if (saved) setSelected(saved);
  }, []);

  const handleChange = (code) => {
    setSelected(code);
    localStorage.setItem('preferred_currency', code);
    onCurrencyChange(code);
  };

  return (
    <select value={selected} onChange={(e) => handleChange(e.target.value)}>
      {currencies.map(curr => (
        <option key={curr.code} value={curr.code}>
          {curr.symbol} {curr.name}
        </option>
      ))}
    </select>
  );
}
```

#### Language Selector Component
```jsx
// components/LanguageSelector.jsx
import { useRouter } from 'next/router';

export default function LanguageSelector() {
  const router = useRouter();
  const { locale, locales, pathname, asPath, query } = router;

  const changeLanguage = (newLocale) => {
    router.push({ pathname, query }, asPath, { locale: newLocale });
    localStorage.setItem('preferred_language', newLocale);
  };

  return (
    <select value={locale} onChange={(e) => changeLanguage(e.target.value)}>
      <option value="en">English</option>
      <option value="es">Español</option>
      <option value="fr">Français</option>
      <option value="de">Deutsch</option>
      <option value="ar">العربية</option>
    </select>
  );
}
```

#### API Helper with Currency & Language
```javascript
// utils/api.js
export async function fetchProducts(currency = 'USD', language = 'en') {
  const response = await fetch('/api/v1/products', {
    headers: {
      'Authorization': `Bearer ${getToken()}`,
      'X-Currency': currency,
      'Accept-Language': language
    }
  });
  
  return response.json();
}

export function formatPrice(amount, currency, locale) {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: currency
  }).format(amount / 100);
}
```

#### Price Display Component
```jsx
// components/Price.jsx
export default function Price({ amount, currency = 'USD', locale = 'en' }) {
  const formatted = new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: currency === 'JPY' ? 0 : 2
  }).format(amount / 100);

  return <span className="price">{formatted}</span>;
}

// Usage
<Price amount={1299} currency="EUR" locale="es" />
// Output: 12,99 €
```

---

### 2. Next.js i18n Configuration

```javascript
// next.config.js
module.exports = {
  i18n: {
    locales: ['en', 'es', 'fr', 'de', 'ar', 'hi'],
    defaultLocale: 'en',
    localeDetection: true
  }
};
```

```javascript
// pages/_app.js
import { IntlProvider } from 'react-intl';
import { useRouter } from 'next/router';

const messages = {
  en: require('../translations/en.json'),
  es: require('../translations/es.json'),
  fr: require('../translations/fr.json')
};

export default function MyApp({ Component, pageProps }) {
  const router = useRouter();
  const { locale } = router;

  return (
    <IntlProvider locale={locale} messages={messages[locale]}>
      <Component {...pageProps} />
    </IntlProvider>
  );
}
```

---

### 3. Translation Files

```json
// translations/en.json
{
  "nav.products": "Products",
  "nav.orders": "Orders",
  "button.add_to_cart": "Add to Cart",
  "button.checkout": "Checkout",
  "order.subtotal": "Subtotal",
  "order.tax": "Tax",
  "order.total": "Total",
  "error.not_found": "Product not found",
  "success.added": "Added to cart successfully"
}
```

```json
// translations/es.json
{
  "nav.products": "Productos",
  "nav.orders": "Pedidos",
  "button.add_to_cart": "Añadir al Carrito",
  "button.checkout": "Finalizar Compra",
  "order.subtotal": "Subtotal",
  "order.tax": "Impuesto",
  "order.total": "Total",
  "error.not_found": "Producto no encontrado",
  "success.added": "Añadido al carrito exitosamente"
}
```

---

## Migration Strategy

### Phase 1: Foundation (Week 1-2)

**Backend Tasks:**
1. ✅ Create currency tables (currencies, exchange_rates)
2. ✅ Create language tables (languages)
3. ✅ Add user preferences (preferred_currency, preferred_language)
4. ✅ Implement exchange rate API integration
5. ✅ Create currency helper functions
6. ✅ Add currency endpoints (/api/v1/currencies, /api/v1/exchange-rates)

**No Breaking Changes:**
- Existing API continues to work with USD
- New endpoints are additive

---

### Phase 2: Translation Tables (Week 3-4)

**Backend Tasks:**
1. ✅ Create translation tables (product_translations, category_translations, etc.)
2. ✅ Migrate existing data to translation tables (English as default)
3. ✅ Implement language detection logic
4. ✅ Add translation endpoints
5. ✅ Update existing endpoints to support Accept-Language header

**Backward Compatible:**
- If no language specified, returns default (English)
- Original fields remain as fallback

---

### Phase 3: API Enhancement (Week 5-6)

**Backend Tasks:**
1. ✅ Add currency conversion to product endpoints
2. ✅ Add currency conversion to order endpoints
3. ✅ Add language support to all text fields
4. ✅ Implement caching for exchange rates (Redis)
5. ✅ Add currency/language to response metadata

**Testing:**
- Test all endpoints with different currencies
- Test all endpoints with different languages
- Performance testing with conversion overhead

---

### Phase 4: Frontend Integration (Week 7-8)

**Frontend Tasks:**
1. ✅ Add currency selector component
2. ✅ Add language selector component
3. ✅ Update API calls to include currency/language headers
4. ✅ Implement price formatting with Intl API
5. ✅ Add translation files for UI text
6. ✅ Test RTL languages (Arabic, Hebrew)

---

### Phase 5: Admin Tools (Week 9-10)

**Admin Panel:**
1. ✅ Currency management UI
2. ✅ Exchange rate management UI
3. ✅ Translation management UI
4. ✅ Bulk translation import/export
5. ✅ Language activation/deactivation

---

## Testing Considerations

### 1. Currency Testing Scenarios

```bash
# Test 1: Default currency (USD)
curl -X GET "http://localhost:8000/api/v1/products/prod-123"
# Expected: price in USD cents

# Test 2: EUR conversion
curl -X GET "http://localhost:8000/api/v1/products/prod-123" \
  -H "X-Currency: EUR"
# Expected: price converted to EUR

# Test 3: JPY (no decimals)
curl -X GET "http://localhost:8000/api/v1/products/prod-123" \
  -H "X-Currency: JPY"
# Expected: price as whole number (no cents)

# Test 4: Order with currency conversion
curl -X POST "http://localhost:8000/api/v1/orders" \
  -H "X-Currency: GBP" \
  -H "Content-Type: application/json" \
  -d '{"items": [{"product_id": "prod-123", "quantity": 2}]}'
# Expected: order totals in GBP
```

---

### 2. Language Testing Scenarios

```bash
# Test 1: Default language (English)
curl -X GET "http://localhost:8000/api/v1/products/prod-123"
# Expected: name and description in English

# Test 2: Spanish translation
curl -X GET "http://localhost:8000/api/v1/products/prod-123" \
  -H "Accept-Language: es"
# Expected: name and description in Spanish

# Test 3: Fallback to default
curl -X GET "http://localhost:8000/api/v1/products/prod-123" \
  -H "Accept-Language: de"
# Expected: If German translation not available, return English

# Test 4: Multiple preferences
curl -X GET "http://localhost:8000/api/v1/products/prod-123" \
  -H "Accept-Language: de,fr;q=0.9,en;q=0.8"
# Expected: Try German, then French, then English
```

---

### 3. Edge Cases

#### Currency Edge Cases
- ✅ Exchange rate not available → fallback to base currency
- ✅ Invalid currency code → return 400 error
- ✅ Stale exchange rate → use last available rate + warning
- ✅ Extreme values → test with very large/small amounts
- ✅ Rounding errors → ensure consistency across calculations

#### Language Edge Cases
- ✅ Translation missing → fallback to default language
- ✅ Invalid language code → return default language
- ✅ Special characters → test Unicode, emojis, RTL text
- ✅ Very long translations → ensure UI doesn't break
- ✅ HTML in translations → sanitize to prevent XSS

---

### 4. Performance Testing

```python
# Load test with currency conversion
import locust

class CurrencyLoadTest(locust.HttpUser):
    @locust.task
    def get_products_eur(self):
        self.client.get("/api/v1/products", headers={"X-Currency": "EUR"})
    
    @locust.task
    def get_products_jpy(self):
        self.client.get("/api/v1/products", headers={"X-Currency": "JPY"})

# Run: locust -f load_test.py --host=http://localhost:8000
```

**Performance Targets:**
- Exchange rate lookup: < 10ms (with caching)
- Currency conversion: < 5ms per item
- Translation lookup: < 10ms (with caching)
- Overall API response: < 200ms (same as without i18n)

---

## Best Practices & Recommendations

### 1. Currency Management

✅ **DO:**
- Store prices in base currency (USD cents)
- Use Decimal type for financial calculations
- Cache exchange rates (Redis, 1-hour TTL)
- Update rates regularly (hourly or daily)
- Log all currency conversions for audit
- Round according to currency conventions
- Display currency symbol with amount

❌ **DON'T:**
- Use float for money (precision errors)
- Store converted prices in database
- Hard-code exchange rates
- Allow negative prices
- Forget to handle zero-decimal currencies (JPY)
- Mix currencies in same calculation

---

### 2. Language Management

✅ **DO:**
- Use ISO 639-1 codes (en, es, fr)
- Provide fallback to default language
- Keep original text as fallback
- Support RTL languages (ar, he)
- Sanitize user-provided translations
- Use professional translation services
- Test with native speakers

❌ **DON'T:**
- Use machine translation in production without review
- Delete default language translations
- Hard-code text in code
- Assume English is universal
- Ignore plural forms (1 item vs 2 items)
- Forget about date/time formatting

---

### 3. API Design

✅ **DO:**
- Accept currency/language in headers
- Provide currency/language in response
- Document all i18n endpoints
- Version API properly
- Return formatted prices for display
- Include metadata (exchange rate, available languages)
- Support both query params and headers

❌ **DON'T:**
- Break existing API when adding i18n
- Return different structures based on language
- Assume client has all translations
- Ignore Accept-Language header
- Force specific currency/language

---

### 4. Frontend Integration

✅ **DO:**
- Use browser's Intl API for formatting
- Store user preference in localStorage
- Detect browser language on first visit
- Provide clear currency/language switcher
- Format dates/times according to locale
- Test on real devices (mobile, tablet)
- Support keyboard navigation

❌ **DON'T:**
- Format prices on server only
- Ignore user's browser settings
- Hide language/currency selector
- Assume USD/$
- Hard-code decimal separators (. vs ,)
- Forget about number formatting (1,000 vs 1.000)

---

## Tools & Libraries

### Backend (Python)

```python
# requirements.txt additions
babel==2.13.1           # i18n and formatting
python-i18n==0.3.9      # Translation management
forex-python==1.8       # Exchange rates
redis==5.0.1            # Caching
celery==5.3.4           # Background tasks

# Usage examples
from babel.numbers import format_currency, format_decimal
from babel.dates import format_datetime

# Format price
format_currency(12.99, 'EUR', locale='es_ES')  # '12,99 €'
format_currency(1299, 'JPY', locale='ja_JP')   # '¥1,299'

# Format date
format_datetime(datetime.now(), locale='es_ES')  # '25 nov 2025 10:30:00'
```

---

### Frontend (React/Next.js)

```json
// package.json additions
{
  "dependencies": {
    "react-intl": "^6.5.0",
    "next-i18next": "^15.0.0",
    "i18next": "^23.7.0",
    "react-i18next": "^13.5.0"
  }
}
```

```javascript
// Using react-intl
import { FormattedMessage, FormattedNumber } from 'react-intl';

<FormattedMessage id="button.add_to_cart" defaultMessage="Add to Cart" />

<FormattedNumber
  value={12.99}
  style="currency"
  currency="EUR"
/>
// Output: €12.99
```

---

## Security Considerations

### 1. Exchange Rate Security

⚠️ **Risks:**
- Rate manipulation attacks
- Stale rate exploitation
- Rounding attack (many small transactions)

🔒 **Mitigations:**
- Validate rates against multiple sources
- Set min/max rate change thresholds
- Log all rate updates with source
- Alert on suspicious rate changes
- Use signed API responses from rate providers

---

### 2. Translation Security

⚠️ **Risks:**
- XSS via user-provided translations
- SQL injection in translation keys
- HTML injection in product descriptions

🔒 **Mitigations:**
- Sanitize all translation inputs
- Use parameterized queries
- Escape HTML in translations
- Validate translation keys (alphanumeric + dots only)
- Require admin approval for new translations

---

### 3. Audit & Compliance

📝 **Logging Requirements:**
- Log all currency conversions with rate used
- Log translation updates (who, when, what)
- Log user language/currency changes
- Track exchange rate source and timestamp

📊 **Reporting:**
- Daily currency usage report
- Translation coverage report (% translated)
- Exchange rate variance alerts
- Revenue by currency report

---

## Summary & Next Steps

### Recommended Implementation Order

1. **Week 1-2:** Currency foundation
   - Create currency tables
   - Integrate exchange rate API
   - Add conversion functions
   - Cache with Redis

2. **Week 3-4:** Language foundation
   - Create translation tables
   - Migrate existing data
   - Add language detection
   - Implement fallback logic

3. **Week 5-6:** API updates
   - Add currency parameter to all endpoints
   - Add language support to all endpoints
   - Update response format
   - Add metadata

4. **Week 7-8:** Frontend integration
   - Add currency/language selectors
   - Update API calls
   - Implement formatting
   - Test on real devices

5. **Week 9-10:** Admin tools & Polish
   - Build admin UI for translations
   - Build admin UI for exchange rates
   - Performance optimization
   - Documentation

### Effort Estimate

- **Backend Development:** 40-50 hours
- **Database Design & Migration:** 15-20 hours
- **Frontend Integration:** 30-40 hours
- **Admin Tools:** 20-25 hours
- **Testing:** 20-25 hours
- **Documentation:** 10-15 hours

**Total:** 135-175 hours (4-5 weeks with 1 developer)

---

### Key Decisions Needed

1. **Which currencies to support initially?**
   - Recommendation: USD, EUR, GBP, INR (cover major markets)

2. **Which languages to support initially?**
   - Recommendation: English, Spanish, French (cover 1B+ people)

3. **Exchange rate provider?**
   - Recommendation: Open Exchange Rates (free tier sufficient)

4. **Update frequency for rates?**
   - Recommendation: Hourly for production, daily for development

5. **Translation strategy?**
   - Recommendation: Professional for initial batch, then crowdsourcing

---

## Conclusion

This guide provides a complete blueprint for implementing multi-currency and multi-language support in your Restaurant POS system **without changing existing code**. The strategy focuses on:

✅ **Backward Compatibility** - existing API continues working  
✅ **Gradual Migration** - implement in phases  
✅ **Performance** - caching and optimization built-in  
✅ **Scalability** - easy to add new currencies/languages  
✅ **Best Practices** - industry-standard patterns  

Follow the phased approach, start with currency support (simpler), then add language support. Test thoroughly at each phase before moving to the next.

---

**Document Status:** Guidelines Only (No Code Changes)  
**Last Updated:** November 25, 2025  
**Version:** 1.0  
**Contact:** For implementation assistance or questions about specific sections
