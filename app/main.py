from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import create_tables
from app.response_formatter import success_response
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import routes
from app.routes import (
    categories, 
    products, 
    customers, 
    orders, 
    modifiers,
    combos,
    qr,
    loyalty,
    tax_settings,
    users,
    auth,
    analytics,
    dashboard,
    file_manager,
    translations,
    onboarding,  # Multi-tenant onboarding
    platform_admin  # NEW: Platform admin dashboard
)

# Create FastAPI application
app = FastAPI(
    title="RestaurantPOS API",
    description="Comprehensive Point of Sale System API with FastAPI and MySQL",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploads
uploads_dir = Path(__file__).parent.parent / "uploads"
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# Include routers
# Authentication
app.include_router(auth.router)

# Multi-tenant Onboarding
app.include_router(onboarding.router)

# Platform Admin Dashboard
app.include_router(platform_admin.router)

# User Management
app.include_router(users.users_router)
app.include_router(users.shifts_router)
app.include_router(users.performance_router)
app.include_router(users.roles_router)

# Products & Catalog
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(combos.router)
app.include_router(combos.items_router)
app.include_router(modifiers.router)
app.include_router(modifiers.options_router)

# Customers & Loyalty
app.include_router(customers.router)
app.include_router(customers.tags_router)
app.include_router(loyalty.rules_router)
app.include_router(loyalty.transactions_router)

# Orders
app.include_router(orders.router)

# QR Ordering
app.include_router(qr.tables_router)
app.include_router(qr.sessions_router)
app.include_router(qr.settings_router)

# Tax & Settings
app.include_router(tax_settings.tax_router)
app.include_router(tax_settings.settings_router)

# Analytics & Reports
app.include_router(analytics.analytics_router)
app.include_router(analytics.reports_router)

# Dashboard API
app.include_router(dashboard.dashboard_router)

# File Manager
app.include_router(file_manager.router)

# Translations
app.include_router(translations.router)


@app.on_event("startup")
async def startup_event():
    """
    Create database tables on startup.
    """
    create_tables()


@app.get("/")
async def root():
    """
    Root endpoint with API information.
    """
    return success_response(
        data={
            "version": "1.0.0",
            "docs": "/docs",
            "redoc": "/redoc",
            "features": [
                "User Management",
                "Product Catalog",
                "Customer & Loyalty",
                "QR Ordering",
                "Order Management",
                "Settings & Configuration"
            ]
        },
        message="Welcome to RestaurantPOS API"
    )


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return success_response(
        data={"database": "mysql"},
        message="System is healthy"
    )


@app.get("/api/stats")
async def get_stats():
    """
    Get basic API statistics.
    """
    return success_response(
        data={
            "total_routes": len(app.routes),
            "models": 26,
            "implemented_endpoints": 111,
            "operational_status": "active",
            "features": {
                "authentication": "✓",
                "user_management": "✓",
                "user_roles": "✓",
                "products": "✓",
                "combos": "✓",
                "modifiers": "✓",
                "customers": "✓",
                "loyalty": "✓",
                "orders": "✓",
                "kot_management": "✓",
                "qr_ordering": "✓",
                "tax_rules": "✓",
                "settings": "✓",
                "analytics": "✓",
                "reports": "✓"
            }
        },
        message="API statistics fetched successfully"
    )
