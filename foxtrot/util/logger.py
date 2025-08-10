from datetime import datetime
from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING
from pathlib import Path
import sys
import inspect
from typing import Optional, Dict, Any

# Graceful fallback if loguru is unavailable
try:
    from loguru import logger  # type: ignore
except Exception:  # pragma: no cover
    import logging

    class _BoundLogger:
        def __init__(self, base: logging.Logger, component: str):
            self._base = base
            self._component = component

        def debug(self, msg: str, *args, **kwargs):
            self._base.debug(msg, extra={"component": self._component})

        def info(self, msg: str, *args, **kwargs):
            self._base.info(msg, extra={"component": self._component})

        def warning(self, msg: str, *args, **kwargs):
            self._base.warning(msg, extra={"component": self._component})

        def error(self, msg: str, *args, **kwargs):
            self._base.error(msg, extra={"component": self._component})

    class _FallbackLogger:
        def __init__(self):
            self._logger = logging.getLogger("Foxtrot")
            self._logger.setLevel(logging.INFO)
            if not self._logger.handlers:
                handler = logging.StreamHandler(sys.stdout)
                fmt = logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s")
                handler.setFormatter(fmt)
                self._logger.addHandler(handler)

        # Compatibility no-ops / minimal implementations
        def remove(self, *args, **kwargs):
            return

        def add(self, sink, level=INFO, format=None, **kwargs):
            # Support stdout or file sinks
            import logging
            if sink is sys.stdout:
                # already added in __init__
                return
            try:
                if isinstance(sink, (str, Path)):
                    fh = logging.FileHandler(str(sink))
                    if format:
                        fh.setFormatter(logging.Formatter(format.replace("<level>", "").replace("</level>", "")))
                    fh.setLevel(level)
                    self._logger.addHandler(fh)
            except Exception:
                # Best-effort only
                pass

        def bind(self, **kwargs):
            component = kwargs.get("component", "Logger")
            return _BoundLogger(self._logger, component)

        def configure(self, *args, **kwargs):
            return

    logger = _FallbackLogger()

from .settings import SETTINGS

__all__ = [
    "DEBUG",
    "INFO", 
    "WARNING",
    "ERROR",
    "CRITICAL",
    "logger",
    "create_foxtrot_logger",
    "get_component_logger",
    "get_performance_logger", 
    "get_adapter_logger",
    "FoxtrotLogger",
]


class FoxtrotLogger:
    """Enhanced logging system for Foxtrot trading platform."""
    
    def __init__(self):
        self._component_loggers: Dict[str, Any] = {}
        self._initialized = False
        self._configure_loggers()
    
    def _detect_context_from_path(self, file_path: str) -> str:
        """Detect logging context from file path."""
        path = Path(file_path).resolve()
        path_str = str(path)
        
        # Check for test contexts
        if any(indicator in path_str.lower() for indicator in ['test_', 'tests/', '/test/', 'pytest']):
            if 'e2e' in path_str.lower():
                return 'e2e'
            elif 'integration' in path_str.lower():
                return 'integration'
            else:
                return 'unittest'
        # Check for adapter context
        elif 'adapter' in path_str:
            return 'adapter'
        # Default to main context
        else:
            return 'main'
    
    def _get_log_directory(self, context: str) -> Path:
        """Get appropriate log directory for context."""
        base_dir = Path("foxtrot_cache/logs")
        
        if context in ['unittest', 'integration', 'e2e']:
            # Tests don't need subdirectories as they're context-specific
            log_dir = base_dir / context
        elif context == 'adapter':
            log_dir = base_dir / "adapters"
        else:
            log_dir = base_dir / "main"
            
        # Create directory if it doesn't exist
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    def _get_legacy_log_file(self) -> Path:
        today_date = datetime.now().strftime("%Y-%m-%d")
        # Store legacy log in user home under .vntrader/log for compatibility
        home_path = Path.home()
        vntrader_dir = home_path.joinpath(".vntrader")
        vntrader_dir.mkdir(parents=True, exist_ok=True)
        legacy_log_path = vntrader_dir.joinpath("log")
        legacy_log_path.mkdir(parents=True, exist_ok=True)
        return legacy_log_path.joinpath(f"vt_{today_date}.log")
    
    def _configure_loggers(self):
        """Configure loguru with Foxtrot-specific settings."""
        if self._initialized:
            return
            
        # Remove default handler to avoid conflicts
        logger.remove()
        
        # Enhanced format template with component context
        format_template = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> "
            "| <level>{level: <8}</level> "
            "| <cyan>{extra[component]: <12}</cyan> "
            "| <level>{message}</level>"
        )
        
        # Add console output if enabled (preserve existing behavior)
        if SETTINGS.get("log.console", True):
            logger.add(
                sink=sys.stdout, 
                level=SETTINGS.get("log.level", INFO),
                format=format_template,
                filter=lambda record: record["extra"].get("component", "Logger") != "EventEngine"  # Reduce console noise
            )
        
        # Legacy file output support (backward compatibility)
        if SETTINGS.get("log.file", True):
            print(f"log.file is enabled")
            legacy_file_path = self._get_legacy_log_file()
            logger.add(
                sink=legacy_file_path,
                level=SETTINGS.get("log.level", INFO),
                format=format_template,
                rotation="100 MB",
                retention="30 days"
            )
        
        self._initialized = True
    
    def get_component_logger(self, component_name: str, caller_file: Optional[str] = None):
        """Get a component-specific logger with context detection."""
        if component_name in self._component_loggers:
            return self._component_loggers[component_name]
        
        # Detect context from caller if not provided
        if caller_file is None:
            frame = inspect.currentframe()
            try:
                caller_frame = frame.f_back.f_back  # Skip this method and get_component_logger
                caller_file = caller_frame.f_code.co_filename
            finally:
                del frame
        
        context = self._detect_context_from_path(caller_file)
        log_dir = self._get_log_directory(context)
        
        # Create component-specific log file
        today_date = datetime.now().strftime("%Y-%m-%d")
        log_file = log_dir / f"{component_name.lower()}-{today_date}.log"
        
        # Enhanced format for component logging
        component_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> "
            "| <level>{level: <8}</level> "
            "| <cyan>{extra[component]: <12}</cyan> "
            "| <level>{message}</level>"
        )
        
        # Create bound logger with component context
        component_logger = logger.bind(component=component_name)
        
        # Add file handler for this component
        logger.add(
            sink=log_file,
            level=SETTINGS.get("log.level", INFO),
            format=component_format,
            rotation="100 MB",
            retention="30 days",
            filter=lambda record: record["extra"].get("component") == component_name
        )
        
        self._component_loggers[component_name] = component_logger
        return component_logger
    
    def get_performance_logger(self, component_name: str):
        """Get a performance-optimized logger for hot paths."""
        performance_dir = Path("foxtrot_cache/logs/performance")
        performance_dir.mkdir(parents=True, exist_ok=True)
        
        today_date = datetime.now().strftime("%Y-%m-%d")
        perf_log_file = performance_dir / f"{component_name.lower()}-{today_date}.log"
        
        # Minimal format for performance
        perf_format = "{time:HH:mm:ss.SSS} | {level} | {extra[component]} | {message}"
        
        # Performance logger with async I/O
        perf_logger = logger.bind(component=component_name)
        
        logger.add(
            sink=perf_log_file,
            level=WARNING,  # Only warnings and errors for performance logs
            format=perf_format,
            rotation="50 MB",
            retention="7 days",
            enqueue=True,  # Async I/O for performance
            filter=lambda record: record["extra"].get("component") == component_name
        )
        
        return perf_logger
    
    def get_adapter_logger(self, adapter_name: str):
        """Get an adapter-specific logger."""
        adapter_dir = Path("foxtrot_cache/logs/adapters")
        adapter_dir.mkdir(parents=True, exist_ok=True)
        
        today_date = datetime.now().strftime("%Y-%m-%d")
        adapter_log_file = adapter_dir / f"{adapter_name.lower()}-{today_date}.log"
        
        # Adapter-specific format with extra context
        adapter_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> "
            "| <level>{level: <8}</level> "
            "| <yellow>Adapter.{extra[component]: <8}</yellow> "
            "| <level>{message}</level>"
        )
        
        adapter_logger = logger.bind(component=adapter_name)
        
        logger.add(
            sink=adapter_log_file,
            level=SETTINGS.get("log.level", INFO),
            format=adapter_format,
            rotation="100 MB", 
            retention="30 days",
            filter=lambda record: record["extra"].get("component") == adapter_name
        )
        
        return adapter_logger


# Factory function for creating logger instances
def create_foxtrot_logger() -> FoxtrotLogger:
    """Create a new FoxtrotLogger instance."""
    return FoxtrotLogger()


# Convenience functions that require an explicit logger instance
def get_component_logger(component_name: str, foxtrot_logger: FoxtrotLogger) -> Any:
    """Get a component-specific logger from the provided FoxtrotLogger instance."""
    return foxtrot_logger.get_component_logger(component_name)


def get_performance_logger(component_name: str, foxtrot_logger: FoxtrotLogger) -> Any:
    """Get a performance-optimized logger from the provided FoxtrotLogger instance."""
    return foxtrot_logger.get_performance_logger(component_name)


def get_adapter_logger(adapter_name: str, foxtrot_logger: FoxtrotLogger) -> Any:
    """Get an adapter-specific logger from the provided FoxtrotLogger instance."""
    return foxtrot_logger.get_adapter_logger(adapter_name)


# Legacy support - configure default logger with gateway context
# NOTE: This still configures the global loguru logger for backward compatibility
# Components should gradually migrate to using injected logger instances
logger.configure(extra={"component": "Legacy"})

# Log level from settings
level: int = SETTINGS.get("log.level", INFO)
