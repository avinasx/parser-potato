"""Main FastAPI application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from contextlib import asynccontextmanager

from app.database import init_db
from app.api.upload import router as upload_router

# Default constants
DEFAULT_LOG_LEVEL = 'INFO'

# Configure logging
log_level = os.getenv('LOG_LEVEL', DEFAULT_LOG_LEVEL).upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info("Starting application...")
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")


# Create FastAPI app
app = FastAPI(
    title="Parser Potato API",
    description="""
    REST API for uploading and parsing large CSV/JSON files into a PostgreSQL database.
    
    ## Features
    
    * **File Upload**: Upload CSV or JSON files
    * **Streaming Parser**: Process large files without loading them entirely in memory
    * **Data Validation**: Schema and data quality validation
    * **Multi-Table Support**: Automatically map data to related database tables
    * **Batch Processing**: Efficient batch insertion for large datasets
    * **Relationship Validation**: Verify foreign key relationships before insertion
    
    ## Supported Tables
    
    * **Customers**: customer_id, name, email, phone, address
    * **Products**: product_id, name, price, description, category, stock_quantity
    * **Orders**: order_id, customer_id, order_date, status, total_amount
    * **Order Items**: order_id, product_id, quantity, unit_price, subtotal
    """,
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload_router, prefix="/api", tags=["Upload"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Parser Potato API",
        "docs_url": "/docs",
        "health_check": "/api/health"
    }
