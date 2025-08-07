"""
Unit tests for the split widget modules.
"""

import pytest
from unittest.mock import MagicMock, patch

# Test that modules can be imported independently
def test_base_monitor_import():
    """Test that base_monitor module can be imported."""
    from foxtrot.app.ui.widgets import base_monitor
    assert hasattr(base_monitor, 'BaseMonitor')
    

def test_cells_import():
    """Test that cells module can be imported."""
    from foxtrot.app.ui.widgets import cells
    assert hasattr(cells, 'BaseCell')
    assert hasattr(cells, 'EnumCell')
    assert hasattr(cells, 'DirectionCell')
    assert hasattr(cells, 'COLOR_LONG')
    

def test_monitors_import():
    """Test that monitors module can be imported."""
    from foxtrot.app.ui.widgets import monitors
    assert hasattr(monitors, 'TickMonitor')
    assert hasattr(monitors, 'OrderMonitor')
    

@patch('foxtrot.app.ui.widgets.base_monitor.QtWidgets.QTableWidget')
def test_base_monitor_instantiation(mock_table):
    """Test that BaseMonitor can be instantiated."""
    from foxtrot.app.ui.widgets.base_monitor import BaseMonitor
    
    mock_engine = MagicMock()
    mock_event_engine = MagicMock()
    
    # Should not raise any errors
    monitor = BaseMonitor(mock_engine, mock_event_engine)
    assert monitor.main_engine == mock_engine
    assert monitor.event_engine == mock_event_engine
    

def test_base_cell_instantiation():
    """Test that BaseCell can be instantiated."""
    from foxtrot.app.ui.widgets.cells import BaseCell
    
    # Should not raise any errors
    cell = BaseCell("test content", {"data": "test"})
    assert cell._text == "test content"
    assert cell._data == {"data": "test"}
    

def test_module_line_counts():
    """Verify that split modules are within line limits."""
    import os
    
    widget_dir = "foxtrot/app/ui/widgets/"
    files = {
        "base_monitor.py": 200,
        "cells.py": 250,
        "monitors.py": 250,  # Slightly higher limit for monitors
        "dialogs.py": 250,
        "trading.py": 600,  # Higher limit for complex trading widgets
    }
    
    for filename, max_lines in files.items():
        filepath = os.path.join(widget_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                line_count = len(f.readlines())
            assert line_count <= max_lines, f"{filename} has {line_count} lines (max: {max_lines})"