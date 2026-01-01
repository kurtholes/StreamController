"""
Tests for src/backend/Store/StoreBackend.py
"""
import os
import zipfile
import pytest
from unittest.mock import MagicMock, patch

# Import after conftest.py sets up mocks
from src.backend.Store.StoreBackend import StoreBackend, safe_extract_zip


@pytest.fixture
def store_backend():
    """Create a StoreBackend instance for testing."""
    with patch.object(StoreBackend, '__init__', lambda x: None):
        backend = StoreBackend()
        backend.STORE_REPO_URL = "https://github.com/StreamController/StreamController-Store"
        backend.STORE_BRANCH = "main"
        return backend


class TestGetUserName:
    """Tests for get_user_name method."""

    def test_standard_github_url(self, store_backend):
        """Test extracting username from standard GitHub URL."""
        url = "https://github.com/StreamController/StreamController"
        result = store_backend.get_user_name(url)
        assert result == "StreamController"

    def test_github_url_with_git_suffix(self, store_backend):
        """Test extracting username from GitHub URL with .git suffix."""
        url = "https://github.com/user123/repo.git"
        result = store_backend.get_user_name(url)
        assert result == "user123"

    def test_github_url_with_path(self, store_backend):
        """Test extracting username from GitHub URL with additional path."""
        url = "https://github.com/myorg/myrepo/tree/main"
        result = store_backend.get_user_name(url)
        assert result == "myorg"


class TestGetRepoName:
    """Tests for get_repo_name method."""

    def test_standard_github_url(self, store_backend):
        """Test extracting repo name from standard GitHub URL."""
        url = "https://github.com/StreamController/StreamController"
        result = store_backend.get_repo_name(url)
        assert result == "StreamController"

    def test_github_url_with_path(self, store_backend):
        """Test extracting repo name from URL with additional path."""
        url = "https://github.com/user/myrepo/tree/main"
        result = store_backend.get_repo_name(url)
        assert result == "myrepo"

    def test_invalid_url_no_github(self, store_backend):
        """Test with URL not containing github."""
        url = "https://gitlab.com/user/repo"
        result = store_backend.get_repo_name(url)
        assert result is None

    def test_incomplete_url(self, store_backend):
        """Test with incomplete GitHub URL."""
        url = "https://github.com/user"
        result = store_backend.get_repo_name(url)
        assert result is None


class TestBuildUrl:
    """Tests for build_url method."""

    def test_builds_raw_content_url(self, store_backend):
        """Test building raw content URL."""
        repo_url = "https://github.com/user/repo"
        file_path = "path/to/file.json"
        branch = "main"

        result = store_backend.build_url(repo_url, file_path, branch)

        assert "raw.githubusercontent.com" in result
        assert "user" in result
        assert "repo" in result
        assert "main" in result
        assert "path/to/file.json" in result

    def test_with_different_branch(self, store_backend):
        """Test with non-main branch."""
        repo_url = "https://github.com/user/repo"
        file_path = "README.md"
        branch = "develop"

        result = store_backend.build_url(repo_url, file_path, branch)

        assert "develop" in result


class TestGetMainFolderOfZip:
    """Tests for get_main_folder_of_zip method."""

    def test_single_folder_zip(self, store_backend, tmp_path):
        """Test ZIP with single top-level folder."""
        zip_path = tmp_path / "test.zip"

        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("myproject/", "")  # Directory entry
            zf.writestr("myproject/file.txt", "content")
            zf.writestr("myproject/subdir/", "")
            zf.writestr("myproject/subdir/file2.txt", "content2")

        result = store_backend.get_main_folder_of_zip(str(zip_path))
        assert result == "myproject"

    def test_multiple_folders_returns_error(self, store_backend, tmp_path):
        """Test ZIP with multiple top-level folders returns error."""
        zip_path = tmp_path / "test.zip"

        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("folder1/", "")
            zf.writestr("folder1/file.txt", "content")
            zf.writestr("folder2/", "")
            zf.writestr("folder2/file.txt", "content")

        result = store_backend.get_main_folder_of_zip(str(zip_path))
        assert result == 400  # Error code

    def test_no_folder_returns_error(self, store_backend, tmp_path):
        """Test ZIP with no folder returns error."""
        zip_path = tmp_path / "test.zip"

        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("file.txt", "content")  # No directory entries

        result = store_backend.get_main_folder_of_zip(str(zip_path))
        assert result == 400  # Error code


class TestSafeExtractZipIntegration:
    """Integration tests for safe_extract_zip with StoreBackend."""

    def test_extract_plugin_style_zip(self, tmp_path):
        """Test extracting a ZIP in the style of plugin downloads."""
        zip_path = tmp_path / "plugin-abc123.zip"
        extract_dir = tmp_path / "cache"
        extract_dir.mkdir()

        # Create a ZIP like GitHub generates
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("plugin-abc123/", "")
            zf.writestr("plugin-abc123/manifest.json", '{"name": "test"}')
            zf.writestr("plugin-abc123/main.py", "# plugin code")
            zf.writestr("plugin-abc123/assets/", "")
            zf.writestr("plugin-abc123/assets/icon.png", b"fake png")

        safe_extract_zip(str(zip_path), str(extract_dir))

        assert (extract_dir / "plugin-abc123" / "manifest.json").exists()
        assert (extract_dir / "plugin-abc123" / "main.py").exists()
        assert (extract_dir / "plugin-abc123" / "assets" / "icon.png").exists()

    def test_extract_preserves_file_content(self, tmp_path):
        """Test that file content is preserved during extraction."""
        zip_path = tmp_path / "test.zip"
        extract_dir = tmp_path / "extracted"
        extract_dir.mkdir()

        content = "Hello, StreamController!"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("file.txt", content)

        safe_extract_zip(str(zip_path), str(extract_dir))

        assert (extract_dir / "file.txt").read_text() == content
