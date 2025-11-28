"""
QR Ordering API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import secrets

from app.database import get_db
from app.models.qr import QRTable, QRSession, QRSettings
from app.models.customer import Customer
from app.schemas.qr import (
    QRTableCreate,
    QRTableUpdate,
    QRTableResponse,
    QRSessionCreate,
    QRSessionUpdate,
    QRSessionResponse,
    QRSettingsCreate,
    QRSettingsUpdate,
    QRSettingsResponse
)
from app.schemas.pagination import PaginationParams
from app.response_formatter import success_response, created_response, list_response, deleted_response, error_response
from app.utils import paginate_query, create_paginated_response


tables_router = APIRouter(prefix="/api/v1/qr/tables", tags=["QR Tables"])
sessions_router = APIRouter(prefix="/api/v1/qr/sessions", tags=["QR Sessions"])
settings_router = APIRouter(prefix="/api/v1/qr/settings", tags=["QR Settings"])


# QR Tables routes
@tables_router.get("")
def get_qr_tables(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    is_active: Optional[bool] = None,
    is_occupied: Optional[bool] = None,
    location: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all QR tables with pagination and optional filtering"""
    query = db.query(QRTable)
    
    if is_active is not None:
        query = query.filter(QRTable.is_active == is_active)
    if is_occupied is not None:
        query = query.filter(QRTable.is_occupied == is_occupied)
    if location:
        query = query.filter(QRTable.location == location)
    
    # Apply pagination
    pagination = PaginationParams(page=page, page_size=page_size)
    tables, pagination_meta = paginate_query(query, pagination)
    
    return create_paginated_response(tables, pagination_meta, "QR tables retrieved successfully")


@tables_router.get("/{table_id}", response_model=QRTableResponse)
def get_qr_table(table_id: str, db: Session = Depends(get_db)):
    """Get QR table by ID"""
    table = db.query(QRTable).filter(QRTable.id == table_id).first()
    if not table:
        raise HTTPException(status_code=404, detail="QR table not found")
    return table


@tables_router.get("/token/{qr_token}", response_model=QRTableResponse)
def get_qr_table_by_token(qr_token: str, db: Session = Depends(get_db)):
    """Get QR table by token (for customer scanning)"""
    table = db.query(QRTable).filter(QRTable.qr_token == qr_token).first()
    if not table:
        raise HTTPException(status_code=404, detail="Invalid QR code")
    if not table.is_active:
        raise HTTPException(status_code=400, detail="This table is currently inactive")
    return table


@tables_router.post("", response_model=QRTableResponse, status_code=201)
def create_qr_table(table: QRTableCreate, db: Session = Depends(get_db)):
    """Create a new QR table"""
    # Check for duplicate table number
    existing = db.query(QRTable).filter(QRTable.table_number == table.table_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Table number already exists")
    
    # Generate unique QR token
    qr_token = secrets.token_urlsafe(16)
    while db.query(QRTable).filter(QRTable.qr_token == qr_token).first():
        qr_token = secrets.token_urlsafe(16)
    
    # Generate QR code URL (assuming base URL from settings)
    base_url = "http://localhost:3000/qr"  # TODO: Get from settings
    qr_code_url = f"{base_url}/{qr_token}"
    
    table_data = table.model_dump()
    table_data["qr_token"] = qr_token
    table_data["qr_code_url"] = qr_code_url
    
    db_table = QRTable(**table_data)
    db.add(db_table)
    db.commit()
    db.refresh(db_table)
    return db_table


@tables_router.put("/{table_id}", response_model=QRTableResponse)
def update_qr_table(table_id: str, table: QRTableUpdate, db: Session = Depends(get_db)):
    """Update a QR table"""
    db_table = db.query(QRTable).filter(QRTable.id == table_id).first()
    if not db_table:
        raise HTTPException(status_code=404, detail="QR table not found")
    
    update_data = table.model_dump(exclude_unset=True)
    
    # Check table number uniqueness if being updated
    if "table_number" in update_data:
        existing = db.query(QRTable).filter(
            QRTable.table_number == update_data["table_number"],
            QRTable.id != table_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Table number already exists")
    
    for field, value in update_data.items():
        setattr(db_table, field, value)
    
    db.commit()
    db.refresh(db_table)
    return db_table


@tables_router.delete("/{table_id}", status_code=204)
def delete_qr_table(table_id: str, db: Session = Depends(get_db)):
    """Delete a QR table"""
    db_table = db.query(QRTable).filter(QRTable.id == table_id).first()
    if not db_table:
        raise HTTPException(status_code=404, detail="QR table not found")
    
    if db_table.is_occupied:
        raise HTTPException(status_code=400, detail="Cannot delete occupied table")
    
    db.delete(db_table)
    db.commit()
    return None


# QR Sessions routes
@sessions_router.get("")
def get_qr_sessions(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    table_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all QR sessions with pagination and optional filtering"""
    query = db.query(QRSession)
    
    if table_id:
        query = query.filter(QRSession.table_id == table_id)
    if status:
        query = query.filter(QRSession.status == status)
    
    query = query.order_by(QRSession.start_time.desc())
    
    # Apply pagination
    pagination = PaginationParams(page=page, page_size=page_size)
    sessions, pagination_meta = paginate_query(query, pagination)
    
    return create_paginated_response(sessions, pagination_meta, "QR sessions retrieved successfully")


@sessions_router.get("/{session_id}", response_model=QRSessionResponse)
def get_qr_session(session_id: str, db: Session = Depends(get_db)):
    """Get QR session by ID"""
    session = db.query(QRSession).filter(QRSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="QR session not found")
    return session


@sessions_router.post("", response_model=QRSessionResponse, status_code=201)
def create_qr_session(session: QRSessionCreate, db: Session = Depends(get_db)):
    """Create a new QR session (customer scans QR code)"""
    # Verify table exists and is active
    table = db.query(QRTable).filter(QRTable.id == session.table_id).first()
    if not table:
        raise HTTPException(status_code=404, detail="QR table not found")
    if not table.is_active:
        raise HTTPException(status_code=400, detail="This table is currently inactive")
    
    # Check if table already has an active session
    existing_session = db.query(QRSession).filter(
        QRSession.table_id == session.table_id,
        QRSession.status == 'active'
    ).first()
    
    if existing_session:
        # Return existing session instead of creating new one
        return existing_session
    
    # Verify customer if provided
    if session.customer_id:
        customer = db.query(Customer).filter(Customer.id == session.customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
    
    db_session = QRSession(**session.model_dump())
    db.add(db_session)
    
    # Update table status
    table.is_occupied = True
    table.current_session_id = db_session.id
    table.last_used = datetime.utcnow()
    
    db.commit()
    db.refresh(db_session)
    return db_session


@sessions_router.put("/{session_id}", response_model=QRSessionResponse)
def update_qr_session(session_id: str, session: QRSessionUpdate, db: Session = Depends(get_db)):
    """Update a QR session"""
    db_session = db.query(QRSession).filter(QRSession.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="QR session not found")
    
    update_data = session.model_dump(exclude_unset=True)
    
    # Update last activity
    update_data["last_activity"] = datetime.utcnow()
    
    # If status is being changed to completed/abandoned, set end_time and update table
    if "status" in update_data and update_data["status"] in ['completed', 'abandoned']:
        update_data["end_time"] = datetime.utcnow()
        
        # Update table status
        table = db.query(QRTable).filter(QRTable.id == db_session.table_id).first()
        if table:
            table.is_occupied = False
            table.current_session_id = None
    
    for field, value in update_data.items():
        setattr(db_session, field, value)
    
    db.commit()
    db.refresh(db_session)
    return db_session


@sessions_router.delete("/{session_id}", status_code=204)
def delete_qr_session(session_id: str, db: Session = Depends(get_db)):
    """Delete a QR session"""
    db_session = db.query(QRSession).filter(QRSession.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="QR session not found")
    
    # Update table if this was the current session
    table = db.query(QRTable).filter(QRTable.id == db_session.table_id).first()
    if table and table.current_session_id == session_id:
        table.is_occupied = False
        table.current_session_id = None
    
    db.delete(db_session)
    db.commit()
    return None


# QR Settings routes (Singleton)
@settings_router.get("", response_model=QRSettingsResponse)
def get_qr_settings(db: Session = Depends(get_db)):
    """Get QR ordering settings"""
    settings = db.query(QRSettings).first()
    if not settings:
        # Create default settings if none exist
        settings = QRSettings(
            restaurant_name="Restaurant POS",
            primary_color="#00A19D",
            accent_color="#FF6D00",
            enable_online_ordering=True,
            enable_payment_at_table=True,
            enable_online_payment=False,
            service_charge_percentage=1000,  # 10.00%
            auto_confirm_orders=False,
            order_timeout_minutes=30,
            max_orders_per_session=10,
            enable_customer_info=False,
            enable_special_instructions=True,
            enable_order_tracking=True,
            payment_gateways=[]
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    return settings


@settings_router.put("", response_model=QRSettingsResponse)
def update_qr_settings(settings: QRSettingsUpdate, db: Session = Depends(get_db)):
    """Update QR ordering settings"""
    db_settings = db.query(QRSettings).first()
    
    if not db_settings:
        # Create settings if they don't exist
        db_settings = QRSettings(**settings.model_dump(exclude_unset=True))
        db.add(db_settings)
    else:
        # Update existing settings
        update_data = settings.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_settings, field, value)
    
    db.commit()
    db.refresh(db_settings)
    return db_settings
