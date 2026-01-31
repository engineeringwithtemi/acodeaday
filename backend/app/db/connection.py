"""Database connection configuration for async PostgreSQL."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config.settings import settings

# Create async engine
# Note: prepared_statement_cache_size=0 is required for Supabase connection pooler
# (Supavisor) which uses transaction mode and doesn't support prepared statements
engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=300,  # Recycle connections every 5 minutes
    echo=settings.debug,  # Log SQL in debug mode
    connect_args={
        "statement_cache_size": 0,
    },
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=True,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession]:
    """
    Dependency that provides an async database session.

    Usage:
        @app.get("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Model))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
