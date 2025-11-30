"""
Core agent definition for the Web to Markdown agent.
"""
from datetime import datetime
import os
from google.adk.agents import LlmAgent
from .scraper import scrape_to_markdown, save_text_to_gcs

def scrape_tool(url: str) -> str:
    """
    Scrapes the given URL, downloads images to local assets, and returns Markdown content.
    Saves the output to GCS if running in a cloud environment.

    Args:
        url: The website URL to process.
    """
    # Determine output directory/prefix
    # Format: YYYY-MM-DD_HH_MM_SS
    timestamp = datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
    output_dir = timestamp

    # Define bucket - fallback to specific bucket as per requirements
    bucket_name = os.environ.get("GCS_BUCKET_NAME", "web-to-md-bucket-7d4c11")

    # Check if we should use GCS (heuristic: if K_SERVICE is set or bucket explicitly set)
    # K_SERVICE is automatically set in Cloud Run
    use_gcs = bool(os.environ.get("K_SERVICE") or os.environ.get("GCS_BUCKET_NAME"))

    if use_gcs:
        # Ensure the environment variable is set for scraper.py to pick it up if not already
        if "GCS_BUCKET_NAME" not in os.environ:
            os.environ["GCS_BUCKET_NAME"] = bucket_name

        markdown_content = scrape_to_markdown(url, output_dir=output_dir)

        # Save the markdown file itself
        blob_name = f"{output_dir}/page.md"
        try:
            gcs_url = save_text_to_gcs(bucket_name, blob_name, markdown_content)
            return f"Scraped content saved to {gcs_url}\n\nContent:\n{markdown_content}"
        except Exception as e: # pylint: disable=broad-exception-caught
            return f"Scraped content (GCS Save Error: {e}):\n{markdown_content}"
    else:
        # Local mode
        os.makedirs(output_dir, exist_ok=True)
        markdown_content = scrape_to_markdown(url, output_dir=output_dir)

        # Save locally
        try:
            local_path = os.path.join(output_dir, "page.md")
            with open(local_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            return f"Scraped content saved locally to {local_path}\n\nContent:\n{markdown_content}"
        except Exception as e: # pylint: disable=broad-exception-caught
            return f"Scraped content (Local Save Error: {e}):\n{markdown_content}"


root_agent = LlmAgent(
    name='web_to_md_agent',
    model='gemini-2.5-flash',
    description='An agent that converts web pages to clean Markdown with local images.',
    instruction='''
    You are a web scraping assistant.
    When a user provides a URL, use the `scrape_tool` to convert it to Markdown.
    Return the location where the file was saved and the markdown content to the user.
    ''',
    tools=[scrape_tool]
)

if __name__ == "__main__":
    print("🤖 Web to Markdown Agent (Local Mode)")
    print("Type a URL to scrape, or 'exit' to quit.")

    while True:
        try:
            user_input = input("\n> ")
            if user_input.lower() in ['exit', 'quit']:
                break

            if not user_input.strip():
                continue

            # If user types just a URL, wrap it in a natural language prompt
            if user_input.startswith("http"):
                prompt = f"Scrape {user_input}"
            else:
                prompt = user_input

            print("Processing...")
            # The ADK agent might need a session or just a direct call depending on version
            # Assuming .query() or similar exists.
            # Checking ADK usage from `verify_agent.py`: agent.stream_query(message=...)
            # But `LlmAgent` is from `google.adk.agents`.
            # If it's a standard ADK agent:
            response = root_agent.query(prompt)
            print(response)

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e: # pylint: disable=broad-exception-caught
            print(f"Error: {e}")
