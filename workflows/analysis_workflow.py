from typing import Annotated
from smolagents import tool
from langchain_core.messages import BaseMessage
from graphs.analysis_workflow import analysis_workflow
from models.tools import AnalysisWorkflowInput


@tool
def run_analysis_workflow(input: AnalysisWorkflowInput) -> dict:
    """
    Runs the full analysis workflow DAG (fetch -> validate -> group -> aggregate).  The input required must follow the AnalysisWorkflowInput schema.  If you get a validation error, call the `describe_model` tool on 'AnalysisWorkflowInput'
    to understand the required schema, then try again.

    Args:
        input (AnalysisWorkflowInput): Parameters required to run the workflow.

    Returns:
        The result of the analysis step.
        
    
    """
    
    try:
        validated_input = AnalysisWorkflowInput(**input)
        return analysis_workflow.invoke(validated_input.dict())
    except Exception as e:
        raise ValueError(
            f"[Workflow Input Error] {str(e)}. "
            f"Hint: Use the `describe_model` tool with class_name='AnalysisWorkflowInput' to understand the required schema, then retry."
        )