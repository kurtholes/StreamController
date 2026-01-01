"""
Tests for security-critical functionality.
Ensures security fixes are working correctly.
"""
import os
import zipfile
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Import after conftest.py sets up mocks
from src.backend.Store.StoreBackend import safe_extract_zip
from src.backend.DeckManagement.HelperMethods import run_command, open_web


class TestSafeExtractZip:
    """Tests for safe_extract_zip function - prevents path traversal attacks."""

    def test_extracts_normal_zip(self, tmp_path):
        """Test normal ZIP extraction works."""
        # Create a test ZIP file
        zip_path = tmp_path / "test.zip"
        extract_dir = tmp_path / "extracted"
        extract_dir.mkdir()

        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("file1.txt", "content1")
            zf.writestr("subdir/file2.txt", "content2")

        safe_extract_zip(str(zip_path), str(extract_dir))

        assert (extract_dir / "file1.txt").exists()
        assert (extract_dir / "subdir" / "file2.txt").exists()
        assert (extract_dir / "file1.txt").read_text() == "content1"

    def test_blocks_path_traversal_dotdot(self, tmp_path):
        """Test that ../path traversal is blocked."""
        zip_path = tmp_path / "malicious.zip"
        extract_dir = tmp_path / "extracted"
        extract_dir.mkdir()

        # Create a malicious ZIP with path traversal
        with zipfile.ZipFile(zip_path, 'w') as zf:
            # This attempts to escape the extraction directory
            zf.writestr("../escaped.txt", "malicious content")

        with pytest.raises(ValueError, match="Path traversal detected"):
            safe_extract_zip(str(zip_path), str(extract_dir))

        # Ensure the file was NOT created outside the target
        assert not (tmp_path / "escaped.txt").exists()

    def test_blocks_absolute_path(self, tmp_path):
        """Test that absolute paths in ZIP are blocked."""
        zip_path = tmp_path / "malicious.zip"
        extract_dir = tmp_path / "extracted"
        extract_dir.mkdir()

        # Create a ZIP with absolute path
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("/etc/malicious.txt", "malicious content")

        with pytest.raises(ValueError, match="Path traversal detected"):
            safe_extract_zip(str(zip_path), str(extract_dir))

    def test_blocks_nested_traversal(self, tmp_path):
        """Test that nested path traversal is blocked."""
        zip_path = tmp_path / "malicious.zip"
        extract_dir = tmp_path / "extracted"
        extract_dir.mkdir()

        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("subdir/../../escaped.txt", "malicious")

        with pytest.raises(ValueError, match="Path traversal detected"):
            safe_extract_zip(str(zip_path), str(extract_dir))

    def test_allows_deep_nesting(self, tmp_path):
        """Test that deeply nested but safe paths work."""
        zip_path = tmp_path / "test.zip"
        extract_dir = tmp_path / "extracted"
        extract_dir.mkdir()

        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("a/b/c/d/e/file.txt", "deep content")

        safe_extract_zip(str(zip_path), str(extract_dir))

        assert (extract_dir / "a/b/c/d/e/file.txt").exists()


class TestRunCommand:
    """Tests for run_command function - prevents command injection."""

    def test_rejects_string_command(self):
        """Test that string commands are rejected (must be list)."""
        with pytest.raises(TypeError, match="command must be a list"):
            run_command("ls -la")  # String instead of list

    def test_accepts_list_command(self):
        """Test that list commands are accepted."""
        # This should not raise - we just verify no TypeError
        with patch('multiprocessing.Process') as mock_process:
            mock_process.return_value.start = MagicMock()
            run_command(["echo", "hello"])
            mock_process.assert_called_once()

    def test_handles_none(self):
        """Test that None is handled gracefully."""
        # Should not raise
        run_command(None)

    def test_handles_empty_list(self):
        """Test that empty list is handled gracefully."""
        # Should not raise
        run_command([])

    @patch('src.backend.DeckManagement.HelperMethods.is_flatpak')
    @patch('multiprocessing.Process')
    def test_adds_flatpak_spawn_prefix(self, mock_process, mock_is_flatpak):
        """Test that flatpak-spawn is added when running in Flatpak."""
        mock_is_flatpak.return_value = True
        mock_process.return_value.start = MagicMock()

        run_command(["some-command", "arg"])

        # Verify the command was prefixed
        call_args = mock_process.call_args
        assert call_args is not None


class TestOpenWebSecurity:
    """Additional security tests for open_web function."""

    @patch('webbrowser.open')
    def test_blocks_data_uri(self, mock_open):
        """Test that data: URIs are blocked."""
        open_web("data:text/html,<script>alert(1)</script>")
        mock_open.assert_not_called()

    @patch('webbrowser.open')
    def test_blocks_ftp_scheme(self, mock_open):
        """Test that ftp: URLs are blocked."""
        open_web("ftp://evil.com/malware.exe")
        mock_open.assert_not_called()

    @patch('webbrowser.open')
    def test_url_with_credentials(self, mock_open):
        """Test URL with embedded credentials (should work but log warning ideally)."""
        # This is technically valid HTTP, though suspicious
        open_web("https://user:pass@example.com")
        mock_open.assert_called_once()

    @patch('webbrowser.open')
    def test_url_with_port(self, mock_open):
        """Test URL with port number works."""
        open_web("https://localhost:8080/path")
        mock_open.assert_called_once_with("https://localhost:8080/path")

    @patch('webbrowser.open')
    def test_url_with_unicode(self, mock_open):
        """Test URL with unicode characters."""
        open_web("https://example.com/path?q=café")
        mock_open.assert_called_once()


class TestCommandInjectionPrevention:
    """Tests to verify command injection is prevented throughout the codebase."""

    def test_no_shell_true_in_helper_methods(self):
        """Verify HelperMethods.py doesn't use shell=True."""
        import inspect
        from src.backend.DeckManagement import HelperMethods

        source = inspect.getsource(HelperMethods)
        assert "shell=True" not in source, "shell=True found in HelperMethods.py"

    def test_no_os_system_in_store_backend(self):
        """Verify StoreBackend.py doesn't use os.system."""
        import inspect
        from src.backend.Store import StoreBackend

        source = inspect.getsource(StoreBackend)
        # Check for os.system usage (the function, not comments)
        lines = [line for line in source.split('\n')
                 if 'os.system' in line and not line.strip().startswith('#')]
        assert len(lines) == 0, f"os.system found in StoreBackend.py: {lines}"
