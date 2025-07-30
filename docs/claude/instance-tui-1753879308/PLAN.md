# Foxtrot TUI Implementation Plan

## Executive Summary

This comprehensive implementation plan outlines the development of a Text User Interface (TUI) that replicates all functionality of the existing Qt-based GUI for the Foxtrot trading platform. The plan preserves the robust event-driven architecture while replacing only the presentation layer, ensuring business logic integrity and maintaining trading functionality.

**Key Principles**:
- Preserve existing EventEngine and MainEngine architecture
- Maintain all trading functionality and safety features
- Optimize for keyboard-driven workflows
- Ensure real-time performance with high-frequency market data
- Enable gradual migration with GUI fallback option

## 1. TUI Architecture Design

### 1.1 Framework Selection

**Primary Framework: Textual 0.45.0+**

**Rationale**:
- Modern Python TUI framework with active development
- Event-driven architecture compatible with existing EventEngine
- Rich widget ecosystem (tables, forms, layouts, modals)
- Built-in asyncio support for non-blocking operations
- CSS-like styling system for professional appearance
- Efficient rendering and update mechanisms

**Alternative Frameworks Considered**:
- Rich + Custom Framework: Requires building custom event loop, more complex
- Urwid: Mature but less modern, harder asyncio integration
- Curses: Too low-level, would require building everything from scratch

### 1.2 Architectural Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    TUI Presentation Layer                    │
├─────────────────────────────────────────────────────────────┤
│                  TUI Integration Layer                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ EventEngineAdapter│  │ TUIUpdateManager│  │LayoutManager │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                   Preserved Backend                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ EventEngine │  │ MainEngine  │  │ Adapters & Data     │  │
│  │ (unchanged) │  │ (unchanged) │  │ Objects (unchanged) │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 Component Mapping

| GUI Component | TUI Equivalent | Framework Widget |
|---------------|----------------|------------------|
| MainWindow | TUIMainApp | textual.app.App |
| QDockWidget | TUIPanel | textual.containers.Container |
| QTableWidget | TUIDataTable | textual.widgets.DataTable |
| TradingWidget | TUITradingPanel | Custom composite widget |
| BaseMonitor | TUIDataMonitor | Custom DataTable extension |
| Qt Dialogs | TUIModal | textual.screen.ModalScreen |
| Qt Signals | Direct callbacks | Event handler functions |

## 2. Implementation Strategy

### 2.1 Development Phases

#### Phase 1: Foundation Infrastructure (2-3 weeks)

**Objectives**: Establish core TUI framework and event integration

**Deliverables**:
- Working Textual application with basic layout
- EventEngineAdapter for event bridging
- TUILogMonitor with real-time log display
- Basic keyboard navigation system
- JSON-based configuration system
- Unit test framework

**Files to Create**:
- `foxtrot/app/tui/main_app.py` - Main Textual application
- `foxtrot/app/tui/integration/event_adapter.py` - EventEngine bridge
- `foxtrot/app/tui/components/base_monitor.py` - Base monitor class
- `foxtrot/app/tui/components/monitors/log_monitor.py` - Log display
- `foxtrot/app/tui/utils/keyboard.py` - Keyboard handling
- `foxtrot/app/tui/config/settings.py` - Configuration management

**Key Technical Tasks**:
1. Set up Textual app with proper error handling
2. Create thread-safe bridge between EventEngine and asyncio
3. Implement basic panel layout system
4. Add configuration file persistence
5. Create logging integration with colored output

#### Phase 2: Data Display Components (3-4 weeks)

**Objectives**: Implement all monitoring widgets with real-time updates

**Deliverables**:
- Complete TUIDataMonitor base class
- All monitor implementations (Tick, Order, Trade, Position, Account)
- Real-time updates with color coding and formatting
- Sorting, filtering, and column management
- Export functionality (CSV)
- Integration tests with live data

**Files to Create**:
- `foxtrot/app/tui/components/monitors/tick_monitor.py`
- `foxtrot/app/tui/components/monitors/order_monitor.py`
- `foxtrot/app/tui/components/monitors/trade_monitor.py`
- `foxtrot/app/tui/components/monitors/position_monitor.py`
- `foxtrot/app/tui/components/monitors/account_monitor.py`
- `foxtrot/app/tui/utils/formatters.py` - Data formatting utilities
- `foxtrot/app/tui/utils/colors.py` - Color scheme management

**Key Technical Tasks**:
1. Implement efficient table updates with differential rendering
2. Add color coding system for bid/ask, P&L, and status indicators
3. Create sortable columns with visual indicators
4. Implement row-level caching for performance
5. Add context menus and export functionality

#### Phase 3: Interactive Trading Interface (2-3 weeks)

**Objectives**: Create full trading functionality with order management

**Deliverables**:
- Complete TUITradingPanel with all form inputs
- Order submission with validation and confirmation
- Real-time market depth display (5-level bid/ask)
- Symbol search and auto-completion
- Order management functions (cancel orders, cancel all)
- Integration with position and order monitors

**Files to Create**:
- `foxtrot/app/tui/components/trading_panel.py` - Main trading interface
- `foxtrot/app/tui/components/market_depth.py` - Market depth display
- `foxtrot/app/tui/components/symbol_search.py` - Contract search widget
- `foxtrot/app/tui/utils/validators.py` - Input validation utilities

**Key Technical Tasks**:
1. Create form-based input system with real-time validation
2. Implement market depth visualization with color coding
3. Add symbol auto-completion with contract details
4. Integrate order submission with MainEngine
5. Add double-click integration from monitors to trading panel

#### Phase 4: Configuration and Modal Dialogs (2-3 weeks)

**Objectives**: Complete system configuration and management interfaces

**Deliverables**:
- Connection management system (ConnectDialog equivalent)
- Contract manager with search and export
- Global settings interface
- About dialog with version information
- Layout persistence and restoration
- Performance optimization and tuning

**Files to Create**:
- `foxtrot/app/tui/dialogs/connect_modal.py` - Connection management
- `foxtrot/app/tui/dialogs/contract_modal.py` - Contract search
- `foxtrot/app/tui/dialogs/settings_modal.py` - Settings management
- `foxtrot/app/tui/dialogs/about_modal.py` - About information
- `foxtrot/app/tui/layout/panel_manager.py` - Layout management
- `foxtrot/app/tui/layout/layout_persistence.py` - Layout saving

**Key Technical Tasks**:
1. Create modal dialog system with form inputs
2. Implement dynamic connection form generation
3. Add contract search with filtering and export
4. Create settings interface with type validation
5. Add layout save/restore functionality

#### Phase 5: Polish and Production Ready (2-3 weeks)

**Objectives**: Finalize system for production deployment

**Deliverables**:
- Comprehensive documentation and user guides
- Migration utilities from Qt settings
- Production deployment scripts
- Performance monitoring and optimization
- User training materials and tutorials

**Files to Create**:
- `foxtrot/app/tui/migration/qt_settings_migrator.py` - Settings migration
- `foxtrot/app/tui/utils/performance_monitor.py` - Performance tracking
- `docs/tui_user_guide.md` - User documentation
- `scripts/deploy_tui.py` - Deployment automation

**Key Technical Tasks**:
1. Create comprehensive documentation
2. Implement Qt settings migration utilities
3. Add performance monitoring and metrics
4. Optimize memory usage and update batching
5. Create user training materials

### 2.2 Parallel Development Strategy

- Maintain existing GUI functionality throughout development
- Use feature flags to switch between GUI and TUI modes
- Create comprehensive test suite for both interfaces
- Enable side-by-side comparison during development
- Preserve all existing configuration and data

## 3. Technical Specifications

### 3.1 Dependencies

**New Dependencies**:
```toml
# Core TUI Framework
textual = "^0.45.0"           # Modern TUI framework
rich = "^13.7.0"              # Text formatting (included with Textual)

# Optional CLI Enhancement
click = "^8.1.0"              # Command-line interface
```

**Preserved Dependencies**:
- All existing foxtrot dependencies remain unchanged
- PySide6, EventEngine, MainEngine, adapters continue as-is
- Trading infrastructure (ccxt, tzlocal, loguru) unchanged
- Data processing libraries (pandas, numpy) still required

### 3.2 File Structure

```
foxtrot/
├── app/
│   ├── ui/                   # Existing Qt GUI (preserved)
│   └── tui/                  # New TUI implementation
│       ├── __init__.py
│       ├── main_app.py       # Main Textual application
│       ├── components/       # TUI widgets and panels
│       │   ├── __init__.py
│       │   ├── base_monitor.py      # Base table widget
│       │   ├── trading_panel.py     # Trading interface
│       │   ├── market_depth.py      # Market depth display
│       │   ├── symbol_search.py     # Contract search
│       │   └── monitors/            # Data monitors
│       │       ├── __init__.py
│       │       ├── tick_monitor.py
│       │       ├── order_monitor.py
│       │       ├── trade_monitor.py
│       │       ├── position_monitor.py
│       │       ├── account_monitor.py
│       │       └── log_monitor.py
│       ├── dialogs/          # Modal screens
│       │   ├── __init__.py
│       │   ├── connect_modal.py     # Connection management
│       │   ├── contract_modal.py    # Contract manager
│       │   ├── settings_modal.py    # Global settings
│       │   └── about_modal.py       # About dialog
│       ├── integration/      # EventEngine integration
│       │   ├── __init__.py
│       │   ├── event_adapter.py     # Event bridge
│       │   └── update_manager.py    # Update coordination
│       ├── layout/           # Layout management
│       │   ├── __init__.py
│       │   ├── panel_manager.py     # Panel arrangement
│       │   └── layout_persistence.py # Layout saving
│       ├── utils/            # TUI utilities
│       │   ├── __init__.py
│       │   ├── keyboard.py          # Keyboard handling
│       │   ├── colors.py            # Color management
│       │   ├── formatters.py        # Data formatting
│       │   └── validators.py        # Input validation
│       ├── config/           # Configuration
│       │   ├── __init__.py
│       │   └── settings.py          # Settings management
│       └── migration/        # Migration utilities
│           ├── __init__.py
│           └── qt_settings_migrator.py
├── run_tui.py               # TUI entry point
└── run.py                   # GUI entry point (existing)
```

### 3.3 Event Handling Architecture

**Current Event Flow**:
```
Adapter → EventEngine → Qt Signal → UI Widget
```

**New TUI Event Flow**:
```
Adapter → EventEngine → EventEngineAdapter → Textual Component
```

**EventEngineAdapter Implementation**:
```python
class EventEngineAdapter:
    def __init__(self, event_engine: EventEngine):
        self.event_engine = event_engine
        self.handlers = {}
        self.update_queue = asyncio.Queue()
        
    def register(self, event_type: str, handler: Callable):
        """Register TUI component for event type"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
            self.event_engine.register(event_type, self._on_event)
        self.handlers[event_type].append(handler)
    
    def _on_event(self, event: Event):
        """Bridge from EventEngine thread to asyncio"""
        asyncio.create_task(self._process_event(event))
    
    async def _process_event(self, event: Event):
        """Process event on asyncio thread"""
        handlers = self.handlers.get(event.type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                # Log error but don't crash
                pass
```

## 4. Component Migration Plan

### 4.1 BaseMonitor → TUIDataMonitor

**Core Functionality**:
- Real-time table updates with differential rendering
- Color coding system for different data types
- Sortable columns with visual indicators
- Context menus for actions (resize, export)
- Column state persistence

**Implementation Strategy**:
```python
class TUIDataMonitor(Widget):
    def __init__(self, event_type: str, data_key: str, headers: dict):
        super().__init__()
        self.event_type = event_type
        self.data_key = data_key
        self.headers = headers
        self.data_cache = {}
        self.table = DataTable()
        
    async def on_mount(self):
        """Initialize table and register for events"""
        self._setup_table()
        self.event_adapter.register(self.event_type, self.process_event)
    
    async def process_event(self, event: Event):
        """Handle incoming events with table updates"""
        data = event.data
        key = getattr(data, self.data_key)
        
        if key in self.data_cache:
            await self._update_row(key, data)
        else:
            await self._insert_row(key, data)
```

### 4.2 TradingWidget → TUITradingPanel

**Core Functionality**:
- Form-based input with real-time validation
- Market depth display (5-level bid/ask)
- Symbol search and auto-completion
- Order submission with confirmation
- Integration with MainEngine

**Implementation Strategy**:
```python
class TUITradingPanel(Container):
    def compose(self):
        yield Vertical(
            Horizontal(
                Select(options=exchanges, id="exchange"),
                Input(placeholder="Symbol", id="symbol"),
            ),
            Horizontal(
                Select(options=directions, id="direction"),
                Select(options=order_types, id="order_type"),
            ),
            Horizontal(
                Input(placeholder="Price", id="price"),
                Input(placeholder="Volume", id="volume"),
            ),
            MarketDepthWidget(id="market_depth"),
            Horizontal(
                Button("Send Order", id="send_order"),
                Button("Cancel All", id="cancel_all"),
            )
        )
    
    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "send_order":
            await self._submit_order()
```

### 4.3 Real-Time Data Display

**Performance Requirements**:
- Sub-100ms update latency for market data
- Support 1000+ simultaneous price updates
- Smooth scrolling with large datasets
- Memory usage optimization

**Update Strategy**:
```python
class TUIUpdateManager:
    def __init__(self):
        self.update_queue = asyncio.Queue()
        self.batch_timer = None
        self.pending_updates = {}
    
    async def schedule_update(self, component, data):
        """Batch updates to prevent flicker"""
        self.pending_updates[component] = data
        
        if self.batch_timer is None:
            self.batch_timer = asyncio.create_task(
                self._process_batched_updates()
            )
    
    async def _process_batched_updates(self):
        """Process all pending updates in single batch"""
        await asyncio.sleep(0.016)  # ~60 FPS
        
        for component, data in self.pending_updates.items():
            await component.update_display(data)
        
        self.pending_updates.clear()
        self.batch_timer = None
```

## 5. Integration Requirements

### 5.1 Thread Safety and Concurrency

**Threading Model**:
- EventEngine: Separate background threads (preserved)
- Textual: Main asyncio event loop
- Adapters: Background threads for network I/O (preserved)

**Integration Strategy**:
```python
class AsyncEventBridge:
    def __init__(self, event_engine: EventEngine):
        self.event_engine = event_engine
        self.loop = None
        
    def start(self, loop: asyncio.AbstractEventLoop):
        """Start bridge with asyncio loop"""
        self.loop = loop
        
    def _thread_safe_callback(self, event: Event):
        """Bridge from thread to asyncio"""
        if self.loop and not self.loop.is_closed():
            self.loop.call_soon_threadsafe(
                lambda: asyncio.create_task(self._process_event(event))
            )
    
    async def _process_event(self, event: Event):
        """Process event on asyncio thread"""
        # Handle event in TUI context
        pass
```

### 5.2 Configuration Management

**Migration from Qt Settings**:
- Convert QSettings to JSON/TOML configuration files
- Maintain backward compatibility during transition
- Add TUI-specific settings (colors, hotkeys, layout)

**Configuration Structure**:
```json
{
  "ui": {
    "interface": "tui",  // or "gui"
    "theme": "dark",
    "font_size": 12
  },
  "tui": {
    "colors": {
      "bid": "green",
      "ask": "red",
      "profit": "green",
      "loss": "red"
    },
    "hotkeys": {
      "quick_trade": "ctrl+q",
      "cancel_all": "ctrl+c"
    },
    "layout": {
      "panels": ["trading", "tick", "order", "position"],
      "sizes": [30, 70, 50, 50]
    }
  },
  "connections": {
    // Existing connection settings preserved
  }
}
```

### 5.3 Backward Compatibility

**Coexistence Strategy**:
- Both GUI and TUI available in same binary
- Command-line flag to select interface: `--interface tui|gui`
- Configuration setting for default interface
- Automatic fallback to GUI if TUI fails to initialize

**Entry Point Modification**:
```python
# run.py (modified)
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--interface', choices=['gui', 'tui'], 
                       default=None, help='User interface type')
    args = parser.parse_args()
    
    interface = args.interface or get_default_interface()
    
    if interface == 'tui':
        try:
            from foxtrot.app.tui.main_app import run_tui
            run_tui()
        except Exception as e:
            print(f"TUI failed to start: {e}")
            print("Falling back to GUI...")
            run_gui()
    else:
        run_gui()
```

## 6. Development Milestones

### 6.1 Success Criteria

**Phase 1 Success Criteria**:
- TUI application starts without errors
- Basic panels display and accept keyboard navigation
- EventEngine integration works with sample events
- Configuration system loads and saves settings
- All unit tests pass

**Phase 2 Success Criteria**:
- All monitors display real-time data correctly
- Color coding works for all data types
- Table sorting and filtering functional
- Export functionality works
- Performance meets latency requirements (<100ms updates)

**Phase 3 Success Criteria**:
- Trading panel accepts all order types
- Order submission works with real brokers
- Market depth displays correctly with real data
- All order management functions work
- Integration with monitors complete

**Phase 4 Success Criteria**:
- All modal dialogs functional
- Connection management works with all adapters
- Settings can be modified and persisted
- Layout save/restore works correctly
- All GUI features replicated

**Phase 5 Success Criteria**:
- Documentation complete and user-tested
- Migration from GUI works seamlessly
- Performance optimized for production use
- User training materials ready
- Production deployment successful

### 6.2 Quality Gates

**Code Quality**:
- 90%+ test coverage for all TUI components
- Type hints for all public interfaces
- Docstrings for all classes and methods
- Linting passes (black, ruff, mypy)

**Performance Quality**:
- <100ms latency for market data updates
- <500MB memory usage under normal load
- <2 seconds startup time
- Smooth operation with 1000+ concurrent updates

**User Experience Quality**:
- All keyboard shortcuts documented and consistent
- Visual clarity comparable to GUI version
- Efficient workflows for common trading tasks
- Error messages clear and actionable

## 7. Risk Assessment and Mitigation

### 7.1 High-Risk Areas

**Threading Integration Risk**:
- **Issue**: EventEngine uses threading, Textual uses asyncio
- **Impact**: Data loss, race conditions, crashes
- **Mitigation**: Robust bridge with queue-based communication
- **Fallback**: Use polling instead of direct event bridge

**Real-Time Performance Risk**:
- **Issue**: Terminal updates may be slower than Qt widgets
- **Impact**: Poor user experience, missed trading opportunities
- **Mitigation**: Efficient batching, selective updates, profiling
- **Fallback**: Configurable update rates, priority queuing

**Data Integrity Risk**:
- **Issue**: Event handling changes could cause data corruption
- **Impact**: Incorrect trading data, financial losses
- **Mitigation**: Extensive testing, comprehensive logging
- **Fallback**: GUI fallback option, data validation

### 7.2 Medium-Risk Areas

**Layout Complexity**:
- **Issue**: TUI panels may not match Qt dock widget flexibility
- **Mitigation**: Comprehensive layout system, user testing
- **Fallback**: Simplified but functional layout options

**Terminal Compatibility**:
- **Issue**: Different terminals have varying capabilities
- **Mitigation**: Test on major terminals, graceful degradation
- **Fallback**: Basic text-only mode for unsupported terminals

**User Adoption**:
- **Issue**: Users may resist change from familiar GUI
- **Mitigation**: Training, gradual rollout, GUI option
- **Fallback**: Keep GUI as primary option initially

### 7.3 Mitigation Strategies

**Development Risk Mitigation**:
- Parallel development with GUI preserved
- Comprehensive test coverage from day one
- Regular performance benchmarking
- User feedback collection throughout development

**Deployment Risk Mitigation**:
- Gradual rollout starting with power users
- Comprehensive documentation and training
- 24/7 support during initial deployment
- Immediate rollback capability to GUI

**Operational Risk Mitigation**:
- Monitoring and alerting for performance issues
- Regular performance and stability testing
- User feedback collection and rapid issue resolution
- Continuous improvement based on real usage

## 8. Conclusion

This comprehensive implementation plan provides a roadmap for creating a feature-complete TUI that preserves all the robust functionality of the existing Qt-based GUI while optimizing for terminal-based trading workflows. The phased approach minimizes risk while ensuring steady progress toward a production-ready system.

**Key Success Factors**:
1. **Preserve Architecture**: Keep the proven event-driven design intact
2. **Focus on Performance**: Ensure real-time capabilities match GUI performance
3. **User-Centric Design**: Optimize for keyboard-driven trading efficiency
4. **Comprehensive Testing**: Validate all functionality with real trading scenarios
5. **Gradual Migration**: Enable smooth transition with GUI fallback option

The estimated timeline of 11-16 weeks provides adequate time for thorough development, testing, and deployment while maintaining high quality standards essential for a trading platform.

## Complete Plan Location:
The plan has been saved to:
`/home/ubuntu/projects/foxtrot/docs/claude/instance-tui-1753879308/PLAN.md`