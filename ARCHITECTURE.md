# Architecture Documentation

## Overview

Parser Potato is a high-performance REST API built with FastAPI for processing large CSV/JSON files and loading data into a PostgreSQL database. The application uses streaming processing to handle files of any size without memory overflow.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                          │
│  (HTTP Clients, Web Browser, curl, Python requests, etc.)   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                      │
│                      (app/main.py)                          │
│  - CORS Middleware                                          │
│  - Lifespan Management                                      │
│  - Auto-generated OpenAPI docs                              │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Endpoints                           │
│                   (app/api/upload.py)                       │
│  - POST /api/upload   : File upload and processing          │
│  - GET  /api/health   : Health check                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
         ┌────────────┴────────────┐
         ▼                         ▼
┌──────────────────┐      ┌──────────────────┐
│  File Parser     │      │  Data Loader     │
│  Service         │      │  Service         │
│  (streaming)     │      │  (validation)    │
└────────┬─────────┘      └────────┬─────────┘
         │                         │
         │  Records (streamed)     │  Validated Data
         │                         │
         └────────────┬────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   Database Layer                             │
│              (PostgreSQL 17 + SQLAlchemy)                   │
│  - Async I/O with asyncpg                                   │
│  - Connection pooling                                        │
│  - Batch insertions                                          │
│  - Transaction management                                    │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
parser-potato/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entry point
│   ├── database.py              # Database configuration and session management
│   ├── api/
│   │   ├── __init__.py
│   │   └── upload.py            # Upload endpoint handlers
│   ├── models/
│   │   └── __init__.py          # SQLAlchemy database models
│   ├── schemas/
│   │   └── __init__.py          # Pydantic validation schemas
│   └── services/
│       ├── __init__.py
│       ├── file_parser.py       # Streaming file parser service
│       └── data_loader.py       # Data validation and loading service
├── sample_files/                # Sample CSV/JSON files for testing
│   ├── customers.csv
│   ├── products.csv
│   ├── orders.csv
│   ├── order_items.csv
│   └── mixed_data.json
├── requirements.txt             # Python dependencies
├── .env.example                # Environment variables template
├── README.md                   # Project documentation
├── TESTING.md                  # Testing guide
└── ARCHITECTURE.md             # This file
```

## Component Details

### 1. FastAPI Application (app/main.py)

**Responsibilities:**
- Application initialization and configuration
- Middleware setup (CORS)
- Route registration
- Database initialization on startup
- OpenAPI documentation generation

**Key Features:**
- Async lifespan management for startup/shutdown events
- Auto-generated Swagger UI at `/docs`
- Auto-generated ReDoc at `/redoc`

### 2. Database Layer (app/database.py)

**Responsibilities:**
- Database connection management
- Session factory creation
- Dependency injection for database sessions
- Table initialization

**Key Features:**
- Async database engine using `asyncpg`
- Connection pooling for performance
- Context manager for automatic session cleanup

**Database Models:**

```python
Customer
  ├── id (PK)
  ├── customer_id (unique, indexed)
  ├── name
  ├── email
  ├── phone
  ├── address
  └── orders (relationship)

Product
  ├── id (PK)
  ├── product_id (unique, indexed)
  ├── name
  ├── price
  ├── description
  ├── category
  ├── stock_quantity
  └── order_items (relationship)

Order
  ├── id (PK)
  ├── order_id (unique, indexed)
  ├── customer_id (FK)
  ├── order_date
  ├── status
  ├── total_amount
  ├── customer (relationship)
  └── order_items (relationship)

OrderItem
  ├── id (PK)
  ├── order_id (FK)
  ├── product_id (FK)
  ├── quantity
  ├── unit_price
  ├── subtotal
  ├── order (relationship)
  └── product (relationship)
```

### 3. API Endpoints (app/api/upload.py)

#### POST /api/upload

**Request:**
- Content-Type: `multipart/form-data`
- Parameter: `file` (CSV or JSON)

**Response:**
```json
{
  "message": "File processed successfully",
  "records_processed": 1000,
  "customers_created": 250,
  "products_created": 150,
  "orders_created": 300,
  "order_items_created": 300,
  "errors": ["error1", "error2"]
}
```

**Processing Flow:**
1. Validate file type (CSV/JSON)
2. Stream records from file
3. Process in chunks of 1000 records
4. Validate and categorize each chunk
5. Verify foreign key relationships
6. Insert data in batches
7. Return summary with counts and errors

### 4. File Parser Service (app/services/file_parser.py)

**Responsibilities:**
- File type detection
- Streaming CSV parsing
- Streaming JSON parsing (array and NDJSON)
- Chunking records for batch processing

**Key Methods:**

```python
detect_file_type(filename: str) -> str
    # Returns 'csv' or 'json'

parse_csv_streaming(file: UploadFile) -> AsyncGenerator[Dict, None]
    # Yields CSV records one by one without loading entire file

parse_json_streaming(file: UploadFile) -> AsyncGenerator[Dict, None]
    # Yields JSON records one by one
    # Supports both JSON arrays and NDJSON format

chunk_records(records: AsyncGenerator, chunk_size: int) -> AsyncGenerator[List[Dict], None]
    # Groups records into chunks for batch processing
```

**Performance Optimization:**
- Uses Python's built-in `csv.DictReader` for efficient CSV parsing
- Uses streaming JSON parsing to avoid memory overflow
- Processes files in chunks to minimize memory footprint
- Default chunk size: 1000 records

### 5. Data Loader Service (app/services/data_loader.py)

**Responsibilities:**
- Table type identification
- Data validation using Pydantic schemas
- Data preparation and type conversion
- Foreign key relationship verification
- Batch database insertion
- Error tracking and reporting

**Key Methods:**

```python
identify_table_type(record: Dict) -> str
    # Identifies target table based on record fields
    # Returns: 'customer', 'product', 'order', or 'order_item'

validate_and_categorize_records(records: List[Dict]) -> Dict
    # Validates and categorizes records by table type
    # Returns: {'customers': [...], 'products': [...], ...}

verify_relationships(categorized: Dict) -> bool
    # Verifies foreign key relationships exist
    # Checks customer_id references, product_id references, etc.

load_data_batch(categorized: Dict) -> Tuple[int, int, int, int]
    # Inserts data in correct order (customers → products → orders → order_items)
    # Returns counts of inserted records
```

**Validation Features:**
- Email format validation
- Required field checking
- Data type validation and conversion
- Business rule validation (e.g., price > 0, quantity > 0)
- Foreign key constraint validation

### 6. Pydantic Schemas (app/schemas/__init__.py)

**Purpose:**
- Define data validation rules
- Ensure data quality before database insertion
- Provide type hints and auto-completion

**Schemas:**
- `CustomerSchema`: Customer data validation
- `ProductSchema`: Product data validation
- `OrderSchema`: Order data validation
- `OrderItemSchema`: Order item data validation
- `UploadResponse`: API response format

## Data Flow

### Upload and Processing Flow

```
1. File Upload
   │
   ├─> File Type Detection
   │
2. Streaming Parser
   │
   ├─> Parse CSV/JSON without full load
   │   (yields records one by one)
   │
3. Chunk Aggregator
   │
   ├─> Group into batches of 1000
   │
4. For Each Chunk:
   │
   ├─> Identify Table Type
   │   (customer, product, order, order_item)
   │
   ├─> Validate Schema
   │   (required fields, data types, formats)
   │
   ├─> Categorize Records
   │   (group by table type)
   │
   ├─> Verify Relationships
   │   (check foreign key references)
   │
   ├─> Batch Insert
   │   (customers → products → orders → order_items)
   │
   └─> Track Errors
       (row-level error messages)
   
5. Return Summary
   (counts and errors)
```

## Performance Characteristics

### Memory Usage

- **Constant Memory**: O(chunk_size)
- File size doesn't affect memory usage
- Default chunk size: 1000 records
- Memory per chunk: ~1-10 MB (depending on record size)

### Time Complexity

- **File Parsing**: O(n) where n = number of records
- **Validation**: O(n) per record
- **Database Insertion**: O(n/chunk_size) transactions
- **Relationship Verification**: O(n) with indexed lookups

### Database Performance

- **Batch Inserts**: Reduces round trips to database
- **Indexed Foreign Keys**: Fast relationship lookups
- **Async I/O**: Non-blocking database operations
- **Connection Pooling**: Reuses connections efficiently

### Scalability

- Can handle files of any size (tested up to 100K+ records)
- Horizontal scaling: Deploy multiple instances behind load balancer
- Vertical scaling: Increase chunk size for more memory
- Database scaling: PostgreSQL replication and partitioning

## Error Handling

### Validation Errors

- Collected per row with row number
- Non-blocking: continues processing valid records
- Returned in response up to 100 errors
- Logged for debugging

### Database Errors

- Transaction rollback on critical errors
- Duplicate key handling: silently skip existing records
- Foreign key violations: tracked as errors
- Connection errors: propagated to client

### File Processing Errors

- Invalid file type: 400 Bad Request
- Malformed CSV/JSON: detailed error message
- Encoding issues: UTF-8 required
- Empty files: accepted but no records processed

## Security Considerations

### Input Validation

- File type whitelist (CSV, JSON only)
- Schema validation for all fields
- SQL injection prevention (parameterized queries)
- XSS prevention (no HTML rendering)

### Database Security

- Connection string in environment variables
- Password not in source code
- Use of async SQLAlchemy ORM (prevents SQL injection)
- Prepared statements for all queries

### Resource Limits

- File size limits (configurable, default: unlimited but chunked)
- Request timeout (configured by server)
- Database connection pool limits
- Memory limits through chunking

## Monitoring and Observability

### Logging

- Application logs: startup, shutdown, errors
- Request logs: file uploads, processing time
- Database logs: queries, connection issues
- Error logs: validation failures, exceptions

### Metrics to Track

- Upload count per day
- Average processing time
- Records processed per second
- Error rate
- Database connection pool usage
- Memory usage per request

### Health Check

- GET `/api/health` endpoint
- Returns `{"status": "healthy"}`
- Can be extended to check database connectivity

## Extension Points

### Adding New Table Types

1. Create new SQLAlchemy model in `app/models/__init__.py`
2. Create Pydantic schema in `app/schemas/__init__.py`
3. Add identification logic in `DataLoaderService.identify_table_type()`
4. Add preparation method in `DataLoaderService`
5. Update insertion order in `load_data_batch()`

### Adding New File Formats

1. Implement parser in `FileParserService`
2. Add file type detection logic
3. Implement streaming generator method
4. Update documentation

### Adding Authentication

1. Add auth middleware to `app/main.py`
2. Protect endpoints with dependencies
3. Update OpenAPI schema
4. Add user management

### Adding Rate Limiting

1. Add rate limiting middleware
2. Configure limits per endpoint
3. Return 429 Too Many Requests
4. Add retry-after header

## Testing Strategy

### Unit Tests

- File parser: CSV, JSON, NDJSON
- Data loader: categorization, validation
- Schema validation: all models
- Database models: relationships

### Integration Tests

- End-to-end file upload
- Database insertion verification
- Error handling scenarios
- Large file processing

### Performance Tests

- Load testing with large files
- Concurrent upload testing
- Memory usage profiling
- Database query performance

## Deployment

### Development

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production

```bash
# Using Gunicorn with Uvicorn workers
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 300
```

### Docker

```dockerfile
FROM python:3.14-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY .env .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `CHUNK_SIZE`: Number of records per batch (default: 1000)
- `LOG_LEVEL`: Logging level (default: INFO)

## Conclusion

Parser Potato provides a robust, scalable, and efficient solution for processing large CSV/JSON files and loading them into a PostgreSQL database. The streaming architecture ensures constant memory usage regardless of file size, while the async I/O and batch processing provide excellent performance characteristics.
