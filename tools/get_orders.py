# tools/get_orders.py

import pandas as pd
import os
import json
import sys
from pydantic import fields
import requests
from datetime import datetime, timedelta, timezone
from smolagents import tool
# from tools import shopify
# from tools.shopify import ShopifyGraphQL
from typing import List, Dict, Any, Optional
from tools.memory_setup import get_agent_memory
from models.shopify import ShopifyOrder, ShopifyLineItem  
from utils import format_shopify_order



# Convert or default dates
def to_iso(d: str, offset: int) -> str:
    if d:
        return f"{d}T00:00:00Z"
    dt = datetime.now(timezone.utc).date() + timedelta(days=offset)
    return f"{dt.isoformat()}T00:00:00Z"


@tool
def get_orders(
    start_date: str,
    end_date: str
) -> List[Dict[str, Any]]:
    """
    Query order data via Shopify GraphQL API and store in local memory as shopify_order_data (represented by the ShopifyOrder pydantic model.   Avoid redundant calls - if the data for this date range is already in memory then use that.

    Args:
        start_date (str): start date in YYYY-MM-DD format.  Pulls all data >= 00:00:00.0000 on this date.
        end_date (str): end date in YYYY-MM-DD format. Pulls all data <= 23:59:59.9999 on this date.

    Returns:
        List of all resources as dictionaries
    """
    url = f"https://{os.environ['SHOPIFY_STORE_URL']}/admin/api/2023-07/graphql.json"
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": os.environ['SHOPIFY_TOKEN']
    }

    all_items: List[Dict[str, Any]] = []
    has_next_page = True
    cursor: Optional[str] = None

    while has_next_page:
        # Build cursor parameter
        cursor_part = f', after: "{cursor}"' if cursor else ""

        # Build query
        filter_part = f', query: "created_at:>={start_date} created_at:<={end_date}"' if filter else ""

        query = f"""
        query {{
          orders(first: 250{cursor_part}{filter_part}) {{
            edges {{
              node {{
                id
                name
                createdAt
                updatedAt
                email
                customer {{ 

                    id
                    email
                }}
                currentTotalPriceSet {{
                  shopMoney {{    
                    amount
                  }}
                }}
                originalTotalPriceSet {{
                  shopMoney {{    
                    amount
                  }}
                }}
                lineItems(first: 100) {{
                  edges {{
                    node {{
                      name
                      quantity
                      sku
                      originalTotalSet {{
                        shopMoney {{
                          amount
                        }}
                      }}
                      # originalUnitPriceSet
                      # totalDiscountSet

                    }}
                  }}
                }}

              }}
            }}
            pageInfo {{
              hasNextPage
              endCursor
            }}
          }}
        }}


        """


        # Make request
        response = requests.post(url, json={"query": query}, headers=headers)
        data = response.json()

        # Handle errors
        if "errors" in data:
            error_messages = "; ".join([e.get("message", "Unknown error") for e in data["errors"]])
            raise Exception(f"GraphQL error: {error_messages}")

        # Extract data
        result = data.get("data", {}).get('orders', {})
        edges = result.get("edges", [])
        items = [edge["node"] for edge in edges]
        all_items.extend(items)

        # Update pagination
        page_info = result.get("pageInfo", {})
        has_next_page = page_info.get("hasNextPage", False)
        cursor = page_info.get("endCursor")

        print(f"Fetched {len(items)} orders. Total: {len(all_items)}")


    # Validate data structure
    # -----------------------------------------------------------------------

    # Validate order-level records match ShopifyOrder schema
    validated_orders = []
    validated_line_items = []
  
    for raw in all_items:
        try:
            formatted_order = format_shopify_order(raw)
  
            # Extract lineItems and temporarily remove for ShopifyOrder validation
            line_items = formatted_order.pop("lineItems", [])
  
            # Validate the order without lineItems
            order = ShopifyOrder(**{**formatted_order, "lineItems": []})
            validated_orders.append({**formatted_order, "lineItems": line_items})  # keep full order in memory
  
            for li in line_items:
                try:
                    # Validate line item before adding order_id/order_name
                    clean_line_item = ShopifyLineItem(
                        **{
                            "sku": li.get("sku"),
                            "name": li.get("name"),
                            "quantity": li.get("quantity"),
                            "amount": li.get("amount"),
                            "order_id": order.id,
                            "order_name": order.name
                        }
                    )
                    validated_line_items.append(clean_line_item.model_dump())
                except Exception as e:
                    raise Exception(
                        f"Line item failed validation: {li} | Order ID: {order.id} | Error: {e}"
                    )
  
        except Exception as e:
            raise Exception(
                f"Order failed validation. Raw data: {raw} | Error: {e}"
            )



    # Save structured tool output
    memory = get_agent_memory()
    memory.remember(key="shopify_order_data", value=validated_orders)
    memory.remember(key="shopify_line_item_data", value=validated_line_items)
    return {"message": f"{len(validated_orders)} Shopify order records stored in memory as 'shopify_order_data'. Example order: {validated_orders[0]}.  {len(validated_line_items)} Shopify line item records stored in memory as 'shopify_line_item_data'. Example line item: {validated_line_items[0]}"}


# # Usage example:

# data = get_orders(start_date="2025-01-01", end_date="2025-01-10")
# # print(data)

# df = pd.DataFrame(data)
# print(len(df))
# print(len(df['name'].unique()))

# print(df.head())

# for _, row in df.sort_values('name',ascending=True).iterrows():
#     print(row['name'], row['createdAt'])