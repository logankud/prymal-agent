# trace_pretty.py
from datetime import datetime
from textwrap import shorten
from pydantic_ai import capture_run_messages
from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    FinalResultEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent
)

def fmt_ts(ts: datetime) -> str:
    return ts.strftime("%H:%M:%S")

def fmt_part(part) -> str:
    """Return a short human string for any *Part object."""
    if part.part_kind == "tool-call":
        return f"🔧→ (tool-call) {part.tool_name} {part.args}"
    if part.part_kind == "tool-return":
        return f"←🔧 (tool-return) {part.tool_name}"
    if part.part_kind == "text":
        return shorten(part.content, width=60, placeholder="…")
    return str(part)

def pretty_print_trace(ev) -> str:
    # ── model REQUEST ──────────────────────────────────────────────
    if isinstance(ev, ModelRequest):

        ts   = ev.parts[0].timestamp
        text = "; ".join(fmt_part(p) for p in ev.parts)
        return f"{fmt_ts(ts)}  ▶️  {text}"

    # ── model RESPONSE ─────────────────────────────────────────────
    if isinstance(ev, ModelResponse):

        ts   = ev.timestamp
        text = "; ".join(fmt_part(p) for p in ev.parts)
        return f"{fmt_ts(ts)}  🤖  {text}"

    # ── tool-call / tool-result ────────────────────────────────────
    if isinstance(ev, FunctionToolCallEvent):

        return f"{fmt_ts(ev.timestamp)}  🔧→ {ev.part.tool_name} {ev.part.args}"

    if isinstance(ev, FunctionToolResultEvent):

        return f"{fmt_ts(ev.timestamp)}  ←🔧 {ev.tool_name} {ev.result.content} \n"

    # ── final answer ───────────────────────────────────────────────
    if isinstance(ev, FinalResultEvent):

        return f"{fmt_ts(ev.timestamp)}  ✅  FINAL: {shorten(str(ev.output), 80)}"

    # fallback
    return str(ev)