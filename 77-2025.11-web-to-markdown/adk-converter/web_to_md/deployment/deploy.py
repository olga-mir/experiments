"""
Deploy script for the Web to Markdown agent using Vertex AI Agent Engine.
"""
import argparse
import vertexai

# Define the API methods your agent will expose
# We define this here (or import it) to pass to the config
class_methods = [
    {
        "name": "stream_query",
        "api_mode": "stream",
        "description": "Stream responses from the agent",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "user_id": {"type": "string"},
                "session_id": {"type": "string"}
            },
            "required": ["message", "user_id"]
        },
    },
]

def deploy(project_id: str, location: str):
    """
    Deploys the agent to Vertex AI Agent Engine.

    Args:
        project_id: Google Cloud Project ID.
        location: Google Cloud Region.
    """
    print(f"Initializing Vertex AI for project {project_id} in {location}...")
    # vertexai.init(project=project_id, location=location)
    client = vertexai.Client(project=project_id, location=location)

    print("🚀 Deploying agent with inline source...")

    config = {
        "display_name": "Web to Markdown Agent",
        "description": "Converts URLs to Markdown",
        "labels": {"env": "dev", "type": "inline-source"},

        # Inline source configuration
        "source_packages": [
            "web_to_md",
            "requirements.txt",
        ],
        "requirements_file": "requirements.txt",
        "entrypoint_module": "web_to_md.deployment.agent_app",
        "entrypoint_object": "adk_app",
        "class_methods": class_methods,
        "agent_framework": "google-adk",  # Identifies as ADK agent in Console UI
        # Explicitly set supported version (currently 3.9, 3.10, 3.11, 3.12, 3.13)
        "python_version": "3.12",
        "env_vars": {
            "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "true",
            "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "true",
        }
    }

    # Implement Update-or-Create Logic
    display_name = config["display_name"]
    existing_agents = client.agent_engines.list()

    target_agent = None
    # Filter locally
    for existing in existing_agents:
        # Check api_resource.display_name
        existing_display_name = getattr(existing.api_resource, "display_name", "")
        if existing_display_name == display_name:
            target_agent = existing
            break

    if target_agent:
        # Extract resource name
        resource_name = getattr(target_agent.api_resource, "name", None)

        print(f"🔄 Found existing agent: {resource_name}")
        print("Updating agent...")

        agent = client.agent_engines.update(
            name=resource_name,
            config=config
        )
    else:
        print("✨ Creating new agent...")
        agent = client.agent_engines.create(config=config)

    print("✅ Deployment complete!")
    resource_name = getattr(agent, "resource_name", None)
    if not resource_name and hasattr(agent, "api_resource"):
        resource_name = agent.api_resource.name

    print(f"Resource: {resource_name}")
    return agent

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, help="Google Cloud Project ID")
    parser.add_argument("--location", default="us-central1", help="Google Cloud Region")
    # bucket argument removed as we can't pass it easily

    args = parser.parse_args()

    deploy(args.project, args.location)
