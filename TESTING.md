# Testing Guide

This document describes how to test the Parser Potato API.

## Quick Tests (No Database Required)

Run the following tests to verify the application structure and logic without needing a database:

### 1. Test Imports
```bash
pipenv run python test_imports.py
```

This verifies:
- All modules can be imported successfully
- File type detection works
- Schema validation works

### 2. Test File Parser
```bash
pipenv run python test_parser.py
```

This verifies:
- CSV parsing with streaming
- JSON parsing with streaming
- Record chunking for batch processing

### 3. Test Data Loader
```bash
pipenv run python test_data_loader.py
```

This verifies:
- Automatic table type identification
- Data preparation and type conversion
- Record categorization logic

## Full API Testing (Requires Database)

### Prerequisites

1. Install and run PostgreSQL 17
2. Create a database:
   ```bash
   createdb parser_potato
   ```
3. Configure your `.env` file:
   ```bash
   cp .env.example .env
   # Edit .env and set DATABASE_URL to your PostgreSQL connection string
   ```

### Start the Server

```bash
pipenv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Access the API Documentation

Open your browser and go to:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Test File Upload

#### Using the Swagger UI

1. Go to http://localhost:8000/docs
2. Click on the POST `/api/upload` endpoint
3. Click "Try it out"
4. Upload one of the sample files from the `sample_files/` directory
5. Click "Execute"
6. Review the response

#### Using curl

**Upload customers:**
```bash
curl -X POST "http://localhost:8000/api/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_files/customers.csv"
```

**Upload products:**
```bash
curl -X POST "http://localhost:8000/api/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_files/products.csv"
```

**Upload orders:**
```bash
curl -X POST "http://localhost:8000/api/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_files/orders.csv"
```

**Upload order items:**
```bash
curl -X POST "http://localhost:8000/api/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_files/order_items.csv"
```

**Upload mixed data (JSON):**
```bash
curl -X POST "http://localhost:8000/api/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_files/mixed_data.json"
```

#### Using Python

```python
import requests

# Upload a CSV file
with open('sample_files/customers.csv', 'rb') as f:
    files = {'file': ('customers.csv', f, 'text/csv')}
    response = requests.post('http://localhost:8000/api/upload', files=files)
    print(response.json())

# Upload a JSON file
with open('sample_files/mixed_data.json', 'rb') as f:
    files = {'file': ('mixed_data.json', f, 'application/json')}
    response = requests.post('http://localhost:8000/api/upload', files=files)
    print(response.json())
```

### Expected Response

```json
{
  "message": "File processed successfully",
  "records_processed": 5,
  "customers_created": 5,
  "products_created": 0,
  "orders_created": 0,
  "order_items_created": 0,
  "errors": []
}
```

## Testing Large Files

### Generate a Large CSV File

Create a script to generate a large test file:

```python
import csv

# Generate 100,000 customer records
with open('large_customers.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['customer_id', 'name', 'email', 'phone', 'address'])
    
    for i in range(100000):
        writer.writerow([
            f'C{i:06d}',
            f'Customer {i}',
            f'customer{i}@example.com',
            f'555-{i:04d}',
            f'{i} Test Street'
        ])

print("Generated large_customers.csv with 100,000 records")
```

Then upload it:

```bash
curl -X POST "http://localhost:8000/api/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@large_customers.csv"
```

### Monitor Performance

You can monitor the application's memory usage and processing time:

```bash
# Monitor with time
time curl -X POST "http://localhost:8000/api/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@large_customers.csv"
```

## Verify Database Contents

After uploading files, verify the data in PostgreSQL:

```bash
psql parser_potato
```

```sql
-- Check counts
SELECT 'customers' as table_name, COUNT(*) as count FROM customers
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'orders', COUNT(*) FROM orders
UNION ALL
SELECT 'order_items', COUNT(*) FROM order_items;

-- View sample data
SELECT * FROM customers LIMIT 5;
SELECT * FROM products LIMIT 5;
SELECT * FROM orders LIMIT 5;
SELECT * FROM order_items LIMIT 5;

-- Test relationships
SELECT 
    o.order_id,
    c.name as customer_name,
    o.total_amount,
    COUNT(oi.id) as item_count
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
LEFT JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY o.order_id, c.name, o.total_amount;
```

## Error Testing

### Test Invalid Files

1. **Wrong file type:**
   ```bash
   echo "test" > test.txt
   curl -X POST "http://localhost:8000/api/upload" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@test.txt"
   ```
   Expected: 400 error with message about unsupported file type

2. **Invalid data:**
   Create a CSV with invalid email:
   ```csv
   customer_id,name,email
   C001,Test User,invalid-email
   ```
   Expected: Errors array in response with validation details

3. **Missing required fields:**
   ```csv
   customer_id,name
   C001,Test User
   ```
   Expected: Errors about missing required field (email)

4. **Invalid foreign key:**
   ```csv
   order_id,customer_id,order_date,status,total_amount
   O999,C999,2024-01-01,pending,100.0
   ```
   Expected: Error about non-existent customer

## Performance Benchmarks

Expected performance on standard hardware:

- **Small files** (<1MB, <1000 records): < 1 second
- **Medium files** (1-10MB, 1K-10K records): 1-5 seconds
- **Large files** (10-100MB, 10K-100K records): 5-30 seconds
- **Very large files** (>100MB, >100K records): 30+ seconds

Memory usage should remain constant regardless of file size due to streaming processing.

## Troubleshooting

### Common Issues

1. **Database connection error:**
   - Ensure PostgreSQL is running
   - Check DATABASE_URL in .env file
   - Verify database exists

2. **Import errors:**
   - Run `pipenv install`
   - Ensure you're using Python 3.12+

3. **File upload fails:**
   - Check file format (CSV or JSON)
   - Verify file encoding is UTF-8
   - Check file size (default max: 100MB)

### Enable Debug Logging

Set logging level to DEBUG in `app/main.py`:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```
