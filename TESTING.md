# Testing Guide

## Overview

This guide provides comprehensive testing instructions for the Parser Potato REST API built with Java Spring Boot.

---

## Prerequisites

- Java 25.0.1+
- Maven 3.9.12+
- PostgreSQL 17
- Sample test files in `sample_files/` directory

---

## Quick Start Testing

### 1. Start the Application

```bash
# Using Maven
mvn spring-boot:run

# Or using the JAR
mvn clean package
java -jar target/parser-potato-1.0.0.jar
```

### 2. Verify Application is Running

```bash
# Health check
curl http://localhost:8000/api/health

# Expected response:
# {"status":"healthy"}
```

### 3. Access Swagger UI

Open your browser: **http://localhost:8000/swagger-ui/index.html/**

This provides interactive API documentation where you can test all endpoints.

---

## Testing Approaches

### 1. Interactive Testing (Swagger UI)

**Best for:** Quick manual testing and exploration

1. Navigate to http://localhost:8000/swagger-ui/index.html/
2. Click on **POST /api/upload**
3. Click **Try it out**
4. Choose a file from `sample_files/` directory
5. Click **Execute**
6. Review the response

### 2. Command Line Testing (curl)

**Best for:** Automated scripts and CI/CD

#### Upload Customers
```bash
curl -X POST "http://localhost:8000/api/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_files/customers.csv"
```

#### Upload Products
```bash
curl -X POST "http://localhost:8000/api/upload" \
  -F "file=@sample_files/products.csv"
```

#### Upload Orders
```bash
curl -X POST "http://localhost:8000/api/upload" \
  -F "file=@sample_files/orders.csv"
```

#### Upload Order Items
```bash
curl -X POST "http://localhost:8000/api/upload" \
  -F "file=@sample_files/order_items.csv"
```

#### Upload Mixed Data (JSON)
```bash
curl -X POST "http://localhost:8000/api/upload" \
  -F "file=@sample_files/mixed_data.json"
```

### 3. Programmatic Testing (Java)

**Best for:** Integration tests

```java
@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
@AutoConfigureMockMvc
class FileUploadIntegrationTest {
    
    @Autowired
    private MockMvc mockMvc;
    
    @Test
    void testUploadCsvFile() throws Exception {
        MockMultipartFile file = new MockMultipartFile(
            "file",
            "customers.csv",
            "text/csv",
            "customer_id,name,email\nC001,Test,test@example.com".getBytes()
        );
        
        mockMvc.perform(multipart("/api/upload").file(file))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.message").value("File processed successfully"))
            .andExpect(jsonPath("$.customersCreated").value(1));
    }
}
```

---

## Unit Testing

### Running Tests

```bash
# Run all unit tests
mvn test

# Run specific test class
mvn test -Dtest=FileParserServiceTest

# Run with coverage
mvn test jacoco:report
```

### Test Structure

```
src/test/java/com/parserpotato/
├── service/
│   ├── FileParserServiceTest.java      # CSV/JSON parsing tests
│   └── DataLoaderServiceTest.java       # Validation and loading tests
├── controller/
│   └── UploadControllerTest.java        # API endpoint tests
└── integration/
    └── FileUploadIntegrationTest.java   # End-to-end tests
```

### Example Unit Test

```java
@ExtendWith(MockitoExtension.class)
class FileParserServiceTest {
    
    @InjectMocks
    private FileParserService fileParserService;
    
    @Test
    void testDetectFileType() {
        assertEquals("csv", fileParserService.detectFileType("test.csv"));
        assertEquals("json", fileParserService.detectFileType("test.json"));
    }
    
    @Test
    void testDetectInvalidFileType() {
        assertThrows(IllegalArgumentException.class, () -> {
            fileParserService.detectFileType("test.txt");
        });
    }
}
```

---

## Integration Testing

### Setup Test Database

```bash
# Create test database
psql -U postgres -c "CREATE DATABASE parser_potato_test;"
```

### Configure Test Properties

Create `src/test/resources/application-test.properties`:

```properties
spring.datasource.url=jdbc:postgresql://localhost:5432/parser_potato_test
spring.jpa.hibernate.ddl-auto=create-drop
```

### Run Integration Tests

```bash
# Run all tests including integration
mvn verify

# Run only integration tests
mvn test -Dtest=*IntegrationTest
```

---

## Expected Responses

### Successful Upload

```json
{
  "message": "File processed successfully",
  "recordsProcessed": 5,
  "successRowsCount": 5,
  "skippedRowsCount": 0,
  "customersCreated": 5,
  "productsCreated": 0,
  "ordersCreated": 0,
  "orderItemsCreated": 0,
  "errors": []
}
```

### Upload with Errors

```json
{
  "message": "File processed successfully",
  "recordsProcessed": 10,
  "successRowsCount": 8,
  "skippedRowsCount": 2,
  "customersCreated": 8,
  "productsCreated": 0,
  "ordersCreated": 0,
  "orderItemsCreated": 0,
  "errors": [
    "Row 3: Email must be valid",
    "Row 7: Customer ID is required"
  ]
}
```

---

## Database Verification

After uploading files, verify data in PostgreSQL:

```bash
psql parser_potato
```

```sql
-- Check record counts
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

---

## Error Testing

### 1. Invalid File Type

```bash
echo "test content" > test.txt
curl -X POST "http://localhost:8000/api/upload" -F "file=@test.txt"
```

**Expected:** 400 Bad Request - "Unsupported file type"

### 2. Invalid Email

Create `invalid_customer.csv`:
```csv
customer_id,name,email
C001,Test User,invalid-email
```

**Expected:** Error in response: "Row 1: Email must be valid"

### 3. Missing Required Field

Create `missing_field.csv`:
```csv
customer_id,name
C001,Test User
```

**Expected:** Error: "Row 1: Email is required"

### 4. Invalid Foreign Key

Create `invalid_order.csv`:
```csv
order_id,customer_id,order_date,status,total_amount
O001,C999,2024-01-01 10:00:00,pending,100.0
```

**Expected:** Error: "Order O001 references non-existent customer: C999"

---

## Performance Testing

### Generate Large Test File

```java
// Create a simple Java program to generate test data
import java.io.*;

public class GenerateLargeCSV {
    public static void main(String[] args) throws IOException {
        try (PrintWriter writer = new PrintWriter("large_customers.csv")) {
            writer.println("customer_id,name,email,phone,address");
            
            for (int i = 0; i < 100000; i++) {
                writer.printf("C%06d,Customer %d,customer%d@example.com,555-%04d,%d Test St%n",
                    i, i, i, i, i);
            }
        }
        System.out.println("Generated large_customers.csv with 100,000 records");
    }
}
```

### Upload and Measure

```bash
# Time the upload
time curl -X POST "http://localhost:8000/api/upload" \
  -F "file=@large_customers.csv"
```

### Expected Performance

| File Size | Records | Processing Time | Throughput |
|-----------|---------|-----------------|------------|
| < 1 MB | < 1,000 | < 1 second | 1,000+ rec/sec |
| 1-10 MB | 1K-10K | 1-5 seconds | 2,000+ rec/sec |
| 10-100 MB | 10K-100K | 5-30 seconds | 2,500+ rec/sec |
| > 100 MB | > 100K | 30+ seconds | 2,500+ rec/sec |

**Note:** Memory usage remains constant due to streaming processing.

---

## Monitoring

### Application Logs

```bash
# View logs while running
mvn spring-boot:run

# Or tail log file
tail -f logs/parser-potato.log
```

### JVM Monitoring

```bash
# Monitor with JConsole
jconsole

# Monitor with VisualVM
visualvm
```

### Metrics Endpoint (if Actuator enabled)

```bash
curl http://localhost:8000/actuator/health
curl http://localhost:8000/actuator/metrics
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Error
```
Error: Unable to connect to database
```

**Solutions:**
- Ensure PostgreSQL is running: `pg_ctl status`
- Check `.env` file has correct credentials
- Verify database exists: `psql -l`
- Test connection: `psql parser_potato`

#### 2. Port Already in Use
```
Error: Port 8000 is already in use
```

**Solutions:**
- Stop the existing application
- Or change port in `application.properties`:
  ```properties
  server.port=8080
  ```

#### 3. Maven Build Fails
```
Error: Maven build failed
```

**Solutions:**
- Verify Java version: `java -version`
- Clean and rebuild: `mvn clean install`
- Check Maven version: `mvn -version`

#### 4. Lombok Annotations Not Working
```
Error: Cannot find symbol: method getName()
```

**Solutions:**
- Ensure IDE has Lombok plugin installed
- Rebuild project: `mvn clean compile`
- Check annotation processor is enabled

### Enable Debug Logging

Update `application.properties`:

```properties
logging.level.com.parserpotato=DEBUG
logging.level.org.springframework.web=DEBUG
```

---

## CI/CD Testing

### GitHub Actions Example

```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:17
        env:
          POSTGRES_DB: parser_potato_test
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up JDK 25
        uses: actions/setup-java@v2
        with:
          java-version: '25'
          
      - name: Run tests
        run: mvn clean verify
        env:
          DATABASE_URL: jdbc:postgresql://localhost:5432/parser_potato_test?user=postgres&password=postgres
```

---

## Best Practices

1. **Always test with small files first** before large files
2. **Use Swagger UI** for interactive testing during development
3. **Write unit tests** for new features
4. **Run integration tests** before committing
5. **Monitor memory usage** during large file uploads
6. **Check database** after uploads to verify data integrity
7. **Test error cases** to ensure proper error handling
8. **Use test database** separate from development/production

---

## Summary

- ✅ **Swagger UI**: Interactive testing at `/swagger-ui/`
- ✅ **Unit Tests**: `mvn test`
- ✅ **Integration Tests**: `mvn verify`
- ✅ **Performance Tests**: Use large generated files
- ✅ **Database Verification**: Query PostgreSQL after uploads
- ✅ **Error Testing**: Test invalid inputs and edge cases

For more information, see:
- [README.md](README.md) - Setup and installation
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [EFFICIENCY_DESIGN.md](EFFICIENCY_DESIGN.md) - Performance details
