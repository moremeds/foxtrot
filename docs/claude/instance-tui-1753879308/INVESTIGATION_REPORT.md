# Foxtrot GUI Architecture Investigation Report

## Executive Summary

This report provides a comprehensive analysis of the current GUI implementation in the Foxtrot trading platform to inform the development of an equivalent Text User Interface (TUI). The investigation reveals a sophisticated Qt-based GUI architecture with real-time event-driven updates, multiple monitoring panels, and extensive trading functionality.

## 1. UI Architecture Analysis

### Core Framework
- **GUI Framework**: PySide6 (Qt 6.8.2.1+)
- **Styling**: QDarkStyle with custom dark theme
- **Architecture Pattern**: Event-driven with docking widgets
- **Threading Model**: Multi-threaded with event queue system

### Main UI Components Structure

```
MainWindow (QMainWindow)
├── MenuBar
│   ├── System Menu (Gateway connections, Exit)
│   ├── Apps Menu (Extensible app system)
│   ├── Settings (Global configuration)
│   └── Help Menu (Contract manager, Forum, About)
├── Toolbar (Left-aligned, 40x40 icon size)
├── Dock Widgets (Resizable, floatable, movable)
│   ├── Trading Widget (Left) - Manual trading interface
│   ├── Tick Monitor (Right) - Real-time market data
│   ├── Order Monitor (Right) - Order management
│   ├── Active Order Monitor (Right) - Active orders only
│   ├── Trade Monitor (Right) - Executed trades
│   ├── Account Monitor (Bottom) - Account information
│   ├── Position Monitor (Bottom) - Portfolio positions
│   └── Log Monitor (Bottom) - System logs
└── Status Bar (Implied but not explicitly shown)
```

### Key UI Files
- `qt.py` - Qt application setup, styling, exception handling
- `mainwindow.py` - Main window orchestration and menu system
- `widget.py` - Core UI widgets and monitoring components

## 2. Functionality Analysis

### Trading Functionality
The GUI provides comprehensive trading capabilities:

#### Manual Trading Widget (`TradingWidget`)
- **Exchange Selection**: Dropdown for available exchanges
- **Symbol Input**: Text field with auto-completion
- **Order Parameters**:
  - Direction: Long/Short
  - Offset: Open/Close/CloseToday/CloseYesterday
  - Order Type: Market/Limit/Stop/FAK/FOK
  - Price: Numeric input with validation
  - Volume: Numeric input with validation
  - Adapter: Broker/exchange selection
- **Market Depth Display**: 5-level bid/ask prices and volumes
- **Real-time Price Updates**: Last price, percentage change
- **Quick Actions**: Send order, Cancel all orders

#### Monitoring Widgets
Each monitor extends `BaseMonitor` with event-driven updates:

1. **TickMonitor**: Real-time market data
   - Symbol, exchange, name
   - OHLC prices, volume
   - Bid/ask prices and volumes (5 levels)
   - Timestamp, adapter info

2. **OrderMonitor**: Order lifecycle management
   - Order ID, reference, symbol, exchange
   - Order type, direction, offset
   - Price, volume, traded volume, status
   - Double-click to cancel orders

3. **ActiveOrderMonitor**: Filtered view of active orders only
   - Same fields as OrderMonitor
   - Automatically hides completed/cancelled orders

4. **TradeMonitor**: Executed trade history
   - Trade ID, order ID, symbol, exchange
   - Direction, offset, price, volume
   - Execution timestamp, adapter

5. **PositionMonitor**: Portfolio positions
   - Symbol, exchange, direction
   - Current volume, yesterday volume
   - Frozen amount, average price, P&L
   - Double-click integration with trading widget

6. **AccountMonitor**: Account balances
   - Account ID, balance, frozen funds
   - Available funds, adapter info

7. **LogMonitor**: System event logs
   - Timestamp, message, adapter source
   - Real-time system status updates

### Dialog Systems

#### Connection Management (`ConnectDialog`)
- Dynamic form generation based on adapter requirements
- Secure password field handling
- Settings persistence (JSON)
- Validation for numeric fields

#### Contract Management (`ContractManager`)
- Search/filter contracts by symbol or exchange
- Comprehensive contract information display
- Export functionality (CSV)
- Integration with trading widget

#### Global Settings (`GlobalDialog`)
- Runtime configuration modification
- Type-safe input validation
- Scrollable interface for extensive settings

#### About Dialog (`AboutDialog`)
- Version information display
- Dependency version tracking
- Platform information

## 3. Event Integration Analysis

### Event System Architecture
The GUI is built on a robust event-driven architecture:

```python
EventEngine (Core)
├── Event Queue (Thread-safe)
├── Event Handlers (Type-specific)
├── General Handlers (All events)
└── Timer Events (Configurable interval)
```

### Event Types and Flow
```
Core Events:
- EVENT_TICK: Market data updates
- EVENT_ORDER: Order status changes  
- EVENT_TRADE: Trade executions
- EVENT_POSITION: Position updates
- EVENT_ACCOUNT: Account balance changes
- EVENT_CONTRACT: Contract information
- EVENT_LOG: System messages
- EVENT_QUOTE: Quote requests/responses
```

### Event Processing Pattern
1. **Event Generation**: Adapters generate events from broker data
2. **Event Queue**: Thread-safe queue buffers events
3. **Event Distribution**: EventEngine distributes to registered handlers
4. **UI Updates**: Qt signals ensure thread-safe UI updates
5. **Error Handling**: Silent exception handling prevents UI crashes

### Widget Event Registration
Each monitor widget:
- Registers for specific event types in `register_event()`
- Uses Qt signals for thread-safe UI updates
- Processes events in `process_event()` method
- Updates table data with type-specific cell formatting

## 4. Data Flow Analysis

### Real-time Data Pipeline
```
Market Data Sources (Binance, IB, etc.)
↓
Adapter Layer (Data normalization)
↓
Event Generation (Standardized events)
↓
EventEngine (Distribution)
↓
UI Components (Display updates)
```

### User Interaction Flow
```
User Input (Trading Widget)
↓
Input Validation (Qt validators)
↓
Request Creation (OrderRequest, etc.)
↓
MainEngine Processing
↓
Adapter Execution
↓
Response Events
↓
UI Feedback Updates
```

### Data Persistence
- Window layouts: Qt QSettings
- Connection settings: JSON files per adapter
- Global settings: JSON configuration file
- Column states: Qt QSettings per monitor

## 5. Dependencies and External Integrations

### Core Dependencies
```toml
# GUI Framework
PySide6 = "^6.8.2.1"          # Qt6 Python bindings
qdarkstyle = "^3.2.3"         # Dark theme styling
pyqtgraph = "^0.13.7"         # Advanced plotting (future use)

# Data Processing  
numpy = "^2.2.3"              # Numerical computing
pandas = "^2.2.3"             # Data manipulation

# Trading Infrastructure
ccxt = "^4.4.96"              # Cryptocurrency exchange library
tzlocal = "^5.3.1"            # Timezone handling
loguru = "^0.7.3"             # Logging system
```

### Qt Integration Points
- **Styling**: QDarkStyle provides professional dark theme
- **Icons**: Custom icon system with .ico files
- **Layouts**: Dock widget system for flexible UI arrangement
- **Threading**: Qt signals/slots for thread-safe updates
- **Settings**: QSettings for persistent configuration
- **Exception Handling**: Custom exception widget with traceback display

### External Resource Requirements
- Icon files (`.ico` format) in `foxtrot/app/ui/ico/` directory
- Font configuration through global settings
- Clipboard integration for data export

## 6. TUI Implementation Considerations

### Critical Features for TUI Equivalent

#### Layout System
- **Current**: Qt dock widgets with flexible positioning
- **TUI Need**: Terminal-based panel system with resize/hide/show capability
- **Recommendation**: Use libraries like `rich`, `textual`, or `urwid` for panel management

#### Real-time Updates
- **Current**: Qt signals for thread-safe updates
- **TUI Need**: Non-blocking UI updates with terminal refresh management
- **Challenge**: Terminal flicker prevention during updates

#### Data Tables
- **Current**: QTableWidget with sortable columns, color coding
- **TUI Need**: Scrollable tables with keyboard navigation
- **Features**: Sort indicators, color coding, column resizing

#### Input Forms
- **Current**: Qt form widgets with validation
- **TUI Need**: Modal forms with field validation and navigation
- **Validation**: Numeric validation, required field checking

#### Menu System
- **Current**: Traditional menu bar with submenus
- **TUI Need**: Hotkey-based navigation or popup menus
- **Integration**: Connection dialogs, settings forms

### Technical Recommendations

#### TUI Framework Selection
1. **Textual** (Recommended)
   - Modern Python TUI framework
   - Rich widget set including tables, forms
   - Event-driven architecture compatible with current system
   - CSS-like styling system

2. **Rich + Custom Framework**
   - Excellent text formatting and tables
   - Would require custom event loop integration
   - Good for read-only displays

3. **Urwid**
   - Mature, stable framework
   - Good widget ecosystem
   - More complex to integrate with asyncio

#### Architecture Adaptations

##### Event System Integration
- Maintain existing EventEngine
- Add TUI-specific event handlers
- Implement terminal-safe update mechanisms
- Preserve event type system

##### Data Model Preservation
- Keep existing data objects (TickData, OrderData, etc.)
- Maintain adapter interface compatibility
- Preserve MainEngine integration

##### Configuration Management
- Adapt Qt QSettings to file-based configuration
- Maintain connection setting persistence
- Add TUI-specific display preferences

### Development Phases

#### Phase 1: Core Infrastructure
- Set up TUI framework
- Implement basic panel system
- Create event integration layer
- Basic logging display

#### Phase 2: Data Display
- Implement table widgets for monitors
- Add real-time update capability
- Color coding and formatting
- Scrolling and navigation

#### Phase 3: Interactive Features
- Trading widget implementation
- Form-based dialogs
- Menu system
- Input validation

#### Phase 4: Advanced Features
- Settings management
- Connection management
- Contract search
- Export functionality

## 7. Conclusions and Recommendations

### Key Insights
1. **Well-Architected System**: The current GUI follows excellent separation of concerns with event-driven updates
2. **Rich Functionality**: Comprehensive trading functionality that must be preserved in TUI
3. **Extensible Design**: App system allows for future expansion
4. **Production-Ready**: Robust error handling and state management

### TUI Development Strategy
1. **Preserve Architecture**: Keep the event-driven architecture intact
2. **Gradual Migration**: Build TUI components alongside GUI for comparison
3. **Feature Parity**: Ensure all critical trading functions are available
4. **User Experience**: Focus on keyboard-driven workflows for efficiency

### Critical Success Factors
- **Real-time Performance**: TUI must handle high-frequency updates without lag
- **Visual Clarity**: Effective use of color and layout in terminal environment
- **Keyboard Navigation**: Efficient hotkey system for power users
- **Data Integrity**: Preserve all trading functionality and safety features

This investigation provides the foundation for implementing a feature-complete TUI that maintains the robustness and functionality of the current Qt-based GUI while optimizing for terminal-based trading workflows.