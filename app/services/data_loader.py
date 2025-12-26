"""Data validation and loading service"""
from typing import Dict, Any, List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from datetime import datetime
from pydantic import ValidationError
import logging

from app.models import Customer, Product, Order, OrderItem
from app.schemas import (
    CustomerSchema, ProductSchema, OrderSchema, OrderItemSchema
)

logger = logging.getLogger(__name__)


class DataLoaderService:
    """Service for validating and loading data into database"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.errors: List[str] = []
    
    @staticmethod
    def identify_table_type(record: Dict[str, Any]) -> Optional[str]:
        """
        Identify which table the record belongs to based on its fields.
        Returns: 'customer', 'product', 'order', or 'order_item'
        """
        keys = set(record.keys())
        
        # Check for customer fields
        if 'customer_id' in keys and 'email' in keys:
            if 'order_id' not in keys and 'product_id' not in keys:
                return 'customer'
        
        # Check for product fields
        if 'product_id' in keys and 'price' in keys:
            if 'customer_id' not in keys and 'order_id' not in keys:
                return 'product'
        
        # Check for order item fields
        if 'order_id' in keys and 'product_id' in keys and 'quantity' in keys:
            return 'order_item'
        
        # Check for order fields
        if 'order_id' in keys and 'customer_id' in keys and 'order_date' in keys:
            return 'order'
        
        return None
    
    @staticmethod
    def prepare_customer_data(record: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare customer data for validation"""
        return {
            'customer_id': record.get('customer_id'),
            'name': record.get('name'),
            'email': record.get('email'),
            'phone': record.get('phone'),
            'address': record.get('address'),
        }
    
    @staticmethod
    def prepare_product_data(record: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare product data for validation"""
        return {
            'product_id': record.get('product_id'),
            'name': record.get('name'),
            'description': record.get('description'),
            'price': float(record.get('price', 0)),
            'category': record.get('category'),
            'stock_quantity': int(record.get('stock_quantity', 0)) if record.get('stock_quantity') else 0,
        }
    
    @staticmethod
    def prepare_order_data(record: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare order data for validation"""
        order_date = record.get('order_date')
        if isinstance(order_date, str):
            # Try to parse various date formats
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y']:
                try:
                    order_date = datetime.strptime(order_date, fmt)
                    break
                except ValueError:
                    continue
        
        return {
            'order_id': record.get('order_id'),
            'customer_id': record.get('customer_id'),
            'order_date': order_date,
            'status': record.get('status', 'pending'),
            'total_amount': float(record.get('total_amount', 0)),
        }
    
    @staticmethod
    def prepare_order_item_data(record: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare order item data for validation"""
        quantity = int(record.get('quantity', 0))
        unit_price = float(record.get('unit_price', 0))
        subtotal = float(record.get('subtotal', quantity * unit_price))
        
        return {
            'order_id': record.get('order_id'),
            'product_id': record.get('product_id'),
            'quantity': quantity,
            'unit_price': unit_price,
            'subtotal': subtotal,
        }
    
    async def validate_and_categorize_records(
        self, records: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Validate records and categorize them by table type.
        Returns dict with keys: 'customers', 'products', 'orders', 'order_items'
        """
        categorized = {
            'customers': [],
            'products': [],
            'orders': [],
            'order_items': [],
        }
        
        for idx, record in enumerate(records):
            try:
                table_type = self.identify_table_type(record)
                
                if not table_type:
                    self.errors.append(f"Row {idx + 1}: Could not identify table type from fields")
                    continue
                
                if table_type == 'customer':
                    data = self.prepare_customer_data(record)
                    validated = CustomerSchema(**data)
                    categorized['customers'].append(validated.model_dump())
                
                elif table_type == 'product':
                    data = self.prepare_product_data(record)
                    validated = ProductSchema(**data)
                    categorized['products'].append(validated.model_dump())
                
                elif table_type == 'order':
                    data = self.prepare_order_data(record)
                    validated = OrderSchema(**data)
                    categorized['orders'].append(validated.model_dump())
                
                elif table_type == 'order_item':
                    data = self.prepare_order_item_data(record)
                    validated = OrderItemSchema(**data)
                    categorized['order_items'].append(validated.model_dump())
            
            except ValidationError as e:
                error_msg = f"Row {idx + 1}: Validation error - {str(e)}"
                self.errors.append(error_msg)
                logger.warning(error_msg)
            except Exception as e:
                error_msg = f"Row {idx + 1}: Error - {str(e)}"
                self.errors.append(error_msg)
                logger.error(error_msg)
        
        return categorized
    
    async def verify_relationships(self, categorized: Dict[str, List[Dict[str, Any]]]) -> bool:
        """
        Verify that foreign key relationships are valid.
        Checks that referenced customers and products exist.
        """
        # Get existing customer IDs
        customer_ids = {c['customer_id'] for c in categorized['customers']}
        result = await self.session.execute(select(Customer.customer_id))
        existing_customer_ids = {row[0] for row in result.fetchall()}
        all_customer_ids = customer_ids | existing_customer_ids
        
        # Get existing product IDs
        product_ids = {p['product_id'] for p in categorized['products']}
        result = await self.session.execute(select(Product.product_id))
        existing_product_ids = {row[0] for row in result.fetchall()}
        all_product_ids = product_ids | existing_product_ids
        
        # Verify orders reference valid customers
        for order in categorized['orders']:
            if order['customer_id'] not in all_customer_ids:
                self.errors.append(
                    f"Order {order['order_id']}: Referenced customer {order['customer_id']} does not exist"
                )
        
        # Verify order items reference valid orders and products
        order_ids = {o['order_id'] for o in categorized['orders']}
        result = await self.session.execute(select(Order.order_id))
        existing_order_ids = {row[0] for row in result.fetchall()}
        all_order_ids = order_ids | existing_order_ids
        
        for item in categorized['order_items']:
            if item['order_id'] not in all_order_ids:
                self.errors.append(
                    f"Order item: Referenced order {item['order_id']} does not exist"
                )
            if item['product_id'] not in all_product_ids:
                self.errors.append(
                    f"Order item: Referenced product {item['product_id']} does not exist"
                )
        
        return len(self.errors) == 0
    
    async def load_data_batch(
        self, categorized: Dict[str, List[Dict[str, Any]]]
    ) -> Tuple[int, int, int, int]:
        """
        Load data into database in batch mode.
        Returns tuple: (customers_count, products_count, orders_count, order_items_count)
        """
        customers_count = 0
        products_count = 0
        orders_count = 0
        order_items_count = 0
        
        try:
            # Insert customers first (no dependencies)
            if categorized['customers']:
                # Use insert().on_conflict_do_nothing() to avoid duplicates
                for customer in categorized['customers']:
                    try:
                        # Check if customer exists
                        result = await self.session.execute(
                            select(Customer).where(Customer.customer_id == customer['customer_id'])
                        )
                        existing = result.scalar_one_or_none()
                        
                        if not existing:
                            new_customer = Customer(**customer)
                            self.session.add(new_customer)
                            customers_count += 1
                    except Exception as e:
                        logger.error(f"Error inserting customer {customer.get('customer_id')}: {str(e)}")
                        self.errors.append(f"Customer {customer.get('customer_id')}: {str(e)}")
                
                await self.session.flush()
            
            # Insert products (no dependencies)
            if categorized['products']:
                for product in categorized['products']:
                    try:
                        result = await self.session.execute(
                            select(Product).where(Product.product_id == product['product_id'])
                        )
                        existing = result.scalar_one_or_none()
                        
                        if not existing:
                            new_product = Product(**product)
                            self.session.add(new_product)
                            products_count += 1
                    except Exception as e:
                        logger.error(f"Error inserting product {product.get('product_id')}: {str(e)}")
                        self.errors.append(f"Product {product.get('product_id')}: {str(e)}")
                
                await self.session.flush()
            
            # Insert orders (depends on customers)
            if categorized['orders']:
                for order in categorized['orders']:
                    try:
                        result = await self.session.execute(
                            select(Order).where(Order.order_id == order['order_id'])
                        )
                        existing = result.scalar_one_or_none()
                        
                        if not existing:
                            new_order = Order(**order)
                            self.session.add(new_order)
                            orders_count += 1
                    except Exception as e:
                        logger.error(f"Error inserting order {order.get('order_id')}: {str(e)}")
                        self.errors.append(f"Order {order.get('order_id')}: {str(e)}")
                
                await self.session.flush()
            
            # Insert order items (depends on orders and products)
            if categorized['order_items']:
                for item in categorized['order_items']:
                    try:
                        new_item = OrderItem(**item)
                        self.session.add(new_item)
                        order_items_count += 1
                    except Exception as e:
                        logger.error(f"Error inserting order item: {str(e)}")
                        self.errors.append(f"Order item: {str(e)}")
                
                await self.session.flush()
            
            # Commit transaction
            await self.session.commit()
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error during batch insert: {str(e)}")
            self.errors.append(f"Database error: {str(e)}")
            raise
        
        return customers_count, products_count, orders_count, order_items_count
