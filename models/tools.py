from pydantic import BaseModel, Field

class AnalysisWorkflowInput (BaseModel):
    """Pydantic model defining the schema for the input to the run_analysis_workflow tool"""

    intent: str = Field(..., description="Intent of the analysis, e.g. 'analyze customer orders'")
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    dataset_name: str = Field(default="shopify_order_data", description="Name of the dataset to store the fetched orders")
    group_by: str = Field(default="email", description="Field name to group orders by")
    agg_field: str = Field(default="id", description="Field to aggregate on")
    agg_fn: str = Field(default="count", description="Aggregation function to apply")
