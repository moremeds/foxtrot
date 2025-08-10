"""
TUI Configuration Management System

This module handles TUI-specific settings, themes, layout persistence,
and configuration migration from the Qt GUI version.
"""

from dataclasses import asdict, dataclass, field
from enum import Enum
import json
import logging
import os
from pathlib import Path
from typing import Any

from foxtrot.util.utility import TRADER_DIR

logger = logging.getLogger(__name__)


class TUITheme(Enum):
    """Available TUI themes."""

    DARK = "dark"
    LIGHT = "light"
    HIGH_CONTRAST = "high_contrast"
    TRADING_GREEN = "trading_green"


class TUIInterface(Enum):
    """Available interface types."""

    TUI = "tui"
    GUI = "gui"


@dataclass
class ColorScheme:
    """Color scheme configuration for TUI."""

    # Trading colors
    bid: str = "green"
    ask: str = "red"
    profit: str = "green"
    loss: str = "red"

    # Status colors
    connected: str = "green"
    disconnected: str = "red"
    warning: str = "yellow"
    error: str = "bright_red"
    info: str = "cyan"

    # UI colors
    primary: str = "blue"
    accent: str = "magenta"
    background: str = "black"
    text: str = "white"
    border: str = "bright_black"

    # Order status colors
    pending: str = "yellow"
    filled: str = "green"
    cancelled: str = "red"
    rejected: str = "bright_red"


@dataclass
class HotKeyConfig:
    """Hotkey configuration for TUI."""

    # Trading hotkeys
    quick_trade: str = "ctrl+q"
    cancel_all: str = "ctrl+c"
    send_order: str = "f5"

    # Navigation hotkeys
    cycle_focus: str = "tab"
    cycle_focus_reverse: str = "shift+tab"

    # Dialog hotkeys
    show_help: str = "f1"
    show_contracts: str = "f2"
    show_settings: str = "f3"
    show_connect: str = "f4"

    # Panel hotkeys
    focus_trading: str = "alt+1"
    focus_tick: str = "alt+2"
    focus_order: str = "alt+3"
    focus_trade: str = "alt+4"
    focus_position: str = "alt+5"
    focus_account: str = "alt+6"
    focus_log: str = "alt+7"


@dataclass
class LayoutConfig:
    """Layout configuration for TUI panels."""

    # Panel visibility
    panels: list[str] = field(
        default_factory=lambda: ["trading", "tick", "order", "trade", "position", "account", "log"]
    )

    # Panel sizes (percentages)
    trading_width: int = 30
    monitor_height_top: int = 60
    monitor_height_bottom: int = 40

    # Panel positions and arrangements
    tick_position: str = "top_right"
    order_position: str = "top_right"
    trade_position: str = "top_right"
    position_position: str = "top_right"
    account_position: str = "bottom"
    log_position: str = "bottom"

    # Table settings
    auto_resize_columns: bool = True
    show_grid_lines: bool = True
    zebra_stripes: bool = True

    # Update settings
    max_table_rows: int = 1000
    update_interval_ms: int = 100


@dataclass
class PerformanceConfig:
    """Performance-related configuration."""

    # Update batching
    batch_interval_ms: int = 16  # ~60 FPS
    max_batch_size: int = 100

    # Memory management
    max_log_entries: int = 5000
    max_tick_history: int = 1000
    max_trade_history: int = 2000
    max_table_rows: int = 1000

    # Threading
    event_queue_size: int = 1000
    worker_threads: int = 2

    # Display optimization
    lazy_loading: bool = True
    virtual_scrolling: bool = True
    differential_updates: bool = True


@dataclass
class TUISettings:
    """Main TUI settings configuration."""

    # Interface settings
    interface: TUIInterface = TUIInterface.TUI
    theme: TUITheme = TUITheme.DARK

    # Configuration sections
    colors: ColorScheme = field(default_factory=ColorScheme)
    hotkeys: HotKeyConfig = field(default_factory=HotKeyConfig)
    layout: LayoutConfig = field(default_factory=LayoutConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)

    # Display settings
    font_size: int = 12
    show_title_bar: bool = True
    show_status_bar: bool = True
    show_clock: bool = True

    # Trading settings
    confirm_orders: bool = True
    double_click_trading: bool = True
    auto_connect_gateway: str = ""

    # File paths
    config_file: str = "tui_config.json"
    layout_file: str = "tui_layout.json"

    def __post_init__(self):
        """Initialize settings after creation."""
        # Prevent recursion by checking if already initialized
        if hasattr(self, '_initialized'):
            return
        
        object.__setattr__(self, '_initialized', True)
        
        self.config_dir = Path(TRADER_DIR) / ".tui"
        self.config_dir.mkdir(exist_ok=True)

        self.config_path = self.config_dir / self.config_file
        self.layout_path = self.config_dir / self.layout_file

        # Apply environment variable overrides
        self._apply_env_overrides()

    async def load(self) -> None:
        """Load settings from configuration file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, encoding="utf-8") as f:
                    data = json.load(f)

                # Update settings from loaded data
                self._update_from_dict(data)

                logger.info(f"TUI settings loaded from {self.config_path}")
            else:
                # Save default settings
                await self.save()
                logger.info("Created default TUI settings")

        except Exception as e:
            logger.error(f"Failed to load TUI settings: {e}")
            # Continue with default settings

    async def save(self) -> None:
        """Save current settings to configuration file."""
        try:
            data = self._to_dict()

            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"TUI settings saved to {self.config_path}")

        except Exception as e:
            logger.error(f"Failed to save TUI settings: {e}")

    def _to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary for JSON serialization."""
        return {
            "interface": self.interface.value,
            "theme": self.theme.value,
            "colors": asdict(self.colors),
            "hotkeys": asdict(self.hotkeys),
            "layout": asdict(self.layout),
            "performance": asdict(self.performance),
            "font_size": self.font_size,
            "show_title_bar": self.show_title_bar,
            "show_status_bar": self.show_status_bar,
            "show_clock": self.show_clock,
            "confirm_orders": self.confirm_orders,
            "double_click_trading": self.double_click_trading,
            "auto_connect_gateway": self.auto_connect_gateway,
        }

    def _update_from_dict(self, data: dict[str, Any]) -> None:
        """Update settings from dictionary loaded from JSON."""
        try:
            # Interface settings
            if "interface" in data:
                self.interface = TUIInterface(data["interface"])
            if "theme" in data:
                self.theme = TUITheme(data["theme"])

            # Update dataclass sections
            if "colors" in data:
                self.colors = ColorScheme(**data["colors"])
            if "hotkeys" in data:
                self.hotkeys = HotKeyConfig(**data["hotkeys"])
            if "layout" in data:
                self.layout = LayoutConfig(**data["layout"])
            if "performance" in data:
                self.performance = PerformanceConfig(**data["performance"])

            # Simple settings
            for key in [
                "font_size",
                "show_title_bar",
                "show_status_bar",
                "show_clock",
                "confirm_orders",
                "double_click_trading",
                "auto_connect_gateway",
            ]:
                if key in data:
                    setattr(self, key, data[key])

        except Exception as e:
            logger.error(f"Error updating settings from dict: {e}")

    async def migrate_from_qt(self, qt_settings_file: Path | None = None) -> bool:
        """
        Migrate settings from Qt GUI version.

        Args:
            qt_settings_file: Path to Qt settings file (optional)

        Returns:
            True if migration was successful, False otherwise
        """
        try:
            # Try to find Qt settings file
            if qt_settings_file is None:
                qt_settings_file = Path(TRADER_DIR) / "vt_setting.json"

            if not qt_settings_file.exists():
                logger.info("No Qt settings file found for migration")
                return False

            with open(qt_settings_file, encoding="utf-8") as f:
                qt_data = json.load(f)

            # Migrate relevant settings
            migrated_settings = self._convert_qt_settings(qt_data)

            if migrated_settings:
                self._update_from_dict(migrated_settings)
                await self.save()
                logger.info("Successfully migrated settings from Qt GUI")
                return True

        except Exception as e:
            logger.error(f"Failed to migrate Qt settings: {e}")

        return False

    def _convert_qt_settings(self, qt_data: dict[str, Any]) -> dict[str, Any]:
        """
        Convert Qt settings to TUI settings format.

        Args:
            qt_data: Qt settings data

        Returns:
            Converted TUI settings data
        """
        converted = {}

        try:
            # Map common settings
            if "font.family" in qt_data:
                # Font size mapping (Qt to TUI approximation)
                converted["font_size"] = 12  # Default TUI font size

            # Connection settings
            if "gateway" in qt_data:
                converted["auto_connect_gateway"] = qt_data.get("gateway", "")

            # Trading preferences
            if "confirm_order" in qt_data:
                converted["confirm_orders"] = qt_data.get("confirm_order", True)

            # Layout preferences (simplified mapping)
            layout_settings = {}
            if "window_geometry" in qt_data:
                # Map window geometry to panel sizes
                layout_settings["auto_resize_columns"] = True

            if layout_settings:
                converted["layout"] = layout_settings

            # Performance settings
            performance_settings = {}
            if "update_interval" in qt_data:
                performance_settings["batch_interval_ms"] = qt_data.get("update_interval", 16)

            if performance_settings:
                converted["performance"] = performance_settings

        except Exception as e:
            logger.error(f"Error converting Qt settings: {e}")

        return converted

    def get_color_scheme(self) -> ColorScheme:
        """Get the current color scheme based on theme."""
        if self.theme == TUITheme.LIGHT:
            return ColorScheme(
                background="white",
                text="black",
                border="gray",
                bid="dark_green",
                ask="dark_red",
                profit="dark_green",
                loss="dark_red",
            )
        if self.theme == TUITheme.HIGH_CONTRAST:
            return ColorScheme(
                background="black",
                text="white",
                border="white",
                bid="bright_green",
                ask="bright_red",
                profit="bright_green",
                loss="bright_red",
                primary="bright_blue",
                accent="bright_magenta",
            )
        if self.theme == TUITheme.TRADING_GREEN:
            return ColorScheme(
                background="black",
                text="green",
                border="green",
                bid="bright_green",
                ask="red",
                profit="bright_green",
                loss="red",
                primary="green",
                accent="bright_green",
            )
        # DARK theme (default)
        return self.colors

    def validate_hotkeys(self) -> list[str]:
        """
        Validate hotkey configuration for conflicts.

        Returns:
            List of validation errors
        """
        errors = []
        hotkey_dict = asdict(self.hotkeys)
        used_keys = set()

        for name, key in hotkey_dict.items():
            if key in used_keys:
                errors.append(f"Duplicate hotkey '{key}' for {name}")
            used_keys.add(key)

        return errors

    def reset_to_defaults(self) -> None:
        """Reset all settings to default values."""
        # Create new instance with defaults
        defaults = TUISettings()
        
        # Copy values from defaults
        self.interface = defaults.interface
        self.theme = defaults.theme
        self.colors = defaults.colors
        self.hotkeys = defaults.hotkeys
        self.layout = defaults.layout
        self.performance = defaults.performance
        self.font_size = defaults.font_size
        self.show_title_bar = defaults.show_title_bar
        self.show_status_bar = defaults.show_status_bar
        self.show_clock = defaults.show_clock
        self.confirm_orders = defaults.confirm_orders
        self.double_click_trading = defaults.double_click_trading
        self.auto_connect_gateway = defaults.auto_connect_gateway
        
        logger.info("TUI settings reset to defaults")

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to settings."""
        try:
            # Theme override
            if "FOXTROT_TUI_THEME" in os.environ:
                theme_value = os.environ["FOXTROT_TUI_THEME"]
                try:
                    # Use object.__setattr__ to avoid triggering __post_init__ recursion
                    object.__setattr__(self, 'theme', TUITheme(theme_value))
                    logger.info(f"Theme set from environment: {theme_value}")
                except ValueError:
                    logger.warning(f"Invalid theme in environment: {theme_value}")

            # Auto-connect gateway override
            if "FOXTROT_PREFERRED_ADAPTER" in os.environ:
                object.__setattr__(self, 'auto_connect_gateway', os.environ["FOXTROT_PREFERRED_ADAPTER"])
                logger.info(f"Preferred adapter set from environment: {self.auto_connect_gateway}")

            # Paper trading mode (affects confirmation settings)
            if "FOXTROT_PAPER_TRADING" in os.environ:
                # In paper trading mode, we might want different confirmation settings
                object.__setattr__(self, 'confirm_orders', os.environ.get("FOXTROT_PAPER_TRADING") != "1")
                logger.info(f"Paper trading mode detected, confirm_orders set to: {self.confirm_orders}")

        except Exception as e:
            logger.warning(f"Error applying environment overrides: {e}")

    def get_env_info(self) -> dict[str, str]:
        """Get information about environment variable settings."""
        env_info = {}

        if "FOXTROT_TUI_THEME" in os.environ:
            env_info["theme"] = os.environ["FOXTROT_TUI_THEME"]

        if "FOXTROT_PREFERRED_ADAPTER" in os.environ:
            env_info["adapter"] = os.environ["FOXTROT_PREFERRED_ADAPTER"]

        if "FOXTROT_PAPER_TRADING" in os.environ:
            env_info["paper_trading"] = "enabled"

        if "TEXTUAL_DEBUG" in os.environ:
            env_info["debug_mode"] = "enabled"

        return env_info


# Global settings instance
_settings_instance: TUISettings | None = None


def get_settings() -> TUISettings:
    """Get the global TUI settings instance."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = TUISettings()
    return _settings_instance


def reset_settings() -> None:
    """Reset the global settings instance."""
    global _settings_instance
    _settings_instance = None
