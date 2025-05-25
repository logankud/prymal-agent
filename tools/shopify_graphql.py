import os
import requests
from smolagents import tool

# Load from environment variables (e.g., via Replit Secrets or .env)
SHOPIFY_GRAPHQL_URL = os.getenv("SHOPIFY_GRAPHQL_URL")  # e.g. https://yourstore.myshopify.com/admin/api/2024-04/graphql.json
SHOPIFY_TOKEN = os.getenv("SHOPIFY_TOKEN")  # Private app or custom app token

@tool
def run_shopify_query(query: str) -> dict:
    """
    Executes a raw GraphQL query against the Shopify Admin API.

    Args:
        query (str): The complete GraphQL query as a string. Must follow the syntax
                     supported by Shopify's Admin API (e.g. 'query { ordersCount { count } }').

    Returns:
        dict: The parsed JSON response from Shopify as a Python dictionary. If the request fails,
              a RuntimeError will be raised with the HTTP status and error message.

    Example:
        >>> run_shopify_query("query { ordersCount { count } }")
        {'data': {'ordersCount': 123}}

    Environment Variables:
        - SHOPIFY_GRAPHQL_URL: Full Shopify GraphQL endpoint.
        - SHOPIFY_TOKEN: Admin access token for authentication.

    Notes:
        - This tool allows your CodeAgent to dynamically query real store data from Shopify.
        - Avoid exposing sensitive data in responses; consider adding sanitization logic if needed.
    """
    if not SHOPIFY_GRAPHQL_URL or not SHOPIFY_TOKEN:
        raise EnvironmentError("Missing required Shopify credentials (SHOPIFY_GRAPHQL_URL or SHOPIFY_TOKEN).")

    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": SHOPIFY_TOKEN
    }

    response = requests.post(
        SHOPIFY_GRAPHQL_URL,
        headers=headers,
        json={"query": query}
    )

    if not response.ok:
        raise RuntimeError(f"Shopify API error {response.status_code}: {response.text}")

    return response.json()
