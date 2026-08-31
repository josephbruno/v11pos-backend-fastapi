from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import uuid

from app.core.config import settings
from app.core.health import check_database, check_redis
from app.core.logging_config import configure_customer_auth_logging
from app.core.database import init_db, close_db
from app.core.response import (
    success_response,
    request_validation_exception_handler,
)
from app.modules.auth.route import router as auth_router
from app.modules.user.route import router as user_router
from app.modules.restaurant.route import router as restaurant_router
from app.modules.product.route import router as product_router
from app.modules.customer.route import router as customer_router
from app.modules.customer_auth.route import router as customer_auth_router
from app.modules.table.route import router as table_router
from app.modules.order.route import router as order_router
from app.modules.kds.route import router as kds_router
from app.modules.inventory.route import router as inventory_router
from app.modules.staff.route import router as staff_router
from app.modules.reports.route import router as reports_router
from app.modules.data_import.route import router as data_import_router
from app.modules.data_copy.route import router as data_copy_router
from app.modules.homebanner.route import router as homebanner_router
from app.modules.row_management.route import router as row_management_router
from app.modules.open_fetch.route import router as open_fetch_router
from app.modules.cart.route import router as cart_router
from app.modules.payment.route import router as payment_router
from app.modules.payment_gateway.route import router as payment_gateway_router
from app.modules.table_session.route import router as table_session_router
from app.modules.table_session.qr_order_route import router as qr_table_order_router
from app.modules.billing.route import router as billing_router
from app.routes.upload import router as upload_router
from app.services.storage_service import init_storage
from app.modules.restaurant.seed import run_seed_subscription_plans


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    configure_customer_auth_logging()
    print("🚀 Starting application...")
    print(f"📝 Environment: {settings.APP_ENV}")
    print(
        f"📧 Customer OTP email: EMAIL_ENABLED={settings.EMAIL_ENABLED} "
        f"(set EMAIL_ENABLED=true in .env or container env to send via SMTP)"
    )
    print(f"🗄️  Database: {settings.DB_NAME} @ {settings.DB_HOST}:{settings.DB_PORT}")
    
    # Initialize database
    await init_db()
    print("✅ Database initialized")

    await run_seed_subscription_plans()
    print("✅ Subscription plans seeded")

    # Initialize MinIO storage (client + bucket)
    init_storage()
    print("✅ MinIO storage initialized")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down application...")
    await close_db()
    print("✅ Database connections closed")


# Create FastAPI application
app = FastAPI(
    title="FastAPI POS System",
    description="Point of Sale System API with JWT Authentication",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url=None,
    servers=[
        {"url": "http://localhost:8000", "description": "Development server"},
    ]
)

# CORS middleware — regex covers https://pos.v11tech.com and other v11tech hosts
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

app.add_exception_handler(RequestValidationError, request_validation_exception_handler)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    Return a JSON 500 from ExceptionMiddleware (inside CORS) so browsers
    never see a raw ServerErrorMiddleware response without Allow-Origin.
    """
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "status_code": 500,
            "message": "Internal server error",
            "data": None,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Internal server error",
                "details": str(exc) if settings.is_development else None,
            },
        },
    )


# Health check endpoint
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - Health check"""
    return success_response(
        message="FastAPI POS System is running",
        data={
            "environment": settings.APP_ENV,
            "version": "1.0.0"
        }
    )


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return success_response(
        message="Service is healthy",
        data={
            "status": "healthy",
            "environment": settings.APP_ENV
        }
    )


@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """Readiness probe — verifies database and Redis connectivity."""
    db_ok, db_msg = await check_database()
    redis_ok, redis_msg = check_redis()
    healthy = db_ok and redis_ok
    payload = {
        "status": "ready" if healthy else "degraded",
        "checks": {
            "database": {"ok": db_ok, "detail": db_msg},
            "redis": {"ok": redis_ok, "detail": redis_msg},
        },
        "environment": settings.APP_ENV,
        "timezone": settings.APP_TIMEZONE,
    }
    return JSONResponse(
        content={
            "success": healthy,
            "status_code": 200 if healthy else 503,
            "message": "Service is ready" if healthy else "Service dependencies unavailable",
            "data": payload,
            "error": None,
        },
        status_code=200 if healthy else 503,
    )


# Override ReDoc to ensure it works with absolute URLs
from fastapi.openapi.docs import get_redoc_html

@app.get("/redoc", include_in_schema=False)
async def redoc_override(request: Request):
    """ReDoc documentation with absolute OpenAPI URL"""
    return get_redoc_html(
        openapi_url="/openapi.json",
        title=app.title + " - ReDoc",
        redoc_js_url="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"
    )


# Include routers with /api/v1/ prefix
app.include_router(auth_router, prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")
app.include_router(restaurant_router, prefix="/api/v1")
app.include_router(product_router, prefix="/api/v1")
app.include_router(customer_router, prefix="/api/v1")
app.include_router(customer_auth_router, prefix="/api/v1")
app.include_router(table_router, prefix="/api/v1")
app.include_router(order_router, prefix="/api/v1")
app.include_router(kds_router, prefix="/api/v1")
app.include_router(inventory_router, prefix="/api/v1")
app.include_router(staff_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
app.include_router(data_import_router, prefix="/api/v1")
app.include_router(data_copy_router, prefix="/api/v1")
app.include_router(homebanner_router, prefix="/api/v1")
app.include_router(row_management_router, prefix="/api/v1")
app.include_router(open_fetch_router, prefix="/api/v1")
app.include_router(cart_router, prefix="/api/v1")
app.include_router(payment_router, prefix="/api/v1")
app.include_router(payment_gateway_router, prefix="/api/v1")
app.include_router(table_session_router, prefix="/api/v1")
app.include_router(qr_table_order_router, prefix="/api/v1")
app.include_router(billing_router, prefix="/api/v1")
app.include_router(upload_router)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development
    )
