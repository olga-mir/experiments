"""
Module for scraping web content and converting it to Markdown.
Handles HTML cleaning, image downloading (local or GCS), and markdown conversion.
"""
import os
import hashlib
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig

try:
    from google.cloud import storage
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False

def upload_to_gcs(bucket_name: str, blob_name: str, data: bytes, content_type: str) -> str:
    """
    Uploads data to GCS and returns the public URL.
    Raises RuntimeError if GCS is not available or upload fails.
    """
    if not GCS_AVAILABLE:
        raise RuntimeError("GCS library not available (google-cloud-storage not installed).")

    try:
        # Use the project explicitly if needed, or default to environment
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        # Upload if it doesn't exist (optimization)
        if not blob.exists():
            blob.upload_from_string(data, content_type=content_type)

        # Return authenticated URL (since bucket is likely private)
        return f"https://storage.cloud.google.com/{bucket_name}/{blob_name}"
    except Exception as e:
        raise RuntimeError(f"GCS Upload Error: {e}") from e

def scrape_to_markdown(url: str, output_dir: str = ".") -> str:
    """
    Scrapes a web page, cleans content, downloads images, and returns Markdown.
    Uses Gemini (LLM) for intelligent content extraction.

    Args:
        url: The URL to scrape.
        output_dir: The directory to save images to (in an 'assets' subdirectory).
                    Ignored for images if GCS_BUCKET_NAME is set.

    Returns:
        The generated Markdown content.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        return f"Error fetching URL: {e}"

    soup = BeautifulSoup(response.content, 'html.parser')

    # Remove unwanted elements to save tokens
    # Decompose script, style, iframe, svg
    for element in soup(['script', 'style', 'iframe', 'svg']):
        element.decompose()

    # Unwrap noscript tags (content often hidden here for crawlers)
    for element in soup.find_all('noscript'):
        element.unwrap()

    # Process images (downloads and updates src to local/GCS paths)
    _process_images(soup, url, output_dir)

    # Use LLM for extraction
    try:
        project_id = os.environ.get("PROJECT_ID")
        if project_id:
            vertexai.init(project=project_id, location="us-central1")

        model = GenerativeModel("gemini-2.5-flash")

        prompt = """
        You are an expert web scraper and content extractor.
        Your task is to convert the provided HTML into clean, readable Markdown.

        Input Context:
        - The HTML is from a web page.
        - The `img` tags have already been processed: their `src` attributes point to valid local or Cloud Storage paths.

        Instructions:
        1. **Identify Main Content**: Extract ONLY the primary article, documentation, or post content.
           - IGNORE: Navigation bars, headers, footers, sidebars, advertisements, "related posts" sections, comment sections, and legal disclaimers.
        2. **Preserve Code**: Keep all code snippets EXACTLY as they appear.
           - Do not truncate, summarize, or "fix" the code.
           - Use 3 backticks (```) for code blocks.
           - **CRITICAL**: You MUST infer the correct language for the code block (e.g., ```python, ```bash, ```json, ```http) based on the content or HTML class attributes. Do not leave it empty.
        3. **Preserve Images**: Include all images found within the main content.
           - output as `![alt text](src)`.
           - **CRITICAL**: Do NOT change the `src` attribute. Use the exact value provided in the HTML.
        4. **Format Content**:
           - Use standard Markdown headings (#, ##, ###) to represent the structure.
           - Format tables as Markdown tables.
           - Use > for blockquotes or callouts.
           - Convert lists (<ul>, <ol>) to Markdown lists.
        5. **Output**: Return ONLY the generated Markdown. Do not wrap it in "```markdown" code blocks. Do not add any conversational text.

        HTML Content:
        """

        # Limit HTML size if necessary (Gemini 2.5 Flash has 1M context, so usually fine)
        html_str = str(soup)

        response = model.generate_content(
            [prompt, html_str],
            generation_config=GenerationConfig(temperature=0.1)
        )

        return response.text
    except Exception as e: # pylint: disable=broad-exception-caught
        return f"Error during LLM extraction: {e}"

def _process_images(soup, base_url, output_dir):
    """Helper to download and replace images."""
    # pylint: disable=too-many-locals
    # Handle Images
    gcs_bucket = os.environ.get("GCS_BUCKET_NAME")

    # Fallback: If running in Cloud Run (K_SERVICE is set) and no bucket provided, use default
    if not gcs_bucket and os.environ.get("K_SERVICE"):
        gcs_bucket = "web-to-md-bucket-7d4c11"

    assets_dir = os.path.join(output_dir, "assets")

    if not gcs_bucket:
        os.makedirs(assets_dir, exist_ok=True)

    images = soup.find_all('img')
    for img in images:
        src = img.get('src')
        if not src:
            continue

        img_url = urljoin(base_url, src)

        # Generate a safe filename
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                              'AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/91.0.4472.124 Safari/537.36'
            }
            img_resp = requests.get(img_url, headers=headers, timeout=10)
            img_data = img_resp.content
            content_type = img_resp.headers.get('Content-Type', 'image/jpeg')

            # Hash content to avoid duplicates and weird filenames
            img_hash = hashlib.md5(img_data).hexdigest()
            ext = os.path.splitext(urlparse(img_url).path)[1]
            if not ext:
                ext = ".jpg" # Default fallback

            filename = f"{img_hash}{ext}"

            if gcs_bucket:
                # Upload to GCS
                # Construct blob path respecting output_dir
                # Ensure output_dir doesn't start with ./ or / if likely to be used as GCS prefix
                prefix = output_dir.strip("./")
                blob_name = f"{prefix}/assets/{filename}" if prefix else f"assets/{filename}"

                gcs_url = upload_to_gcs(gcs_bucket, blob_name, img_data, content_type)
                if gcs_url:
                    img['src'] = gcs_url
            else:
                # Save locally
                file_path = os.path.join(assets_dir, filename)
                with open(file_path, 'wb') as f:
                    f.write(img_data)
                # Update src to point to local file (relative path for markdown)
                img['src'] = f"assets/{filename}"

        except Exception as e: # pylint: disable=broad-exception-caught
            print(f"Failed to process image {img_url}: {e}")


def save_text_to_gcs(bucket_name: str, blob_name: str, content: str) -> str:
    """Uploads text content to GCS. Raises RuntimeError on failure."""
    return upload_to_gcs(bucket_name, blob_name, content.encode('utf-8'), 'text/markdown')
