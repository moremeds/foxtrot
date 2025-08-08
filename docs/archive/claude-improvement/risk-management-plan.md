# Foxtrot Risk Management System Plan

**Document Version:** 1.0  
**Date:** August 6, 2025

## Overview

This document outlines a comprehensive risk management system inspired by Nautilus Trader's sophisticated risk controls, adapted for Foxtrot's Python-native environment. The plan transforms Foxtrot from having basic risk awareness to implementing production-grade risk management suitable for live trading operations.

---

## Current State Assessment

**Existing Risk Management:**
- No formal risk engine
- Basic position tracking in OMS
- Manual risk assessment
- No pre-trade risk controls
- Limited exposure monitoring

**Key Gaps:**
- Missing pre-trade risk validation
- No position size limits
- Absence of drawdown controls
- No real-time risk monitoring
- Lack of automated risk responses

---

## Core Risk Engine Architecture

### Risk Management Framework

```python
# foxtrot/server/engines/risk_engine.py
from typing import Dict, List, Optional, Callable
from abc import ABC, abstractmethod
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum
import threading
import time
from foxtrot.server.engines.base_engine import BaseEngine
from foxtrot.util.object import OrderData, PositionData, AccountData
from foxtrot.util.structured_logger import StructuredLogger

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"

class RiskAction(Enum):
    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"
    LIQUIDATE = "liquidate"

@dataclass
class RiskViolation:
    """Risk rule violation details"""
    rule_name: str
    level: RiskLevel
    action: RiskAction
    message: str
    current_value: float
    limit_value: float
    context: Dict[str, str]
    timestamp: float

class RiskRule(ABC):
    """Abstract base class for all risk rules"""
    
    def __init__(self, name: str, enabled: bool = True):
        self.name = name
        self.enabled = enabled
        self.violation_count = 0
        self.last_violation: Optional[float] = None
    
    @abstractmethod
    def evaluate(self, context: Dict[str, any]) -> Optional[RiskViolation]:
        """Evaluate rule against current context"""
        pass
    
    @abstractmethod  
    def get_description(self) -> str:
        """Get human-readable description"""
        pass

class PositionSizeRule(RiskRule):
    """Maximum position size risk rule"""
    
    def __init__(
        self, 
        symbol: str, 
        max_quantity: Decimal,
        level: RiskLevel = RiskLevel.HIGH,
        action: RiskAction = RiskAction.BLOCK
    ):
        super().__init__(f"position_size_{symbol}")
        self.symbol = symbol
        self.max_quantity = max_quantity
        self.level = level
        self.action = action
    
    def evaluate(self, context: Dict[str, any]) -> Optional[RiskViolation]:
        order: OrderData = context.get("order")
        position: PositionData = context.get("position")
        
        if not order or order.symbol != self.symbol:
            return None
        
        current_quantity = position.quantity if position else Decimal(0)
        new_quantity = current_quantity + order.quantity
        
        if abs(new_quantity) > self.max_quantity:
            return RiskViolation(
                rule_name=self.name,
                level=self.level,
                action=self.action,
                message=f"Position size {new_quantity} exceeds maximum {self.max_quantity}",
                current_value=float(abs(new_quantity)),
                limit_value=float(self.max_quantity),
                context={
                    "symbol": self.symbol,
                    "current_position": str(current_quantity),
                    "order_quantity": str(order.quantity)
                },
                timestamp=time.time()
            )
        
        return None
    
    def get_description(self) -> str:
        return f"Maximum position size for {self.symbol}: {self.max_quantity}"

class AccountBalanceRule(RiskRule):
    """Account balance risk rule"""
    
    def __init__(
        self, 
        min_balance_pct: float = 0.1,  # 10% minimum balance
        level: RiskLevel = RiskLevel.CRITICAL,
        action: RiskAction = RiskAction.BLOCK
    ):
        super().__init__("account_balance")
        self.min_balance_pct = min_balance_pct
        self.level = level
        self.action = action
    
    def evaluate(self, context: Dict[str, any]) -> Optional[RiskViolation]:
        account: AccountData = context.get("account")
        order: OrderData = context.get("order")
        
        if not account or not order:
            return None
        
        # Estimate order cost (simplified)
        estimated_cost = order.quantity * order.price
        remaining_balance = account.balance - estimated_cost
        min_balance = account.balance * self.min_balance_pct
        
        if remaining_balance < min_balance:
            return RiskViolation(
                rule_name=self.name,
                level=self.level,
                action=self.action,
                message=f"Order would leave balance {remaining_balance:.2f} below minimum {min_balance:.2f}",
                current_value=remaining_balance,
                limit_value=min_balance,
                context={
                    "account_balance": str(account.balance),
                    "estimated_cost": str(estimated_cost),
                    "min_balance_pct": str(self.min_balance_pct)
                },
                timestamp=time.time()
            )
        
        return None
    
    def get_description(self) -> str:
        return f"Minimum account balance: {self.min_balance_pct:.1%} of total"

class DrawdownRule(RiskRule):
    """Maximum drawdown risk rule"""
    
    def __init__(
        self, 
        max_drawdown_pct: float = 0.05,  # 5% maximum drawdown
        level: RiskLevel = RiskLevel.CRITICAL,
        action: RiskAction = RiskAction.LIQUIDATE
    ):
        super().__init__("max_drawdown")
        self.max_drawdown_pct = max_drawdown_pct
        self.level = level
        self.action = action
        self.peak_balance: Optional[float] = None
    
    def evaluate(self, context: Dict[str, any]) -> Optional[RiskViolation]:
        account: AccountData = context.get("account")
        
        if not account:
            return None
        
        # Track peak balance
        if self.peak_balance is None or account.balance > self.peak_balance:
            self.peak_balance = account.balance
        
        # Calculate current drawdown
        current_drawdown = (self.peak_balance - account.balance) / self.peak_balance
        
        if current_drawdown > self.max_drawdown_pct:
            return RiskViolation(
                rule_name=self.name,
                level=self.level,
                action=self.action,
                message=f"Drawdown {current_drawdown:.2%} exceeds maximum {self.max_drawdown_pct:.2%}",
                current_value=current_drawdown,
                limit_value=self.max_drawdown_pct,
                context={
                    "peak_balance": str(self.peak_balance),
                    "current_balance": str(account.balance),
                    "drawdown_amount": str(self.peak_balance - account.balance)
                },
                timestamp=time.time()
            )
        
        return None
    
    def get_description(self) -> str:
        return f"Maximum drawdown: {self.max_drawdown_pct:.1%}"

class RiskEngine(BaseEngine):
    """Core risk management engine"""
    
    def __init__(self, main_engine, event_engine):
        super().__init__(main_engine, event_engine, "risk")
        
        # Risk rules storage
        self.rules: List[RiskRule] = []
        self.violations_history: List[RiskViolation] = []
        
        # Risk monitoring
        self.monitoring_enabled = True
        self.risk_listeners: List[Callable[[RiskViolation], None]] = []
        
        # Logger
        self.logger = StructuredLogger("foxtrot.risk")
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Setup default rules
        self._setup_default_rules()
        
        # Register for events
        self._register_event_handlers()
    
    def _setup_default_rules(self):
        """Setup default risk rules"""
        # Account balance protection
        self.add_rule(AccountBalanceRule(min_balance_pct=0.1))
        
        # Default drawdown protection
        self.add_rule(DrawdownRule(max_drawdown_pct=0.05))
        
        self.logger.info(
            "Default risk rules initialized",
            rule_count=len(self.rules)
        )
    
    def add_rule(self, rule: RiskRule) -> None:
        """Add risk rule to engine"""
        with self._lock:
            self.rules.append(rule)
            
        self.logger.info(
            "Risk rule added",
            rule_name=rule.name,
            rule_type=type(rule).__name__,
            enabled=rule.enabled
        )
    
    def remove_rule(self, rule_name: str) -> bool:
        """Remove risk rule by name"""
        with self._lock:
            for i, rule in enumerate(self.rules):
                if rule.name == rule_name:
                    del self.rules[i]
                    self.logger.info("Risk rule removed", rule_name=rule_name)
                    return True
        
        self.logger.warning("Risk rule not found for removal", rule_name=rule_name)
        return False
    
    def get_rule(self, rule_name: str) -> Optional[RiskRule]:
        """Get risk rule by name"""
        with self._lock:
            for rule in self.rules:
                if rule.name == rule_name:
                    return rule
        return None
    
    def evaluate_order_risk(self, order: OrderData) -> List[RiskViolation]:
        """Evaluate pre-trade risk for order"""
        if not self.monitoring_enabled:
            return []
        
        violations = []
        
        # Get current context
        context = self._build_risk_context(order)
        
        with self._lock:
            for rule in self.rules:
                if not rule.enabled:
                    continue
                
                try:
                    violation = rule.evaluate(context)
                    if violation:
                        violations.append(violation)
                        self._record_violation(violation)
                        
                except Exception as e:
                    self.logger.error(
                        "Risk rule evaluation failed",
                        rule_name=rule.name,
                        error=str(e)
                    )
        
        return violations
    
    def evaluate_account_risk(self, account: AccountData) -> List[RiskViolation]:
        """Evaluate ongoing account risk"""
        if not self.monitoring_enabled:
            return []
        
        violations = []
        context = {"account": account}
        
        with self._lock:
            for rule in self.rules:
                if not rule.enabled:
                    continue
                
                try:
                    violation = rule.evaluate(context)
                    if violation:
                        violations.append(violation)
                        self._record_violation(violation)
                        
                except Exception as e:
                    self.logger.error(
                        "Account risk evaluation failed",
                        rule_name=rule.name,
                        error=str(e)
                    )
        
        return violations
    
    def _build_risk_context(self, order: OrderData) -> Dict[str, any]:
        """Build risk evaluation context"""
        context = {"order": order}
        
        # Get position for symbol
        oms_engine = self.main_engine.get_engine("oms")
        if oms_engine:
            position = oms_engine.get_position(order.symbol)
            context["position"] = position
        
        # Get account data
        # This would get account from appropriate adapter
        context["account"] = None  # Placeholder
        
        return context
    
    def _record_violation(self, violation: RiskViolation) -> None:
        """Record risk violation"""
        self.violations_history.append(violation)
        
        # Keep only last 1000 violations
        if len(self.violations_history) > 1000:
            self.violations_history = self.violations_history[-1000:]
        
        # Log violation
        if violation.level == RiskLevel.CRITICAL:
            self.logger.error(
                "CRITICAL RISK VIOLATION",
                rule_name=violation.rule_name,
                message=violation.message,
                action=violation.action.value,
                **violation.context
            )
        elif violation.level == RiskLevel.HIGH:
            self.logger.error(
                "HIGH RISK VIOLATION",
                rule_name=violation.rule_name,
                message=violation.message,
                action=violation.action.value,
                **violation.context
            )
        else:
            self.logger.warning(
                "Risk violation",
                rule_name=violation.rule_name,
                message=violation.message,
                level=violation.level.value,
                action=violation.action.value
            )
        
        # Notify listeners
        for listener in self.risk_listeners:
            try:
                listener(violation)
            except Exception as e:
                self.logger.error(
                    "Risk listener error",
                    error=str(e)
                )
    
    def add_risk_listener(self, listener: Callable[[RiskViolation], None]) -> None:
        """Add risk violation listener"""
        self.risk_listeners.append(listener)
    
    def get_violations_summary(self) -> Dict[str, any]:
        """Get risk violations summary"""
        with self._lock:
            total_violations = len(self.violations_history)
            recent_violations = [
                v for v in self.violations_history 
                if time.time() - v.timestamp < 3600  # Last hour
            ]
            
            by_level = {}
            by_rule = {}
            
            for violation in recent_violations:
                level = violation.level.value
                rule = violation.rule_name
                
                by_level[level] = by_level.get(level, 0) + 1
                by_rule[rule] = by_rule.get(rule, 0) + 1
            
            return {
                "total_violations": total_violations,
                "recent_violations": len(recent_violations),
                "violations_by_level": by_level,
                "violations_by_rule": by_rule,
                "active_rules": len([r for r in self.rules if r.enabled])
            }
    
    def set_position_limit(self, symbol: str, max_quantity: Decimal) -> None:
        """Set position limit for symbol"""
        rule_name = f"position_size_{symbol}"
        
        # Remove existing rule if any
        self.remove_rule(rule_name)
        
        # Add new rule
        rule = PositionSizeRule(symbol, max_quantity)
        self.add_rule(rule)
    
    def enable_monitoring(self) -> None:
        """Enable risk monitoring"""
        self.monitoring_enabled = True
        self.logger.info("Risk monitoring enabled")
    
    def disable_monitoring(self) -> None:
        """Disable risk monitoring"""
        self.monitoring_enabled = False
        self.logger.warning("Risk monitoring DISABLED")
```

---

## Real-Time Risk Monitoring

### Risk Monitoring Dashboard Integration

```python
# foxtrot/server/engines/risk_monitor.py
import time
import threading
from typing import Dict, List
from foxtrot.util.metrics import metrics

class RiskMonitor:
    """Real-time risk monitoring and alerting"""
    
    def __init__(self, risk_engine: RiskEngine):
        self.risk_engine = risk_engine
        self.monitoring_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.alert_cooldowns: Dict[str, float] = {}
        
        # Register as risk listener
        risk_engine.add_risk_listener(self._on_risk_violation)
    
    def start_monitoring(self):
        """Start risk monitoring thread"""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            return
        
        self.stop_event.clear()
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            name="risk_monitor",
            daemon=True
        )
        self.monitoring_thread.start()
    
    def stop_monitoring(self):
        """Stop risk monitoring"""
        self.stop_event.set()
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while not self.stop_event.wait(10):  # Check every 10 seconds
            try:
                self._update_risk_metrics()
                self._check_risk_thresholds()
            except Exception as e:
                self.risk_engine.logger.error(
                    "Risk monitoring error",
                    error=str(e)
                )
    
    def _update_risk_metrics(self):
        """Update risk metrics"""
        summary = self.risk_engine.get_violations_summary()
        
        # Record metrics
        metrics.gauge("risk.active_rules", summary["active_rules"])
        metrics.gauge("risk.recent_violations", summary["recent_violations"])
        metrics.gauge("risk.total_violations", summary["total_violations"])
        
        # Record by level
        for level, count in summary["violations_by_level"].items():
            metrics.gauge(f"risk.violations.{level}", count)
    
    def _check_risk_thresholds(self):
        """Check if risk thresholds exceeded"""
        summary = self.risk_engine.get_violations_summary()
        
        # Alert on high violation rates
        if summary["recent_violations"] > 10:
            self._send_alert(
                "high_violation_rate",
                f"High risk violation rate: {summary['recent_violations']} in last hour"
            )
    
    def _on_risk_violation(self, violation: RiskViolation):
        """Handle risk violation"""
        # Record violation metric
        metrics.counter(
            "risk.violations",
            rule=violation.rule_name,
            level=violation.level.value,
            action=violation.action.value
        )
        
        # Send immediate alert for critical violations
        if violation.level == RiskLevel.CRITICAL:
            self._send_alert(
                f"critical_violation_{violation.rule_name}",
                f"CRITICAL: {violation.message}"
            )
    
    def _send_alert(self, alert_key: str, message: str):
        """Send alert with cooldown"""
        current_time = time.time()
        last_alert = self.alert_cooldowns.get(alert_key, 0)
        
        # 5 minute cooldown for same alert
        if current_time - last_alert > 300:
            self.alert_cooldowns[alert_key] = current_time
            
            self.risk_engine.logger.error(
                "RISK ALERT",
                alert_key=alert_key,
                message=message
            )
            
            # Could integrate with external alerting system here
            # await self.alert_system.send_alert(message)
```

---

## Risk Rule Configuration System

### Dynamic Risk Configuration

```python
# foxtrot/util/risk_config.py
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List
from decimal import Decimal

class RiskConfigManager:
    """Manage risk configuration from files"""
    
    def __init__(self, config_path: str = "risk_config.yaml"):
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self):
        """Load risk configuration from file"""
        if not self.config_path.exists():
            self._create_default_config()
        
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
    
    def save_config(self):
        """Save configuration to file"""
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
    
    def _create_default_config(self):
        """Create default risk configuration"""
        default_config = {
            "account_rules": {
                "min_balance_pct": 0.1,
                "max_drawdown_pct": 0.05
            },
            "position_rules": {
                "default_max_position_pct": 0.02,  # 2% of account per position
                "symbol_limits": {}
            },
            "order_rules": {
                "max_order_size_pct": 0.01,  # 1% of account per order
                "max_orders_per_minute": 10
            },
            "monitoring": {
                "enabled": True,
                "alert_thresholds": {
                    "violations_per_hour": 10,
                    "critical_violations_per_day": 1
                }
            }
        }
        
        self.config = default_config
        self.save_config()
    
    def get_position_limit(self, symbol: str) -> Optional[Decimal]:
        """Get position limit for symbol"""
        symbol_limits = self.config.get("position_rules", {}).get("symbol_limits", {})
        if symbol in symbol_limits:
            return Decimal(str(symbol_limits[symbol]))
        
        # Use default percentage
        default_pct = self.config.get("position_rules", {}).get("default_max_position_pct", 0.02)
        # Would need account balance to calculate actual limit
        return None
    
    def set_position_limit(self, symbol: str, limit: Decimal):
        """Set position limit for symbol"""
        if "position_rules" not in self.config:
            self.config["position_rules"] = {}
        if "symbol_limits" not in self.config["position_rules"]:
            self.config["position_rules"]["symbol_limits"] = {}
        
        self.config["position_rules"]["symbol_limits"][symbol] = float(limit)
        self.save_config()
    
    def get_account_rules(self) -> Dict[str, float]:
        """Get account risk rules"""
        return self.config.get("account_rules", {})
    
    def update_account_rules(self, rules: Dict[str, float]):
        """Update account risk rules"""
        if "account_rules" not in self.config:
            self.config["account_rules"] = {}
        
        self.config["account_rules"].update(rules)
        self.save_config()

# Integration with RiskEngine
class ConfigurableRiskEngine(RiskEngine):
    """Risk engine with configuration file support"""
    
    def __init__(self, main_engine, event_engine, config_path: str = "risk_config.yaml"):
        super().__init__(main_engine, event_engine)
        self.config_manager = RiskConfigManager(config_path)
        self._apply_configuration()
    
    def _apply_configuration(self):
        """Apply configuration to risk rules"""
        # Clear existing rules
        self.rules.clear()
        
        # Apply account rules
        account_rules = self.config_manager.get_account_rules()
        if "min_balance_pct" in account_rules:
            self.add_rule(AccountBalanceRule(
                min_balance_pct=account_rules["min_balance_pct"]
            ))
        
        if "max_drawdown_pct" in account_rules:
            self.add_rule(DrawdownRule(
                max_drawdown_pct=account_rules["max_drawdown_pct"]
            ))
        
        # Apply position rules for specific symbols
        position_config = self.config_manager.config.get("position_rules", {})
        symbol_limits = position_config.get("symbol_limits", {})
        
        for symbol, limit in symbol_limits.items():
            self.add_rule(PositionSizeRule(
                symbol=symbol,
                max_quantity=Decimal(str(limit))
            ))
        
        self.logger.info(
            "Risk configuration applied",
            total_rules=len(self.rules)
        )
    
    def reload_configuration(self):
        """Reload configuration from file"""
        self.config_manager.load_config()
        self._apply_configuration()
```

---

## Success Metrics

### Risk Management Quality Indicators
- **Risk Coverage**: 100% of orders pass through pre-trade risk checks
- **Violation Detection**: <1 second detection time for risk violations  
- **Alert Accuracy**: >95% of alerts actionable, <2% false positives
- **Recovery Time**: <30 seconds for automated risk responses

### Risk Control Effectiveness
- **Prevented Losses**: Track losses prevented through risk controls
- **Drawdown Limitation**: Maximum 5% account drawdown protection
- **Position Control**: 100% compliance with position size limits
- **Account Protection**: Zero account blow-ups due to risk failures

This comprehensive risk management system transforms Foxtrot from an unprotected trading platform to a production-grade system with sophisticated risk controls, enabling safe live trading operations while maintaining Python accessibility.