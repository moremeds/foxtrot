"""
Order entry control widgets.
"""

from foxtrot.server.engine import MainEngine
from foxtrot.util.constants import Direction, Exchange, Offset, OrderType

from ..qt import QtCore, QtGui, QtWidgets


class OrderControlsWidget(QtWidgets.QWidget):
    """
    Order entry controls with input validation.
    """

    # Signals for parent widget to connect
    symbol_changed: QtCore.Signal = QtCore.Signal()
    send_order: QtCore.Signal = QtCore.Signal()
    cancel_all: QtCore.Signal = QtCore.Signal()

    def __init__(self, main_engine: MainEngine) -> None:
        """Initialize order controls widget."""
        super().__init__()
        self.main_engine = main_engine
        self._create_controls()
        self._create_layout()

    def _create_controls(self) -> None:
        """Create all control widgets."""
        exchanges: list[Exchange] = self.main_engine.get_all_exchanges()
        self.exchange_combo: QtWidgets.QComboBox = QtWidgets.QComboBox()
        self.exchange_combo.addItems([exchange.value for exchange in exchanges])

        self.symbol_line: QtWidgets.QLineEdit = QtWidgets.QLineEdit()
        self.symbol_line.returnPressed.connect(self.symbol_changed.emit)

        self.name_line: QtWidgets.QLineEdit = QtWidgets.QLineEdit()
        self.name_line.setReadOnly(True)

        self.direction_combo: QtWidgets.QComboBox = QtWidgets.QComboBox()
        self.direction_combo.addItems([Direction.LONG.value, Direction.SHORT.value])

        self.offset_combo: QtWidgets.QComboBox = QtWidgets.QComboBox()
        self.offset_combo.addItems([offset.value for offset in Offset])

        self.order_type_combo: QtWidgets.QComboBox = QtWidgets.QComboBox()
        self.order_type_combo.addItems([order_type.value for order_type in OrderType])

        double_validator: QtGui.QDoubleValidator = QtGui.QDoubleValidator()
        double_validator.setBottom(0)

        self.price_line: QtWidgets.QLineEdit = QtWidgets.QLineEdit()
        self.price_line.setValidator(double_validator)

        self.volume_line: QtWidgets.QLineEdit = QtWidgets.QLineEdit()
        self.volume_line.setValidator(double_validator)

        self.adapter_combo: QtWidgets.QComboBox = QtWidgets.QComboBox()
        self.adapter_combo.addItems(self.main_engine.get_all_adapter_names())

        self.price_check: QtWidgets.QCheckBox = QtWidgets.QCheckBox()
        self.price_check.setToolTip("Set price to update with market")

        send_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Send Order")
        send_button.clicked.connect(self.send_order.emit)

        cancel_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Cancel All")
        cancel_button.clicked.connect(self.cancel_all.emit)

        # Store buttons as instance variables for external access
        self.send_button = send_button
        self.cancel_button = cancel_button

    def _create_layout(self) -> None:
        """Create and set the grid layout."""
        grid: QtWidgets.QGridLayout = QtWidgets.QGridLayout()
        grid.addWidget(QtWidgets.QLabel("Exchange"), 0, 0)
        grid.addWidget(QtWidgets.QLabel("Code"), 1, 0)
        grid.addWidget(QtWidgets.QLabel("Name"), 2, 0)
        grid.addWidget(QtWidgets.QLabel("Direction"), 3, 0)
        grid.addWidget(QtWidgets.QLabel("Offset"), 4, 0)
        grid.addWidget(QtWidgets.QLabel("Type"), 5, 0)
        grid.addWidget(QtWidgets.QLabel("Price"), 6, 0)
        grid.addWidget(QtWidgets.QLabel("Volume"), 7, 0)
        grid.addWidget(QtWidgets.QLabel("Adapter"), 8, 0)
        grid.addWidget(self.exchange_combo, 0, 1, 1, 2)
        grid.addWidget(self.symbol_line, 1, 1, 1, 2)
        grid.addWidget(self.name_line, 2, 1, 1, 2)
        grid.addWidget(self.direction_combo, 3, 1, 1, 2)
        grid.addWidget(self.offset_combo, 4, 1, 1, 2)
        grid.addWidget(self.order_type_combo, 5, 1, 1, 2)
        grid.addWidget(self.price_line, 6, 1, 1, 1)
        grid.addWidget(self.price_check, 6, 2, 1, 1)
        grid.addWidget(self.volume_line, 7, 1, 1, 2)
        grid.addWidget(self.adapter_combo, 8, 1, 1, 2)
        grid.addWidget(self.send_button, 9, 0, 1, 3)
        grid.addWidget(self.cancel_button, 10, 0, 1, 3)
        self.setLayout(grid)

    def get_symbol(self) -> str:
        """Get current symbol text."""
        return str(self.symbol_line.text())

    def get_exchange(self) -> str:
        """Get current exchange text."""
        return str(self.exchange_combo.currentText())

    def get_direction(self) -> str:
        """Get current direction text."""
        return str(self.direction_combo.currentText())

    def get_offset(self) -> str:
        """Get current offset text."""
        return str(self.offset_combo.currentText())

    def get_order_type(self) -> str:
        """Get current order type text."""
        return str(self.order_type_combo.currentText())

    def get_volume(self) -> str:
        """Get current volume text."""
        return str(self.volume_line.text())

    def get_price(self) -> str:
        """Get current price text."""
        return str(self.price_line.text())

    def get_adapter(self) -> str:
        """Get current adapter text."""
        return str(self.adapter_combo.currentText())

    def is_price_check_enabled(self) -> bool:
        """Check if price auto-update is enabled."""
        return self.price_check.isChecked()

    def set_name(self, name: str) -> None:
        """Set contract name display."""
        self.name_line.setText(name)

    def set_adapter_index(self, adapter_name: str) -> None:
        """Set adapter combo box index by name."""
        ix: int = self.adapter_combo.findText(adapter_name)
        self.adapter_combo.setCurrentIndex(ix)

    def set_price(self, price: str) -> None:
        """Set price line text."""
        self.price_line.setText(price)

    def set_symbol(self, symbol: str) -> None:
        """Set symbol line text."""
        self.symbol_line.setText(symbol)

    def set_exchange_index(self, exchange: str) -> None:
        """Set exchange combo box index by value."""
        self.exchange_combo.setCurrentIndex(self.exchange_combo.findText(exchange))

    def set_direction_index(self, direction: str) -> None:
        """Set direction combo box index by value."""
        self.direction_combo.setCurrentIndex(self.direction_combo.findText(direction))

    def set_offset_index(self, offset: str) -> None:
        """Set offset combo box index by value."""
        self.offset_combo.setCurrentIndex(self.offset_combo.findText(offset))

    def set_volume(self, volume: str) -> None:
        """Set volume line text."""
        self.volume_line.setText(volume)

    def clear_inputs(self) -> None:
        """Clear volume and price inputs."""
        self.volume_line.setText("")
        self.price_line.setText("")