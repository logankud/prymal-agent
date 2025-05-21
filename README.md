# Prymal Copilot

Minimal skeleton for an LLM agent that routes tool calls through a Model Context Protocol (MCP).

* **agent.py** – main entrypoint using Pydantic‑AI.
* **mcp_adapter.py** – translates agent tool calls to JSON MCP requests/responses.
* **tools/** – Pydantic‑typed tool definitions the agent can call.
* **context_providers/** – business‑logic functions that satisfy MCP requests (DB/API calls).

Swap the model in *agent.py* by changing one line, e.g. `OpenAIModel("gpt-4o")` → `ClaudeModel("claude-3-sonnet")`.
