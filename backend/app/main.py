"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import acreate_client

from app.config.logging import configure_logging, get_logger
from app.config.settings import settings
from app.db.connection import engine
from app.routes import chat, code, execution, problems, progress, submissions

configure_logging()
logger = get_logger(__name__)


async def ensure_default_user_exists(supabase_client, admin_client=None):
    """Create default user in Supabase Auth if it doesn't exist."""
    try:
        await supabase_client.auth.sign_in_with_password({
            "email": settings.auth_user_email,
            "password": settings.auth_password,
        })
        logger.info("default_user_exists", email=settings.auth_user_email)
    except Exception:
        try:
            # Use admin API if service role key is available (auto-confirms email)
            if admin_client:
                await admin_client.auth.admin.create_user({
                    "email": settings.auth_user_email,
                    "password": settings.auth_password,
                    "email_confirm": True,
                })
                logger.info("default_user_created_confirmed", email=settings.auth_user_email)
            else:
                # Fallback to regular sign_up (requires manual email confirmation)
                await supabase_client.auth.sign_up({
                    "email": settings.auth_user_email,
                    "password": settings.auth_password,
                })
                logger.info("default_user_created_unconfirmed", email=settings.auth_user_email)
        except Exception as e:
            logger.warning(
                "default_user_creation_failed",
                email=settings.auth_user_email,
                error=str(e),
            )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info(
        "application_starting",
        project=settings.project_name,
        version=settings.version,
        environment=settings.environment,
    )

    # Initialize async Supabase client and store on app state
    supabase_client = await acreate_client(settings.supabase_url, settings.supabase_key)
    app.state.supabase = supabase_client

    # Create admin client if service role key is available (for user creation with auto-confirm)
    admin_client = None
    if settings.supabase_service_role_key:
        admin_client = await acreate_client(settings.supabase_url, settings.supabase_service_role_key)

    await ensure_default_user_exists(supabase_client, admin_client)

    yield

    logger.info("application_shutting_down")
    await engine.dispose()


app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    lifespan=lifespan,
    description="Backend for acodeaday - daily coding practice with spaced repetition",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(problems.router)
app.include_router(execution.router)
app.include_router(progress.router)
app.include_router(submissions.router)
app.include_router(code.router)
app.include_router(chat.router)


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
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.project_name,
        "version": settings.version,
    }
