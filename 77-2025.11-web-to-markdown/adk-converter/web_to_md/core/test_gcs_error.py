"""
Tests for GCS error handling.
"""
from unittest.mock import patch, MagicMock
import pytest
from web_to_md.core.scraper import save_text_to_gcs

# pylint: disable=redefined-outer-name

def test_save_text_to_gcs_failure():
    """Test that save_text_to_gcs raises RuntimeError on failure."""
    with patch("web_to_md.core.scraper.GCS_AVAILABLE", True):
        with patch("web_to_md.core.scraper.storage") as mock_storage:
            mock_client = MagicMock()
            mock_storage.Client.return_value = mock_client
            mock_bucket = MagicMock()
            mock_client.bucket.return_value = mock_bucket
            mock_blob = MagicMock()
            mock_bucket.blob.return_value = mock_blob

            # Simulate upload failure
            mock_blob.exists.side_effect = Exception("Permission denied")

            with pytest.raises(RuntimeError, match="GCS Upload Error: Permission denied"):
                save_text_to_gcs("my-bucket", "my-blob", "content")

def test_save_text_to_gcs_no_library():
    """Test that save_text_to_gcs raises RuntimeError if GCS lib is missing."""
    with patch("web_to_md.core.scraper.GCS_AVAILABLE", False):
        with pytest.raises(RuntimeError, match="GCS library not available"):
            save_text_to_gcs("my-bucket", "my-blob", "content")
