"""
Database Connection and Session Management
PostgreSQL with pgvector extension
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create SQLAlchemy engine with psycopg (version 3)
# Convert postgresql:// to postgresql+psycopg://
database_url = settings.DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://')

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency to get database session
    Usage: db = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables and pgvector extension"""
    from sqlalchemy import text
    import psycopg
    
    # Import models to register them with Base before create_all()
    from app.models.document import Document, Chunk  # noqa: F401
    
    # First, try to create the database if it doesn't exist
    # Connect to postgres database to create cerebro database
    try:
        # Parse the database URL to get connection params
        from urllib.parse import urlparse
        parsed = urlparse(settings.DATABASE_URL)
        
        # Connect to default 'postgres' database to create 'cerebro' if needed
        postgres_url = f"postgresql://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port or 5432}/postgres"
        
        conn = psycopg.connect(postgres_url, autocommit=True)
        cursor = conn.cursor()
        
        # Check if cerebro database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'cerebro'")
        exists = cursor.fetchone()
        
        if not exists:
            print("📊 Creating 'cerebro' database...")
            cursor.execute("CREATE DATABASE cerebro")
            print("✅ Database 'cerebro' created")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"⚠️  Database creation check: {e}")
        # Continue anyway - database might already exist
    
    # Create pgvector extension
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
