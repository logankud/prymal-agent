# tools/shopify.py

import os
import requests
import yaml

# Read config
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

SHOPIFY_API_VERSION = config["shopify"]["api_version"]

class ShopifyGraphQL:
    def __init__(self):
        self.shop_url = os.environ["SHOPIFY_STORE_URL"]
        self.token = os.environ["SHOPIFY_TOKEN"]
        self.graphql_endpoint = f"https://{self.shop_url}/admin/api/{SHOPIFY_API_VERSION}/graphql.json"
        self.headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": self.token
        }

    def graphql(self, query: str, variables: dict = None):
        """Send a GraphQL query to Shopify."""
        payload = {
            "query": query,
            "variables": variables or {}
        }
        response = requests.post(self.graphql_endpoint, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
