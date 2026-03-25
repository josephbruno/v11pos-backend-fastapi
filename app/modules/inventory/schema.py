from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from app.modules.inventory.model import (
    UnitOfMeasure,
    StockTransactionType,
    SupplierStatus,
    PurchaseOrderStatus
)


# Ingredient Schemas
class IngredientCreate(BaseModel):
    restaurant_id: str
    name: str
    description: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    tags: Optional[List[str]] = None
    unit_of_measure: UnitOfMeasure
    current_stock: float = 0.0
    minimum_stock: float = 0.0
    maximum_stock: Optional[float] = None
    reorder_level: float = 0.0
    reorder_quantity: Optional[float] = None
    cost_price: int = 0
    storage_location: Optional[str] = None
    shelf_life_days: Optional[int] = None
    primary_supplier_id: Optional[str] = None
    is_perishable: bool = False
    track_batch: bool = False
    track_expiry: bool = False
    low_stock_alert_enabled: bool = True
    notes: Optional[str] = None
    created_by: Optional[str] = None


class IngredientUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    tags: Optional[List[str]] = None
    unit_of_measure: Optional[UnitOfMeasure] = None
    minimum_stock: Optional[float] = None
    maximum_stock: Optional[float] = None
    reorder_level: Optional[float] = None
    reorder_quantity: Optional[float] = None
    cost_price: Optional[int] = None
    storage_location: Optional[str] = None
    shelf_life_days: Optional[int] = None
    primary_supplier_id: Optional[str] = None
    is_perishable: Optional[bool] = None
    track_batch: Optional[bool] = None
    track_expiry: Optional[bool] = None
    low_stock_alert_enabled: Optional[bool] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class IngredientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    restaurant_id: str
    name: str
    description: Optional[str]
    sku: Optional[str]
    barcode: Optional[str]
    category: Optional[str]
    sub_category: Optional[str]
    tags: Optional[dict]
    unit_of_measure: str
    current_stock: float
    minimum_stock: float
    maximum_stock: Optional[float]
    reorder_level: float
    reorder_quantity: Optional[float]
    cost_price: int
    average_cost: int
    last_purchase_price: Optional[int]
    storage_location: Optional[str]
    shelf_life_days: Optional[int]
    primary_supplier_id: Optional[str]
    is_perishable: bool
    is_active: bool
    track_batch: bool
    track_expiry: bool
    low_stock_alert_enabled: bool
    low_stock_notified_at: Optional[datetime]
    notes: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime


# Recipe Schemas
class RecipeIngredientCreate(BaseModel):
    ingredient_id: str
    quantity: float
    unit: str
    preparation_note: Optional[str] = None
    is_optional: bool = False
    display_order: int = 0


class RecipeIngredientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    recipe_id: str
    ingredient_id: str
    quantity: float
    unit: str
    cost_per_unit: int
    total_cost: int
    preparation_note: Optional[str]
    is_optional: bool
    display_order: int
    created_at: datetime
    updated_at: datetime


class RecipeCreate(BaseModel):
    restaurant_id: str
    product_id: str
    name: str
    description: Optional[str] = None
    version: str = "1.0"
    yield_quantity: float = 1.0
    yield_unit: Optional[str] = None
    prep_time_minutes: Optional[int] = None
    cook_time_minutes: Optional[int] = None
    instructions: Optional[str] = None
    ingredients: List[RecipeIngredientCreate]
    notes: Optional[str] = None
    created_by: Optional[str] = None


class RecipeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    yield_quantity: Optional[float] = None
    yield_unit: Optional[str] = None
    prep_time_minutes: Optional[int] = None
    cook_time_minutes: Optional[int] = None
    instructions: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class RecipeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    restaurant_id: str
    product_id: str
    name: str
    description: Optional[str]
    version: str
    yield_quantity: float
    yield_unit: Optional[str]
    total_cost: int
    cost_per_serving: int
    prep_time_minutes: Optional[int]
    cook_time_minutes: Optional[int]
    instructions: Optional[str]
    is_active: bool
    notes: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    ingredients: Optional[List[RecipeIngredientResponse]] = None


# Stock Transaction Schemas
class StockTransactionCreate(BaseModel):
    restaurant_id: str
    ingredient_id: str
    transaction_type: StockTransactionType
    quantity: float
    unit: str
    unit_cost: int = 0
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    supplier_id: Optional[str] = None
    batch_number: Optional[str] = None
    expiry_date: Optional[datetime] = None
    reason: Optional[str] = None
    requires_approval: bool = False
    notes: Optional[str] = None
    created_by: Optional[str] = None


class StockTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    restaurant_id: str
    ingredient_id: str
    transaction_type: str
    transaction_number: str
    transaction_date: datetime
    quantity: float
    unit: str
    stock_before: float
    stock_after: float
    unit_cost: int
    total_cost: int
    reference_type: Optional[str]
    reference_id: Optional[str]
    supplier_id: Optional[str]
    batch_number: Optional[str]
    expiry_date: Optional[datetime]
    reason: Optional[str]
    requires_approval: bool
    is_approved: bool
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    notes: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime


class StockAdjustmentRequest(BaseModel):
    ingredient_id: str
    adjustment_quantity: float
    reason: str
    notes: Optional[str] = None


class WastageEntry(BaseModel):
    ingredient_id: str
    quantity: float
    reason: str
    notes: Optional[str] = None


# Supplier Schemas
class SupplierCreate(BaseModel):
    restaurant_id: str
    name: str
    code: Optional[str] = None
    company_name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    alternate_phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "India"
    gstin: Optional[str] = None
    pan: Optional[str] = None
    payment_terms_days: int = 0
    credit_limit: Optional[int] = None
    supply_categories: Optional[List[str]] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    notes: Optional[str] = None
    created_by: Optional[str] = None


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    company_name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    alternate_phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    payment_terms_days: Optional[int] = None
    credit_limit: Optional[int] = None
    supply_categories: Optional[List[str]] = None
    status: Optional[SupplierStatus] = None
    rating: Optional[float] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    notes: Optional[str] = None


class SupplierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    restaurant_id: str
    name: str
    code: Optional[str]
    company_name: Optional[str]
    contact_person: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    alternate_phone: Optional[str]
    address_line1: Optional[str]
    address_line2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    postal_code: Optional[str]
    country: str
    gstin: Optional[str]
    pan: Optional[str]
    payment_terms_days: int
    credit_limit: Optional[int]
    current_balance: int
    supply_categories: Optional[dict]
    rating: Optional[float]
    total_orders: int
    total_purchase_value: int
    status: str
    bank_name: Optional[str]
    account_number: Optional[str]
    ifsc_code: Optional[str]
    notes: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime


# Purchase Order Schemas
class PurchaseOrderItemCreate(BaseModel):
    ingredient_id: str
    quantity_ordered: float
    unit: str
    unit_price: int
    tax_percentage: float = 0.0
    discount_percentage: float = 0.0
    notes: Optional[str] = None


class PurchaseOrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    purchase_order_id: str
    ingredient_id: str
    quantity_ordered: float
    quantity_received: float
    unit: str
    unit_price: int
    tax_percentage: float
    tax_amount: int
    discount_percentage: float
    discount_amount: int
    total_amount: int
    is_fully_received: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class PurchaseOrderCreate(BaseModel):
    restaurant_id: str
    supplier_id: str
    expected_delivery_date: Optional[datetime] = None
    items: List[PurchaseOrderItemCreate]
    delivery_address: Optional[str] = None
    shipping_method: Optional[str] = None
    shipping_charges: int = 0
    other_charges: int = 0
    payment_terms: Optional[str] = None
    terms_conditions: Optional[str] = None
    requires_approval: bool = False
    notes: Optional[str] = None
    created_by: Optional[str] = None


class PurchaseOrderUpdate(BaseModel):
    supplier_id: Optional[str] = None
    expected_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None
    status: Optional[PurchaseOrderStatus] = None
    delivery_address: Optional[str] = None
    shipping_method: Optional[str] = None
    shipping_charges: Optional[int] = None
    other_charges: Optional[int] = None
    payment_terms: Optional[str] = None
    terms_conditions: Optional[str] = None
    notes: Optional[str] = None


class PurchaseOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    restaurant_id: str
    supplier_id: str
    po_number: str
    po_date: datetime
    expected_delivery_date: Optional[datetime]
    actual_delivery_date: Optional[datetime]
    status: str
    subtotal: int
    tax_amount: int
    discount_amount: int
    shipping_charges: int
    other_charges: int
    total_amount: int
    delivery_address: Optional[str]
    shipping_method: Optional[str]
    payment_terms: Optional[str]
    terms_conditions: Optional[str]
    requires_approval: bool
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    notes: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    items: Optional[List[PurchaseOrderItemResponse]] = None


class ReceiveItemsRequest(BaseModel):
    items: List[dict]  # [{"po_item_id": "id", "quantity_received": 10.5, "batch_number": "B123", "expiry_date": "2024-12-31"}]


# Low Stock Alert Schema
class LowStockAlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    restaurant_id: str
    ingredient_id: str
    current_stock: float
    minimum_stock: float
    reorder_level: float
    unit: str
    is_resolved: bool
    resolved_at: Optional[datetime]
    resolved_by: Optional[str]
    action_taken: Optional[str]
    purchase_order_id: Optional[str]
    created_at: datetime
    updated_at: datetime


# Analytics and Reports
class InventoryValueReport(BaseModel):
    total_ingredients: int
    total_value: int
    category_breakdown: List[dict]
    low_stock_items: int
    out_of_stock_items: int


class ConsumptionReport(BaseModel):
    ingredient_id: str
    ingredient_name: str
    opening_stock: float
    stock_in: float
    stock_out: float
    closing_stock: float
    unit: str
    total_consumption_cost: int


class WastageReport(BaseModel):
    ingredient_id: str
    ingredient_name: str
    total_wastage: float
    unit: str
    total_cost: int
    wastage_percentage: float
    reasons: List[dict]
