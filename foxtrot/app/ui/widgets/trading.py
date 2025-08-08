"""
Trading-related widgets.
"""

from foxtrot.core.event import EVENT_TICK
from foxtrot.core.event_engine import Event, EventEngine
from foxtrot.server.engine import MainEngine
from foxtrot.util.constants import Direction, Exchange, Offset, OrderType
from foxtrot.util.object import (
    CancelRequest,
    ContractData,
    OrderData,
    OrderRequest,
    PositionData,
    SubscribeRequest,
    TickData,
)
from foxtrot.util.utility import get_digits

from ..qt import QtCore, QtWidgets
from .cells import BaseCell
from .market_depth_widget import MarketDepthWidget
from .order_controls_widget import OrderControlsWidget


class TradingWidget(QtWidgets.QWidget):
    """
    General manual trading widget.
    """

    signal_tick: QtCore.Signal = QtCore.Signal(Event)

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine) -> None:
        """Initialize trading widget."""
        super().__init__()

        self.main_engine: MainEngine = main_engine
        self.event_engine: EventEngine = event_engine

        self.vt_symbol: str = ""
        self.price_digits: int = 0

        self.init_ui()
        self.register_event()

    def init_ui(self) -> None:
        """Initialize user interface."""
        self.setFixedWidth(300)
        
        # Create UI sections
        self.order_controls = OrderControlsWidget(self.main_engine)
        self.market_depth = MarketDepthWidget()
        
        # Connect control signals
        self.order_controls.symbol_changed.connect(self.set_vt_symbol)
        self.order_controls.send_order.connect(self.send_order)
        self.order_controls.cancel_all.connect(self.cancel_all)
        
        # Overall layout
        vbox: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.order_controls)
        vbox.addWidget(self.market_depth)
        self.setLayout(vbox)

    def register_event(self) -> None:
        """Register event handlers."""
        self.signal_tick.connect(self.process_tick_event)
        self.event_engine.register(EVENT_TICK, self.signal_tick.emit)

    def process_tick_event(self, event: Event) -> None:
        """Process tick event and update market depth display."""
        tick: TickData = event.data
        if tick.vt_symbol != self.vt_symbol:
            return

        self.market_depth.update_tick(tick, self.price_digits)

        if self.order_controls.is_price_check_enabled():
            self.order_controls.set_price(f"{tick.last_price:.{self.price_digits}f}")

    def set_vt_symbol(self) -> None:
        """Set the tick depth data to monitor by vt_symbol."""
        symbol: str = self.order_controls.get_symbol()
        if not symbol:
            return

        # Generate vt_symbol from symbol and exchange
        exchange_value: str = self.order_controls.get_exchange()
        vt_symbol: str = f"{symbol}.{exchange_value}"

        if vt_symbol == self.vt_symbol:
            return
        self.vt_symbol = vt_symbol

        # Update name line widget and clear all labels
        contract: ContractData | None = self.main_engine.get_contract(vt_symbol)
        if not contract:
            self.order_controls.set_name("")
            adapter_name: str = self.order_controls.get_adapter()
        else:
            self.order_controls.set_name(contract.name)
            adapter_name = contract.adapter_name
            self.order_controls.set_adapter_index(adapter_name)
            self.price_digits = get_digits(contract.pricetick)

        self.market_depth.clear_all_labels()
        self.order_controls.clear_inputs()

        # Subscribe tick data
        req: SubscribeRequest = SubscribeRequest(symbol=symbol, exchange=Exchange(exchange_value))
        self.main_engine.subscribe(req, adapter_name)

    def send_order(self) -> None:
        """Send new order manually."""
        symbol: str = self.order_controls.get_symbol()
        if not symbol:
            QtWidgets.QMessageBox.critical(self, "Send Order Failed", "Please enter contract code")
            return

        volume_text: str = self.order_controls.get_volume()
        if not volume_text:
            QtWidgets.QMessageBox.critical(self, "Send Order Failed", "Please enter order volume")
            return
        volume: float = float(volume_text)

        price_text: str = self.order_controls.get_price()
        price: float = float(price_text) if price_text else 0

        req: OrderRequest = OrderRequest(
            symbol=symbol,
            exchange=Exchange(self.order_controls.get_exchange()),
            direction=Direction(self.order_controls.get_direction()),
            type=OrderType(self.order_controls.get_order_type()),
            volume=volume,
            price=price,
            offset=Offset(self.order_controls.get_offset()),
            reference="ManualTrading",
        )

        adapter_name: str = self.order_controls.get_adapter()
        self.main_engine.send_order(req, adapter_name)

    def cancel_all(self) -> None:
        """Cancel all active orders."""
        order_list: list[OrderData] = self.main_engine.get_all_active_orders()
        for order in order_list:
            req: CancelRequest = order.create_cancel_request()
            self.main_engine.cancel_order(req, order.adapter_name)

    def update_with_cell(self, cell: BaseCell) -> None:
        """Update trading widget with data from cell."""
        data = cell.get_data()

        self.order_controls.set_symbol(data.symbol)
        self.order_controls.set_exchange_index(data.exchange.value)
        self.set_vt_symbol()

        if isinstance(data, PositionData):
            if data.direction == Direction.SHORT:
                direction: Direction = Direction.LONG
            elif data.direction == Direction.LONG:
                direction = Direction.SHORT
            else:  # Net position mode
                direction = Direction.SHORT if data.volume > 0 else Direction.LONG

            self.order_controls.set_direction_index(direction.value)
            self.order_controls.set_offset_index(Offset.CLOSE.value)
            self.order_controls.set_volume(str(abs(data.volume)))