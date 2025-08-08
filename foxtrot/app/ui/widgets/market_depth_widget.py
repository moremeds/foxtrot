"""
Market depth display widget.
"""

from foxtrot.util.object import TickData

from ..qt import Qt, QtCore, QtWidgets


class MarketDepthWidget(QtWidgets.QWidget):
    """
    Market depth display with bid/ask levels.
    """

    def __init__(self) -> None:
        """Initialize market depth widget."""
        super().__init__()
        self._create_labels()
        self._create_layout()

    def _create_labels(self) -> None:
        """Create all market depth labels."""
        bid_color: str = "rgb(255,174,201)"
        ask_color: str = "rgb(160,255,160)"

        # Bid labels
        self.bp1_label: QtWidgets.QLabel = self._create_label(bid_color)
        self.bp2_label: QtWidgets.QLabel = self._create_label(bid_color)
        self.bp3_label: QtWidgets.QLabel = self._create_label(bid_color)
        self.bp4_label: QtWidgets.QLabel = self._create_label(bid_color)
        self.bp5_label: QtWidgets.QLabel = self._create_label(bid_color)

        self.bv1_label: QtWidgets.QLabel = self._create_label(
            bid_color, alignment=QtCore.Qt.AlignmentFlag.AlignRight
        )
        self.bv2_label: QtWidgets.QLabel = self._create_label(
            bid_color, alignment=QtCore.Qt.AlignmentFlag.AlignRight
        )
        self.bv3_label: QtWidgets.QLabel = self._create_label(
            bid_color, alignment=QtCore.Qt.AlignmentFlag.AlignRight
        )
        self.bv4_label: QtWidgets.QLabel = self._create_label(
            bid_color, alignment=QtCore.Qt.AlignmentFlag.AlignRight
        )
        self.bv5_label: QtWidgets.QLabel = self._create_label(
            bid_color, alignment=QtCore.Qt.AlignmentFlag.AlignRight
        )

        # Ask labels
        self.ap1_label: QtWidgets.QLabel = self._create_label(ask_color)
        self.ap2_label: QtWidgets.QLabel = self._create_label(ask_color)
        self.ap3_label: QtWidgets.QLabel = self._create_label(ask_color)
        self.ap4_label: QtWidgets.QLabel = self._create_label(ask_color)
        self.ap5_label: QtWidgets.QLabel = self._create_label(ask_color)

        self.av1_label: QtWidgets.QLabel = self._create_label(
            ask_color, alignment=QtCore.Qt.AlignmentFlag.AlignRight
        )
        self.av2_label: QtWidgets.QLabel = self._create_label(
            ask_color, alignment=QtCore.Qt.AlignmentFlag.AlignRight
        )
        self.av3_label: QtWidgets.QLabel = self._create_label(
            ask_color, alignment=QtCore.Qt.AlignmentFlag.AlignRight
        )
        self.av4_label: QtWidgets.QLabel = self._create_label(
            ask_color, alignment=QtCore.Qt.AlignmentFlag.AlignRight
        )
        self.av5_label: QtWidgets.QLabel = self._create_label(
            ask_color, alignment=QtCore.Qt.AlignmentFlag.AlignRight
        )

        # Price and return labels
        self.lp_label: QtWidgets.QLabel = self._create_label()
        self.return_label: QtWidgets.QLabel = self._create_label(
            alignment=QtCore.Qt.AlignmentFlag.AlignRight
        )

    def _create_layout(self) -> None:
        """Create and set the form layout."""
        form: QtWidgets.QFormLayout = QtWidgets.QFormLayout()
        form.addRow(self.ap5_label, self.av5_label)
        form.addRow(self.ap4_label, self.av4_label)
        form.addRow(self.ap3_label, self.av3_label)
        form.addRow(self.ap2_label, self.av2_label)
        form.addRow(self.ap1_label, self.av1_label)
        form.addRow(self.lp_label, self.return_label)
        form.addRow(self.bp1_label, self.bv1_label)
        form.addRow(self.bp2_label, self.bv2_label)
        form.addRow(self.bp3_label, self.bv3_label)
        form.addRow(self.bp4_label, self.bv4_label)
        form.addRow(self.bp5_label, self.bv5_label)
        self.setLayout(form)

    def _create_label(
        self, color: str = "", alignment: int = QtCore.Qt.AlignmentFlag.AlignLeft
    ) -> QtWidgets.QLabel:
        """Create label with certain font color."""
        label: QtWidgets.QLabel = QtWidgets.QLabel()
        if color:
            label.setStyleSheet(f"color:{color}")
        label.setAlignment(Qt.AlignmentFlag(alignment))
        return label

    def update_tick(self, tick: TickData, price_digits: int) -> None:
        """Update all market depth information with tick data."""
        self.lp_label.setText(f"{tick.last_price:.{price_digits}f}")
        self.bp1_label.setText(f"{tick.bid_price_1:.{price_digits}f}")
        self.bv1_label.setText(str(tick.bid_volume_1))
        self.ap1_label.setText(f"{tick.ask_price_1:.{price_digits}f}")
        self.av1_label.setText(str(tick.ask_volume_1))

        if tick.pre_close:
            r: float = (tick.last_price / tick.pre_close - 1) * 100
            self.return_label.setText(f"{r:.2f}%")

        if tick.bid_price_2:
            self._update_level_2_5_prices(tick, price_digits)

    def _update_level_2_5_prices(self, tick: TickData, price_digits: int) -> None:
        """Update level 2-5 market depth prices."""
        self.bp2_label.setText(f"{tick.bid_price_2:.{price_digits}f}")
        self.bv2_label.setText(str(tick.bid_volume_2))
        self.ap2_label.setText(f"{tick.ask_price_2:.{price_digits}f}")
        self.av2_label.setText(str(tick.ask_volume_2))

        self.bp3_label.setText(f"{tick.bid_price_3:.{price_digits}f}")
        self.bv3_label.setText(str(tick.bid_volume_3))
        self.ap3_label.setText(f"{tick.ask_price_3:.{price_digits}f}")
        self.av3_label.setText(str(tick.ask_volume_3))

        self.bp4_label.setText(f"{tick.bid_price_4:.{price_digits}f}")
        self.bv4_label.setText(str(tick.bid_volume_4))
        self.ap4_label.setText(f"{tick.ask_price_4:.{price_digits}f}")
        self.av4_label.setText(str(tick.ask_volume_4))

        self.bp5_label.setText(f"{tick.bid_price_5:.{price_digits}f}")
        self.bv5_label.setText(str(tick.bid_volume_5))
        self.ap5_label.setText(f"{tick.ask_price_5:.{price_digits}f}")
        self.av5_label.setText(str(tick.ask_volume_5))

    def clear_all_labels(self) -> None:
        """Clear text on all labels."""
        self.lp_label.setText("")
        self.return_label.setText("")

        for i in range(1, 6):
            getattr(self, f"bv{i}_label").setText("")
            getattr(self, f"av{i}_label").setText("")
            getattr(self, f"bp{i}_label").setText("")
            getattr(self, f"ap{i}_label").setText("")