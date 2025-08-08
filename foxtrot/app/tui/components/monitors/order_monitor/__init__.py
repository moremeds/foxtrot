"""Order monitoring components."""

def create_order_monitor(main_engine, event_engine):
    """Create a configured order monitor instance."""
    # Lazy import to avoid circular dependency
    from ..order_monitor import create_order_monitor as _create_order_monitor
    return _create_order_monitor(main_engine, event_engine)

__all__ = ['create_order_monitor']