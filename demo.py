"""
Demo script to showcase the Parser Potato API functionality

This script demonstrates:
1. How to use the file parser service
2. How to validate and categorize data
3. How the system handles different data types
"""
import asyncio
import sys
import os
from io import BytesIO

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.file_parser import FileParserService
from app.services.data_loader import DataLoaderService
from fastapi import UploadFile


async def demo_csv_processing():
    """Demonstrate CSV file processing"""
    print("=" * 70)
    print("DEMO 1: CSV File Processing")
    print("=" * 70)
    
    csv_content = b"""customer_id,name,email,phone,address
C001,John Doe,john@example.com,555-0100,123 Main St
C002,Jane Smith,jane@example.com,555-0101,456 Oak Ave
C003,Bob Johnson,bob@example.com,555-0102,789 Pine Rd"""
    
    file = UploadFile(filename="customers.csv", file=BytesIO(csv_content))
    
    print("\nInput CSV:")
    print(csv_content.decode('utf-8'))
    
    print("\nParsing records...")
    records = []
    async for record in FileParserService.parse_csv_streaming(file):
        records.append(record)
        print(f"  → Parsed: {record['name']} ({record['email']})")
    
    print(f"\n✓ Successfully parsed {len(records)} records from CSV")
    return records


async def demo_json_processing():
    """Demonstrate JSON file processing"""
    print("\n" + "=" * 70)
    print("DEMO 2: JSON File Processing")
    print("=" * 70)
    
    json_content = b"""[
  {"product_id": "P001", "name": "Laptop", "price": 999.99, "category": "Electronics", "stock_quantity": 50},
  {"product_id": "P002", "name": "Mouse", "price": 29.99, "category": "Electronics", "stock_quantity": 200},
  {"product_id": "P003", "name": "Keyboard", "price": 79.99, "category": "Electronics", "stock_quantity": 150}
]"""
    
    file = UploadFile(filename="products.json", file=BytesIO(json_content))
    
    print("\nInput JSON:")
    print(json_content.decode('utf-8'))
    
    print("\nParsing records...")
    records = []
    async for record in FileParserService.parse_json_streaming(file):
        records.append(record)
        print(f"  → Parsed: {record['name']} - ${record['price']}")
    
    print(f"\n✓ Successfully parsed {len(records)} records from JSON")
    return records


async def demo_mixed_data_processing():
    """Demonstrate processing mixed data types in one file"""
    print("\n" + "=" * 70)
    print("DEMO 3: Mixed Data Types (Auto-categorization)")
    print("=" * 70)
    
    mixed_content = b"""[
  {"customer_id": "C001", "name": "Alice", "email": "alice@example.com"},
  {"product_id": "P001", "name": "Laptop", "price": 999.99},
  {"order_id": "O001", "customer_id": "C001", "order_date": "2024-01-15 10:30:00", "status": "pending", "total_amount": 999.99},
  {"order_id": "O001", "product_id": "P001", "quantity": 1, "unit_price": 999.99, "subtotal": 999.99}
]"""
    
    file = UploadFile(filename="mixed.json", file=BytesIO(mixed_content))
    
    print("\nInput (mixed record types):")
    print(mixed_content.decode('utf-8'))
    
    print("\nParsing and categorizing...")
    records = []
    async for record in FileParserService.parse_json_streaming(file):
        records.append(record)
    
    # Create a mock loader (without database)
    class MockSession:
        async def execute(self, query):
            class Result:
                def fetchall(self):
                    return []
                def scalar_one_or_none(self):
                    return None
            return Result()
    
    loader = DataLoaderService(MockSession())
    categorized = await loader.validate_and_categorize_records(records)
    
    print("\nCategorization Results:")
    print(f"  → Customers: {len(categorized['customers'])}")
    print(f"  → Products: {len(categorized['products'])}")
    print(f"  → Orders: {len(categorized['orders'])}")
    print(f"  → Order Items: {len(categorized['order_items'])}")
    
    if loader.errors:
        print(f"\n⚠ Validation Errors: {len(loader.errors)}")
        for error in loader.errors[:5]:
            print(f"    - {error}")
    else:
        print("\n✓ All records validated successfully")
    
    return categorized


async def demo_chunking():
    """Demonstrate chunking for large files"""
    print("\n" + "=" * 70)
    print("DEMO 4: Chunking for Large Files")
    print("=" * 70)
    
    async def generate_large_dataset():
        """Generate a large dataset for demonstration"""
        for i in range(2500):
            yield {
                "customer_id": f"C{i:05d}",
                "name": f"Customer {i}",
                "email": f"customer{i}@example.com"
            }
    
    print("\nGenerating 2,500 customer records...")
    print("Processing in chunks of 1000...")
    
    chunk_num = 0
    total_records = 0
    async for chunk in FileParserService.chunk_records(generate_large_dataset(), chunk_size=1000):
        chunk_num += 1
        total_records += len(chunk)
        print(f"  → Chunk {chunk_num}: {len(chunk)} records")
    
    print(f"\n✓ Processed {total_records} records in {chunk_num} chunks")
    print("✓ Memory usage remains constant regardless of file size")


async def demo_validation():
    """Demonstrate data validation"""
    print("\n" + "=" * 70)
    print("DEMO 5: Data Validation")
    print("=" * 70)
    
    test_records = [
        # Valid customer
        {"customer_id": "C001", "name": "Valid User", "email": "valid@example.com"},
        # Invalid email
        {"customer_id": "C002", "name": "Invalid User", "email": "not-an-email"},
        # Missing required field
        {"customer_id": "C003", "name": "Incomplete User"},
        # Valid product
        {"product_id": "P001", "name": "Valid Product", "price": 99.99},
        # Invalid price (negative)
        {"product_id": "P002", "name": "Bad Product", "price": -10},
    ]
    
    print("\nValidating test records...")
    
    class MockSession:
        async def execute(self, query):
            class Result:
                def fetchall(self):
                    return []
                def scalar_one_or_none(self):
                    return None
            return Result()
    
    loader = DataLoaderService(MockSession())
    categorized = await loader.validate_and_categorize_records(test_records)
    
    valid_count = sum(len(v) for v in categorized.values())
    print(f"\n✓ Valid records: {valid_count}/{len(test_records)}")
    print(f"✗ Invalid records: {len(loader.errors)}")
    
    if loader.errors:
        print("\nValidation Errors:")
        for error in loader.errors:
            print(f"  - {error}")


async def main():
    """Run all demonstrations"""
    print("\n" + "=" * 70)
    print("PARSER POTATO - Feature Demonstration")
    print("=" * 70)
    
    try:
        await demo_csv_processing()
        await demo_json_processing()
        await demo_mixed_data_processing()
        await demo_chunking()
        await demo_validation()
        
        print("\n" + "=" * 70)
        print("ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("\nKey Features Demonstrated:")
        print("  ✓ Streaming CSV/JSON parsing")
        print("  ✓ Automatic table type detection")
        print("  ✓ Data validation and error handling")
        print("  ✓ Chunking for large files")
        print("  ✓ Memory-efficient processing")
        print("\nTo test with a real database, see TESTING.md")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
