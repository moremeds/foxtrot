"""
Dialog widgets for user interaction.
"""

from importlib import metadata
import platform
from typing import Any, cast

from foxtrot.core.event_engine import EventEngine
from foxtrot.server.engine import MainEngine
from foxtrot.util.utility import load_json, save_json

from ..qt import QtCore, QtGui, QtWidgets


class ConnectDialog(QtWidgets.QDialog):
    """
    Start connection of a certain Adapter.
    """

    def __init__(self, main_engine: MainEngine, adapter_name: str) -> None:
        """Initialize connection dialog."""
        super().__init__()

        self.main_engine: MainEngine = main_engine
        self.adapter_name: str = adapter_name
        self.filename: str = f"connect_{adapter_name.lower()}.json"

        self.widgets: dict[str, tuple[QtWidgets.QWidget, type]] = {}

        self.init_ui()

    def init_ui(self) -> None:
        """"""
        self.setWindowTitle(f"Connect {self.adapter_name}")

        # Default setting provides field name, field data type and field default value.
        default_setting: dict | None = self.main_engine.get_default_setting(self.adapter_name)

        # Saved setting provides field data used last time.
        loaded_setting: dict = load_json(self.filename)

        # Initialize line edits and form layout based on setting.
        form: QtWidgets.QFormLayout = QtWidgets.QFormLayout()

        if default_setting:
            for field_name, field_value in default_setting.items():
                field_type: type = type(field_value)

                if field_type is list:
                    combo: QtWidgets.QComboBox = QtWidgets.QComboBox()
                    combo.addItems(field_value)

                    if field_name in loaded_setting:
                        saved_value = loaded_setting[field_name]
                        ix: int = combo.findText(saved_value)
                        combo.setCurrentIndex(ix)

                    form.addRow(f"{field_name} <{field_type.__name__}>", combo)
                    self.widgets[field_name] = (combo, field_type)
                else:
                    line: QtWidgets.QLineEdit = QtWidgets.QLineEdit(str(field_value))

                    if field_name in loaded_setting:
                        saved_value = loaded_setting[field_name]
                        line.setText(str(saved_value))

                    if "Password" in field_name:
                        line.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)

                    if field_type is int:
                        validator: QtGui.QIntValidator = QtGui.QIntValidator()
                        line.setValidator(validator)

                    form.addRow(f"{field_name} <{field_type.__name__}>", line)
                    self.widgets[field_name] = (line, field_type)

        button: QtWidgets.QPushButton = QtWidgets.QPushButton("Connect")
        button.clicked.connect(self.connect_adapter)
        form.addRow(button)

        self.setLayout(form)

    def connect_adapter(self) -> None:
        """
        Get setting value from line edits and connect the adapter.
        """
        setting: dict = {}

        for field_name, tp in self.widgets.items():
            widget, field_type = tp
            if field_type is list:
                combo: QtWidgets.QComboBox = cast(QtWidgets.QComboBox, widget)
                field_value = str(combo.currentText())
            else:
                line: QtWidgets.QLineEdit = cast(QtWidgets.QLineEdit, widget)
                try:
                    field_value = field_type(line.text())
                except ValueError:
                    field_value = field_type()
            setting[field_name] = field_value

        save_json(self.filename, setting)

        self.main_engine.connect(setting, self.adapter_name)
        self.accept()


class AboutDialog(QtWidgets.QDialog):
    """
    Information about the trading platform.
    """

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine) -> None:
        """Initialize about dialog."""
        super().__init__()

        self.main_engine: MainEngine = main_engine
        self.event_engine: EventEngine = event_engine

        self.init_ui()

    def init_ui(self) -> None:
        """Initialize about dialog UI."""
        self.setWindowTitle("About Foxtrot")

        from foxtrot import __version__ as foxtrot_version

        text: str = f"""By Traders, For Traders.

Created by Foxtrot Technology

License：MIT
Website：www.foxtrot.com
Github：www.github.com/foxtrot/foxtrot

Foxtrot - {foxtrot_version}
Python - {platform.python_version()}
PySide6 - {metadata.version("pyside6")}
NumPy - {metadata.version("numpy")}
pandas - {metadata.version("pandas")}"""

        label: QtWidgets.QLabel = QtWidgets.QLabel()
        label.setText(text)
        label.setMinimumWidth(500)

        vbox: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout()
        vbox.addWidget(label)
        self.setLayout(vbox)

