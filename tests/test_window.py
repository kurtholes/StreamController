"""
Tests for src/backend/WindowGrabber/Window.py
"""
import pytest
from dataclasses import is_dataclass

from src.backend.WindowGrabber.Window import Window


class TestWindow:
    """Tests for Window dataclass."""

    def test_is_dataclass(self):
        """Verify Window is a dataclass."""
        assert is_dataclass(Window)

    def test_create_window(self):
        """Test creating a Window instance."""
        window = Window(wm_class="firefox", title="Mozilla Firefox")
        assert window.wm_class == "firefox"
        assert window.title == "Mozilla Firefox"

    def test_window_equality(self):
        """Test that windows with same attributes are equal."""
        window1 = Window(wm_class="code", title="Visual Studio Code")
        window2 = Window(wm_class="code", title="Visual Studio Code")
        assert window1 == window2

    def test_window_inequality_class(self):
        """Test that windows with different wm_class are not equal."""
        window1 = Window(wm_class="firefox", title="Browser")
        window2 = Window(wm_class="chrome", title="Browser")
        assert window1 != window2

    def test_window_inequality_title(self):
        """Test that windows with different titles are not equal."""
        window1 = Window(wm_class="firefox", title="Tab 1")
        window2 = Window(wm_class="firefox", title="Tab 2")
        assert window1 != window2

    def test_window_with_empty_strings(self):
        """Test creating window with empty strings."""
        window = Window(wm_class="", title="")
        assert window.wm_class == ""
        assert window.title == ""

    def test_window_with_special_characters(self):
        """Test creating window with special characters."""
        window = Window(
            wm_class="org.gnome.Nautilus",
            title="Files - /home/user/Documents & Photos"
        )
        assert window.wm_class == "org.gnome.Nautilus"
        assert "&" in window.title

    def test_window_with_unicode(self):
        """Test creating window with unicode characters."""
        window = Window(wm_class="terminal", title="日本語タイトル 🎮")
        assert window.title == "日本語タイトル 🎮"

    def test_window_repr(self):
        """Test string representation of Window."""
        window = Window(wm_class="app", title="My App")
        repr_str = repr(window)
        assert "app" in repr_str
        assert "My App" in repr_str

    def test_window_not_hashable_by_default(self):
        """Test that Window is not hashable (standard dataclass behavior)."""
        window = Window(wm_class="app", title="App")

        # Standard dataclass is not hashable by default
        with pytest.raises(TypeError, match="unhashable"):
            hash(window)
