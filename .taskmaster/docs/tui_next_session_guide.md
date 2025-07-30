# TUI Implementation - Next Session Quick Start Guide

## 🚀 Quick Start (First 5 Minutes)

### 1. Environment Setup
```bash
cd /home/ubuntu/projects/foxtrot
uv sync
```

### 2. Test Current Status
```bash
# Test imports (should work)
uv run python -c "from foxtrot.app.tui import main, FoxtrotTUIApp; print('✅ TUI imports OK')"

# Test runtime (currently fails with MainEngine timeout)
uv run foxtrot-tui
```

### 3. Review Implementation
- **Status Document**: `.taskmaster/docs/tui_implementation_status.md`
- **Code Review**: Available from previous session analysis
- **File Structure**: `foxtrot/app/tui/` (15 files created)

## 🔥 Immediate Priorities (Next 1-2 Hours)

### Critical Issue #1: Runtime Initialization
**Problem**: MainEngine creation times out
**Location**: `main_app.py:355` - `MainEngine(event_engine)` hangs
**Investigation**: 
```bash
# Test EventEngine alone (works)
uv run python -c "from foxtrot.core.event_engine import EventEngine; print('OK')"

# Test MainEngine (fails)  
uv run python -c "from foxtrot.server.engine import MainEngine, EventEngine; MainEngine(EventEngine())"
```

**Likely Causes**:
- Missing `vt_setting.json` configuration file
- Database initialization issues
- Missing adapter dependencies
- Settings file path issues

**Fix Strategy**:
1. Check for required configuration files
2. Create minimal `vt_setting.json` 
3. Mock or bypass database initialization
4. Add timeout handling to MainEngine creation

### Critical Issue #2: Missing Imports
**Problem**: `LogData` import missing in `main_app.py`
**Location**: Line 240 in `_log_message` method
**Fix**: Add import or use alternative logging approach

### Quick Win #3: Basic Testing
**Goal**: Add simple unit tests to validate components
**Files to create**:
- `tests/tui/test_monitors.py`
- `tests/tui/test_formatters.py`
- `tests/tui/test_colors.py`

## 🛠️ Development Strategy

### Phase 3A: Fix Runtime Issues (1-2 hours)
1. **MainEngine Investigation**
   - Create minimal reproduction case
   - Identify blocking dependency
   - Implement workaround or mock

2. **Import Fixes**
   - Fix LogData import in main_app.py
   - Verify all imports work correctly
   - Test basic TUI startup

3. **Configuration Setup**
   - Create minimal vt_setting.json
   - Test with empty/default configuration
   - Ensure graceful degradation

### Phase 3B: Complete Core Features (2-4 hours)
1. **Trading Panel Implementation**
   - Complete order placement interface
   - Add volume/price input handling
   - Implement send order logic

2. **Dialog System**
   - Help dialog with keyboard shortcuts
   - Settings dialog for theme switching
   - Connection dialog for adapter management

3. **Error Handling**
   - Improve error recovery mechanisms
   - Add user-friendly error messages
   - Implement fallback behaviors

### Phase 3C: Polish & Testing (2-3 hours)
1. **Color System Completion**
   - Finish price movement color coding
   - Test all theme variations
   - Implement dynamic color updates

2. **Basic Testing Suite**
   - Unit tests for monitors
   - Integration tests for event flow
   - Mock data testing

3. **Performance Validation**
   - Test with sample market data
   - Validate memory usage
   - Check update performance

## 📁 Key Files to Focus On

### Primary Files (Most Important)
1. `foxtrot/app/tui/main_app.py` - Fix runtime issues here
2. `foxtrot/server/engine.py` - Investigation target for timeout
3. `vt_setting.json` - May need to create this file

### Secondary Files (Feature Complete)
1. `foxtrot/app/tui/components/monitors/*.py` - All monitors complete
2. `foxtrot/app/tui/utils/*.py` - Formatters and colors complete
3. `foxtrot/app/tui/integration/event_adapter.py` - Event system complete

## 🧪 Testing Commands

### Basic Functionality Tests
```bash
# Test individual components
uv run python -c "from foxtrot.app.tui.components.monitors.tick_monitor import create_tick_monitor; print('✅ TickMonitor')"
uv run python -c "from foxtrot.app.tui.utils.formatters import TUIFormatter; print('✅ Formatters')"
uv run python -c "from foxtrot.app.tui.utils.colors import get_color_manager; print('✅ Colors')"

# Test configuration
uv run python -c "from foxtrot.app.tui.config.settings import TUISettings; print('✅ Settings')"

# Test event adapter
uv run python -c "from foxtrot.app.tui.integration.event_adapter import EventEngineAdapter; print('✅ EventAdapter')"
```

### Runtime Investigation
```bash
# Test core foxtrot components
uv run python -c "from foxtrot.core.event_engine import EventEngine; e = EventEngine(); print('EventEngine OK')"

# Test settings file existence
ls -la vt_setting.json

# Test database dependencies
uv run python -c "from foxtrot.server.database import DATABASE; print('Database OK')"
```

## 🎯 Success Metrics for Next Session

### Minimum Success (2 hours)
- [ ] MainEngine initialization timeout resolved
- [ ] TUI starts without errors
- [ ] Basic monitors display sample data
- [ ] All imports working correctly

### Good Success (4 hours)
- [ ] Trading panel functional for order placement
- [ ] At least one dialog working (help/settings)
- [ ] Basic testing suite added
- [ ] Color system fully functional

### Excellent Success (6+ hours)
- [ ] Complete Phase 3 implementation
- [ ] Comprehensive testing coverage
- [ ] Performance optimization completed
- [ ] Ready for production testing

## 🔍 Debugging Resources

### Log Files to Check
- Event engine logs
- MainEngine initialization logs
- TUI application logs

### Configuration Files
- `vt_setting.json` - Main configuration
- `.taskmaster/config.json` - TUI-specific settings

### Documentation References
- Textual framework docs for UI issues
- Foxtrot architecture docs for integration
- Previous session analysis for context

## 💡 Development Tips

### Quick Development Cycle
1. **Make small changes**: Test imports after each change
2. **Use incremental testing**: Test components individually  
3. **Keep fallbacks**: Always have working version to return to
4. **Document blockers**: Note any issues that need investigation

### Common Patterns Used
- **Event handling**: `async def _process_event(self, event)`
- **Data formatting**: `TUIFormatter.format_*()` methods
- **Color coding**: `color_manager.get_*_color()` methods
- **Configuration**: `get_settings().section.property`

### Architecture Principles
- **Event-driven**: All data flows through events
- **Thread-safe**: EventEngineAdapter handles threading
- **Modular**: Each monitor is independent
- **Configurable**: Everything controlled via settings

---

**Ready to Continue**: The foundation is solid and ready for Phase 3 development. Focus on resolving the runtime initialization issue first, then complete the remaining functionality.