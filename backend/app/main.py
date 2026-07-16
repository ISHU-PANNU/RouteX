import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config.config import settings
from app.core.exceptions import RouteXException
from app.database.session import engine
from app.database.base import Base
from app.routes import auth, shipments, routes, tracking, analytics

# Configure application logging namespaces
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("routex")

# Modern FastAPI Lifespan Handler replacing deprecated @app.on_event("startup")
@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.ENV != "testing":
        logger.info("Initializing relational database schema tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database schemas ready.")
    yield
    logger.info("Shutting down RouteX server context.")

# Setup FastAPI App
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="RouteX Logistics Courier Platform Backend API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Apply CORS configuration middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to allowed dashboard origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Custom Exception Handler
@app.exception_handler(RouteXException)
def routex_exception_handler(request: Request, exc: RouteXException):
    logger.error(f"Application error: {exc.error_code} - {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status_code": exc.status_code,
            "error_code": exc.error_code,
            "message": exc.message,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "details": exc.details
        }
    )

# Global Validation / Uncaught Exceptions Handler
@app.exception_handler(Exception)
def universal_exception_handler(request: Request, exc: Exception):
    logger.exception("An unhandled exception occurred in the route context:")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status_code": 500,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Please try again later.",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        }
    )

# Include Submodules Router mappings
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(shipments.router, prefix=settings.API_V1_STR)
app.include_router(routes.router, prefix=settings.API_V1_STR)
app.include_router(tracking.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Health Check"])
def read_root():
    return {
        "status": "online",
        "app_name": settings.PROJECT_NAME,
        "environment": settings.ENV,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }
