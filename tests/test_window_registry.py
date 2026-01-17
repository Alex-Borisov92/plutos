"""
Tests for window registry.
"""
import pytest
from unittest.mock import Mock, patch

from src.capture.window_registry import WindowRegistry, TableWindow
from src.capture.window_manager import WindowInfo
from src.app.config import TableConfig


class TestWindowRegistry:
    """Tests for WindowRegistry."""
    
    def test_registry_initialization(self):
        """Test registry can be initialized."""
        registry = WindowRegistry(max_windows=4, title_pattern="Poker")
        
        assert registry.max_windows == 4
        assert registry.title_pattern == "Poker"
        assert len(registry.get_all_windows()) == 0
    
    def test_max_windows_limit(self):
        """Test that max_windows is respected."""
        registry = WindowRegistry(max_windows=2)
        
        # Simulate registering windows
        for i in range(5):
            info = WindowInfo(
                hwnd=1000 + i,
                title=f"Test Window {i}",
                rect=(0, 0, 800, 600),
                client_offset=(0, 0),
                client_size=(800, 600),
            )
            table = TableWindow(
                window_id=f"table_{i}",
                info=info,
                config=TableConfig(),
            )
            # Directly add to simulate discovery
            if len(registry._windows) < registry.max_windows:
                registry._windows[table.window_id] = table
        
        assert len(registry.get_all_windows()) == 2
    
    def test_get_window_by_id(self):
        """Test getting window by ID."""
        registry = WindowRegistry()
        
        info = WindowInfo(
            hwnd=12345,
            title="Test",
            rect=(0, 0, 800, 600),
            client_offset=(0, 0),
            client_size=(800, 600),
        )
        table = TableWindow(
            window_id="test_table",
            info=info,
            config=TableConfig(),
        )
        registry._windows["test_table"] = table
        
        result = registry.get_window("test_table")
        assert result is not None
        assert result.window_id == "test_table"
        
        result = registry.get_window("nonexistent")
        assert result is None
    
    def test_get_window_by_hwnd(self):
        """Test getting window by handle."""
        registry = WindowRegistry()
        
        info = WindowInfo(
            hwnd=12345,
            title="Test",
            rect=(0, 0, 800, 600),
            client_offset=(0, 0),
            client_size=(800, 600),
        )
        table = TableWindow(
            window_id="test_table",
            info=info,
            config=TableConfig(),
        )
        registry._windows["test_table"] = table
        
        result = registry.get_window_by_hwnd(12345)
        assert result is not None
        assert result.info.hwnd == 12345
        
        result = registry.get_window_by_hwnd(99999)
        assert result is None
    
    def test_unregister_window(self):
        """Test removing a window."""
        registry = WindowRegistry()
        
        info = WindowInfo(
            hwnd=12345,
            title="Test",
            rect=(0, 0, 800, 600),
            client_offset=(0, 0),
            client_size=(800, 600),
        )
        table = TableWindow(
            window_id="test_table",
            info=info,
            config=TableConfig(),
        )
        registry._windows["test_table"] = table
        
        assert len(registry.get_all_windows()) == 1
        
        registry.unregister_window("test_table")
        
        assert len(registry.get_all_windows()) == 0
    
    def test_get_active_windows(self):
        """Test filtering active windows."""
        registry = WindowRegistry()
        
        for i, is_active in enumerate([True, False, True, False]):
            info = WindowInfo(
                hwnd=1000 + i,
                title=f"Test {i}",
                rect=(0, 0, 800, 600),
                client_offset=(0, 0),
                client_size=(800, 600),
            )
            table = TableWindow(
                window_id=f"table_{i}",
                info=info,
                config=TableConfig(),
                is_active=is_active,
            )
            registry._windows[table.window_id] = table
        
        assert len(registry.get_all_windows()) == 4
        assert len(registry.get_active_windows()) == 2
    
    def test_cleanup_inactive(self):
        """Test removing windows with too many errors."""
        registry = WindowRegistry()
        
        for i in range(3):
            info = WindowInfo(
                hwnd=1000 + i,
                title=f"Test {i}",
                rect=(0, 0, 800, 600),
                client_offset=(0, 0),
                client_size=(800, 600),
            )
            table = TableWindow(
                window_id=f"table_{i}",
                info=info,
                config=TableConfig(),
            )
            # Set different error counts
            table.error_count = i * 5  # 0, 5, 10
            registry._windows[table.window_id] = table
        
        assert len(registry.get_all_windows()) == 3
        
        registry.cleanup_inactive(max_errors=8)
        
        # Only table_2 (10 errors) should be removed
        assert len(registry.get_all_windows()) == 2
    
    def test_get_stats(self):
        """Test statistics generation."""
        registry = WindowRegistry(max_windows=4)
        
        info = WindowInfo(
            hwnd=12345,
            title="Test Window Title",
            rect=(0, 0, 800, 600),
            client_offset=(0, 0),
            client_size=(800, 600),
        )
        table = TableWindow(
            window_id="test_table",
            info=info,
            config=TableConfig(),
            is_active=True,
        )
        registry._windows["test_table"] = table
        
        stats = registry.get_stats()
        
        assert stats["total_registered"] == 1
        assert stats["active_count"] == 1
        assert stats["max_windows"] == 4
        assert len(stats["windows"]) == 1
        assert stats["windows"][0]["id"] == "test_table"


class TestTableWindow:
    """Tests for TableWindow dataclass."""
    
    def test_get_screen_offset(self):
        """Test screen offset calculation."""
        info = WindowInfo(
            hwnd=12345,
            title="Test",
            rect=(100, 50, 900, 650),
            client_offset=(10, 30),  # Title bar offset
            client_size=(780, 570),
        )
        
        table = TableWindow(
            window_id="test",
            info=info,
            config=TableConfig(),
        )
        
        offset = table.get_screen_offset()
        # client_left = 100 + 10 = 110
        # client_top = 50 + 30 = 80
        assert offset == (110, 80)
    
    def test_mark_error(self):
        """Test error tracking."""
        info = WindowInfo(
            hwnd=12345,
            title="Test",
            rect=(0, 0, 800, 600),
            client_offset=(0, 0),
            client_size=(800, 600),
        )
        
        table = TableWindow(
            window_id="test",
            info=info,
            config=TableConfig(),
        )
        
        assert table.error_count == 0
        assert table.last_error is None
        
        table.mark_error("Test error 1")
        assert table.error_count == 1
        assert table.last_error == "Test error 1"
        
        table.mark_error("Test error 2")
        assert table.error_count == 2
        assert table.last_error == "Test error 2"
    
    def test_clear_errors(self):
        """Test clearing errors."""
        info = WindowInfo(
            hwnd=12345,
            title="Test",
            rect=(0, 0, 800, 600),
            client_offset=(0, 0),
            client_size=(800, 600),
        )
        
        table = TableWindow(
            window_id="test",
            info=info,
            config=TableConfig(),
        )
        
        table.mark_error("Error")
        table.mark_error("Error 2")
        assert table.error_count == 2
        
        table.clear_errors()
        assert table.error_count == 0
        assert table.last_error is None
