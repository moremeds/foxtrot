from datetime import datetime
from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING
from pathlib import Path
import sys
import inspect
from typing import Optional, Dict, Any

from loguru import logger

from .settings import SETTINGS
from .utility import get_folder_path

__all__ = [
    "DEBUG",
    "INFO", 
    "WARNING",
    "ERROR",
    "CRITICAL",
    "logger",
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
            today_date = datetime.now().strftime("%Y-%m-%d")
            legacy_log_path = get_folder_path("log")
            legacy_file_path = legacy_log_path.joinpath(f"vt_{today_date}.log")
            
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


# Global logger instance
_foxtrot_logger: Optional[FoxtrotLogger] = None


def get_foxtrot_logger() -> FoxtrotLogger:
    """Get the global FoxtrotLogger instance."""
    global _foxtrot_logger
    if _foxtrot_logger is None:
        _foxtrot_logger = FoxtrotLogger()
    return _foxtrot_logger


# Convenience functions for backward compatibility and easy access
def get_component_logger(component_name: str) -> Any:
    """Get a component-specific logger."""
    return get_foxtrot_logger().get_component_logger(component_name)


def get_performance_logger(component_name: str) -> Any:
    """Get a performance-optimized logger."""
    return get_foxtrot_logger().get_performance_logger(component_name)


def get_adapter_logger(adapter_name: str) -> Any:
    """Get an adapter-specific logger."""
    return get_foxtrot_logger().get_adapter_logger(adapter_name)


# Legacy support - configure default logger with gateway context
logger.configure(extra={"component": "Legacy"})

# Log level from settings
level: int = SETTINGS.get("log.level", INFO)

# Initialize the enhanced logging system
get_foxtrot_logger()
