from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://username:password@localhost:5432/parser_potato")

# Convert to async URL for asyncpg
if DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    ASYNC_DATABASE_URL = DATABASE_URL

# Remove unsupported query parameters for asyncpg
if "?" in ASYNC_DATABASE_URL:
    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
    
    parsed = urlparse(ASYNC_DATABASE_URL)
    query_params = parse_qs(parsed.query)
    
    # asyncpg doesn't support these as direct kwargs or in the DSN in the way SQLAlchemy passes them
    unsupported_params = ["sslmode", "channel_binding", "target_session_attrs"]
    
    for param in unsupported_params:
        if param in query_params:
            del query_params[param]
        
    new_query = urlencode(query_params, doseq=True)
    parsed = parsed._replace(query=new_query)
    ASYNC_DATABASE_URL = urlunparse(parsed)

engine = create_async_engine(ASYNC_DATABASE_URL, echo=True, future=True)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    """Dependency for getting database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
