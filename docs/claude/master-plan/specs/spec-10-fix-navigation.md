# Specification: Fix TUI Navigation

**Spec ID**: spec-10  
**Phase**: 4 - TUI Basic Functionality  
**Priority**: P2 - Medium  
**Effort**: 3 hours

## Problem Statement

TUI navigation is completely broken:
- Tab key doesn't move between panels
- Mouse clicks don't focus elements
- No visual indication of focused element
- Can't access buttons or inputs

This makes the TUI unusable.

## Solution Approach

### Step 1: Fix Focus Management
```python
# Current (BROKEN):
class FoxtrotTUIApp(App):
    def on_key(self, event):
        if event.key == "tab":
            pass  # Nothing happens!

# Fixed:
class FoxtrotTUIApp(App):
    def on_key(self, event):
        if event.key == "tab":
            self.screen.focus_next()
        elif event.key == "shift+tab":
            self.screen.focus_previous()
```

### Step 2: Add Visual Focus Indicators
```css
/* app/tui/styles.css */
/* Current - no focus styles */

/* Fixed - clear focus indication */
*:focus {
    border: double $accent;
}

Button:focus {
    background: $primary;
    color: $background;
}

Input:focus {
    border: thick $accent;
}
```

### Step 3: Implement Focus Order
```python
# Define explicit focus order
class TradingPanel(Container):
    def compose(self):
        widgets = [
            self.symbol_input,
            self.quantity_input, 
            self.price_input,
            self.buy_button,
            self.sell_button,
            self.cancel_button
        ]
        
        # Set can_focus and tab_index
        for i, widget in enumerate(widgets):
            widget.can_focus = True
            widget.tab_index = i
```

## Implementation Details

### Navigation Flow

1. **Panel Navigation**
   - Tab: Next panel
   - Shift+Tab: Previous panel
   - Arrow keys: Move within panel

2. **Widget Navigation**
   - Enter: Activate button/input
   - Escape: Exit input/cancel
   - Space: Toggle checkboxes

3. **Focus Chain**
```
Trading Panel → Order Monitor → Position Monitor → 
Account Monitor → Market Data → Back to Trading Panel
```

### Keyboard Shortcuts
```python
BINDINGS = [
    ("tab", "focus_next", "Next field"),
    ("shift+tab", "focus_previous", "Previous field"),
    ("ctrl+o", "focus_orders", "Jump to orders"),
    ("ctrl+p", "focus_positions", "Jump to positions"),
    ("ctrl+t", "focus_trading", "Jump to trading"),
    ("escape", "unfocus", "Clear focus"),
]
```

### Mouse Support
```python
def on_click(self, event):
    """Handle mouse clicks to focus elements"""
    # Get widget at mouse position
    widget = self.get_widget_at(event.x, event.y)
    if widget and widget.can_focus:
        widget.focus()
```

## Success Criteria

### Measurable Outcomes
- ✅ Tab key cycles through all panels
- ✅ All buttons can be reached via keyboard
- ✅ Focused element clearly visible
- ✅ Mouse clicks focus elements
- ✅ Enter key activates buttons

### Verification Method
```python
# Manual test procedure:
"""
1. Start TUI: python run_tui.py
2. Press Tab - focus should move to next panel
3. Press Shift+Tab - focus should move back
4. Navigate to button and press Enter - should trigger action
5. Click on input field - should focus and allow typing
6. Press Escape - should clear focus
"""

# Automated test:
async def test_navigation():
    app = FoxtrotTUIApp()
    async with app.run_test() as pilot:
        # Test tab navigation
        await pilot.press("tab")
        assert app.focused.id == "symbol_input"
        
        await pilot.press("tab")
        assert app.focused.id == "quantity_input"
        
        # Test button activation
        await pilot.press("enter")
        assert button_clicked
```

## Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Textual API changes | Low | High | Pin Textual version |
| Focus conflicts | Medium | Medium | Test all navigation paths |
| Performance impact | Low | Low | Focus changes are lightweight |

## Estimated Timeline

- Hour 1: Implement basic Tab navigation
- Hour 2: Add visual focus indicators
- Hour 3: Test and refine navigation flow

## Dependencies

- TUI must be running (even if broken)
- Textual library properly installed

## Notes

- Don't redesign the UI, just fix navigation
- Keep changes minimal
- Test with keyboard-only navigation
- Ensure accessibility compliance