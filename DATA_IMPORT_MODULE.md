# Data Import Module Documentation

## Overview

The Data Import Module provides comprehensive functionality for importing categories and products from CSV or Excel files. It includes duplicate detection, validation, error tracking, and sample file generation - all scoped to specific restaurants to prevent cross-restaurant data contamination.

## Key Features

### ✅ Multi-Format Support
- **CSV**: Comma-separated values
- **Excel**: .xlsx and .xls formats
- Automatic format detection

### ✅ Restaurant-Scoped Operations
- All imports are tied to a specific restaurant
- Duplicate checks are **only within the selected restaurant**
- Data from other restaurants is completely ignored
- Super admin can import for any restaurant
- Restaurant users can only import for their restaurant

### ✅ Duplicate Prevention
- Checks existing records **only in the target restaurant**
- Categories checked by: `name` (case-insensitive)
- Products checked by: `name` (case-insensitive)
- Optional SKU uniqueness check for products
- Two handling modes:
  - **Skip duplicates**: Ignore records that already exist
  - **Update existing**: Update existing records with new data

### ✅ Comprehensive Validation
- Pre-import validation of all rows
- Required field checks
- Data type validation
- Foreign key validation (e.g., category must exist for products)
- Length constraints
- Range validation (tax rates, stock levels)
- Duplicate detection within file

### ✅ Import Tracking
- Detailed import records with statistics
- Row-level logging
- Success/failure tracking
- Processing time metrics
- Error messages and details

### ✅ Sample File Generation
- Generate sample Excel or CSV files
- Pre-populated with example data
- Correct column structure
- Downloadable via API

## Database Tables

### 1. data_imports
Main import tracking table:

```sql
- id (UUID): Primary key
- restaurant_id (FK): Target restaurant
- import_number: Unique import identifier (IMP-YYYYMMDDHHMMSS-XXXXXXXX)
- import_name: User-defined import name
- import_type: category | product | category_product
- file_name, file_path, file_size, file_format
- status: pending | processing | completed | failed | partial
- processing_started_at, processing_completed_at, processing_time
- total_rows, rows_processed, rows_imported, rows_updated, rows_skipped, rows_failed
- duplicates_found, duplicates_skipped, duplicates_updated
- validation_errors_count, validation_warnings_count
- update_existing, skip_duplicates, validate_only (boolean flags)
- imported_by: User who initiated import
- created_at, updated_at, deleted_at
```

**Key Fields** (40+ total)

### 2. import_logs
Row-level import logs:

```sql
- id (UUID): Primary key
- data_import_id (FK): Parent import
- row_number: Row number in file (1-indexed, excluding header)
- row_data (JSON): Original row data
- status: success | failed | skipped | updated
- action_taken: created | updated | skipped
- entity_id: ID of created/updated record
- entity_type: category | product
- error_message, error_type
- is_duplicate, duplicate_field, duplicate_value, existing_entity_id
- validation_errors, validation_warnings (JSON)
- processed_at, processing_time_ms
```

**Key Fields** (20+ total)

### 3. import_templates
Predefined import templates:

```sql
- id (UUID): Primary key
- template_name, template_description
- import_type: category | product
- file_format: csv | excel
- required_columns, optional_columns (JSON)
- column_mapping (JSON)
- sample_data (JSON)
- validation_rules (JSON)
- is_active, is_system_template
- usage_count, last_used_at
- created_by, created_at, updated_at
```

**Key Fields** (20+ total)

## API Endpoints

### Base URL
All endpoints are prefixed with: `/api/v1/data-import`

### 1. Upload File for Import

```http
POST /api/v1/data-import/upload
Content-Type: multipart/form-data
Authorization: Bearer <token>

Form Data:
- file: <CSV or Excel file>
- import_name: "January 2025 Products"
- import_type: "category" | "product"
- restaurant_id: "restaurant-uuid"
- update_existing: false (default: false)
- skip_duplicates: true (default: true)
- validate_only: false (default: false)
- notes: "Optional notes"
```

**Response:**
```json
{
  "success": true,
  "message": "Import completed: 45 created, 3 updated, 2 skipped",
  "data": {
    "import": {
      "id": "uuid",
      "import_number": "IMP-20251231120000-abc123",
      "import_name": "January 2025 Products",
      "import_type": "product",
      "restaurant_id": "restaurant-uuid",
      "status": "completed",
      "total_rows": 50,
      "rows_imported": 45,
      "rows_updated": 3,
      "rows_skipped": 2,
      "rows_failed": 0,
      "duplicates_found": 5,
      "duplicates_skipped": 2,
      "duplicates_updated": 3,
      "processing_time": 5,
      "created_at": "2025-12-31T12:00:00Z"
    },
    "validation": {
      "is_valid": true,
      "total_rows": 50,
      "valid_rows": 50,
      "invalid_rows": 0,
      "errors": [],
      "warnings": [],
      "duplicates": [
        {
          "row": 3,
          "field": "name",
          "value": "Cappuccino",
          "message": "Product 'Cappuccino' already exists in restaurant"
        }
      ]
    }
  }
}
```

**Permissions:**
- **Super Admin**: Can import for any restaurant
- **Restaurant User**: Can only import for their restaurant

**Validation:**
- File format must be CSV, XLS, or XLSX
- File is validated before import
- If validation fails, import is not executed
- If `validate_only=true`, only validation is performed

### 2. Get Import Details

```http
GET /api/v1/data-import/imports/{import_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "message": "Import retrieved successfully",
  "data": {
    "id": "uuid",
    "import_number": "IMP-20251231120000-abc123",
    "import_name": "January 2025 Products",
    "status": "completed",
    "total_rows": 50,
    "rows_imported": 45,
    // ... full import details
  }
}
```

### 3. List Imports

```http
GET /api/v1/data-import/imports
Authorization: Bearer <token>

Query Parameters:
- restaurant_id: string (optional, super admin only)
- import_type: "category" | "product" (optional)
- status: "pending" | "processing" | "completed" | "failed" (optional)
- page: integer (default: 1)
- page_size: integer (default: 20, max: 100)
```

**Response:**
```json
{
  "success": true,
  "message": "Imports retrieved successfully",
  "data": {
    "total": 25,
    "page": 1,
    "page_size": 20,
    "data": [
      { /* import objects */ }
    ]
  }
}
```

### 4. Generate Sample File

```http
POST /api/v1/data-import/generate-sample
Authorization: Bearer <token>
Content-Type: application/json

Body:
{
  "import_type": "category" | "product",
  "file_format": "excel" | "csv",
  "include_sample_data": true,
  "row_count": 10
}
```

**Response:**
- Downloads Excel or CSV file
- Pre-populated with sample data
- Correct column structure

**File Names:**
- `sample_category_import.xlsx`
- `sample_product_import.csv`

### 5. Get Template Information

#### Category Template
```http
GET /api/v1/data-import/templates/category
Authorization: Bearer <token>
```

Returns structure and requirements for category import.

#### Product Template
```http
GET /api/v1/data-import/templates/product
Authorization: Bearer <token>
```

Returns structure and requirements for product import.

### 6. Delete Import

```http
DELETE /api/v1/data-import/imports/{import_id}
Authorization: Bearer <token>
```

Soft deletes import record.

## Import Formats

### Category Import Format

**Required Columns:**
- `name` (string, max 100 chars): Category name - **unique per restaurant**

**Optional Columns:**
- `description` (string): Category description
- `parent_category` (string): Parent category name (for sub-categories)
- `display_order` (integer): Display order
- `is_active` (boolean): Active status (default: true)
- `image_url` (string): Category image URL
- `tax_rate` (float, 0-100): Tax rate percentage
- `cgst_rate` (float, 0-100): CGST rate percentage
- `sgst_rate` (float, 0-100): SGST rate percentage
- `preparation_time` (integer): Preparation time in minutes
- `is_vegetarian` (boolean): Vegetarian category
- `is_non_vegetarian` (boolean): Non-vegetarian category
- `is_vegan` (boolean): Vegan category

**Sample CSV:**
```csv
name,description,display_order,is_active,tax_rate,cgst_rate,sgst_rate,is_vegetarian
Beverages,Hot and cold beverages,1,true,18.0,9.0,9.0,true
Appetizers,Starters and appetizers,2,true,18.0,9.0,9.0,false
Main Course,Main course dishes,3,true,18.0,9.0,9.0,false
```

**Sample Excel:**
| name | description | display_order | is_active | tax_rate | cgst_rate | sgst_rate | is_vegetarian |
|------|-------------|---------------|-----------|----------|-----------|-----------|---------------|
| Beverages | Hot and cold beverages | 1 | TRUE | 18.0 | 9.0 | 9.0 | TRUE |
| Appetizers | Starters and appetizers | 2 | TRUE | 18.0 | 9.0 | 9.0 | FALSE |

### Product Import Format

**Required Columns:**
- `name` (string, max 200 chars): Product name - **unique per restaurant**
- `category_name` (string): Category name - **must exist in restaurant**
- `price` (integer): Price in paise/cents (e.g., 1000 = ₹10.00 or $10.00)

**Optional Columns:**
- `description` (string): Product description
- `sku` (string, max 100 chars): Stock keeping unit - **unique if provided**
- `barcode` (string, max 100 chars): Product barcode
- `cost_price` (integer): Cost price in paise
- `track_inventory` (boolean): Track inventory (default: true)
- `current_stock` (integer): Current stock quantity
- `minimum_stock` (integer): Minimum stock level
- `maximum_stock` (integer): Maximum stock level
- `reorder_level` (integer): Reorder level
- `tax_rate` (float, 0-100): Tax rate percentage
- `cgst_rate` (float, 0-100): CGST rate
- `sgst_rate` (float, 0-100): SGST rate
- `is_tax_inclusive` (boolean): Price includes tax
- `is_active` (boolean): Active status (default: true)
- `is_available` (boolean): Available status (default: true)
- `preparation_time` (integer): Preparation time in minutes
- `calories` (integer): Calorie count
- `spice_level` (string): Spice level (mild, medium, hot)
- `is_vegetarian` (boolean): Vegetarian product
- `is_non_vegetarian` (boolean): Non-vegetarian product
- `is_vegan` (boolean): Vegan product
- `is_bestseller` (boolean): Bestseller tag
- `is_featured` (boolean): Featured product
- `display_order` (integer): Display order
- `image_url` (string): Product image URL

**Sample CSV:**
```csv
name,category_name,description,sku,price,cost_price,current_stock,is_active,tax_rate,is_vegetarian
Cappuccino,Beverages,Hot cappuccino with foam,BEV001,15000,9000,100,true,18.0,true
Espresso,Beverages,Strong espresso shot,BEV002,10000,6000,100,true,18.0,true
Caesar Salad,Appetizers,Fresh caesar salad,APP001,25000,15000,50,true,18.0,true
```

**Important Notes:**
1. **Price in Paise**: All prices are in the smallest currency unit (paise for INR, cents for USD)
   - ₹150.00 = 15000 paise
   - $15.00 = 1500 cents
2. **Category Must Exist**: Categories must be created before importing products
3. **Restaurant Scoping**: Products are only checked against the target restaurant

## Duplicate Detection Logic

### Category Duplicates
```python
# Check within restaurant only
duplicate_check = (
    category.name.lower() == import_row.name.lower()
    AND category.restaurant_id == target_restaurant_id
    AND category.deleted_at IS NULL
)
```

**Behavior:**
- If duplicate found and `skip_duplicates=True`: Skip row
- If duplicate found and `update_existing=True`: Update existing category
- If duplicate in different restaurant: Ignored, creates new record

### Product Duplicates
```python
# Check within restaurant only
duplicate_check = (
    product.name.lower() == import_row.name.lower()
    AND product.restaurant_id == target_restaurant_id
    AND product.deleted_at IS NULL
)

# Optional SKU check
sku_check = (
    product.sku.lower() == import_row.sku.lower()
    AND product.restaurant_id == target_restaurant_id
    AND product.deleted_at IS NULL
)
```

**Behavior:**
- If duplicate found and `skip_duplicates=True`: Skip row
- If duplicate found and `update_existing=True`: Update existing product
- If duplicate in different restaurant: Ignored, creates new record
- SKU duplicates generate warnings

## Validation Rules

### Category Validation
- ✅ `name`: Required, max 100 characters, unique per restaurant
- ✅ `tax_rate`: 0-100 range
- ✅ `cgst_rate`: 0-100 range
- ✅ `sgst_rate`: 0-100 range
- ✅ `display_order`: Integer
- ✅ Duplicate check in file (warns if duplicate names)
- ✅ Duplicate check in database (per restaurant)

### Product Validation
- ✅ `name`: Required, max 200 characters, unique per restaurant
- ✅ `category_name`: Required, must exist in target restaurant
- ✅ `price`: Required, positive integer
- ✅ `cost_price`: Positive integer if provided
- ✅ `sku`: Max 100 characters, unique per restaurant if provided
- ✅ `current_stock`: Non-negative integer
- ✅ `minimum_stock`: Non-negative integer
- ✅ `maximum_stock`: Non-negative integer
- ✅ `tax_rate`: 0-100 range
- ✅ Duplicate check in database (per restaurant)
- ✅ Category existence check (in same restaurant)

## Import Modes

### Mode 1: Skip Duplicates (Default)
```json
{
  "update_existing": false,
  "skip_duplicates": true
}
```
- Creates new records only
- Skips existing records
- Logs skipped rows
- Safe for adding new items

### Mode 2: Update Existing
```json
{
  "update_existing": true,
  "skip_duplicates": false
}
```
- Creates new records
- Updates existing records
- Overwrites data
- Use for bulk updates

### Mode 3: Validate Only
```json
{
  "validate_only": true
}
```
- Only validates file
- No records created/updated
- Returns validation results
- Use before actual import

## Error Handling

### Validation Errors
```json
{
  "errors": [
    "Row 3: Category name is required",
    "Row 5: Price must be positive",
    "Row 8: Category 'Beverages' does not exist in restaurant"
  ]
}
```

### Validation Warnings
```json
{
  "warnings": [
    "Row 4: Duplicate category name in file: Appetizers",
    "Row 10: SKU 'BEV001' already exists"
  ]
}
```

### Duplicate Detection
```json
{
  "duplicates": [
    {
      "row": 6,
      "field": "name",
      "value": "Cappuccino",
      "message": "Product 'Cappuccino' already exists in restaurant"
    }
  ]
}
```

## Usage Examples

### Example 1: Import Categories (Skip Duplicates)

1. **Generate Sample File:**
```http
POST /api/v1/data-import/generate-sample
{
  "import_type": "category",
  "file_format": "excel",
  "row_count": 5
}
```

2. **Edit the downloaded file** with your categories

3. **Upload File:**
```http
POST /api/v1/data-import/upload
Form Data:
- file: categories.xlsx
- import_name: "My Categories"
- import_type: "category"
- restaurant_id: "my-restaurant-uuid"
- skip_duplicates: true
```

4. **Result:**
```json
{
  "success": true,
  "message": "Import completed: 5 created, 0 updated, 0 skipped",
  "data": {
    "import": {
      "rows_imported": 5,
      "rows_skipped": 0
    }
  }
}
```

### Example 2: Import Products (Update Existing)

1. **Ensure categories exist** (import categories first if needed)

2. **Generate Sample File:**
```http
POST /api/v1/data-import/generate-sample
{
  "import_type": "product",
  "file_format": "csv",
  "row_count": 10
}
```

3. **Edit CSV** with your products (ensure category_name matches existing categories)

4. **Upload File:**
```http
POST /api/v1/data-import/upload
Form Data:
- file: products.csv
- import_name: "Updated Menu"
- import_type: "product"
- restaurant_id: "my-restaurant-uuid"
- update_existing: true
```

5. **Result:**
```json
{
  "success": true,
  "message": "Import completed: 8 created, 2 updated, 0 skipped",
  "data": {
    "import": {
      "rows_imported": 8,
      "rows_updated": 2
    }
  }
}
```

### Example 3: Validate Before Import

```http
POST /api/v1/data-import/upload
Form Data:
- file: products.xlsx
- import_name: "Test Import"
- import_type: "product"
- restaurant_id: "my-restaurant-uuid"
- validate_only: true
```

**Result:** Validation report without importing data

## Best Practices

### 1. Import Order
1. **Import categories first**
2. **Then import products** (requires categories to exist)

### 2. Data Preparation
- Ensure category names match exactly (case-insensitive)
- Use consistent naming
- Price in paise (multiply by 100)
- Remove duplicate rows in file

### 3. Testing
- Use `validate_only=true` first
- Test with small files
- Review validation errors
- Check duplicate warnings

### 4. Large Imports
- Split large files into batches
- Import categories separately
- Import products in groups by category
- Monitor processing time

### 5. Error Recovery
- Review import logs
- Export failed rows
- Fix errors
- Re-import failed rows

## Troubleshooting

### Issue: "Category does not exist"
**Solution:** Import categories before products, or ensure category names match exactly

### Issue: "Duplicate found"
**Solution:**
- Use `skip_duplicates=true` to skip
- Use `update_existing=true` to update
- Or rename the item in your file

### Issue: "Validation failed"
**Solution:** Check validation errors in response, fix file, re-upload

### Issue: "Price must be positive"
**Solution:** Price must be in paise (multiply by 100)

### Issue: "Wrong restaurant data"
**Solution:** Data is scoped to selected restaurant - verify `restaurant_id`

## Dependencies

Required Python packages:
```
pandas==2.1.4
openpyxl==3.1.2
xlrd==2.0.1
```

Install with:
```bash
pip install pandas openpyxl xlrd
```

## Migration

Migration: `bf2c2e13f3c9`

```bash
# Apply migration
alembic upgrade head

# Verify
alembic current
# Output: bf2c2e13f3c9 (head)
```

## File Structure

```
app/modules/data_import/
├── __init__.py          # Module initialization
├── model.py            # 3 SQLAlchemy models (DataImport, ImportLog, ImportTemplate)
├── schema.py           # Pydantic schemas
├── service.py          # Import logic and validation
└── route.py            # API endpoints

uploads/imports/         # Uploaded files stored here
```

## API Documentation

Access full API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- Look for "Data Import" section

## Security

- ✅ Authentication required for all endpoints
- ✅ Role-based access control
- ✅ Restaurant-scoped data isolation
- ✅ File type validation
- ✅ Input sanitization
- ✅ Soft delete support

---

**Module Version**: 1.0.0  
**Migration**: bf2c2e13f3c9  
**Commit**: 389996e  
**Date**: December 2025
