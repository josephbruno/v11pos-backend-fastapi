from fastapi import APIRouter, Depends, HTTPException, Query, Path, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
import os
import shutil
from pathlib import Path as FilePath

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.response import create_response
from app.modules.data_import.schema import (
    DataImportCreate, DataImportUpdate, DataImportResponse,
    DataImportListResponse, ImportLogListResponse, ValidationResult,
    GenerateSampleRequest, ImportTypeEnum, ImportFileFormatEnum,
    FileUploadRequest
)
from app.modules.data_import.service import DataImportService
from app.modules.data_import.model import DataImport, ImportLog

router = APIRouter(prefix="/api/v1/data-import", tags=["Data Import"])

# Upload directory
UPLOAD_DIR = FilePath("uploads/imports")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload", response_model=dict)
async def upload_file_for_import(
    file: UploadFile = File(..., description="CSV or Excel file to import"),
    import_name: str = Form(..., description="Import name"),
    import_type: ImportTypeEnum = Form(..., description="Import type (category, product, etc.)"),
    restaurant_id: str = Form(..., description="Restaurant ID"),
    update_existing: bool = Form(False, description="Update existing records"),
    skip_duplicates: bool = Form(True, description="Skip duplicate records"),
    validate_only: bool = Form(False, description="Only validate, don't import"),
    notes: Optional[str] = Form(None, description="Additional notes"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload CSV or Excel file for import
    
    Supported formats: CSV, XLS, XLSX
    
    **Permissions:**
    - Super Admin: Can import for any restaurant
    - Restaurant User: Can only import for their restaurant
    """
    
    # Check permissions
    user_role = current_user.get("role")
    user_restaurant_id = current_user.get("restaurant_id")
    
    if user_role != "super_admin":
        if restaurant_id != user_restaurant_id:
            raise HTTPException(status_code=403, detail="Access denied to this restaurant")
    
    # Validate file format
    file_extension = file.filename.split(".")[-1].lower()
    if file_extension not in ["csv", "xls", "xlsx"]:
        raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")
    
    # Determine file format
    if file_extension == "csv":
        file_format = "csv"
    else:
        file_format = "excel"
    
    # Save file
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = UPLOAD_DIR / safe_filename
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = os.path.getsize(file_path)
        
        # Create import record
        import_data = DataImportCreate(
            import_name=import_name,
            import_type=import_type,
            restaurant_id=restaurant_id,
            update_existing=update_existing,
            skip_duplicates=skip_duplicates,
            validate_only=validate_only,
            notes=notes
        )
        
        data_import = await DataImportService.create_import(
            db=db,
            import_data=import_data,
            file_name=file.filename,
            file_path=str(file_path),
            file_size=file_size,
            file_format=file_format,
            imported_by=current_user.get("id")
        )
        
        # Read and validate file
        df = DataImportService.read_file(str(file_path), file_format)
        data_import.total_rows = len(df)
        
        # Validate based on import type
        if import_type == ImportTypeEnum.CATEGORY:
            validation_result = await DataImportService.validate_category_import(
                db=db,
                df=df,
                restaurant_id=restaurant_id
            )
        elif import_type == ImportTypeEnum.PRODUCT:
            validation_result = await DataImportService.validate_product_import(
                db=db,
                df=df,
                restaurant_id=restaurant_id
            )
        else:
            raise HTTPException(status_code=400, detail=f"Import type '{import_type}' not yet supported")
        
        # Update import with validation results
        data_import.validation_errors_count = len(validation_result.errors)
        data_import.validation_warnings_count = len(validation_result.warnings)
        data_import.duplicates_found = len(validation_result.duplicates)
        data_import.validation_errors = {"errors": validation_result.errors}
        data_import.validation_warnings = {"warnings": validation_result.warnings}
        
        if not validation_result.is_valid:
            data_import.status = "failed"
            data_import.error_message = "Validation failed"
            await db.commit()
            await db.refresh(data_import)
            
            return create_response(
                success=False,
                message="Validation failed",
                data={
                    "import": DataImportResponse.model_validate(data_import),
                    "validation": validation_result
                }
            )
        
        # If validate_only, don't proceed with import
        if validate_only:
            data_import.status = "completed"
            await db.commit()
            await db.refresh(data_import)
            
            return create_response(
                success=True,
                message="Validation successful",
                data={
                    "import": DataImportResponse.model_validate(data_import),
                    "validation": validation_result
                }
            )
        
        # Proceed with import
        data_import.status = "processing"
        data_import.processing_started_at = datetime.utcnow()
        await db.commit()
        
        # Import based on type
        if import_type == ImportTypeEnum.CATEGORY:
            result = await DataImportService.import_categories(
                db=db,
                df=df,
                restaurant_id=restaurant_id,
                import_id=data_import.id,
                update_existing=update_existing,
                skip_duplicates=skip_duplicates
            )
        elif import_type == ImportTypeEnum.PRODUCT:
            result = await DataImportService.import_products(
                db=db,
                df=df,
                restaurant_id=restaurant_id,
                import_id=data_import.id,
                update_existing=update_existing,
                skip_duplicates=skip_duplicates
            )
        
        # Update import with results
        data_import.status = "completed"
        data_import.processing_completed_at = datetime.utcnow()
        data_import.processing_time = result["processing_time"]
        data_import.rows_processed = result["stats"]["total_rows"]
        data_import.rows_imported = result["stats"]["imported"]
        data_import.rows_updated = result["stats"]["updated"]
        data_import.rows_skipped = result["stats"]["skipped"]
        data_import.rows_failed = result["stats"]["failed"]
        data_import.duplicates_skipped = result["stats"]["skipped"]
        data_import.duplicates_updated = result["stats"]["updated"]
        data_import.import_summary = result["stats"]
        
        await db.commit()
        await db.refresh(data_import)
        
        return create_response(
            success=True,
            message=f"Import completed: {result['stats']['imported']} created, {result['stats']['updated']} updated, {result['stats']['skipped']} skipped",
            data={
                "import": DataImportResponse.model_validate(data_import),
                "validation": validation_result
            }
        )
        
    except Exception as e:
        # Clean up file if import fails
        if file_path.exists():
            file_path.unlink()
        
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.get("/imports/{import_id}", response_model=dict)
async def get_import(
    import_id: str = Path(..., description="Import ID"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get import details by ID"""
    
    data_import = await DataImportService.get_import_by_id(db, import_id)
    
    if not data_import:
        raise HTTPException(status_code=404, detail="Import not found")
    
    # Check permissions
    user_role = current_user.get("role")
    user_restaurant_id = current_user.get("restaurant_id")
    
    if user_role != "super_admin":
        if data_import.restaurant_id != user_restaurant_id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    return create_response(
        success=True,
        message="Import retrieved successfully",
        data=DataImportResponse.model_validate(data_import)
    )


@router.get("/imports", response_model=dict)
async def list_imports(
    restaurant_id: Optional[str] = Query(None, description="Filter by restaurant ID"),
    import_type: Optional[str] = Query(None, description="Filter by import type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List imports with pagination
    
    **Permissions:**
    - Super Admin: Can view all imports
    - Restaurant User: Can only view their restaurant's imports
    """
    
    # Check permissions
    user_role = current_user.get("role")
    user_restaurant_id = current_user.get("restaurant_id")
    
    if user_role != "super_admin":
        restaurant_id = user_restaurant_id
    
    imports, total = await DataImportService.list_imports(
        db=db,
        restaurant_id=restaurant_id,
        import_type=import_type,
        status=status,
        page=page,
        page_size=page_size
    )
    
    return create_response(
        success=True,
        message="Imports retrieved successfully",
        data=DataImportListResponse(
            total=total,
            page=page,
            page_size=page_size,
            data=[DataImportResponse.model_validate(imp) for imp in imports]
        )
    )


@router.post("/generate-sample", response_model=None)
async def generate_sample_file(
    request: GenerateSampleRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate sample Excel or CSV file for import
    
    Returns a downloadable file with sample data and correct format.
    
    **Import Types:**
    - category: Category import template
    - product: Product import template
    """
    
    try:
        if request.file_format in [ImportFileFormatEnum.EXCEL, ImportFileFormatEnum.XLSX]:
            file_content = DataImportService.generate_sample_excel(
                import_type=request.import_type.value,
                row_count=request.row_count
            )
            filename = f"sample_{request.import_type.value}_import.xlsx"
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:  # CSV
            file_content = DataImportService.generate_sample_csv(
                import_type=request.import_type.value,
                row_count=request.row_count
            )
            filename = f"sample_{request.import_type.value}_import.csv"
            media_type = "text/csv"
        
        return StreamingResponse(
            file_content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate sample file: {str(e)}")


@router.get("/templates/category", response_model=dict)
async def get_category_template_info(current_user: dict = Depends(get_current_user)):
    """
    Get category import template information
    
    Returns the structure and requirements for category import.
    """
    
    template_info = {
        "import_type": "category",
        "required_columns": [
            {"name": "name", "type": "string", "max_length": 100, "description": "Category name (unique per restaurant)"}
        ],
        "optional_columns": [
            {"name": "description", "type": "string", "description": "Category description"},
            {"name": "parent_category", "type": "string", "description": "Parent category name (for sub-categories)"},
            {"name": "display_order", "type": "integer", "description": "Display order (default: 0)"},
            {"name": "is_active", "type": "boolean", "description": "Active status (default: true)"},
            {"name": "image_url", "type": "string", "description": "Category image URL"},
            {"name": "tax_rate", "type": "float", "range": "0-100", "description": "Tax rate percentage"},
            {"name": "cgst_rate", "type": "float", "range": "0-100", "description": "CGST rate percentage"},
            {"name": "sgst_rate", "type": "float", "range": "0-100", "description": "SGST rate percentage"},
            {"name": "preparation_time", "type": "integer", "description": "Preparation time in minutes"},
            {"name": "is_vegetarian", "type": "boolean", "description": "Vegetarian category"},
            {"name": "is_non_vegetarian", "type": "boolean", "description": "Non-vegetarian category"},
            {"name": "is_vegan", "type": "boolean", "description": "Vegan category"}
        ],
        "validation_rules": {
            "name": "Required, unique per restaurant, max 100 characters",
            "tax_rate": "Must be between 0 and 100",
            "display_order": "Integer value"
        },
        "duplicate_check": "Categories are checked by 'name' field within the restaurant. Duplicates can be skipped or updated.",
        "sample_row": {
            "name": "Beverages",
            "description": "Hot and cold beverages",
            "display_order": 1,
            "is_active": True,
            "tax_rate": 18.0,
            "cgst_rate": 9.0,
            "sgst_rate": 9.0,
            "is_vegetarian": True
        }
    }
    
    return create_response(
        success=True,
        message="Category template information",
        data=template_info
    )


@router.get("/templates/product", response_model=dict)
async def get_product_template_info(current_user: dict = Depends(get_current_user)):
    """
    Get product import template information
    
    Returns the structure and requirements for product import.
    """
    
    template_info = {
        "import_type": "product",
        "required_columns": [
            {"name": "name", "type": "string", "max_length": 200, "description": "Product name (unique per restaurant)"},
            {"name": "category_name", "type": "string", "description": "Category name (must exist in restaurant)"},
            {"name": "price", "type": "integer", "description": "Price in paise (e.g., 1000 = ₹10.00)"}
        ],
        "optional_columns": [
            {"name": "description", "type": "string", "description": "Product description"},
            {"name": "sku", "type": "string", "max_length": 100, "description": "Stock keeping unit (unique)"},
            {"name": "barcode", "type": "string", "max_length": 100, "description": "Product barcode"},
            {"name": "cost_price", "type": "integer", "description": "Cost price in paise"},
            {"name": "track_inventory", "type": "boolean", "description": "Track inventory (default: true)"},
            {"name": "current_stock", "type": "integer", "description": "Current stock quantity"},
            {"name": "minimum_stock", "type": "integer", "description": "Minimum stock level"},
            {"name": "maximum_stock", "type": "integer", "description": "Maximum stock level"},
            {"name": "reorder_level", "type": "integer", "description": "Reorder level"},
            {"name": "tax_rate", "type": "float", "range": "0-100", "description": "Tax rate percentage"},
            {"name": "cgst_rate", "type": "float", "range": "0-100", "description": "CGST rate"},
            {"name": "sgst_rate", "type": "float", "range": "0-100", "description": "SGST rate"},
            {"name": "is_tax_inclusive", "type": "boolean", "description": "Price includes tax"},
            {"name": "is_active", "type": "boolean", "description": "Active status (default: true)"},
            {"name": "is_available", "type": "boolean", "description": "Available status (default: true)"},
            {"name": "preparation_time", "type": "integer", "description": "Preparation time in minutes"},
            {"name": "calories", "type": "integer", "description": "Calorie count"},
            {"name": "spice_level", "type": "string", "description": "Spice level (mild, medium, hot)"},
            {"name": "is_vegetarian", "type": "boolean", "description": "Vegetarian product"},
            {"name": "is_non_vegetarian", "type": "boolean", "description": "Non-vegetarian product"},
            {"name": "is_vegan", "type": "boolean", "description": "Vegan product"},
            {"name": "is_bestseller", "type": "boolean", "description": "Bestseller tag"},
            {"name": "is_featured", "type": "boolean", "description": "Featured product"},
            {"name": "display_order", "type": "integer", "description": "Display order"},
            {"name": "image_url", "type": "string", "description": "Product image URL"}
        ],
        "validation_rules": {
            "name": "Required, unique per restaurant, max 200 characters",
            "category_name": "Required, must exist in restaurant",
            "price": "Required, must be positive integer (in paise)",
            "sku": "Unique per restaurant if provided",
            "stock": "Must be non-negative integers"
        },
        "duplicate_check": "Products are checked by 'name' field within the restaurant. Duplicates can be skipped or updated.",
        "important_notes": [
            "Category must exist before importing products",
            "You can import categories first, then products",
            "Price is in paise (smallest currency unit): 1000 = ₹10.00 or $10.00",
            "All stock quantities must be non-negative"
        ],
        "sample_row": {
            "name": "Cappuccino",
            "category_name": "Beverages",
            "description": "Hot cappuccino with foam",
            "sku": "BEV001",
            "price": 15000,
            "cost_price": 9000,
            "track_inventory": True,
            "current_stock": 100,
            "minimum_stock": 10,
            "tax_rate": 18.0,
            "cgst_rate": 9.0,
            "sgst_rate": 9.0,
            "is_active": True,
            "is_available": True,
            "preparation_time": 5,
            "is_vegetarian": True
        }
    }
    
    return create_response(
        success=True,
        message="Product template information",
        data=template_info
    )


@router.delete("/imports/{import_id}", response_model=dict)
async def delete_import(
    import_id: str = Path(..., description="Import ID"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Soft delete import record"""
    
    data_import = await DataImportService.get_import_by_id(db, import_id)
    
    if not data_import:
        raise HTTPException(status_code=404, detail="Import not found")
    
    # Check permissions
    user_role = current_user.get("role")
    user_restaurant_id = current_user.get("restaurant_id")
    
    if user_role != "super_admin":
        if data_import.restaurant_id != user_restaurant_id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    data_import.deleted_at = datetime.utcnow()
    await db.commit()
    
    return create_response(
        success=True,
        message="Import deleted successfully",
        data={"deleted": True}
    )
