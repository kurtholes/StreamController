"""
Tests for src/backend/DeckManagement/HelperMethods.py
"""
import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Import after conftest.py sets up mocks
from src.backend.DeckManagement.HelperMethods import (
    sha256,
    file_in_dir,
    recursive_hasattr,
    get_last_dir,
    has_dict_recursive,
    is_video,
    is_image,
    is_svg,
    create_empty_json,
    get_file_name_from_url,
    natural_keys,
    natural_sort,
    natural_sort_by_filenames,
    add_default_keys,
    get_sub_folders,
    sort_times,
    open_web,
)


class TestSha256:
    """Tests for sha256 function."""

    def test_sha256_string(self):
        """Test hashing a plain string."""
        result = sha256("hello")
        assert len(result) == 64  # SHA256 produces 64 hex chars
        assert result == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"

    def test_sha256_file(self, sample_text_file):
        """Test hashing a file's contents."""
        result = sha256(str(sample_text_file))
        assert len(result) == 64

    def test_sha256_different_inputs(self):
        """Test that different inputs produce different hashes."""
        hash1 = sha256("hello")
        hash2 = sha256("world")
        assert hash1 != hash2

    def test_sha256_same_input(self):
        """Test that same input produces same hash."""
        assert sha256("test") == sha256("test")


class TestFileInDir:
    """Tests for file_in_dir function."""

    def test_file_exists_in_dir(self, tmp_path):
        """Test when file exists in directory."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        assert file_in_dir(str(test_file), str(tmp_path)) is True

    def test_file_not_in_dir(self, tmp_path):
        """Test when file doesn't exist in directory."""
        assert file_in_dir("nonexistent.txt", str(tmp_path)) is False

    def test_invalid_directory(self):
        """Test with non-existent directory."""
        result = file_in_dir("test.txt", "/nonexistent/path")
        assert result is None


class TestRecursiveHasattr:
    """Tests for recursive_hasattr function."""

    def test_single_level(self):
        """Test with single attribute."""
        class Obj:
            foo = "bar"
        obj = Obj()
        assert recursive_hasattr(obj, "foo") is True
        assert recursive_hasattr(obj, "baz") is False

    def test_nested_attributes(self):
        """Test with nested attributes."""
        class Inner:
            baz = "value"
        class Middle:
            bar = Inner()
        class Outer:
            foo = Middle()
        obj = Outer()
        assert recursive_hasattr(obj, "foo.bar.baz") is True
        assert recursive_hasattr(obj, "foo.bar.missing") is False

    def test_missing_intermediate(self):
        """Test when intermediate attribute is missing."""
        class Obj:
            pass
        obj = Obj()
        assert recursive_hasattr(obj, "foo.bar") is False


class TestGetLastDir:
    """Tests for get_last_dir function."""

    def test_directory_path(self, tmp_path):
        """Test with directory path."""
        sub_dir = tmp_path / "subdir"
        sub_dir.mkdir()
        assert get_last_dir(str(sub_dir)) == "subdir"

    def test_file_path(self, tmp_path):
        """Test with file path - returns parent dir name."""
        sub_dir = tmp_path / "subdir"
        sub_dir.mkdir()
        test_file = sub_dir / "test.txt"
        test_file.write_text("content")
        assert get_last_dir(str(test_file)) == "subdir"

    def test_nonexistent_path(self):
        """Test with non-existent path."""
        result = get_last_dir("/nonexistent/path")
        assert result is None


class TestHasDictRecursive:
    """Tests for has_dict_recursive function."""

    def test_single_key(self):
        """Test with single key."""
        d = {"foo": "bar"}
        assert has_dict_recursive(d, "foo") is True
        assert has_dict_recursive(d, "baz") is False

    def test_nested_keys(self):
        """Test with nested keys."""
        d = {"foo": {"bar": {"baz": "value"}}}
        assert has_dict_recursive(d, "foo", "bar", "baz") is True
        assert has_dict_recursive(d, "foo", "bar", "missing") is False

    def test_empty_dict(self):
        """Test with empty dictionary."""
        assert has_dict_recursive({}, "foo") is False


class TestIsVideo:
    """Tests for is_video function."""

    def test_video_file(self, tmp_path):
        """Test with video file extension."""
        video_file = tmp_path / "video.mp4"
        video_file.write_bytes(b"fake video content")
        assert is_video(str(video_file)) is True

    def test_non_video_file(self, tmp_path):
        """Test with non-video file."""
        text_file = tmp_path / "text.txt"
        text_file.write_text("content")
        assert is_video(str(text_file)) is False

    def test_none_input(self):
        """Test with None input."""
        assert is_video(None) is None

    def test_nonexistent_file(self):
        """Test with non-existent file."""
        assert is_video("/nonexistent/video.mp4") is False


class TestIsImage:
    """Tests for is_image function."""

    def test_image_file(self, tmp_path):
        """Test with image file extension."""
        image_file = tmp_path / "image.png"
        image_file.write_bytes(b"fake image content")
        assert is_image(str(image_file)) is True

    def test_non_image_file(self, tmp_path):
        """Test with non-image file."""
        text_file = tmp_path / "text.txt"
        text_file.write_text("content")
        assert is_image(str(text_file)) is False

    def test_none_input(self):
        """Test with None input."""
        assert is_image(None) is False


class TestIsSvg:
    """Tests for is_svg function."""

    def test_svg_file(self, tmp_path):
        """Test with SVG file."""
        svg_file = tmp_path / "image.svg"
        svg_file.write_text("<svg></svg>")
        assert is_svg(str(svg_file)) is True

    def test_svg_string(self):
        """Test with SVG string content."""
        assert is_svg("<svg xmlns='...'></svg>") is True

    def test_non_svg(self, tmp_path):
        """Test with non-SVG file."""
        text_file = tmp_path / "text.txt"
        text_file.write_text("content")
        assert is_svg(str(text_file)) is False

    def test_none_input(self):
        """Test with None input."""
        assert is_svg(None) is False


class TestCreateEmptyJson:
    """Tests for create_empty_json function."""

    def test_creates_empty_json(self, tmp_path):
        """Test creating empty JSON file."""
        json_path = tmp_path / "subdir" / "test.json"
        create_empty_json(str(json_path))

        assert json_path.exists()
        with open(json_path) as f:
            content = json.load(f)
        assert content == {}

    def test_does_not_overwrite_existing(self, tmp_path):
        """Test that existing file is not overwritten."""
        json_path = tmp_path / "test.json"
        json_path.write_text('{"existing": "data"}')

        create_empty_json(str(json_path))

        with open(json_path) as f:
            content = json.load(f)
        assert content == {"existing": "data"}

    def test_overwrite_when_ignore_present(self, tmp_path):
        """Test overwriting when ignore_present is True."""
        json_path = tmp_path / "test.json"
        json_path.write_text('{"existing": "data"}')

        create_empty_json(str(json_path), ignore_present=True)

        with open(json_path) as f:
            content = json.load(f)
        assert content == {}


class TestGetFileNameFromUrl:
    """Tests for get_file_name_from_url function."""

    def test_simple_url(self):
        """Test with simple URL."""
        url = "https://example.com/path/to/file.zip"
        assert get_file_name_from_url(url) == "file.zip"

    def test_url_with_query_params(self):
        """Test URL with query parameters."""
        url = "https://example.com/file.tar.gz?token=abc"
        # Note: This will include query params in the path component
        result = get_file_name_from_url(url)
        assert "file.tar.gz" in result

    def test_url_without_filename(self):
        """Test URL ending with slash."""
        url = "https://example.com/path/"
        assert get_file_name_from_url(url) == ""


class TestNaturalSort:
    """Tests for natural_keys and natural_sort functions."""

    def test_natural_keys(self):
        """Test natural_keys extracts numbers correctly."""
        assert natural_keys("file10") == ["file", 10, ""]
        assert natural_keys("file2") == ["file", 2, ""]

    def test_natural_sort(self):
        """Test natural sorting of strings."""
        items = ["file10", "file2", "file1", "file20"]
        result = natural_sort(items)
        assert result == ["file1", "file2", "file10", "file20"]

    def test_natural_sort_by_filenames(self):
        """Test natural sorting by filename in paths."""
        paths = ["/path/file10.txt", "/path/file2.txt", "/path/file1.txt"]
        result = natural_sort_by_filenames(paths)
        assert result == ["/path/file1.txt", "/path/file2.txt", "/path/file10.txt"]


class TestAddDefaultKeys:
    """Tests for add_default_keys function."""

    def test_add_single_key(self):
        """Test adding a single key."""
        d = {}
        add_default_keys(d, ["foo"])
        assert d == {"foo": {}}

    def test_add_nested_keys(self):
        """Test adding nested keys."""
        d = {}
        add_default_keys(d, ["foo", "bar", "baz"])
        assert d == {"foo": {"bar": {"baz": {}}}}

    def test_existing_keys_preserved(self):
        """Test that existing keys are preserved."""
        d = {"foo": {"existing": "value"}}
        add_default_keys(d, ["foo", "bar"])
        assert d == {"foo": {"existing": "value", "bar": {}}}


class TestGetSubFolders:
    """Tests for get_sub_folders function."""

    def test_returns_subfolders(self, tmp_path):
        """Test returning list of subfolders."""
        (tmp_path / "folder1").mkdir()
        (tmp_path / "folder2").mkdir()
        (tmp_path / "file.txt").write_text("content")

        result = get_sub_folders(str(tmp_path))
        assert set(result) == {"folder1", "folder2"}

    def test_empty_directory(self, tmp_path):
        """Test with empty directory."""
        result = get_sub_folders(str(tmp_path))
        assert result == []

    def test_nonexistent_directory(self):
        """Test with non-existent directory."""
        result = get_sub_folders("/nonexistent/path")
        assert result == []


class TestSortTimes:
    """Tests for sort_times function."""

    def test_sort_iso_times(self):
        """Test sorting ISO format times."""
        times = [
            "2024-03-15T10:30:00",
            "2024-01-01T00:00:00",
            "2024-02-20T15:45:00"
        ]
        result = sort_times(times)
        assert result == [
            "2024-01-01T00:00:00",
            "2024-02-20T15:45:00",
            "2024-03-15T10:30:00"
        ]


class TestOpenWeb:
    """Tests for open_web function - security-critical."""

    @patch('webbrowser.open')
    def test_opens_https_url(self, mock_open):
        """Test opening HTTPS URL."""
        open_web("https://example.com")
        mock_open.assert_called_once_with("https://example.com")

    @patch('webbrowser.open')
    def test_opens_http_url(self, mock_open):
        """Test opening HTTP URL."""
        open_web("http://example.com")
        mock_open.assert_called_once_with("http://example.com")

    @patch('webbrowser.open')
    def test_adds_https_prefix(self, mock_open):
        """Test that URLs without scheme get https:// prefix."""
        open_web("example.com")
        mock_open.assert_called_once_with("https://example.com")

    @patch('webbrowser.open')
    def test_rejects_file_scheme(self, mock_open):
        """Test that file:// URLs are rejected (security)."""
        open_web("file:///etc/passwd")
        mock_open.assert_not_called()

    @patch('webbrowser.open')
    def test_rejects_javascript_scheme(self, mock_open):
        """Test that javascript: URLs are rejected (security)."""
        open_web("javascript:alert(1)")
        mock_open.assert_not_called()

    @patch('webbrowser.open')
    def test_empty_url(self, mock_open):
        """Test with empty URL."""
        open_web("")
        mock_open.assert_not_called()

    @patch('webbrowser.open')
    def test_none_url(self, mock_open):
        """Test with None URL."""
        open_web(None)
        mock_open.assert_not_called()
