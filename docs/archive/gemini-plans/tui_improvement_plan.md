### Analysis

Based on the user's feedback and an analysis of the project structure, the current TUI implementation has several critical issues that prevent it from being a usable interface.

1.  **Lack of Responsive Layout:** The TUI does not adapt to changes in terminal size. This indicates that the layout is likely static and does not use a responsive layout manager. For a terminal application, this is a fundamental flaw that makes it unusable in different environments.

2.  **Navigation and Interaction Issues:** The inability to navigate between panels and the non-functional buttons suggest problems with the event handling and focus management within the TUI application. The core logic for user interaction is either missing or incorrectly implemented.

3.  **Component Integration:** The problems described point to a potential disconnect between the TUI components and the underlying application logic. The TUI is not correctly sending events to the main engine or receiving updates from it.

4.  **Code Structure:** I will investigate the `foxtrot/app/tui/` directory to understand the current implementation. I'll look for the main TUI application class, the layout definition, and the event handlers for key presses and mouse clicks. I will also examine `run_tui.py` to see how the TUI is initialized and integrated with the rest of the application.

### Plan

Based on this analysis, I propose the following plan to fix the TUI and make it a functional and user-friendly interface.

1.  **Implement a Responsive Layout:**
    *   Replace the current static layout with a dynamic layout manager. I recommend using a library like `textual` which provides a sophisticated layout system that handles resizing automatically.
    *   Define the TUI layout using a hierarchical structure of containers and widgets. This will ensure that the interface adapts gracefully to different terminal sizes.

2.  **Fix Navigation and Focus Management:**
    *   Implement a robust focus management system that allows the user to navigate between panels using the keyboard (e.g., Tab key) and mouse.
    *   Ensure that only one widget has focus at a time and that the focused widget is clearly indicated to the user.

3.  **Implement Button and Input Handling:**
    *   Connect the button widgets to the appropriate callback functions. When a button is pressed, it should trigger the corresponding action in the application.
    *   Implement input handlers for text boxes and other input widgets. The input should be validated and then sent to the main engine.

4.  **Integrate with the Main Engine:**
    *   Establish a clear communication channel between the TUI and the `MainEngine`.
    *   The TUI should send user actions (e.g., placing an order) to the `MainEngine` as events.
    *   The TUI should subscribe to events from the `MainEngine` (e.g., order updates, market data) and update the display accordingly.

5.  **Create a TUI Test Suite:**
    *   Develop a suite of integration tests for the TUI.
    *   These tests should simulate user interactions (e.g., key presses, mouse clicks) and verify that the TUI behaves as expected.
    *   This will help to prevent regressions and ensure that the TUI remains functional as the application evolves.

6.  **Present Plan for Approval:**
    *   Save this analysis and plan to `/home/ubuntu/projects/foxtrot/docs/gemini/plans/tui_improvement_plan.md`.
    *   Present the plan to the user for review and approval before any implementation begins.

### Deeper Analysis and Recommendations

After reviewing the TUI source code, I have identified the following specific issues and areas for improvement that align with the initial plan.

**1. Layout and Resizing (Relates to Plan Item 1)**

*   **Finding:** The main layout is defined in `FoxtrotTUIApp.CSS` using a `grid` layout. While `grid` is a powerful layout mode in Textual, the current implementation is static (`grid-size: 3 3;`). This is the primary reason the TUI does not resize correctly. The components are placed in fixed grid cells and do not adapt to terminal size changes.
*   **Challenge:** The current layout is simple but not robust. A more complex and nested layout is needed to achieve true responsiveness.
*   **Recommendation:**
    *   Refactor the `compose` method in `FoxtrotTUIApp` to use nested `Horizontal` and `Vertical` containers instead of a single top-level grid. This will allow for more flexible and responsive layouts.
    *   Use fractional `width` and `height` units (e.g., `width="1fr"`) for widgets to allow them to grow and shrink with the available space.
    *   The `TUITradingPanel` should be designed to be a self-contained, responsive component that can be placed in any layout.

**2. Navigation and Interaction (Relates to Plan Items 2 & 3)**

*   **Finding:** The application relies on Textual's default focus management (`self.screen.focus_next()`). While this works for simple layouts, it is likely failing in the current grid layout because the focus order is not explicitly defined. The buttons in `TUITradingPanel` have `on_button_pressed` handlers, but if they never receive focus, these handlers will not be called.
*   **Challenge:** The current event handling is fragmented. The `TUITradingPanel` has its own event handlers, but the main app also has global key bindings. This can lead to conflicts and unexpected behavior.
*   **Recommendation:**
    *   Implement a more explicit focus management system. Use Textual's `focus()` method to programmatically set focus on specific widgets when needed (e.g., after submitting an order).
    *   Consolidate key bindings. The most important actions should be available as global key bindings in `FoxtrotTUIApp`, and these actions should call methods on the appropriate child widgets. This creates a single source of truth for user actions.
    *   Ensure that all interactive widgets (inputs, buttons, selects) are focusable and have a clear visual state when focused.

**3. Component Integration and Event Handling (Relates to Plan Item 4)**

*   **Finding:** The `EventEngineAdapter` is a good pattern for bridging the gap between the synchronous `MainEngine` and the asynchronous Textual TUI. However, the integration is incomplete. For example, the `TUITradingPanel` has `_on_tick_event` and other event handlers, but they are not fully implemented to update the UI in real-time.
*   **Challenge:** The current implementation mixes direct calls to the `MainEngine` with event-based communication. This can lead to inconsistencies and race conditions.
*   **Recommendation:**
    *   Strictly adhere to an event-driven architecture within the TUI. The TUI should *only* interact with the `MainEngine` by sending events through the `EventEngineAdapter`. It should *only* receive updates by listening for events from the `EventEngine`.
    *   The `TUITradingPanel` should be completely decoupled from the `MainEngine`. It should receive all necessary data (e.g., account balance, market data) through events.
    *   Implement the `_on_tick_event`, `_on_order_event`, and `_on_account_event` handlers in `TUITradingPanel` to update the UI with the latest data from the event engine.

**4. Code Structure and "Bad Tastes"**

*   **Finding:** The monitor components (`TUIOrderMonitor`, `TUIPositionMonitor`, etc.) are well-structured and inherit from a common `TUIDataMonitor` base class. This is a good example of code reuse. However, the `TUITradingPanel` is a large, monolithic component that handles validation, UI logic, and event handling.
*   **Challenge:** The `TUITradingPanel` is becoming a "god object" that knows too much and does too much. This makes it difficult to test and maintain.
*   **Recommendation:**
    *   Refactor the `TUITradingPanel` into smaller, more focused components. For example:
        *   `OrderForm`: A component that only handles the order entry form and its validation.
        *   `OrderPreview`: A component that displays the order preview.
        *   `MarketDataDisplay`: A component that displays market data.
    *   These smaller components can then be composed together in the `TUITradingPanel`. This will improve modularity and make the code easier to understand and test.
    *   The validation logic in `TUITradingPanel` should be extracted into a separate `FormValidator` class that can be tested independently.