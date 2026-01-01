"""
Pytest configuration and fixtures for StreamController tests.
"""
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add the project root to the path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Mock all external dependencies before they're imported
# GTK and GUI modules
sys.modules['gi'] = MagicMock()
sys.modules['gi.repository'] = MagicMock()
sys.modules['gi.repository.Gtk'] = MagicMock()
sys.modules['gi.repository.Gdk'] = MagicMock()
sys.modules['gi.repository.Adw'] = MagicMock()
sys.modules['gi.repository.GLib'] = MagicMock()
sys.modules['gi.repository.Pango'] = MagicMock()
sys.modules['gi.repository.Xdp'] = MagicMock()

# Scientific/image libraries
sys.modules['matplotlib'] = MagicMock()
sys.modules['matplotlib.font_manager'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()
sys.modules['cairosvg'] = MagicMock()

# Async and network libraries
sys.modules['async_lru'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['rpyc'] = MagicMock()
sys.modules['rpyc.utils'] = MagicMock()
sys.modules['rpyc.utils.server'] = MagicMock()
sys.modules['rpyc.core'] = MagicMock()
sys.modules['rpyc.core.protocol'] = MagicMock()
sys.modules['rpyc.core.netref'] = MagicMock()
sys.modules['packaging'] = MagicMock()
sys.modules['packaging.version'] = MagicMock()

# Logging
mock_logger = MagicMock()
mock_logger.catch = lambda: lambda f: f  # Make @log.catch a no-op decorator
sys.modules['loguru'] = MagicMock()
sys.modules['loguru'].logger = mock_logger

# Mock globals module
mock_globals = MagicMock()
mock_globals.IS_MAC = False
mock_globals.threads_running = True
mock_globals.video_extensions = ['mp4', 'avi', 'mkv', 'mov', 'webm']
mock_globals.image_extensions = ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp']
mock_globals.svg_extensions = ['svg']
mock_globals.DATA_PATH = '/tmp/streamcontroller'
mock_globals.PLUGIN_DIR = '/tmp/streamcontroller/plugins'
sys.modules['globals'] = mock_globals

# Mock autostart module
mock_autostart = MagicMock()
mock_autostart.is_flatpak = MagicMock(return_value=False)
sys.modules['autostart'] = mock_autostart

# Mock internal modules that may have complex dependencies
sys.modules['src.backend.PluginManager.ActionHolderGroup'] = MagicMock()
sys.modules['src.backend.PluginManager.PluginSettings'] = MagicMock()
sys.modules['src.backend.PluginManager.PluginSettings.Asset'] = MagicMock()
sys.modules['src.backend.PluginManager.PluginSettings.PluginAssetManager'] = MagicMock()
sys.modules['locales'] = MagicMock()
sys.modules['locales.LocaleManager'] = MagicMock()
sys.modules['src.Signals'] = MagicMock()
sys.modules['src.backend.Store.StoreCache'] = MagicMock()
sys.modules['src.backend.PluginManager.PluginBase'] = MagicMock()
sys.modules['src.windows.Store.StoreData'] = MagicMock()

# Mock GtkHelper
sys.modules['GtkHelper'] = MagicMock()
sys.modules['GtkHelper.GtkHelper'] = MagicMock()


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for tests."""
    return tmp_path


@pytest.fixture
def sample_text_file(tmp_path):
    """Create a sample text file for testing."""
    file_path = tmp_path / "sample.txt"
    file_path.write_text("Hello, World!")
    return file_path
