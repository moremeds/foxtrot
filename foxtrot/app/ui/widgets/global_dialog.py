"""
Global settings dialog widget.
"""

from copy import copy

from foxtrot.util.settings import SETTING_FILENAME, SETTINGS
from foxtrot.util.utility import load_json, save_json

from ..qt import QtWidgets


class GlobalDialog(QtWidgets.QDialog):
    """
    Global settings dialog for system configuration.
    """

    def __init__(self) -> None:
        """Initialize global settings dialog."""
        super().__init__()

        self.widgets: dict[str, tuple[QtWidgets.QLineEdit, type]] = {}

        self.init_ui()

    def init_ui(self) -> None:
        """Initialize global settings dialog UI."""
        self.setWindowTitle("Global Settings")
        self.setMinimumWidth(800)

        settings: dict = copy(SETTINGS)
        settings.update(load_json(SETTING_FILENAME))

        # Initialize line edits and form layout based on setting.
        form: QtWidgets.QFormLayout = QtWidgets.QFormLayout()

        for field_name, field_value in settings.items():
            field_type: type = type(field_value)
            widget: QtWidgets.QLineEdit = QtWidgets.QLineEdit(str(field_value))

            form.addRow(f"{field_name} <{field_type.__name__}>", widget)
            self.widgets[field_name] = (widget, field_type)

        button: QtWidgets.QPushButton = QtWidgets.QPushButton("Confirm")
        button.clicked.connect(self.update_setting)
        form.addRow(button)

        scroll_widget: QtWidgets.QWidget = QtWidgets.QWidget()
        scroll_widget.setLayout(form)

        scroll_area: QtWidgets.QScrollArea = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_widget)

        vbox: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout()
        vbox.addWidget(scroll_area)
        self.setLayout(vbox)

    def update_setting(self) -> None:
        """Get setting value from line edits and update global setting file."""
        settings: dict = {}
        for field_name, tp in self.widgets.items():
            widget, field_type = tp
            value_text: str = widget.text().strip()

            if field_type is bool:
                field_value = self._parse_boolean(value_text, field_name)
            else:
                try:
                    field_value = field_type(value_text)
                except (ValueError, TypeError) as e:
                    QtWidgets.QMessageBox.warning(
                        self,
                        "Invalid Input",
                        f"Invalid value for {field_name}: {value_text}\n"
                        f"Expected type: {field_type.__name__}\n"
                        f"Error: {str(e)}",
                        QtWidgets.QMessageBox.StandardButton.Ok,
                    )
                    return  # Don't save if validation fails

            settings[field_name] = field_value

        QtWidgets.QMessageBox.information(
            self,
            "Notice",
            "The modification of global settings requires a restart to take effect!",
            QtWidgets.QMessageBox.StandardButton.Ok,
        )

        save_json(SETTING_FILENAME, settings)
    
    def _parse_boolean(self, value: str, field_name: str) -> bool:
        """
        Parse a string value to boolean with robust handling.
        
        Accepts various boolean representations:
        - True values: 'true', 'True', 'TRUE', '1', 'yes', 'Yes', 'YES', 'on', 'On', 'ON'
        - False values: 'false', 'False', 'FALSE', '0', 'no', 'No', 'NO', 'off', 'Off', 'OFF'
        - Empty string defaults to False
        
        Args:
            value: String value to parse
            field_name: Name of the field being parsed (for error messages)
            
        Returns:
            Boolean value
            
        Raises:
            Shows warning dialog for invalid values
        """
        # Handle empty string
        if not value:
            return False
        
        # Normalize the value
        normalized = value.lower().strip()
        
        # Define true and false values
        true_values = {'true', '1', 'yes', 'on', 't', 'y'}
        false_values = {'false', '0', 'no', 'off', 'f', 'n'}
        
        if normalized in true_values:
            return True
        elif normalized in false_values:
            return False
        else:
            # Show warning for invalid boolean value
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid Boolean Value",
                f"Invalid boolean value for {field_name}: '{value}'\n"
                f"Accepted values:\n"
                f"  True: true, True, TRUE, 1, yes, Yes, YES, on, On, ON, t, T, y, Y\n"
                f"  False: false, False, FALSE, 0, no, No, NO, off, Off, OFF, f, F, n, N\n"
                f"Using default: False",
                QtWidgets.QMessageBox.StandardButton.Ok,
            )
            return False