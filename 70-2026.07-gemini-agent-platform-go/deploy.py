#!/usr/bin/env python3
"""Deploy llm-auditor Go container to Gemini Enterprise Agent Platform (Agent Engine)."""

import argparse
import json

import agentplatform

# Methods declared by the adk-go agentengine server (server/agentengine/handler.go)
CLASS_METHODS = [
    {"name": "async_create_session", "api_mode": ""},
    {"name": "async_get_session", "api_mode": ""},
    {"name": "async_list_sessions", "api_mode": ""},
    {"name": "async_delete_session", "api_mode": ""},
    {"name": "async_stream_query", "api_mode": "async_stream"},
    {"name": "streaming_agent_run_with_events", "api_mode": "async_stream"},
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image-uri", required=True, help="Container image URI in Artifact Registry")
    parser.add_argument("--project", required=True, help="GCP project ID")
    parser.add_argument("--location", default="us-central1", help="GCP region")
    parser.add_argument("--display-name", default="llm-auditor", help="Agent display name")
    parser.add_argument("--resource-id", default=None, help="Existing resource ID to update (skips create)")
    args = parser.parse_args()

    client = agentplatform.Client(project=args.project, location=args.location)

    config = {
        "display_name": args.display_name,
        "container_spec": {
            "image_uri": args.image_uri,
        },
        "class_methods": CLASS_METHODS,
        "agent_framework": "google-adk",
    }

    if args.resource_id:
        resource_name = f"projects/{args.project}/locations/{args.location}/reasoningEngines/{args.resource_id}"
        print(f"Updating existing agent engine {args.resource_id}...")
        agent_engine = client.agent_engines.update(
            name=resource_name,
            config=config,
        )
    else:
        print(f"Creating new agent engine with image {args.image_uri}...")
        agent_engine = client.agent_engines.create(config=config)

    resource_name = agent_engine.api_resource.name
    resource_id = resource_name.split("/")[-1]

    print(f"\nDeployed: {resource_name}")
    print(f"Resource ID: {resource_id}")
    print(f"\nTest with the Python SDK:")
    print(f"  import agentplatform")
    print(f"  client = agentplatform.Client(project='{args.project}', location='{args.location}')")
    print(f"  agent = client.agent_engines.get('{resource_name}')")
    print(f"  session = agent.create_session(user_id='user1')")
    print(f"  for chunk in agent.stream_query(user_id='user1', session_id=session['id'], message='...'):")
    print(f"      print(chunk)")

    metadata = {
        "resource_name": resource_name,
        "remote_agent_runtime_id": resource_name,
        "resource_id": resource_id,
        "project": args.project,
        "location": args.location,
        "image_uri": args.image_uri,
        "deployment_target": "agent_runtime",
        "is_a2a": False,
    }
    with open("deployment_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"\nMetadata written to deployment_metadata.json")


if __name__ == "__main__":
    main()
