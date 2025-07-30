"""
Unit tests for utility functions module.

Tests utility functions, path management, mathematical operations,
file operations, and technical analysis classes.
"""

from datetime import datetime, time
import json
from pathlib import Path
import tempfile
from unittest.mock import Mock, mock_open, patch

import numpy as np
import pytest

from foxtrot.util.constants import Exchange, Interval
from foxtrot.util.object import BarData, TickData
from foxtrot.util.utility import (
    TEMP_DIR,
    TRADER_DIR,
    ArrayManager,
    BarGenerator,
    ceil_to,
    extract_vt_symbol,
    floor_to,
    generate_vt_symbol,
    get_digits,
    get_file_path,
    get_folder_path,
    get_icon_path,
    load_json,
    round_to,
    save_json,
    virtual,
)


class TestVTSymbolFunctions:
    """Test VT symbol utility functions."""

    def test_extract_vt_symbol_basic(self):
        """Test basic VT symbol extraction."""
        symbol, exchange = extract_vt_symbol("AAPL.NYSE")
        assert symbol == "AAPL"
        assert exchange == Exchange.NYSE

    def test_extract_vt_symbol_with_dots_in_symbol(self):
        """Test VT symbol extraction with dots in symbol name."""
        symbol, exchange = extract_vt_symbol("BRK.B.NYSE")
        assert symbol == "BRK.B"
        assert exchange == Exchange.NYSE

    def test_extract_vt_symbol_crypto(self):
        """Test VT symbol extraction for crypto pairs."""
        symbol, exchange = extract_vt_symbol("BTCUSDT.BINANCE")
        assert symbol == "BTCUSDT"
        assert exchange == Exchange.BINANCE

    def test_extract_vt_symbol_complex_symbol(self):
        """Test VT symbol extraction with complex symbol names."""
        symbol, exchange = extract_vt_symbol("ES2023-12.GLOBEX")
        assert symbol == "ES2023-12"
        assert exchange == Exchange.GLOBEX

    def test_extract_vt_symbol_invalid_format(self):
        """Test VT symbol extraction with invalid format."""
        with pytest.raises(ValueError):
            extract_vt_symbol("INVALID_SYMBOL")

    def test_extract_vt_symbol_unknown_exchange(self):
        """Test VT symbol extraction with unknown exchange."""
        with pytest.raises(ValueError):
            extract_vt_symbol("AAPL.UNKNOWN")

    def test_generate_vt_symbol_basic(self):
        """Test basic VT symbol generation."""
        vt_symbol = generate_vt_symbol("AAPL", Exchange.NYSE)
        assert vt_symbol == "AAPL.NYSE"

    def test_generate_vt_symbol_crypto(self):
        """Test VT symbol generation for crypto."""
        vt_symbol = generate_vt_symbol("BTCUSDT", Exchange.BINANCE)
        assert vt_symbol == "BTCUSDT.BINANCE"

    def test_generate_vt_symbol_complex(self):
        """Test VT symbol generation with complex names."""
        vt_symbol = generate_vt_symbol("BRK.B", Exchange.NYSE)
        assert vt_symbol == "BRK.B.NYSE"

    def test_extract_generate_roundtrip(self):
        """Test extract and generate are inverse operations."""
        original_vt_symbol = "SPY.SMART"
        symbol, exchange = extract_vt_symbol(original_vt_symbol)
        regenerated = generate_vt_symbol(symbol, exchange)
        assert regenerated == original_vt_symbol


class TestPathUtilities:
    """Test path utility functions."""

    def test_trader_dir_exists(self):
        """Test TRADER_DIR constant exists and is Path."""
        assert TRADER_DIR is not None
        assert isinstance(TRADER_DIR, Path)

    def test_temp_dir_exists(self):
        """Test TEMP_DIR constant exists and is Path."""
        assert TEMP_DIR is not None
        assert isinstance(TEMP_DIR, Path)

    @patch("foxtrot.util.utility.TEMP_DIR")
    def test_get_file_path(self, mock_temp_dir):
        """Test get_file_path function."""
        mock_temp_dir.joinpath.return_value = Path("/mock/path/test.json")

        result = get_file_path("test.json")

        mock_temp_dir.joinpath.assert_called_once_with("test.json")
        assert result == Path("/mock/path/test.json")

    @patch("foxtrot.util.utility.TEMP_DIR")
    def test_get_folder_path_existing(self, mock_temp_dir):
        """Test get_folder_path with existing folder."""
        mock_folder = Mock()
        mock_folder.exists.return_value = True
        mock_temp_dir.joinpath.return_value = mock_folder

        result = get_folder_path("test_folder")

        mock_temp_dir.joinpath.assert_called_once_with("test_folder")
        mock_folder.exists.assert_called_once()
        mock_folder.mkdir.assert_not_called()
        assert result == mock_folder

    @patch("foxtrot.util.utility.TEMP_DIR")
    def test_get_folder_path_new(self, mock_temp_dir):
        """Test get_folder_path with new folder."""
        mock_folder = Mock()
        mock_folder.exists.return_value = False
        mock_temp_dir.joinpath.return_value = mock_folder

        result = get_folder_path("new_folder")

        mock_temp_dir.joinpath.assert_called_once_with("new_folder")
        mock_folder.exists.assert_called_once()
        mock_folder.mkdir.assert_called_once()
        assert result == mock_folder

    def test_get_icon_path(self):
        """Test get_icon_path function."""
        test_filepath = "/path/to/ui/module.py"
        result = get_icon_path(test_filepath, "test.ico")

        expected = str(Path("/path/to/ui").joinpath("ico", "test.ico"))
        assert result == expected


class TestJSONUtilities:
    """Test JSON utility functions."""

    @patch("foxtrot.util.utility.get_file_path")
    def test_load_json_existing_file(self, mock_get_file_path):
        """Test loading existing JSON file."""
        test_data = {"key": "value", "number": 123}
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_get_file_path.return_value = mock_path

        with patch("builtins.open", mock_open(read_data=json.dumps(test_data))):
            result = load_json("test.json")

        assert result == test_data
        mock_get_file_path.assert_called_once_with("test.json")

    @patch("foxtrot.util.utility.get_file_path")
    @patch("foxtrot.util.utility.save_json")
    def test_load_json_nonexistent_file(self, mock_save_json, mock_get_file_path):
        """Test loading non-existent JSON file creates empty file."""
        mock_path = Mock()
        mock_path.exists.return_value = False
        mock_get_file_path.return_value = mock_path

        result = load_json("nonexistent.json")

        assert result == {}
        mock_save_json.assert_called_once_with("nonexistent.json", {})

    @patch("foxtrot.util.utility.get_file_path")
    def test_save_json(self, mock_get_file_path):
        """Test saving JSON file."""
        test_data = {"key": "value", "list": [1, 2, 3]}
        mock_path = Mock()
        mock_get_file_path.return_value = mock_path

        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            save_json("test.json", test_data)

        mock_get_file_path.assert_called_once_with("test.json")
        mock_file.assert_called_once_with(mock_path, mode="w+", encoding="UTF-8")

        # Verify JSON was written with correct formatting
        written_data = "".join(call.args[0] for call in mock_file().write.call_args_list)
        loaded_data = json.loads(written_data)
        assert loaded_data == test_data

    def test_load_save_json_roundtrip(self):
        """Test load and save JSON roundtrip with real files."""
        test_data = {"string": "test", "number": 42, "list": [1, 2, 3], "nested": {"key": "value"}}

        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock TEMP_DIR to use our temporary directory
            with patch("foxtrot.util.utility.TEMP_DIR", Path(temp_dir)):
                # Save data
                save_json("test_roundtrip.json", test_data)

                # Load data
                loaded_data = load_json("test_roundtrip.json")

                assert loaded_data == test_data


class TestMathematicalUtilities:
    """Test mathematical utility functions."""

    def test_round_to_basic(self):
        """Test basic round_to functionality."""
        assert round_to(12.34, 0.1) == 12.3
        assert round_to(12.36, 0.1) == 12.4
        assert round_to(12.35, 0.1) == 12.4  # Round half up

    def test_round_to_different_targets(self):
        """Test round_to with different target values."""
        assert round_to(127, 5) == 125
        assert round_to(128, 5) == 130
        assert round_to(12.567, 0.01) == 12.57
        assert round_to(12.561, 0.01) == 12.56

    def test_round_to_edge_cases(self):
        """Test round_to edge cases."""
        assert round_to(0, 0.1) == 0
        assert round_to(0.05, 0.1) == 0.0  # Banker's rounding: 0.05 rounds to nearest even (0.0)
        assert round_to(-12.34, 0.1) == -12.3
        assert round_to(-12.36, 0.1) == -12.4

    def test_floor_to_basic(self):
        """Test basic floor_to functionality."""
        assert floor_to(12.9, 0.1) == 12.9
        assert floor_to(12.91, 0.1) == 12.9
        assert floor_to(12.99, 0.1) == 12.9

    def test_floor_to_different_targets(self):
        """Test floor_to with different target values."""
        assert floor_to(127, 5) == 125
        assert floor_to(129, 5) == 125
        assert floor_to(12.567, 0.01) == 12.56

    def test_floor_to_edge_cases(self):
        """Test floor_to edge cases."""
        assert floor_to(0, 0.1) == 0
        assert floor_to(0.09, 0.1) == 0
        assert floor_to(-12.34, 0.1) == -12.4  # Floor of negative

    def test_ceil_to_basic(self):
        """Test basic ceil_to functionality."""
        assert ceil_to(12.1, 0.1) == 12.1
        assert ceil_to(12.01, 0.1) == 12.1
        assert ceil_to(12.11, 0.1) == 12.2

    def test_ceil_to_different_targets(self):
        """Test ceil_to with different target values."""
        assert ceil_to(123, 5) == 125
        assert ceil_to(121, 5) == 125
        assert ceil_to(12.561, 0.01) == 12.57

    def test_ceil_to_edge_cases(self):
        """Test ceil_to edge cases."""
        assert ceil_to(0, 0.1) == 0
        assert ceil_to(0.01, 0.1) == 0.1
        assert ceil_to(-12.34, 0.1) == -12.3  # Ceil of negative

    def test_get_digits_integers(self):
        """Test get_digits with integers."""
        assert get_digits(123) == 0
        assert get_digits(0) == 0
        assert get_digits(-456) == 0

    def test_get_digits_decimals(self):
        """Test get_digits with decimal numbers."""
        assert get_digits(12.34) == 2
        assert get_digits(0.1) == 1
        assert get_digits(3.14159) == 5
        assert get_digits(-2.5) == 1

    def test_get_digits_scientific_notation(self):
        """Test get_digits with scientific notation."""
        assert get_digits(1e-5) == 5  # 0.00001
        assert get_digits(2e-3) == 3  # 0.002
        assert get_digits(1.5e-4) == 5  # 0.00015

    def test_get_digits_edge_cases(self):
        """Test get_digits edge cases."""
        assert get_digits(0.0) == 1  # "0.0"
        assert get_digits(1.0) == 1  # "1.0"
        assert get_digits(10.0) == 1  # "10.0"


class TestBarGenerator:
    """Test BarGenerator class functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.generated_bars = []
        self.window_bars = []

        def on_bar(bar):
            self.generated_bars.append(bar)

        def on_window_bar(bar):
            self.window_bars.append(bar)

        self.on_bar = on_bar
        self.on_window_bar = on_window_bar

    def create_test_tick(
        self, symbol="AAPL", exchange=Exchange.NYSE, price=100.0, volume=1000, datetime_obj=None
    ):
        """Create a test tick data object."""
        if datetime_obj is None:
            datetime_obj = datetime(2023, 1, 1, 9, 30, 0)

        return TickData(
            symbol=symbol,
            exchange=exchange,
            datetime=datetime_obj,
            adapter_name="test",
            last_price=price,
            volume=volume,
        )

    def test_bar_generator_initialization(self):
        """Test BarGenerator initialization."""
        generator = BarGenerator(self.on_bar)

        assert generator.on_bar == self.on_bar
        assert generator.bar is None
        assert generator.interval == Interval.MINUTE
        assert generator.window == 0
        assert generator.on_window_bar is None

    def test_bar_generator_with_window(self):
        """Test BarGenerator initialization with window."""
        generator = BarGenerator(self.on_bar, window=5, on_window_bar=self.on_window_bar)

        assert generator.window == 5
        assert generator.on_window_bar == self.on_window_bar

    def test_bar_generator_daily_without_end_time(self):
        """Test BarGenerator daily interval requires end time."""
        with pytest.raises(RuntimeError, match="daily closing time"):
            BarGenerator(self.on_bar, interval=Interval.DAILY)

    def test_bar_generator_daily_with_end_time(self):
        """Test BarGenerator daily interval with end time."""
        end_time = time(15, 0)
        generator = BarGenerator(self.on_bar, interval=Interval.DAILY, daily_end=end_time)

        assert generator.daily_end == end_time
        assert generator.interval == Interval.DAILY

    def test_update_tick_creates_first_bar(self):
        """Test updating tick creates first bar."""
        generator = BarGenerator(self.on_bar)
        tick = self.create_test_tick(price=100.0, volume=1000)

        generator.update_tick(tick)

        assert generator.bar is not None
        assert generator.bar.open_price == 100.0
        assert generator.bar.high_price == 100.0
        assert generator.bar.low_price == 100.0
        assert generator.bar.close_price == 100.0

    def test_update_tick_filters_zero_price(self):
        """Test update_tick filters out zero last_price."""
        generator = BarGenerator(self.on_bar)
        tick = self.create_test_tick(price=0.0)

        generator.update_tick(tick)

        assert generator.bar is None

    def test_update_tick_same_minute_updates_bar(self):
        """Test updating tick in same minute updates existing bar."""
        generator = BarGenerator(self.on_bar)

        # First tick
        tick1 = self.create_test_tick(price=100.0, datetime_obj=datetime(2023, 1, 1, 9, 30, 0))
        generator.update_tick(tick1)

        # Second tick same minute
        tick2 = self.create_test_tick(
            price=102.0, volume=2000, datetime_obj=datetime(2023, 1, 1, 9, 30, 30)
        )
        generator.update_tick(tick2)

        assert generator.bar.high_price == 102.0
        assert generator.bar.close_price == 102.0
        assert len(self.generated_bars) == 0  # No bar completed yet

    def test_update_tick_new_minute_completes_bar(self):
        """Test updating tick in new minute completes previous bar."""
        generator = BarGenerator(self.on_bar)

        # First tick
        tick1 = self.create_test_tick(price=100.0, datetime_obj=datetime(2023, 1, 1, 9, 30, 0))
        generator.update_tick(tick1)

        # Second tick new minute
        tick2 = self.create_test_tick(price=101.0, datetime_obj=datetime(2023, 1, 1, 9, 31, 0))
        generator.update_tick(tick2)

        assert len(self.generated_bars) == 1
        completed_bar = self.generated_bars[0]
        assert completed_bar.open_price == 100.0
        assert completed_bar.close_price == 100.0

        # New bar should be created
        assert generator.bar.open_price == 101.0

    def test_update_tick_volume_calculation(self):
        """Test volume calculation from tick updates."""
        generator = BarGenerator(self.on_bar)

        # First tick
        tick1 = self.create_test_tick(volume=1000, datetime_obj=datetime(2023, 1, 1, 9, 30, 0))
        generator.update_tick(tick1)

        # Second tick with increased volume
        tick2 = self.create_test_tick(volume=1500, datetime_obj=datetime(2023, 1, 1, 9, 30, 30))
        generator.update_tick(tick2)

        # Volume change should be added
        assert generator.bar.volume == 500  # 1500 - 1000

    def test_generate_method(self):
        """Test generate method."""
        generator = BarGenerator(self.on_bar)
        tick = self.create_test_tick()

        generator.update_tick(tick)
        bar = generator.generate()

        assert bar is not None
        assert len(self.generated_bars) == 1
        assert generator.bar is None  # Bar should be cleared

    def test_generate_method_no_bar(self):
        """Test generate method with no current bar."""
        generator = BarGenerator(self.on_bar)
        bar = generator.generate()

        assert bar is None
        assert len(self.generated_bars) == 0


class TestArrayManager:
    """Test ArrayManager class functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.array_manager = ArrayManager(size=10)

    def create_test_bar(
        self,
        open_price=100,
        high_price=102,
        low_price=98,
        close_price=101,
        volume=1000,
        turnover=101000,
        open_interest=50,
    ):
        """Create a test bar data object."""
        return BarData(
            symbol="TEST",
            exchange=Exchange.NYSE,
            datetime=datetime(2023, 1, 1, 9, 30),
            adapter_name="test",
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            close_price=close_price,
            volume=volume,
            turnover=turnover,
            open_interest=open_interest,
        )

    def test_array_manager_initialization(self):
        """Test ArrayManager initialization."""
        am = ArrayManager(size=20)

        assert am.size == 20
        assert am.count == 0
        assert am.inited is False

        # Check arrays are initialized
        assert len(am.open_array) == 20
        assert len(am.high_array) == 20
        assert len(am.close_array) == 20
        assert np.all(am.open_array == 0)

    def test_array_manager_default_size(self):
        """Test ArrayManager default size."""
        am = ArrayManager()
        assert am.size == 100

    def test_update_bar_basic(self):
        """Test basic bar update."""
        bar = self.create_test_bar(open_price=100, close_price=105)

        self.array_manager.update_bar(bar)

        assert self.array_manager.count == 1
        assert self.array_manager.open_array[-1] == 100
        assert self.array_manager.close_array[-1] == 105
        assert self.array_manager.inited is False  # Not enough data yet

    def test_update_bar_multiple(self):
        """Test updating multiple bars."""
        for i in range(5):
            bar = self.create_test_bar(close_price=100 + i)
            self.array_manager.update_bar(bar)

        assert self.array_manager.count == 5
        assert self.array_manager.close_array[-1] == 104  # Last bar
        assert self.array_manager.close_array[-5] == 100  # First bar

    def test_array_manager_initialization_threshold(self):
        """Test ArrayManager initialization after reaching size."""
        # Fill to size
        for i in range(10):
            bar = self.create_test_bar(close_price=100 + i)
            self.array_manager.update_bar(bar)

        assert self.array_manager.count == 10
        assert self.array_manager.inited is True

    def test_array_manager_rolling_window(self):
        """Test ArrayManager rolling window behavior."""
        # Fill beyond size
        for i in range(15):
            bar = self.create_test_bar(close_price=100 + i)
            self.array_manager.update_bar(bar)

        # Should contain last 10 values
        assert self.array_manager.close_array[-1] == 114  # Latest
        assert self.array_manager.close_array[0] == 105  # Oldest in window

    def test_array_properties(self):
        """Test array property accessors."""
        bar = self.create_test_bar(
            open_price=100,
            high_price=105,
            low_price=95,
            close_price=102,
            volume=1000,
            turnover=102000,
            open_interest=50,
        )

        self.array_manager.update_bar(bar)

        assert self.array_manager.open[-1] == 100
        assert self.array_manager.high[-1] == 105
        assert self.array_manager.low[-1] == 95
        assert self.array_manager.close[-1] == 102
        assert self.array_manager.volume[-1] == 1000
        assert self.array_manager.turnover[-1] == 102000
        assert self.array_manager.open_interest[-1] == 50


class TestTechnicalIndicators:
    """Test ArrayManager technical indicator methods."""

    def setup_method(self):
        """Setup test fixtures with sample data."""
        self.array_manager = ArrayManager(size=50)

        # Add sample price data for testing indicators
        prices = [100, 101, 102, 101, 103, 104, 103, 105, 106, 105]
        for i, price in enumerate(prices):
            bar = BarData(
                symbol="TEST",
                exchange=Exchange.NYSE,
                datetime=datetime(2023, 1, 1, 9, 30 + i),
                adapter_name="test",
                open_price=price,
                high_price=price + 1,
                low_price=price - 1,
                close_price=price,
                volume=1000 + i * 10,
            )
            self.array_manager.update_bar(bar)

    @patch("foxtrot.util.utility.talib")
    def test_sma_indicator(self, mock_talib):
        """Test SMA (Simple Moving Average) indicator."""
        mock_talib.SMA.return_value = np.array([100, 100.5, 101, 101.5, 102])

        result = self.array_manager.sma(5, array=False)
        assert result == 102

        result_array = self.array_manager.sma(5, array=True)
        assert isinstance(result_array, np.ndarray)

        mock_talib.SMA.assert_called_with(self.array_manager.close, 5)

    @patch("foxtrot.util.utility.talib")
    def test_rsi_indicator(self, mock_talib):
        """Test RSI (Relative Strength Index) indicator."""
        mock_talib.RSI.return_value = np.array([50, 55, 60, 65, 70])

        result = self.array_manager.rsi(14, array=False)
        assert result == 70

        mock_talib.RSI.assert_called_with(self.array_manager.close, 14)

    @patch("foxtrot.util.utility.talib")
    def test_macd_indicator(self, mock_talib):
        """Test MACD indicator."""
        mock_macd = np.array([1.0, 1.2, 1.5])
        mock_signal = np.array([0.8, 1.0, 1.2])
        mock_hist = np.array([0.2, 0.2, 0.3])

        mock_talib.MACD.return_value = (mock_macd, mock_signal, mock_hist)

        macd, signal, hist = self.array_manager.macd(12, 26, 9, array=False)
        assert macd == 1.5
        assert signal == 1.2
        assert hist == 0.3

        mock_talib.MACD.assert_called_with(self.array_manager.close, 12, 26, 9)

    @patch("foxtrot.util.utility.talib")
    def test_bollinger_bands(self, mock_talib):
        """Test Bollinger Bands calculation."""
        mock_talib.SMA.return_value = np.array([100, 101, 102])
        mock_talib.STDDEV.return_value = np.array([1.0, 1.2, 1.5])

        up, down = self.array_manager.boll(20, 2.0, array=False)

        # up = mid + std * dev = 102 + 1.5 * 2.0 = 105
        # down = mid - std * dev = 102 - 1.5 * 2.0 = 99
        assert up == 105.0
        assert down == 99.0


class TestVirtualDecorator:
    """Test virtual decorator function."""

    def test_virtual_decorator_basic(self):
        """Test virtual decorator basic functionality."""

        @virtual
        def test_function():
            return "test"

        assert test_function() == "test"
        assert callable(test_function)

    def test_virtual_decorator_with_arguments(self):
        """Test virtual decorator with function arguments."""

        @virtual
        def test_function_with_args(x, y=10):
            return x + y

        assert test_function_with_args(5) == 15
        assert test_function_with_args(5, y=20) == 25

    def test_virtual_decorator_preserves_function(self):
        """Test virtual decorator preserves original function."""

        def original_function():
            """Original docstring."""
            return "original"

        decorated = virtual(original_function)

        assert decorated == original_function
        assert decorated.__doc__ == "Original docstring."
        assert decorated() == "original"

    def test_virtual_decorator_on_method(self):
        """Test virtual decorator on class methods."""

        class TestClass:
            @virtual
            def virtual_method(self):
                return "virtual"

        instance = TestClass()
        assert instance.virtual_method() == "virtual"


class TestUtilityEdgeCases:
    """Test edge cases and error conditions."""

    def test_extract_vt_symbol_empty_string(self):
        """Test extract_vt_symbol with empty string."""
        with pytest.raises(ValueError):
            extract_vt_symbol("")

    def test_extract_vt_symbol_no_dot(self):
        """Test extract_vt_symbol with no dot separator."""
        with pytest.raises(ValueError):
            extract_vt_symbol("SYMBOL")

    def test_generate_vt_symbol_empty_symbol(self):
        """Test generate_vt_symbol with empty symbol."""
        result = generate_vt_symbol("", Exchange.NYSE)
        assert result == ".NYSE"

    def test_mathematical_functions_with_zero(self):
        """Test mathematical functions with zero values."""
        assert round_to(0, 0.1) == 0
        assert floor_to(0, 0.1) == 0
        assert ceil_to(0, 0.1) == 0
        assert get_digits(0) == 0

    def test_path_functions_integration(self):
        """Test path functions work together."""
        # This tests the actual path creation logic
        test_filename = "integration_test.json"
        file_path = get_file_path(test_filename)

        assert isinstance(file_path, Path)
        assert file_path.name == test_filename


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
