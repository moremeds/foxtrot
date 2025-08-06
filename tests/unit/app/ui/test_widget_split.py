"""
Unit tests for the split widget modules.
"""

import pytest
from unittest.mock import MagicMock, patch

# Test that modules can be imported independently
def test_base_widget_import():
    """Test that base_widget module can be imported."""
    from foxtrot.app.ui.widgets import base_widget
    assert hasattr(base_widget, 'BaseMonitor')
    assert hasattr(base_widget, 'COLOR_LONG')
    

def test_cell_widget_import():
    """Test that cell_widget module can be imported."""
    from foxtrot.app.ui.widgets import cell_widget
    assert hasattr(cell_widget, 'BaseCell')
    assert hasattr(cell_widget, 'EnumCell')
    assert hasattr(cell_widget, 'DirectionCell')
    

def test_monitor_widget_import():
    """Test that monitor_widget module can be imported."""
    from foxtrot.app.ui.widgets import monitor_widget
    assert hasattr(monitor_widget, 'TickMonitor')
    assert hasattr(monitor_widget, 'OrderMonitor')
    

@patch('foxtrot.app.ui.widgets.base_widget.QtWidgets.QTableWidget')
def test_base_monitor_instantiation(mock_table):
    """Test that BaseMonitor can be instantiated."""
    from foxtrot.app.ui.widgets.base_widget import BaseMonitor
    
    mock_engine = MagicMock()
    mock_event_engine = MagicMock()
    
    # Should not raise any errors
    monitor = BaseMonitor(mock_engine, mock_event_engine)
    assert monitor.main_engine == mock_engine
    assert monitor.event_engine == mock_event_engine
    

def test_base_cell_instantiation():
    """Test that BaseCell can be instantiated."""
    from foxtrot.app.ui.widgets.cell_widget import BaseCell
    
    # Should not raise any errors
    cell = BaseCell("test content", {"data": "test"})
    assert cell._text == "test content"
    assert cell._data == {"data": "test"}
    

def test_module_line_counts():
    """Verify that split modules are within line limits."""
    import os
    
    widget_dir = "foxtrot/app/ui/widgets/"
    files = {
        "base_widget.py": 200,
        "cell_widget.py": 200,
        "monitor_widget.py": 250,  # Slightly higher limit for monitors
    }
    
    for filename, max_lines in files.items():
        filepath = os.path.join(widget_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                line_count = len(f.readlines())
            assert line_count <= max_lines, f"{filename} has {line_count} lines (max: {max_lines})"