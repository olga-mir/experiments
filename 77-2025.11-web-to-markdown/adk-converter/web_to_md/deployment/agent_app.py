"""
Entrypoint for the Vertex AI Agent Engine application.
Wraps the agent using AdkApp.
"""
from vertexai import agent_engines
from web_to_md.core.agent import root_agent

# Wrap the agent for Agent Engine deployment
adk_app = agent_engines.AdkApp(
    agent=root_agent,
    enable_tracing=True,
)
