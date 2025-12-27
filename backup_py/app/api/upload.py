"""API endpoints for file upload and processing"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging

from app.database import get_db
from app.schemas import UploadResponse
from app.services.file_parser import FileParserService
from app.services.data_loader import DataLoaderService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload and process a CSV or JSON file.
    
    The file should contain data for one or more of the following tables:
    - Customers: customer_id, name, email, phone (optional), address (optional)
    - Products: product_id, name, price, description (optional), category (optional), stock_quantity (optional)
    - Orders: order_id, customer_id, order_date, status, total_amount
    - Order Items: order_id, product_id, quantity, unit_price, subtotal
    
    The system will automatically identify which table each record belongs to
    based on the fields present in the data.
    """
    logger.info(f"Processing file upload: {file.filename}")
    
    # Validate file type
    try:
        file_type = await FileParserService.detect_file_type(file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Initialize counters
    total_records = 0
    total_success_rows = 0
    total_skipped_rows = 0
    customers_created = 0
    products_created = 0
    orders_created = 0
    order_items_created = 0
    all_errors = []
    
    # Parse file and process in chunks
    parser = FileParserService()
    records_generator = parser.parse_file(file)
    chunks_generator = parser.chunk_records(records_generator)
    
    try:
        async for chunk in chunks_generator:
            total_records += len(chunk)
            logger.info(f"Processing chunk of {len(chunk)} records")
            
            # Create data loader for this chunk
            loader = DataLoaderService(db)
            
            # Validate and categorize records
            categorized = await loader.validate_and_categorize_records(chunk)
            
            # Verify relationships
            await loader.verify_relationships(categorized)
            
            # Load data if no errors
            if not loader.errors:
                try:
                    c_count, p_count, o_count, oi_count = await loader.load_data_batch(categorized)
                    customers_created += c_count
                    products_created += p_count
                    orders_created += o_count
                    order_items_created += oi_count
                except Exception as e:
                    logger.error(f"Error loading data batch: {str(e)}")
                    all_errors.append(f"Database error: {str(e)}")
            
            # Aggregate counts from this chunk
            total_success_rows += loader.success_rows
            total_skipped_rows += loader.skipped_rows
            
            # Collect errors from this chunk
            all_errors.extend(loader.errors)
    
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    
    return UploadResponse(
        message="File processed successfully" if not all_errors else "File processed with errors",
        records_processed=total_records,
        success_rows_count=total_success_rows,
        skipped_rows_count=total_skipped_rows,
        customers_created=customers_created,
        products_created=products_created,
        orders_created=orders_created,
        order_items_created=order_items_created,
        errors=all_errors[:100]  # Limit errors to first 100
    )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
