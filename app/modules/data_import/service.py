from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime
from typing import Optional, List, Dict, Any, BinaryIO
import uuid
import pandas as pd
import openpyxl
from io import BytesIO
import csv

from app.modules.data_import.model import (
    DataImport, ImportLog, ImportTemplate, ImportType, ImportStatus, ImportFileFormat
)
from app.modules.data_import.schema import (
    DataImportCreate, DataImportUpdate, CategoryImportRow, ProductImportRow,
    ValidationResult, ImportTypeEnum, ImportFileFormatEnum
)
from app.modules.product.model import Category, Product
from sqlalchemy.orm import selectinload


class DataImportService:
    """Service for data import operations"""
    
    @staticmethod
    async def create_import(
        db: AsyncSession,
        import_data: DataImportCreate,
        file_name: str,
        file_path: str,
        file_size: int,
        file_format: str,
        imported_by: str
    ) -> DataImport:
        """Create import record"""
        
        import_number = f"IMP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8]}"
        
        data_import = DataImport(
            id=str(uuid.uuid4()),
            restaurant_id=import_data.restaurant_id,
            import_number=import_number,
            import_name=import_data.import_name,
            import_type=import_data.import_type,
            file_name=file_name,
            file_format=file_format,
            file_path=file_path,
            file_size=file_size,
            update_existing=import_data.update_existing,
            skip_duplicates=import_data.skip_duplicates,
            validate_only=import_data.validate_only,
            column_mapping=import_data.column_mapping,
            import_options=import_data.import_options,
            imported_by=imported_by,
            notes=import_data.notes
        )
        
        db.add(data_import)
        await db.commit()
        await db.refresh(data_import)
        
        return data_import
    
    @staticmethod
    async def get_import_by_id(db: AsyncSession, import_id: str) -> Optional[DataImport]:
        """Get import by ID"""
        query = select(DataImport).where(
            and_(
                DataImport.id == import_id,
                DataImport.deleted_at.is_(None)
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_imports(
        db: AsyncSession,
        restaurant_id: Optional[str] = None,
        import_type: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[DataImport], int]:
        """List imports with pagination"""
        
        query = select(DataImport).where(DataImport.deleted_at.is_(None))
        
        if restaurant_id:
            query = query.where(DataImport.restaurant_id == restaurant_id)
        
        if import_type:
            query = query.where(DataImport.import_type == import_type)
        
        if status:
            query = query.where(DataImport.status == status)
        
        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()
        
        # Pagination
        query = query.order_by(DataImport.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(query)
        imports = result.scalars().all()
        
        return imports, total
    
    @staticmethod
    def read_file(file_path: str, file_format: str) -> pd.DataFrame:
        """Read CSV or Excel file"""
        
        if file_format in ['csv']:
            return pd.read_csv(file_path)
        elif file_format in ['excel', 'xlsx', 'xls']:
            return pd.read_excel(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_format}")
    
    @staticmethod
    async def validate_category_import(
        db: AsyncSession,
        df: pd.DataFrame,
        restaurant_id: str
    ) -> ValidationResult:
        """Validate category import data"""
        
        errors = []
        warnings = []
        duplicates = []
        valid_rows = 0
        
        # Check required columns
        required_columns = ['name']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            errors.append({
                "type": "missing_columns",
                "message": f"Missing required columns: {', '.join(missing_columns)}"
            })
            return ValidationResult(
                is_valid=False,
                total_rows=len(df),
                valid_rows=0,
                invalid_rows=len(df),
                errors=errors,
                warnings=warnings,
                duplicates=duplicates
            )
        
        # Get existing categories for restaurant
        query = select(Category).where(
            and_(
                Category.restaurant_id == restaurant_id,
                Category.deleted_at.is_(None)
            )
        )
        result = await db.execute(query)
        existing_categories = result.scalars().all()
        existing_names = {cat.name.lower() for cat in existing_categories}
        
        # Validate each row
        for idx, row in df.iterrows():
            row_errors = []
            row_warnings = []
            
            # Validate name
            if pd.isna(row.get('name')) or not str(row.get('name')).strip():
                row_errors.append(f"Row {idx + 2}: Name is required")
            else:
                name = str(row['name']).strip()
                
                # Check duplicate in file
                name_lower = name.lower()
                if df[df['name'].str.lower() == name_lower].shape[0] > 1:
                    row_warnings.append(f"Row {idx + 2}: Duplicate category name in file: {name}")
                
                # Check duplicate in database
                if name_lower in existing_names:
                    duplicates.append({
                        "row": idx + 2,
                        "field": "name",
                        "value": name,
                        "message": f"Category '{name}' already exists in restaurant"
                    })
                
                # Validate length
                if len(name) > 100:
                    row_errors.append(f"Row {idx + 2}: Name too long (max 100 characters)")
            
            # Validate tax rates
            if 'tax_rate' in df.columns and not pd.isna(row.get('tax_rate')):
                try:
                    tax_rate = float(row['tax_rate'])
                    if tax_rate < 0 or tax_rate > 100:
                        row_errors.append(f"Row {idx + 2}: Tax rate must be between 0 and 100")
                except (ValueError, TypeError):
                    row_errors.append(f"Row {idx + 2}: Invalid tax rate")
            
            if row_errors:
                errors.extend(row_errors)
            elif row_warnings:
                warnings.extend(row_warnings)
                valid_rows += 1
            else:
                valid_rows += 1
        
        is_valid = len(errors) == 0
        invalid_rows = len(df) - valid_rows
        
        return ValidationResult(
            is_valid=is_valid,
            total_rows=len(df),
            valid_rows=valid_rows,
            invalid_rows=invalid_rows,
            errors=errors,
            warnings=warnings,
            duplicates=duplicates
        )
    
    @staticmethod
    async def validate_product_import(
        db: AsyncSession,
        df: pd.DataFrame,
        restaurant_id: str
    ) -> ValidationResult:
        """Validate product import data"""
        
        errors = []
        warnings = []
        duplicates = []
        valid_rows = 0
        
        # Check required columns
        required_columns = ['name', 'category_name', 'price']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            errors.append({
                "type": "missing_columns",
                "message": f"Missing required columns: {', '.join(missing_columns)}"
            })
            return ValidationResult(
                is_valid=False,
                total_rows=len(df),
                valid_rows=0,
                invalid_rows=len(df),
                errors=errors,
                warnings=warnings,
                duplicates=duplicates
            )
        
        # Get existing categories for restaurant
        category_query = select(Category).where(
            and_(
                Category.restaurant_id == restaurant_id,
                Category.deleted_at.is_(None)
            )
        )
        category_result = await db.execute(category_query)
        existing_categories = category_result.scalars().all()
        category_map = {cat.name.lower(): cat.id for cat in existing_categories}
        
        # Get existing products for restaurant
        product_query = select(Product).where(
            and_(
                Product.restaurant_id == restaurant_id,
                Product.deleted_at.is_(None)
            )
        )
        product_result = await db.execute(product_query)
        existing_products = product_result.scalars().all()
        existing_names = {prod.name.lower() for prod in existing_products}
        existing_skus = {prod.sku.lower() for prod in existing_products if prod.sku}
        
        # Validate each row
        for idx, row in df.iterrows():
            row_errors = []
            row_warnings = []
            
            # Validate name
            if pd.isna(row.get('name')) or not str(row.get('name')).strip():
                row_errors.append(f"Row {idx + 2}: Product name is required")
            else:
                name = str(row['name']).strip()
                
                # Check duplicate in database
                if name.lower() in existing_names:
                    duplicates.append({
                        "row": idx + 2,
                        "field": "name",
                        "value": name,
                        "message": f"Product '{name}' already exists in restaurant"
                    })
                
                # Validate length
                if len(name) > 200:
                    row_errors.append(f"Row {idx + 2}: Name too long (max 200 characters)")
            
            # Validate category
            if pd.isna(row.get('category_name')) or not str(row.get('category_name')).strip():
                row_errors.append(f"Row {idx + 2}: Category name is required")
            else:
                category_name = str(row['category_name']).strip()
                if category_name.lower() not in category_map:
                    row_errors.append(f"Row {idx + 2}: Category '{category_name}' does not exist in restaurant")
            
            # Validate price
            if pd.isna(row.get('price')):
                row_errors.append(f"Row {idx + 2}: Price is required")
            else:
                try:
                    price = int(row['price'])
                    if price < 0:
                        row_errors.append(f"Row {idx + 2}: Price must be positive")
                except (ValueError, TypeError):
                    row_errors.append(f"Row {idx + 2}: Invalid price")
            
            # Validate SKU uniqueness
            if 'sku' in df.columns and not pd.isna(row.get('sku')):
                sku = str(row['sku']).strip()
                if sku.lower() in existing_skus:
                    row_warnings.append(f"Row {idx + 2}: SKU '{sku}' already exists")
            
            # Validate stock
            if 'current_stock' in df.columns and not pd.isna(row.get('current_stock')):
                try:
                    stock = int(row['current_stock'])
                    if stock < 0:
                        row_errors.append(f"Row {idx + 2}: Stock cannot be negative")
                except (ValueError, TypeError):
                    row_errors.append(f"Row {idx + 2}: Invalid stock value")
            
            if row_errors:
                errors.extend(row_errors)
            elif row_warnings:
                warnings.extend(row_warnings)
                valid_rows += 1
            else:
                valid_rows += 1
        
        is_valid = len(errors) == 0
        invalid_rows = len(df) - valid_rows
        
        return ValidationResult(
            is_valid=is_valid,
            total_rows=len(df),
            valid_rows=valid_rows,
            invalid_rows=invalid_rows,
            errors=errors,
            warnings=warnings,
            duplicates=duplicates
        )
    
    @staticmethod
    async def import_categories(
        db: AsyncSession,
        df: pd.DataFrame,
        restaurant_id: str,
        import_id: str,
        update_existing: bool = False,
        skip_duplicates: bool = True
    ) -> Dict[str, Any]:
        """Import categories from DataFrame"""
        
        start_time = datetime.utcnow()
        
        # Get existing categories
        query = select(Category).where(
            and_(
                Category.restaurant_id == restaurant_id,
                Category.deleted_at.is_(None)
            )
        )
        result = await db.execute(query)
        existing_categories = result.scalars().all()
        existing_map = {cat.name.lower(): cat for cat in existing_categories}
        
        stats = {
            "total_rows": len(df),
            "imported": 0,
            "updated": 0,
            "skipped": 0,
            "failed": 0
        }
        
        # Process each row
        for idx, row in df.iterrows():
            try:
                name = str(row['name']).strip()
                name_lower = name.lower()
                
                # Check if exists
                if name_lower in existing_map:
                    if skip_duplicates and not update_existing:
                        stats["skipped"] += 1
                        await DataImportService._log_import_row(
                            db, import_id, idx + 2, row.to_dict(), "skipped",
                            "skipped", None, is_duplicate=True,
                            duplicate_field="name", duplicate_value=name,
                            existing_entity_id=existing_map[name_lower].id
                        )
                        continue
                    elif update_existing:
                        # Update existing category
                        category = existing_map[name_lower]
                        category.description = str(row.get('description', '')).strip() if not pd.isna(row.get('description')) else None
                        
                        if 'display_order' in df.columns and not pd.isna(row.get('display_order')):
                            category.display_order = int(row['display_order'])
                        
                        if 'is_active' in df.columns and not pd.isna(row.get('is_active')):
                            category.is_active = bool(row['is_active'])
                        
                        if 'tax_rate' in df.columns and not pd.isna(row.get('tax_rate')):
                            category.tax_rate = float(row['tax_rate'])
                        
                        stats["updated"] += 1
                        await DataImportService._log_import_row(
                            db, import_id, idx + 2, row.to_dict(), "success",
                            "updated", category.id, entity_type="category"
                        )
                        continue
                
                # Create new category
                category = Category(
                    id=str(uuid.uuid4()),
                    restaurant_id=restaurant_id,
                    name=name,
                    description=str(row.get('description', '')).strip() if not pd.isna(row.get('description')) else None,
                    display_order=int(row.get('display_order', 0)) if not pd.isna(row.get('display_order')) else 0,
                    is_active=bool(row.get('is_active', True)) if not pd.isna(row.get('is_active')) else True,
                    tax_rate=float(row.get('tax_rate', 0)) if not pd.isna(row.get('tax_rate')) else None
                )
                
                db.add(category)
                stats["imported"] += 1
                
                await DataImportService._log_import_row(
                    db, import_id, idx + 2, row.to_dict(), "success",
                    "created", category.id, entity_type="category"
                )
                
            except Exception as e:
                stats["failed"] += 1
                await DataImportService._log_import_row(
                    db, import_id, idx + 2, row.to_dict(), "failed",
                    None, None, error_message=str(e)
                )
        
        await db.commit()
        
        processing_time = int((datetime.utcnow() - start_time).total_seconds())
        
        return {
            "stats": stats,
            "processing_time": processing_time
        }
    
    @staticmethod
    async def import_products(
        db: AsyncSession,
        df: pd.DataFrame,
        restaurant_id: str,
        import_id: str,
        update_existing: bool = False,
        skip_duplicates: bool = True
    ) -> Dict[str, Any]:
        """Import products from DataFrame"""
        
        start_time = datetime.utcnow()
        
        # Get existing categories
        category_query = select(Category).where(
            and_(
                Category.restaurant_id == restaurant_id,
                Category.deleted_at.is_(None)
            )
        )
        category_result = await db.execute(category_query)
        existing_categories = category_result.scalars().all()
        category_map = {cat.name.lower(): cat.id for cat in existing_categories}
        
        # Get existing products
        product_query = select(Product).where(
            and_(
                Product.restaurant_id == restaurant_id,
                Product.deleted_at.is_(None)
            )
        )
        product_result = await db.execute(product_query)
        existing_products = product_result.scalars().all()
        existing_map = {prod.name.lower(): prod for prod in existing_products}
        
        stats = {
            "total_rows": len(df),
            "imported": 0,
            "updated": 0,
            "skipped": 0,
            "failed": 0
        }
        
        # Process each row
        for idx, row in df.iterrows():
            try:
                name = str(row['name']).strip()
                name_lower = name.lower()
                category_name = str(row['category_name']).strip()
                
                # Get category ID
                category_id = category_map.get(category_name.lower())
                if not category_id:
                    stats["failed"] += 1
                    await DataImportService._log_import_row(
                        db, import_id, idx + 2, row.to_dict(), "failed",
                        None, None, error_message=f"Category '{category_name}' not found"
                    )
                    continue
                
                # Check if exists
                if name_lower in existing_map:
                    if skip_duplicates and not update_existing:
                        stats["skipped"] += 1
                        await DataImportService._log_import_row(
                            db, import_id, idx + 2, row.to_dict(), "skipped",
                            "skipped", None, is_duplicate=True,
                            duplicate_field="name", duplicate_value=name,
                            existing_entity_id=existing_map[name_lower].id
                        )
                        continue
                    elif update_existing:
                        # Update existing product
                        product = existing_map[name_lower]
                        product.category_id = category_id
                        product.description = str(row.get('description', '')).strip() if not pd.isna(row.get('description')) else None
                        product.price = int(row['price'])
                        
                        if 'cost_price' in df.columns and not pd.isna(row.get('cost_price')):
                            product.cost_price = int(row['cost_price'])
                        
                        if 'current_stock' in df.columns and not pd.isna(row.get('current_stock')):
                            product.current_stock = int(row['current_stock'])
                        
                        if 'is_active' in df.columns and not pd.isna(row.get('is_active')):
                            product.is_active = bool(row['is_active'])
                        
                        stats["updated"] += 1
                        await DataImportService._log_import_row(
                            db, import_id, idx + 2, row.to_dict(), "success",
                            "updated", product.id, entity_type="product"
                        )
                        continue
                
                # Create new product
                product = Product(
                    id=str(uuid.uuid4()),
                    restaurant_id=restaurant_id,
                    category_id=category_id,
                    name=name,
                    description=str(row.get('description', '')).strip() if not pd.isna(row.get('description')) else None,
                    price=int(row['price']),
                    cost_price=int(row.get('cost_price', 0)) if not pd.isna(row.get('cost_price')) else None,
                    sku=str(row.get('sku', '')).strip() if not pd.isna(row.get('sku')) else None,
                    track_inventory=bool(row.get('track_inventory', True)) if not pd.isna(row.get('track_inventory')) else True,
                    current_stock=int(row.get('current_stock', 0)) if not pd.isna(row.get('current_stock')) else 0,
                    is_active=bool(row.get('is_active', True)) if not pd.isna(row.get('is_active')) else True,
                    is_available=bool(row.get('is_available', True)) if not pd.isna(row.get('is_available')) else True
                )
                
                db.add(product)
                stats["imported"] += 1
                
                await DataImportService._log_import_row(
                    db, import_id, idx + 2, row.to_dict(), "success",
                    "created", product.id, entity_type="product"
                )
                
            except Exception as e:
                stats["failed"] += 1
                await DataImportService._log_import_row(
                    db, import_id, idx + 2, row.to_dict(), "failed",
                    None, None, error_message=str(e)
                )
        
        await db.commit()
        
        processing_time = int((datetime.utcnow() - start_time).total_seconds())
        
        return {
            "stats": stats,
            "processing_time": processing_time
        }
    
    @staticmethod
    async def _log_import_row(
        db: AsyncSession,
        data_import_id: str,
        row_number: int,
        row_data: Dict[str, Any],
        status: str,
        action_taken: Optional[str],
        entity_id: Optional[str],
        entity_type: Optional[str] = None,
        error_message: Optional[str] = None,
        is_duplicate: bool = False,
        duplicate_field: Optional[str] = None,
        duplicate_value: Optional[str] = None,
        existing_entity_id: Optional[str] = None
    ):
        """Log import row"""
        
        log = ImportLog(
            id=str(uuid.uuid4()),
            data_import_id=data_import_id,
            row_number=row_number,
            row_data=row_data,
            status=status,
            action_taken=action_taken,
            entity_id=entity_id,
            entity_type=entity_type,
            error_message=error_message,
            is_duplicate=is_duplicate,
            duplicate_field=duplicate_field,
            duplicate_value=duplicate_value,
            existing_entity_id=existing_entity_id
        )
        
        db.add(log)
    
    @staticmethod
    def generate_sample_excel(import_type: str, row_count: int = 10) -> BytesIO:
        """Generate sample Excel file"""
        
        if import_type == "category":
            data = {
                "name": [f"Category {i}" for i in range(1, row_count + 1)],
                "description": [f"Description for category {i}" for i in range(1, row_count + 1)],
                "parent_category": ["" for _ in range(row_count)],
                "display_order": list(range(1, row_count + 1)),
                "is_active": [True] * row_count,
                "tax_rate": [18.0] * row_count,
                "cgst_rate": [9.0] * row_count,
                "sgst_rate": [9.0] * row_count,
                "preparation_time": [15] * row_count,
                "is_vegetarian": [True, False] * (row_count // 2) + [True] * (row_count % 2)
            }
        elif import_type == "product":
            data = {
                "name": [f"Product {i}" for i in range(1, row_count + 1)],
                "category_name": ["Beverages", "Food", "Snacks"] * (row_count // 3) + ["Beverages"] * (row_count % 3),
                "description": [f"Description for product {i}" for i in range(1, row_count + 1)],
                "sku": [f"SKU{i:04d}" for i in range(1, row_count + 1)],
                "price": [i * 1000 for i in range(1, row_count + 1)],  # in paise
                "cost_price": [i * 600 for i in range(1, row_count + 1)],
                "track_inventory": [True] * row_count,
                "current_stock": [100] * row_count,
                "minimum_stock": [10] * row_count,
                "tax_rate": [18.0] * row_count,
                "cgst_rate": [9.0] * row_count,
                "sgst_rate": [9.0] * row_count,
                "is_active": [True] * row_count,
                "is_available": [True] * row_count,
                "preparation_time": [15] * row_count,
                "is_vegetarian": [True, False] * (row_count // 2) + [True] * (row_count % 2)
            }
        else:
            raise ValueError(f"Unsupported import type: {import_type}")
        
        df = pd.DataFrame(data)
        
        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Data')
        
        output.seek(0)
        return output
    
    @staticmethod
    def generate_sample_csv(import_type: str, row_count: int = 10) -> BytesIO:
        """Generate sample CSV file"""
        
        if import_type == "category":
            data = {
                "name": [f"Category {i}" for i in range(1, row_count + 1)],
                "description": [f"Description for category {i}" for i in range(1, row_count + 1)],
                "display_order": list(range(1, row_count + 1)),
                "is_active": [True] * row_count,
                "tax_rate": [18.0] * row_count
            }
        elif import_type == "product":
            data = {
                "name": [f"Product {i}" for i in range(1, row_count + 1)],
                "category_name": ["Beverages", "Food", "Snacks"] * (row_count // 3) + ["Beverages"] * (row_count % 3),
                "description": [f"Description for product {i}" for i in range(1, row_count + 1)],
                "sku": [f"SKU{i:04d}" for i in range(1, row_count + 1)],
                "price": [i * 1000 for i in range(1, row_count + 1)],
                "cost_price": [i * 600 for i in range(1, row_count + 1)],
                "current_stock": [100] * row_count,
                "is_active": [True] * row_count
            }
        else:
            raise ValueError(f"Unsupported import type: {import_type}")
        
        df = pd.DataFrame(data)
        
        # Create CSV file in memory
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        return output
