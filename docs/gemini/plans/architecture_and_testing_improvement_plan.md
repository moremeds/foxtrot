
# Foxtrot Architecture and Testing Improvement Plan

## 1. Introduction

This document outlines a plan to refactor the architecture and enhance the testing strategy of the Foxtrot trading platform. The goal is to improve modularity, reduce coupling, and increase test coverage, leading to a more robust and maintainable codebase. This plan is based on the principles outlined in the project's `GEMINI.md` file.

## 2. Architectural Refactoring

The current architecture, particularly the `MainEngine`, exhibits tight coupling and violates the Open/Closed Principle. The following steps will address these issues.

### 2.1. Decouple `MainEngine` with a Service Locator

1.  **Create `ServiceLocator`:**
    *   Create a new file: `foxtrot/server/service_locator.py`.
    *   Implement a `ServiceLocator` class in this file.
    *   The `ServiceLocator` will have methods to `register` and `get` services (engines and adapters).

2.  **Refactor `MainEngine`:**
    *   Modify `MainEngine` to take the `ServiceLocator` as a dependency in its `__init__` method.
    *   Remove the `add_engine` and `add_adapter` methods from `MainEngine`.
    *   Modify `MainEngine` to retrieve engines and adapters from the `ServiceLocator` instead of creating them directly.

### 2.2. Refactor `server/engine.py`

The `server/engine.py` file currently exceeds the 200-line limit and contains multiple classes. This will be addressed by splitting the file.

1.  **Create `engines` Directory:**
    *   Create a new directory: `foxtrot/server/engines/`.

2.  **Move Engine Classes:**
    *   Move `LogEngine` to `foxtrot/server/engines/log_engine.py`.
    *   Move `OmsEngine` to `foxtrot/server/engines/oms_engine.py`.
    *   Move `EmailEngine` to `foxtrot/server/engines/email_engine.py`.

3.  **Update Imports:**
    *   Update all necessary imports to reflect the new file structure.

### 2.3. Introduce a Plugin System

To make the system more extensible, we will introduce a plugin-style registration system.

1.  **Registration at Startup:**
    *   The main application entry point (e.g., `run.py`) will be responsible for creating the `ServiceLocator`.
    *   It will then register all the desired engines and adapters with the `ServiceLocator`.
    *   Finally, it will create the `MainEngine`, passing the `ServiceLocator` to it.

## 3. Testing Enhancements

The following steps will improve the test coverage and quality.

### 3.1. Implement Comprehensive Unit Tests

1.  **Test `MainEngine`:**
    *   Create `tests/unit/server/test_main_engine.py`.
    *   Write unit tests for `MainEngine`, using a mock `ServiceLocator` to provide mock engines and adapters.

2.  **Test Engines:**
    *   Create `tests/unit/server/engines/test_log_engine.py`.
    *   Create `tests/unit/server/engines/test_oms_engine.py`.
    *   Create `tests/unit/server/engines/test_email_engine.py`.
    *   Write unit tests for each engine, mocking their dependencies.

3.  **Test `EventEngine`:**
    *   Create `tests/unit/core/test_event_engine.py`.
    *   Write unit tests to verify the thread safety and event dispatching logic of the `EventEngine`.

### 3.2. Improve Integration Testing

1.  **Targeted Integration Tests:**
    *   Create integration tests in the `tests/integration/` directory that test the interaction between specific components.
    *   For example, test the `OmsEngine` with a real `EventEngine` to ensure they work together correctly.

### 3.3. Adopt a Clear Mocking Strategy

1.  **Create Reusable Mocks:**
    *   In the `tests/mocks/` directory, create reusable mock classes for core components like `MockEventEngine`, `MockMainEngine`, and `MockServiceLocator`.
    *   These mocks will be used across the test suite to ensure consistency.

## 4. Plan Execution

This plan will be executed in the following order:

1.  Perform the architectural refactoring (Service Locator, file splitting).
2.  Implement the unit tests for the refactored components.
3.  Implement the integration tests.
4.  Review the test coverage and add more tests as needed.

## 5. Present for Approval

This plan is now ready for review and approval.
