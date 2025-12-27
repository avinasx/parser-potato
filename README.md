# Parser Potato - CSV/JSON File Parser REST API

A high-performance Spring Boot 4.0.1 REST API for uploading and parsing large CSV/JSON files into a PostgreSQL database. Supports streaming processing, multi-table relationships, data validation, and batch insertions.

## Features

- **Multi-format Support**: Parse CSV files and JSON files (arrays or NDJSON)
- **Streaming Processing**: Handle files of any size with constant memory usage
- **Multi-table Support**: Automatically categorize and insert data into related tables:
  - Customers, Products, Orders, Order Items
- **Data Validation**: Jakarta Bean Validation for data integrity
- **Relationship Validation**: Verify foreign key constraints before insertion
- **Batch Processing**: Efficient batch insertions with Hibernate
- **Error Tracking**: Detailed row-level error reporting
- **Interactive Documentation**: Swagger UI for easy API testing
- **Production Ready**: Connection pooling, transaction management, comprehensive logging

## Technology Stack

- **Java 25.0.1**
- **Spring Boot 4.0.1**
- **PostgreSQL 17**
- **Maven 3.9.12**
- **Apache Commons CSV 1.11.0** for CSV parsing
- **Jackson** for JSON parsing
- **Hibernate** for ORM
- **SpringDoc OpenAPI** for API documentation

## Prerequisites

- Java 25.0.1 or higher
- Maven 3.9.12 or higher
- PostgreSQL 17

## Quick Start

1. Clone and navigate to the project:
```bash
git clone <repository-url>
cd parser-potato
```

2. Verify prerequisites:
```bash
java -version  # Should show Java 25.0.1 or higher
mvn -version   # Should show Maven 3.9.12 or higher
```

3. **Configure Database (Local Development)**:

Parser Potato uses **Spring profiles** for configuration (Java standard).

**Step 1:** Copy the example file:
```bash
cp application-local.properties.example src/main/resources/application-local.properties
```

**Step 2:** Edit `src/main/resources/application-local.properties` with your database:
```properties
spring.datasource.url=jdbc:postgresql://your-host:5432/your-database?user=username&password=password&sslmode=require
app.chunk-size=1000
```

**Note:** `application-local.properties` is gitignored (safe for credentials).

4. **Run the Application**:

**Local Development (use `local` profile):**
```bash
# ⚠️ IMPORTANT: Always specify the 'local' profile
mvn spring-boot:run -Dspring-boot.run.profiles=local
```

**Production (use environment variable):**
```bash
export DATABASE_URL="jdbc:postgresql://..."
mvn clean package
java -jar target/parser-potato-1.0.0.jar
```

## Database Setup

The application will automatically create the necessary tables on startup using JPA/Hibernate. Ensure your PostgreSQL server is running:

```bash
# For local PostgreSQL (if needed)
psql -U postgres -c "CREATE DATABASE parser_potato;"
```

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
- `stock_quantity` (Integer, Optional)

### Orders Table
- `order_id` (String, Primary Key)
- `customer_id` (Foreign Key → Customers, Required)
- `order_date` (DateTime, Required)
- `status` (String, Required: pending/processing/completed/cancelled)
- `total_amount` (Float, Required, ≥ 0)

### Order Items Table
- `order_id` (Foreign Key → Orders, Required)
- `product_id` (Foreign Key → Products, Required)
- `quantity` (Integer, Required, > 0)
- `unit_price` (Float, Required, > 0)
- `subtotal` (Float, Required, ≥ 0)

## API Documentation

Once the application is running, you can access:

- **Swagger UI**: http://localhost:8000/swagger-ui/index.html/index.html
- **Health Check**: http://localhost:8000/api/health

## API Endpoints

### POST /api/upload

Upload and process a CSV or JSON file.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Parameter: `file` (CSV or JSON file)

**Response:**
```json
{
  "message": "File processed successfully",
  "recordsProcessed": 1000,
  "successRowsCount": 950,
  "skippedRowsCount": 50,
  "customersCreated": 250,
  "productsCreated": 200,
  "ordersCreated": 300,
  "orderItemsCreated": 200,
  "errors": [
    "Row 10: Email must be valid",
    "Row 25: Customer C999 not found"
  ]
}
```

### GET /api/health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

## File Format Examples

### CSV Format
```csv
customer_id,name,email,phone,address
C001,John Doe,john@example.com,555-1234,123 Main St
C002,Jane Smith,jane@example.com,555-5678,456 Oak Ave
```

### JSON Format (Array)
```json
[
  {
    "customer_id": "C001",
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "555-1234",
    "address": "123 Main St"
  },
  {
    "customer_id": "C002",
    "name": "Jane Smith",
    "email": "jane@example.com",
    "phone": "555-5678",
    "address": "456 Oak Ave"
  }
]
```

### JSON Format (NDJSON - Newline Delimited)
```json
{"customer_id":"C001","name":"John Doe","email":"john@example.com"}
{"customer_id":"C002","name":"Jane Smith","email":"jane@example.com"}
```

## Data Loading Order

The application automatically determines the correct insertion order based on foreign key relationships:

1. **Customers** (no dependencies)
2. **Products** (no dependencies)
3. **Orders** (depends on Customers)
4. **Order Items** (depends on Orders and Products)

## Validation Rules

### Email Validation
- Must be a valid email format

### Required Fields
- All primary keys must be provided
- Foreign keys must exist in referenced tables

### Business Rules
- Price and total_amount must be > 0
- Quantity must be > 0
- Status must be one of: pending, processing, completed, cancelled

## Features in Detail

### Streaming Processing
- Files are processed line-by-line
- Constant memory usage regardless of file size
- Uses Java Streams API for lazy evaluation

### Batch Processing
- Records processed in chunks of 1000 (configurable via `app.chunk-size`)
- Hibernate batch inserts for optimal performance
- Reduces database round trips

### Error Handling
- Row-level error tracking with specific messages
- Validation errors don't stop processing
- Returns comprehensive error list in response

### Duplicate Handling
- Checks for existing records by primary key
- Skips duplicates (counted as skipped, not errors)
- Existing records tracked separately from validation errors

## Performance

- **Streaming Processing**: Handles files of any size with constant memory usage
- **Batch Insertions**: Processes records in configurable batches (default: 1000)
- **Connection Pooling**: HikariCP for efficient database connections
- **Indexed Lookups**: Fast foreign key validation
- **Throughput**: ~2000-5000 records/second on standard hardware

## Testing

Use the Swagger UI at http://localhost:8000/swagger-ui/ to test file uploads interactively.

Example using curl:
```bash
curl -X POST "http://localhost:8000/api/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_files/customers.csv"
```

## Troubleshooting

### Common Issues

#### 1. "Failed to determine suitable jdbc url"

**Problem:** Running without the `local` profile.

**Error message:**
```
Failed to configure a DataSource: 'url' attribute is not specified
```

**Solution:**
```bash
# ✅ Correct - specify local profile
mvn spring-boot:run -Dspring-boot.run.profiles=local

# ❌ Wrong - missing profile
mvn spring-boot:run
```

#### 2. Application doesn't connect to database

**Problem:** `application-local.properties` not configured.

**Solution:**
```bash
# Create the file
cp application-local.properties.example src/main/resources/application-local.properties

# Edit with your database credentials
vim src/main/resources/application-local.properties
```

#### 3. Port 8000 already in use

**Problem:** Another instance is running.

**Solution:**
```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9

# Or change port in application.properties
server.port=8080
```

#### 4. Build fails with Lombok errors

**Problem:** IDE not configured for Lombok.

**Solution:**
```bash
# Clean and rebuild
mvn clean compile

# Ensure Lombok plugin is installed in your IDE
```

## Configuration

### Spring Profiles

**Local Development:**
- Profile: `local`
- Config file: `src/main/resources/application-local.properties`
- Usage: `mvn spring-boot:run -Dspring-boot.run.profiles=local`

**Production:**
- No profile needed
- Set `DATABASE_URL` environment variable
- Usage: `java -jar parser-potato.jar`

### Application Settings

Edit `application.properties` to configure:
- Server port (default: 8000)
- File upload limits (default: 1GB)
- Batch size (default: 1000)
- Logging levels

### Environment Variables

**Required for Production:**
```bash
DATABASE_URL=jdbc:postgresql://host:5432/database?user=username&password=password
```

**Optional:**
```bash
CHUNK_SIZE=1000
LOG_LEVEL=INFO
```

## Project Structure

```
parser-potato/
├── src/main/java/com/parserpotato/
│   ├── ParserPotatoApplication.java    # Main application
│   ├── model/                           # JPA entities
│   ├── repository/                      # Spring Data repositories
│   ├── dto/                             # Data transfer objects
│   ├── service/                         # Business logic
│   ├── controller/                      # REST endpoints
│   ├── config/                          # Configuration classes
│   └── exception/                       # Error handling
├── src/main/resources/
│   ├── application.properties           # Main configuration
│   └── application-local.properties     # Local dev config (gitignored)
├── sample_files/                        # Test data
├── pom.xml                              # Maven dependencies
└── README.md                            # This file
```

## License

MIT License

## Author

**avinasx** - [GitHub](https://github.com/avinasx)

---

**For detailed implementation information, see:**
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture and design
- [TESTING.md](TESTING.md) - Testing strategies and examples
- [EFFICIENCY_DESIGN.md](EFFICIENCY_DESIGN.md) - Performance optimization details
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Complete implementation summary


extra notes 
#### kill port 8000
lsof -ti:8000 | xargs kill -9