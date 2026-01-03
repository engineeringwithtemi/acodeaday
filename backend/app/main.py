"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.logging import configure_logging, get_logger
from app.config.settings import settings
from app.db.connection import engine

# Configure logging before any other imports
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info(
        "application_starting",
        project=settings.project_name,
        version=settings.version,
        environment=settings.environment,
    )

    yield

    # Shutdown
    logger.info("application_shutting_down")
    await engine.dispose()  # Close database connections


# Create FastAPI application
app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    lifespan=lifespan,
    description="Backend for acodeaday - daily coding practice with spaced repetition",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server (Create React App)
        "http://localhost:5173",  # Vite dev server (TanStack)
        "http://localhost:5174",  # Alternative Vite port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - returns application info."""
    return {
        "name": settings.project_name,
        "version": settings.version,
        "environment": settings.environment,
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint - verifies application is running."""
    return {
        "status": "healthy",
        "service": settings.project_name,
        "version": settings.version,
    }


# Register route modules
from app.routes import execution, problems, progress, submissions

app.include_router(problems.router)
app.include_router(execution.router)
app.include_router(progress.router)
app.include_router(submissions.router)
