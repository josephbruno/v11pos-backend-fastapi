from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import init_db, close_db
from app.modules.auth.route import router as auth_router
from app.modules.user.route import router as user_router
from app.modules.restaurant.route import router as restaurant_router
from app.modules.product.route import router as product_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    print("🚀 Starting application...")
    print(f"📝 Environment: {settings.APP_ENV}")
    print(f"🗄️  Database: {settings.DB_NAME} @ {settings.DB_HOST}:{settings.DB_PORT}")
    
    # Initialize database
    await init_db()
    print("✅ Database initialized")
    
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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - Health check"""
    return {
        "success": True,
        "message": "FastAPI POS System is running",
        "data": {
            "environment": settings.APP_ENV,
            "version": "1.0.0"
        },
        "error": None
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "success": True,
        "message": "Service is healthy",
        "data": {
            "status": "healthy",
            "environment": settings.APP_ENV
        },
        "error": None
    }


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


# Include routers
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(restaurant_router)
app.include_router(product_router)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development
    )
