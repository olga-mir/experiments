"""Minimal JSON-RPC client for Google Cloud remote MCP servers.

No MCP SDK: AgentCore direct-code deploy is a zipped venv, and Google's
MCP HTTP examples are plain POST + JSON-RPC (JSON or SSE body).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

import gcp_auth

LOGGING_MCP_URL = "https://logging.googleapis.com/mcp"


def _parse_body(body: str) -> dict[str, Any]:
    text = body.strip()
    if not text:
        raise RuntimeError("empty MCP response")
    if text[0] in "{[":
        return json.loads(text)
    data_lines = [
        line[5:].strip() for line in text.splitlines() if line.startswith("data:")
    ]
    if not data_lines:
        raise RuntimeError(f"unrecognized MCP response: {text[:800]}")
    return json.loads(data_lines[-1])


def call_tool(url: str, name: str, arguments: dict[str, Any] | None = None) -> Any:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments or {}},
    }
    token = gcp_auth.get_access_token()
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"MCP HTTP {e.code} from {url}: {detail[:2000]}") from e

    message = _parse_body(raw)
    if "error" in message:
        raise RuntimeError(f"MCP error: {message['error']}")
    result = message.get("result", message)
    if isinstance(result, dict) and result.get("isError"):
        raise RuntimeError(f"MCP tool error: {result}")
    return _result_to_text(result)


def _result_to_text(result: Any) -> str:
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        content = result.get("content")
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    parts.append(str(item.get("text", "")))
                else:
                    parts.append(json.dumps(item, default=str))
            if parts:
                return "\n".join(parts)
        structured = result.get("structuredContent")
        if structured is not None:
            return json.dumps(structured, indent=2, default=str)
    return json.dumps(result, indent=2, default=str)


def list_log_entries(
    *,
    project_id: str,
    filter: str,
    page_size: int = 20,
    order_by: str = "timestamp desc",
) -> str:
    return call_tool(
        LOGGING_MCP_URL,
        "list_log_entries",
        {
            "resourceNames": [f"projects/{project_id}"],
            "filter": filter,
            "pageSize": page_size,
            "orderBy": order_by,
        },
    )


def list_log_names(*, project_id: str, page_size: int = 100) -> str:
    return call_tool(
        LOGGING_MCP_URL,
        "list_log_names",
        {
            "parent": f"projects/{project_id}",
            "pageSize": page_size,
        },
    )
