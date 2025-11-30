"""
Verification script for the deployed Web to Markdown agent.
"""
import sys
import os
import argparse
import vertexai
from vertexai.preview import reasoning_engines

def verify_agent(project_id_arg, location_arg, resource_id_arg, url=None):
    """
    Verify that a deployed agent is working correctly.

    Args:
        project_id_arg: GCP project ID
        location_arg: GCP location (e.g., us-central1)
        resource_id_arg: Reasoning Engine resource ID
        url: Optional URL to scrape (defaults to https://example.com)
    """
    print(f"Verifying agent {resource_id_arg} in {project_id_arg}/{location_arg}")
    vertexai.init(project=project_id_arg, location=location_arg)

    agent = reasoning_engines.ReasoningEngine(resource_id_arg)

    # Use provided URL or default
    test_url = url or "https://example.com"
    message = f"Scrape {test_url}"

    try:
        print(f"Sending stream_query with message: '{message}'")
        # pylint: disable=no-member
        response_stream = agent.stream_query(
            message=message,
            user_id="test-user"
        )

        print("Response Stream:")
        for chunk in response_stream:
            print(chunk)

        print("\n✅ Agent verification successful!")
        return True

    except Exception as e: # pylint: disable=broad-exception-caught
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify a deployed Reasoning Engine agent")
    parser.add_argument("--resource-id", help="Reasoning Engine Resource ID")
    parser.add_argument("--url", help="URL to scrape (optional, defaults to https://example.com)")
    parser.add_argument("--project", help="GCP Project ID (defaults to PROJECT_ID env var)")
    parser.add_argument("--location", default="us-central1",
                        help="GCP location (defaults to us-central1)")
    args = parser.parse_args()

    project_id = args.project or os.environ.get("PROJECT_ID")
    location = args.location
    resource_id = args.resource_id or os.environ.get("RESOURCE_ID")

    if not project_id:
        print("Error: PROJECT_ID must be provided via --project or PROJECT_ID env var.")
        sys.exit(1)

    if not resource_id:
        print("Error: RESOURCE_ID must be provided via --resource-id or RESOURCE_ID env var.")
        sys.exit(1)

    IS_SUCCESS = verify_agent(project_id, location, resource_id, args.url)
    sys.exit(0 if IS_SUCCESS else 1)
