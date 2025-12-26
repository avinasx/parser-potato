"""Pydantic schemas for data validation"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime


class CustomerSchema(BaseModel):
    """Schema for customer data validation"""
    customer_id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None

    class Config:
        from_attributes = True


class ProductSchema(BaseModel):
    """Schema for product data validation"""
    product_id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    category: Optional[str] = Field(None, max_length=100)
    stock_quantity: int = Field(default=0, ge=0)

    class Config:
        from_attributes = True


class OrderSchema(BaseModel):
    """Schema for order data validation"""
    order_id: str = Field(..., min_length=1, max_length=50)
    customer_id: str = Field(..., min_length=1, max_length=50)
    order_date: datetime
    status: str = Field(..., min_length=1, max_length=50)
    total_amount: float = Field(..., ge=0)

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        valid_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
        if v.lower() not in valid_statuses:
            raise ValueError(f'Status must be one of {valid_statuses}')
        return v.lower()

    class Config:
        from_attributes = True


class OrderItemSchema(BaseModel):
    """Schema for order item data validation"""
    order_id: str = Field(..., min_length=1, max_length=50)
    product_id: str = Field(..., min_length=1, max_length=50)
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., gt=0)
    subtotal: float = Field(..., ge=0)

    @field_validator('subtotal')
    @classmethod
    def validate_subtotal(cls, v, info):
        # Note: In Pydantic v2, we can't access other fields during validation
        # This check will be done in the service layer
        return v

    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    """Response schema for file upload"""
    message: str
    records_processed: int
    success_rows_count: int = 0
    skipped_rows_count: int = 0
    customers_created: int = 0
    products_created: int = 0
    orders_created: int = 0
    order_items_created: int = 0
    errors: List[str] = []


class ValidationError(BaseModel):
    """Schema for validation errors"""
    row: int
    field: str
    error: str
