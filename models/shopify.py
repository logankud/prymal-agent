from pydantic import BaseModel, Field
from typing import List, Optional


class ShopifyLineItem(BaseModel):
    """Pydantic model defining the schema of each line item nested in a Shopify order object (which contains one record per order, and a list of line items)"""
    order_id: Optional[str] = Field(..., description="Shopify global ID for the order")
    order_name: Optional[str] = Field(..., description="Order name as shown in Shopify")
    sku: str = Field(None, description="Stock Keeping Unit identifier")
    name: str = Field(..., description="Name of the product purchased")
    quantity: int = Field(..., description="Quantity of the item ordered")
    amount: float = Field(None, description="Total amount in USD$ for this line item")


class ShopifyOrder(BaseModel):
    """Pydantic model defining the schema of a Shopify order object, one record per order"""
    id: str = Field(..., description="Shopify global ID for the order")
    name: str = Field(..., description="Order name as shown in Shopify")
    created_at_ts: str = Field(
        ..., description="ISO timestamp of when the order was created")
    updated_at_ts: str = Field(
        ..., description="ISO timestamp of the last update to the order")
    created_at_date: str = Field(
        ..., description="Date (ISO timestamp converted to YYYY-MM-DD format) of when the order was created")
    updated_at_date: str = Field(
        ..., description="Date (ISO timestamp converted to YYYY-MM-DD format) of the last update to the order")
    email: Optional[str] = Field(
        None, description="Customer's email address on file")
    customer_email: Optional[str] = Field(
        None, description="Email address from the customer object, if available")
    original_total: float = Field(
        ..., description="Original total amount in USD$ for the order, including discounts & taxes")
    current_total: float = Field(
        ..., description="Current total amount in USD$ for the order, including discounts & taxes")
    line_items: List[ShopifyLineItem] = Field(
        ..., description="List of line items included in the order")
