import os
from unittest.mock import MagicMock, patch
from app.config import config
from app.tools import save_screenshot_to_bucket

def test_screenshot_config():
    os.environ["SCREENSHOTS_BUCKET_NAME"] = "test-bucket"
    
    # Mock get_current_screen to return dummy data
    with patch("app.tools.get_current_screen") as mock_get_screen:
        mock_get_screen.return_value = {
            "captured_at": "2026-06-13T10:00:00Z",
            "frame_key": "frame.jpg"
        }
        
        # Mock urllib.request.urlopen to return dummy image data
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = b"fake-image-data"
            mock_resp.headers = {"Content-Type": "image/jpeg"}
            mock_resp.__enter__.return_value = mock_resp
            mock_urlopen.return_value = mock_resp
            
            # Mock google.cloud.storage.Client
            with patch("google.cloud.storage.Client") as mock_storage:
                mock_client = MagicMock()
                mock_bucket = MagicMock()
                mock_blob = MagicMock()
                mock_storage.return_value = mock_client
                mock_client.bucket.return_value = mock_bucket
                mock_bucket.blob.return_value = mock_blob
                
                result = save_screenshot_to_bucket("keynotes")
                
                print(f"Result: {result}")
                assert result["status"] == "success"
                assert "test-bucket" in result["gcs_uri"]
                mock_bucket.blob.assert_called_with("keynotes/2026-06-13T10-00-00Z.jpg")

if __name__ == "__main__":
    try:
        test_screenshot_config()
        print("✅ Screenshot configuration test passed")
    except Exception as e:
        print(f"❌ Screenshot configuration test failed: {e}")
        import traceback
        traceback.print_exc()
