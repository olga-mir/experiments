# Copyright 2026 Google LLC
import os
from typing import List, Optional, Union
from google.adk.tools.mcp_tool import McpToolset, SseConnectionParams
from google.adk.tools.base_toolset import ToolPredicate

def get_github_mcp_toolset(
    tool_filter: Optional[Union[ToolPredicate, List[str]]] = None,
    tool_name_prefix: Optional[str] = None,
) -> McpToolset:
    """Creates and returns an McpToolset connected to the remote GitHub MCP server.
    
    This toolset connects to the official remote GitHub MCP server via SSE transport.
    
    It retrieves the GitHub token from the environment variable `GITHUB_TOKEN`
    (or `GITHUB_PERSONAL_ACCESS_TOKEN`) and sends it in the Authorization header.

    Args:
        tool_filter: Optional filter to select specific tools. Can be a list of tool names 
                     or a ToolPredicate function.
        tool_name_prefix: A prefix added to the name of each tool in the toolset (e.g. 'github_').
                          This helps avoid name conflicts with other tools.
    """
    token = (
        os.environ.get("GITHUB_TOKEN") or 
        os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
    )
    if not token or "placeholder" in token:
        raise ValueError(
            "GitHub Personal Access Token (PAT) not found. Please ensure GITHUB_TOKEN "
            "is set in your environment configuration (e.g., `.setup-env` file)."
        )
        
    return McpToolset(
        connection_params=SseConnectionParams(
            url="https://api.githubcopilot.com/mcp/",
            headers={
                "Authorization": f"Bearer {token.strip()}"
            }
        ),
        tool_filter=tool_filter,
        tool_name_prefix=tool_name_prefix
    )

