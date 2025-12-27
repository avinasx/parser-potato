# Parser Potato - CSV/JSON File Parser REST API

A high-performance REST API built with FastAPI for uploading and parsing large CSV/JSON files into a PostgreSQL database.

## Features

- **Streaming File Processing**: Handle large files efficiently without loading them entirely in memory
- **Multi-Format Support**: Process both CSV and JSON files (including NDJSON)
- **Multi-Table Architecture**: Automatically map data to related database tables (Customers, Products, Orders, Order Items)
- **Data Validation**: Comprehensive schema and data quality validation
- **Relationship Validation**: Verify foreign key relationships before insertion
- **Batch Processing**: Efficient batch insertion for optimal performance
- **Error Handling**: Detailed error reporting with row-level granularity

## Requirements

- Python 3.14+ (managed with pipenv)
- PostgreSQL 17
- FastAPI 0.127.0

## Documentation
[Install Postgress and provide the link in .env file]
- [Project Overview (README)](README.md)
- [System Architecture](ARCHITECTURE.md)
- [Efficiency & Design](EFFICIENCY_DESIGN.md)
- [Testing Guide](TESTING.md)
- [Implementation Summary](IMPLEMENTATION_SUMMARY.md)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/avinasx/parser-potato.git
cd parser-potato
```

2. Install pipenv (if not already installed):
```bash
pip install --user pipenv
```

3. Install dependencies and create virtual environment:
```bash
pipenv install
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and set your PostgreSQL connection string
```

Example `.env` file:
```
DATABASE_URL=postgresql://username:password@localhost:5432/parser_potato
```

## Database Setup

The application will automatically create the necessary tables on startup. Ensure your PostgreSQL server is running and the database exists.

## Database Schema

### Customers Table
- `customer_id` (String, Primary Key)
- `name` (String, Required)
- `email` (Email, Required)
- `phone` (String, Optional)
- `address` (Text, Optional)

### Products Table
- `product_id` (String, Primary Key)
- `name` (String, Required)
- `price` (Float, Required, > 0)
- `description` (Text, Optional)
- `category` (String, Optional)
- `stock_quantity` (Integer, Optional, >= 0)

### Orders Table
- `order_id` (String, Primary Key)
- `customer_id` (Foreign Key to Customers)
- `order_date` (DateTime, Required)
- `status` (String, Required: pending/processing/shipped/delivered/cancelled)
- `total_amount` (Float, Required, >= 0)

### Order Items Table
- `order_id` (Foreign Key to Orders)
- `product_id` (Foreign Key to Products)
- `quantity` (Integer, Required, > 0)
- `unit_price` (Float, Required, > 0)
- `subtotal` (Float, Required, >= 0)

## Running the Application

Start the server using pipenv:
```bash
pipenv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Alternatively, activate the pipenv shell and run directly:
```bash
pipenv shell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000

## API Endpoints

### POST /api/upload
Upload and process a CSV or JSON file.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: file (CSV or JSON)

**Response:**
```json
{
  "message": "File processed successfully",
  "records_processed": 1000,
  "success_rows_count": 950,
  "skipped_rows_count": 50,
  "customers_created": 250,
  "products_created": 150,
  "orders_created": 300,
  "order_items_created": 300,
  "errors": ["Row 10: Validation error - invalid email", "Row 25: Order O999 references non-existent customer"]
}
```

### GET /api/health
Health check endpoint.

## File Format Examples

### CSV Format

**customers.csv:**
```csv
customer_id,name,email,phone,address
C001,John Doe,john@example.com,555-0100,123 Main St
C002,Jane Smith,jane@example.com,555-0101,456 Oak Ave
```

**products.csv:**
```csv
product_id,name,price,description,category,stock_quantity
P001,Laptop,999.99,High-performance laptop,Electronics,50
P002,Mouse,29.99,Wireless mouse,Electronics,200
```

**orders.csv:**
```csv
order_id,customer_id,order_date,status,total_amount
O001,C001,2024-01-15 10:30:00,delivered,1029.98
O002,C002,2024-01-16 14:20:00,processing,29.99
```

**order_items.csv:**
```csv
order_id,product_id,quantity,unit_price,subtotal
O001,P001,1,999.99,999.99
O001,P002,1,29.99,29.99
O002,P002,1,29.99,29.99
```

### JSON Format

**data.json:**
```json
[
  {
    "customer_id": "C001",
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "555-0100",
    "address": "123 Main St"
  },
  {
    "product_id": "P001",
    "name": "Laptop",
    "price": 999.99,
    "description": "High-performance laptop",
    "category": "Electronics",
    "stock_quantity": 50
  },
  {
    "order_id": "O001",
    "customer_id": "C001",
    "order_date": "2024-01-15 10:30:00",
    "status": "delivered",
    "total_amount": 1029.98
  },
  {
    "order_id": "O001",
    "product_id": "P001",
    "quantity": 1,
    "unit_price": 999.99,
    "subtotal": 999.99
  }
]
```

## Design Highlights

### Efficient Architecture

1. **Streaming Processing**: Files are processed in chunks to avoid memory overflow
2. **Batch Insertion**: Records are inserted in batches of 1000 for optimal database performance
3. **Async I/O**: All database operations are asynchronous for better concurrency
4. **Connection Pooling**: SQLAlchemy manages database connections efficiently

For detailed documentation on how the streaming architecture efficiently handles large files without full in-memory loads, see [EFFICIENCY_DESIGN.md](EFFICIENCY_DESIGN.md).

### Data Flow

1. File upload → File type detection
2. Streaming parser → Yields records one by one
3. Chunk aggregator → Groups records into batches
4. Validator → Validates schema and data quality
5. Categorizer → Identifies target table for each record
6. Relationship validator → Verifies foreign key constraints
7. Batch loader → Inserts data in correct order (customers → products → orders → order_items)

### Error Handling

- Row-level error tracking with detailed error messages
- Transaction rollback on critical errors
- Detailed error messages with row numbers and reasons
- Continues processing valid records even if some fail
- Returns comprehensive statistics:
  - `success_rows_count`: Number of rows successfully processed
  - `skipped_rows_count`: Number of rows skipped due to validation/insertion errors
  - `errors`: Array of error messages with row numbers and reasons

## Testing

Use the interactive API documentation at http://localhost:8000/swagger-ui/index.html 
 to test file uploads.

Example using curl:
```bash
curl -X POST "http://localhost:8000/api/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@customers.csv"
```

## Performance Considerations

- Processes files in chunks of 1000 records
- Uses async database operations for I/O efficiency
- Minimizes memory usage by streaming file content
- Batch inserts reduce database round trips
- Proper indexing on foreign key columns for fast lookups

## License

MIT License
