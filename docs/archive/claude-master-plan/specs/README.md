# Foxtrot Improvement Specifications

This directory contains granular specifications for fixing Foxtrot's fundamental issues. Each spec has clear, verifiable outcomes.

## Phase 1: Code Health Emergency (Week 1-2)

- [spec-01-file-splitting.md](./spec-01-file-splitting.md) - Break up files exceeding 200 lines
- [spec-02-remove-globals.md](./spec-02-remove-globals.md) - Eliminate global instances
- [spec-03-basic-docstrings.md](./spec-03-basic-docstrings.md) - Add minimal documentation

## Phase 2: Test Infrastructure Repair (Week 3-4)

- [spec-04-fix-test-collection.md](./spec-04-fix-test-collection.md) - Make pytest collect tests
- [spec-05-basic-unit-tests.md](./spec-05-basic-unit-tests.md) - One test per component
- [spec-06-test-fixtures.md](./spec-06-test-fixtures.md) - Reusable test utilities

## Phase 3: Architecture Cleanup (Week 5-6)

- [spec-07-fix-circular-deps.md](./spec-07-fix-circular-deps.md) - Break dependency cycles
- [spec-08-extract-data-classes.md](./spec-08-extract-data-classes.md) - Fix data clumps
- [spec-09-standardize-errors.md](./spec-09-standardize-errors.md) - Consistent error handling

## Phase 4: TUI Basic Functionality (Week 7)

- [spec-10-fix-navigation.md](./spec-10-fix-navigation.md) - Enable Tab navigation
- [spec-11-connect-buttons.md](./spec-11-connect-buttons.md) - Make buttons work
- [spec-12-responsive-layout.md](./spec-12-responsive-layout.md) - Handle terminal resize

## Phase 5: Integration & Validation (Week 8)

- [spec-13-integration-tests.md](./spec-13-integration-tests.md) - Test component interactions
- [spec-14-e2e-workflows.md](./spec-14-e2e-workflows.md) - End-to-end scenarios
- [spec-15-documentation.md](./spec-15-documentation.md) - Update docs to match reality

## Implementation Order

1. **Critical** (Do First):
   - spec-01: File splitting
   - spec-02: Remove globals
   - spec-04: Fix test collection

2. **High Priority** (Do Second):
   - spec-05: Basic unit tests
   - spec-07: Fix circular dependencies

3. **Medium Priority** (Do Third):
   - spec-10: Fix navigation
   - spec-13: Integration tests

4. **Low Priority** (Do Last):
   - spec-15: Documentation

## Success Tracking

Each spec includes:
- ✅ Clear success criteria
- 📊 Measurable outcomes  
- 🧪 Verification methods
- ⏱️ Time estimates

Track progress by checking off success criteria in each spec.

## Anti-Patterns to Avoid

While implementing these specs, DO NOT:
- Add new features
- Copy Nautilus patterns
- Over-engineer solutions
- Pursue perfection
- Skip verification

## Notes

- Specs can be implemented independently
- Each spec is self-contained
- Focus on one spec at a time
- Verify success before moving on