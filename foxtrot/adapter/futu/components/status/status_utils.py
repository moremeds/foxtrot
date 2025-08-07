"""Status utilities for Futu API client components."""

import time
from typing import Any, Dict

import futu as ft


def get_opend_gateway_status(api_client: Any) -> Dict[str, Any]:
    """Get OpenD gateway status information."""
    if not api_client:
        return {"error": "API client not available"}

    status = {
        "connected": getattr(api_client, 'connected', False),
        "quote_context": api_client.quote_ctx is not None,
        "hk_trade_context": api_client.trade_ctx_hk is not None,
        "us_trade_context": api_client.trade_ctx_us is not None,
        "market_access": {
            "hk": getattr(api_client, 'hk_access', False),
            "us": getattr(api_client, 'us_access', False), 
            "cn": getattr(api_client, 'cn_access', False),
        },
        "paper_trading": getattr(api_client, 'paper_trading', True),
    }

    # Get OpenD gateway global state if available
    if api_client.quote_ctx:
        try:
            ret, data = api_client.quote_ctx.get_global_state()
            if ret == ft.RET_OK:
                status["global_state"] = data
            else:
                status["global_state_error"] = data
        except Exception as e:
            status["global_state_error"] = str(e)

    return status


def get_context_health_status(api_client: Any) -> Dict[str, Any]:
    """Get context health information."""
    if not api_client:
        return {}
        
    return {
        "quote_context_healthy": api_client.quote_ctx is not None,
        "hk_trade_context_healthy": (api_client.trade_ctx_hk is not None 
                                   if getattr(api_client, 'hk_access', False) else None),
        "us_trade_context_healthy": (api_client.trade_ctx_us is not None
                                   if getattr(api_client, 'us_access', False) else None),
    }


def create_base_status(api_client: Any) -> Dict[str, Any]:
    """Create base status dictionary."""
    return {
        "api_client_alive": api_client is not None,
        "connected": getattr(api_client, 'connected', False) if api_client else False,
        "timestamp": time.time()
    }