"""
Fixtures and utilities for UI testing.

This module provides a fake customtkinter implementation that allows
testing the UI logic without requiring the actual GUI library.
"""

import sys
import types
from unittest.mock import MagicMock


class FakeCTk:
    """Fake CTk main window class."""
    
    def __init__(self, *args, **kwargs):
        pass
    
    def geometry(self, *args):
        pass
    
    def resizable(self, *args):
        pass
    
    def title(self, *args):
        pass
    
    def mainloop(self):
        pass
    
    def after(self, ms, func, *args):
        """Force synchronous execution of callbacks for testing."""
        if func:
            func(*args)


class FakeWidget:
    """Fake widget class for all CTk widgets."""
    
    def __init__(self, *args, **kwargs):
        self._value = "12345"  # Default value for entry
    
    def pack(self, *args, **kwargs):
        pass
    
    def configure(self, *args, **kwargs):
        pass
    
    def get(self):
        return self._value
    
    def insert(self, *args):
        pass
    
    def see(self, *args):
        pass
    
    def set(self, val):
        self._value = val


def setup_fake_customtkinter():
    """
    Setup a fake customtkinter module for testing.
    
    This must be called before importing any modules that depend on customtkinter.
    Returns the fake module for further customization if needed.
    """
    fake_ctk_module = types.ModuleType("customtkinter")
    
    # Assign fake classes
    fake_ctk_module.CTk = FakeCTk
    fake_ctk_module.CTkButton = FakeWidget
    fake_ctk_module.CTkEntry = FakeWidget
    fake_ctk_module.CTkLabel = FakeWidget
    fake_ctk_module.CTkProgressBar = FakeWidget
    fake_ctk_module.CTkTextbox = FakeWidget
    fake_ctk_module.CTkOptionMenu = FakeWidget
    fake_ctk_module.StringVar = MagicMock
    fake_ctk_module.set_appearance_mode = MagicMock()
    fake_ctk_module.set_default_color_theme = MagicMock()
    
    # Inject into sys.modules
    sys.modules['customtkinter'] = fake_ctk_module
    
    return fake_ctk_module


def create_mock_app_widgets(app):
    """
    Setup mock widgets for a DotaRaceApp instance.
    
    Args:
        app: DotaRaceApp instance to configure
    
    Returns:
        Dict of mock widgets for easy access in tests
    """
    mocks = {
        'log_box': MagicMock(),
        'entry_id': MagicMock(),
        'progress': MagicMock(),
        'progress_label': MagicMock(),
        'btn_run': MagicMock()
    }
    
    # Configure entry to return a default Steam ID
    mocks['entry_id'].get.return_value = "12345"
    
    # Apply mocks to app
    for attr, mock_obj in mocks.items():
        setattr(app, attr, mock_obj)
    
    return mocks
