
"""Very small adapter that forwards tool calls via MCP JSON messages."""

from pydantic import BaseModel
from typing import Any, Dict, Literal

class MCPRequest(BaseModel):
    type: Literal["request"] = "request"
    request_id: str
    tool: str
    args: Dict[str, Any]

class MCPResponse(BaseModel):
    type: Literal["response"] = "response"
    request_id: str
    ok: bool
    data: Any | None = None
    error: str | None = None
