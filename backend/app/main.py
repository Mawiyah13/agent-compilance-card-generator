import time
import logging
from contextlib import asynccontextmanager
from typing import Any
from fastapi import FastAPI, HTTPException, Request, Response, status, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from redis import Redis
import jwt

from app.core.config import settings
import app.core.database as database
from app.api.v1.router import api_router
from app.models import Base

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("main")

# Initialize Redis (caching / rate limiting)
try:
    redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=2)
except Exception as e:
    logger.warning(f"Failed to connect to Redis. Rate limiting will be bypassed. Error: {e}")
    redis_client = None

# Lifespan manager for database auto-bootstrapping
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Verifying database connection...")
    
    # Try connecting to PostgreSQL, fallback to SQLite if down
    try:
        async with database.async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Connected to PostgreSQL successfully.")
    except Exception as pg_err:
        logger.warning(f"PostgreSQL connection failed: {pg_err}. Falling back to SQLite local database.")
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        sqlite_async_uri = "sqlite+aiosqlite:///./compliance_db.sqlite"
        sqlite_sync_uri = "sqlite:///./compliance_db.sqlite"
        
        # Override database engines
        import app.core.database as db_mod
        db_mod.async_engine = create_async_engine(sqlite_async_uri, echo=False)
        db_mod.AsyncSessionLocal = async_sessionmaker(
            bind=db_mod.async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
        db_mod.engine = create_engine(sqlite_sync_uri, echo=False)
        db_mod.SessionLocal = sessionmaker(
            bind=db_mod.engine,
            autocommit=False,
            autoflush=False
        )
        logger.info(f"SQLite database engines initialized at {sqlite_async_uri}")

    logger.info("Initializing database tables...")
    try:
        async with database.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.critical(f"Failed to initialize database tables: {e}")
    yield

# Custom Rate Limiter Dependency
async def rate_limiter(request: Request):

    if not redis_client:
        return
    
    ip = request.client.host if request.client else "unknown"
    current_minute = int(time.time() / 60)
    key = f"rate:{ip}:{current_minute}"
    
    try:
        current = redis_client.get(key)
        if current and int(current) >= settings.RATE_LIMIT_PER_MINUTE:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later."
            )
        
        # Increment and set expire if new key
        pipe = redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, 60)
        pipe.execute()
    except Exception as e:
        # Rate limit failure shouldn't crash the server
        logger.error(f"Redis rate limiting error: {e}")
        pass

# App Setup
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    dependencies=[Depends(rate_limiter)],
    lifespan=lifespan
)

# CORS Middleware
# Configure to match your frontend client URL (e.g. localhost:5173 / localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handling
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logger.warning(f"Request validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    logger.warning(f"HTTP exception raised: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception occurred")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please contact system support."}
    )

@app.exception_handler(jwt.ExpiredSignatureError)
async def jwt_expired_exception_handler(request: Request, exc: jwt.ExpiredSignatureError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Token has expired"}
    )

@app.exception_handler(jwt.InvalidTokenError)
async def jwt_invalid_exception_handler(request: Request, exc: jwt.InvalidTokenError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Invalid token details"}
    )


# Health checks
@app.get("/health", tags=["health"])
async def health_check() -> Any:
    """Consolidated Health check for services."""
    db_status = "healthy"
    redis_status = "healthy"
    
    # Check Database Connection
    try:
        async with database.async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Database healthcheck failed: {e}")
        db_status = f"unhealthy: {str(e)}"
        
    # Check Redis
    if redis_client:
        try:
            redis_client.ping()
        except Exception as e:
            logger.error(f"Redis healthcheck failed: {e}")
            redis_status = f"unhealthy: {str(e)}"
    else:
        redis_status = "unhealthy: redis unavailable"
        
    status_code = status.HTTP_200_OK
    if db_status != "healthy" or redis_status != "healthy":
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if status_code == 200 else "unhealthy",
            "database": db_status,
            "redis": redis_status,
            "timestamp": time.time()
        }
    )


@app.get("/health/liveness", tags=["health"])
async def liveness_check() -> Any:
    """Fast check for process liveness."""
    return {"status": "alive"}


@app.get("/health/readiness", tags=["health"])
async def readiness_check() -> Any:
    """Verifies backend is ready to accept traffic."""
    # Check DB
    try:
        async with database.async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "reason": "database unavailable"}
        )

    # Check Redis
    if not redis_client:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "reason": "redis unavailable"}
        )

    try:
        redis_client.ping()
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "reason": "redis unavailable"}
        )

    return {"status": "ready"}


# API Router
app.include_router(api_router, prefix=settings.API_V1_STR)
