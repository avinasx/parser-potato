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
log_level_str = os.getenv('LOG_LEVEL', DEFAULT_LOG_LEVEL).upper()
# Validate log level and fallback to default if invalid
try:
    log_level = getattr(logging, log_level_str)
except AttributeError:
    log_level = getattr(logging, DEFAULT_LOG_LEVEL)
    
logging.basicConfig(
    level=log_level,
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


from fastapi.responses import HTMLResponse
import markdown

# ... existing imports ...

# Documentation Configuration
DOCS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ALLOWED_DOCS = {
    "README.md": "Project Overview and Setup",
    "ARCHITECTURE.md": "System Architecture",
    "TESTING.md": "Testing Strategy",
    "EFFICIENCY_DESIGN.md": "Efficiency & Design",
    "IMPLEMENTATION_SUMMARY.md": "Implementation Summary"
}

# Create FastAPI app
app = FastAPI(
    title="Parser Potato API",
    description="""
REST API for uploading and parsing large CSV/JSON files into a PostgreSQL database.

## Documentation

* <a href="/docs/static/README.md" target="_blank">Project Overview (README)</a>
* <a href="/docs/static/ARCHITECTURE.md" target="_blank">System Architecture</a>
* <a href="/docs/static/EFFICIENCY_DESIGN.md" target="_blank">Efficiency & Design</a>
* <a href="/docs/static/TESTING.md" target="_blank">Testing Guide</a>
* <a href="/docs/static/IMPLEMENTATION_SUMMARY.md" target="_blank">Implementation Summary</a>

## Features
[Please install postgress and provide the link in .env file]
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


**Document Version:** 1.0  
**Last Updated:** December 2025  
**Author:** [avinasx](https://github.com/avinasx)
""",
    version="1.0.0",
    lifespan=lifespan
)

# ... middleware ...

@app.get("/docs/static/{filename}", response_class=HTMLResponse)
async def get_doc_file(filename: str):
    """Serve static documentation files as HTML"""
    if filename not in ALLOWED_DOCS:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = os.path.join(DOCS_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on server")
        
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    html_content = markdown.markdown(content, extensions=['fenced_code', 'tables', 'nl2br'])
    
    # Add some basic styling
    styled_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{ALLOWED_DOCS[filename]}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                line-height: 1.6;
                max-width: 900px;
                margin: 0 auto;
                padding: 40px 20px;
                color: #24292e;
                background-color: #ffffff;
            }}
            h1, h2, h3, h4, h5, h6 {{
                margin-top: 24px;
                margin-bottom: 16px;
                font-weight: 600;
                line-height: 1.25;
            }}
            h1 {{ font-size: 2em; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }}
            h2 {{ font-size: 1.5em; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }}
            h3 {{ font-size: 1.25em; }}
            p {{ margin-top: 0; margin-bottom: 16px; }}
            a {{ color: #0366d6; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            pre {{
                padding: 16px;
                overflow: auto;
                font-size: 85%;
                line-height: 1.45;
                background-color: #f6f8fa;
                border-radius: 6px;
            }}
            code {{
                padding: 0.2em 0.4em;
                margin: 0;
                font-size: 85%;
                background-color: rgba(27,31,35,0.05);
                border-radius: 3px;
                font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            }}
            pre code {{
                display: inline;
                padding: 0;
                margin: 0;
                overflow: visible;
                line-height: inherit;
                word-wrap: normal;
                background-color: transparent;
                border: 0;
            }}
            table {{
                display: block;
                width: 100%;
                overflow: auto;
                margin-top: 0;
                margin-bottom: 16px;
                border-spacing: 0;
                border-collapse: collapse;
            }}
            table tr {{
                background-color: #fff;
                border-top: 1px solid #c6cbd1;
            }}
            table tr:nth-child(2n) {{
                background-color: #f6f8fa;
            }}
            table th, table td {{
                padding: 6px 13px;
                border: 1px solid #dfe2e5;
            }}
            table th {{
                font-weight: 600;
            }}
            blockquote {{
                padding: 0 1em;
                color: #6a737d;
                border-left: 0.25em solid #dfe2e5;
                margin: 0;
            }}
            ul, ol {{ padding-left: 2em; margin-bottom: 16px; }}
            img {{ max-width: 100%; box-sizing: content-box; background-color: #fff; }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
        
    return HTMLResponse(content=styled_html)

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
