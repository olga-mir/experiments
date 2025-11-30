"""
Cleanup script to delete all Agent Engine resources in a project.

This script:
1. Lists all reasoning engines in the project
2. For each reasoning engine, deletes all sessions
3. Deletes the reasoning engine itself

Usage:
    python -m web_to_md.deployment.cleanup_agents --project PROJECT_ID --location LOCATION
"""

import argparse
import sys
from google.cloud import aiplatform


def cleanup_agents(project_id: str, location: str, dry_run: bool = False):
    """
    Delete all Agent Engine resources in a project.

    Args:
        project_id: GCP project ID
        location: GCP location (e.g., us-central1)
        dry_run: If True, only list resources without deleting
    """
    # pylint: disable=too-many-locals
    print(f"{'[DRY RUN] ' if dry_run else ''}Cleaning up agents in {project_id}/{location}...")

    # Initialize Vertex AI
    aiplatform.init(project=project_id, location=location)

    try:
        # List all reasoning engines
        parent = f"projects/{project_id}/locations/{location}"
        client = aiplatform.gapic.ReasoningEngineServiceClient(
            client_options={"api_endpoint": f"{location}-aiplatform.googleapis.com"}
        )

        print(f"\n📋 Listing reasoning engines in {parent}...")
        reasoning_engines = client.list_reasoning_engines(parent=parent)

        engines_list = list(reasoning_engines)
        if not engines_list:
            print("✅ No reasoning engines found. Nothing to clean up.")
            return True

        print(f"Found {len(engines_list)} reasoning engine(s)")

        for engine in engines_list:
            engine_name = engine.name
            engine_id = engine_name.split('/')[-1]
            display_name = engine.display_name or "Unnamed"

            print(f"\n{'─' * 70}")
            print(f"🤖 Engine: {display_name}")
            print(f"   ID: {engine_id}")
            print(f"   Full name: {engine_name}")

            # Delete the reasoning engine (force=True will delete sessions automatically)
            if dry_run:
                print(f"   [DRY RUN] Would delete engine: {engine_id} "
                      "(with force=True to delete sessions)")
            else:
                print(f"   🗑️  Deleting reasoning engine: {engine_id}")
                print("   ℹ️  Using force=True to automatically delete all sessions")
                try:
                    # pylint: disable=import-outside-toplevel
                    from google.cloud.aiplatform_v1.types import DeleteReasoningEngineRequest

                    request = DeleteReasoningEngineRequest(
                        name=engine_name,
                        force=True  # This will delete sessions automatically
                    )
                    operation = client.delete_reasoning_engine(request=request)
                    print("   ⏳ Deletion in progress...")
                    operation.result(timeout=300)  # Wait up to 5 minutes
                    print(f"   ✅ Engine {engine_id} deleted successfully "
                          "(including all sessions)")
                except Exception as e: # pylint: disable=broad-exception-caught
                    print(f"   ❌ Error deleting engine: {e}")
                    return False

        print(f"\n{'═' * 70}")
        if dry_run:
            print("✅ [DRY RUN] Completed. No resources were actually deleted.")
        else:
            print(f"✅ Cleanup complete! Deleted {len(engines_list)} reasoning engine(s)")
        return True

    except Exception as e: # pylint: disable=broad-exception-caught
        print(f"❌ Error during cleanup: {e}")
        import traceback # pylint: disable=import-outside-toplevel
        traceback.print_exc()
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Delete all Agent Engine resources in a project"
    )
    parser.add_argument(
        "--project",
        required=True,
        help="GCP Project ID"
    )
    parser.add_argument(
        "--location",
        default="us-central1",
        help="GCP location (default: us-central1)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List resources without deleting them"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt"
    )

    args = parser.parse_args()

    if not args.dry_run and not args.force:
        print("\n⚠️  WARNING: This will delete ALL reasoning engines and sessions in the project!")
        print(f"Project: {args.project}")
        print(f"Location: {args.location}")
        response = input("\nAre you sure you want to continue? (yes/no): ")

        if response.lower() != "yes":
            print("Cancelled.")
            sys.exit(0)

    IS_SUCCESS = cleanup_agents(args.project, args.location, args.dry_run)
    sys.exit(0 if IS_SUCCESS else 1)
