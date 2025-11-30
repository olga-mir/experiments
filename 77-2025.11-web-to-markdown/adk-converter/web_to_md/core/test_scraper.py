"""
Tests for scraper module.
"""
from unittest.mock import patch, MagicMock
from web_to_md.core.scraper import scrape_to_markdown

@patch("web_to_md.core.scraper.requests.get")
@patch("web_to_md.core.scraper.vertexai.init")
@patch("web_to_md.core.scraper.GenerativeModel")
def test_scrape_to_markdown(mock_model_cls, mock_init, mock_get): # pylint: disable=unused-argument
    """Test basic scraping flow with mocks."""
    # Mock requests
    mock_response = MagicMock()
    mock_response.content = b"<html><body><h1>Test</h1></body></html>"
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    # Mock Vertex AI
    mock_model = MagicMock()
    mock_response_gen = MagicMock()
    mock_response_gen.text = "# Test\n\nParsed content"
    mock_model.generate_content.return_value = mock_response_gen
    mock_model_cls.return_value = mock_model

    # Run
    result = scrape_to_markdown("http://example.com")

    # Verify
    assert result == "# Test\n\nParsed content"
    mock_get.assert_called_once()
    mock_model.generate_content.assert_called_once()

    # Verify prompt contains instructions
    call_args = mock_model.generate_content.call_args
    # call_args[0] is positional args, which is [[prompt, html_str], generation_config=...]
    # Actually, scraper calls: model.generate_content([prompt, html_str], ...)
    # So the first arg is the list contents.
    content_list = call_args[0][0]
    prompt_text = content_list[0]

    assert "Preserve Images" in prompt_text
    assert "Format Content" in prompt_text
    assert "MUST infer the correct language" in prompt_text
