# Foxtrot Trading Platform - Realistic Master Plan

**Version:** 2.0  
**Date:** August 6, 2025  
**Status:** Replacing Over-Engineered Plans

## Executive Summary

This master plan replaces the over-engineered improvement plans that focus on copying Nautilus Trader's production features. Foxtrot is a Python research platform, not a production trading system. The project currently has fundamental problems that must be fixed before any advanced features.

### Critical Issues Found

1. **Code Organization Crisis**: Files with 1290 lines (6x over the 200-line limit from CLAUDE.md)
2. **Test Infrastructure Broken**: Tests don't run at all, 0% actual coverage
3. **TUI Non-Functional**: Buttons don't work, panels can't be navigated
4. **Over-Engineering**: Existing plans propose circuit breakers and metrics systems when basic tests don't work

### Core Philosophy

- **Fix fundamentals first** - No new features until basics work
- **Incremental improvements** - Small, verifiable changes
- **Avoid over-engineering** - Simple solutions for Python research platform
- **Clear success metrics** - Each task has measurable outcomes

## Rejected Over-Engineering

### What We're NOT Doing

| Rejected Feature | Why It's Over-Engineering | What We'll Do Instead |
|-----------------|---------------------------|---------------------|
| Circuit Breakers | Production feature for high-frequency systems | Simple retry with exponential backoff |
| Metrics Collection System | Unnecessary for research platform | Basic logging with levels |
| Advanced Cache System | Premature optimization | Simple dict-based cache |
| Service Locator Pattern | Adds complexity without benefit | Direct imports and dependency injection |
| Property-Based Testing | Too complex for current state | Simple unit tests first |
| 90% Test Coverage | Unrealistic initial target | 50% coverage of critical paths |
| Rust/Cython Extensions | Against Python-native philosophy | Pure Python optimization |
| Nanosecond Precision | Over-kill for research | Millisecond precision sufficient |

## Realistic Implementation Plan

### Phase 1: Code Health Emergency (Week 1-2)

**Problem**: Massive file size violations destroying maintainability

**Specifications**:
- [spec-01-file-splitting.md](./specs/spec-01-file-splitting.md) - Break up oversized files
- [spec-02-remove-globals.md](./specs/spec-02-remove-globals.md) - Eliminate global instances
- [spec-03-basic-docstrings.md](./specs/spec-03-basic-docstrings.md) - Add minimal documentation

**Success Criteria**:
- ✅ All files under 200 lines
- ✅ No global instances in imports
- ✅ All public methods have docstrings

### Phase 2: Test Infrastructure Repair (Week 3-4)

**Problem**: Tests don't run, making development dangerous

**Specifications**:
- [spec-04-fix-test-collection.md](./specs/spec-04-fix-test-collection.md) - Make pytest collect tests
- [spec-05-basic-unit-tests.md](./specs/spec-05-basic-unit-tests.md) - One test per component
- [spec-06-test-fixtures.md](./specs/spec-06-test-fixtures.md) - Reusable test utilities

**Success Criteria**:
- ✅ `pytest tests/` runs without errors
- ✅ At least 1 test per major component
- ✅ 50% code coverage on critical paths

### Phase 3: Architecture Cleanup (Week 5-6)

**Problem**: Circular dependencies, data clumps, code duplication

**Specifications**:
- [spec-07-fix-circular-deps.md](./specs/spec-07-fix-circular-deps.md) - Break dependency cycles
- [spec-08-extract-data-classes.md](./specs/spec-08-extract-data-classes.md) - Fix data clumps
- [spec-09-standardize-errors.md](./specs/spec-09-standardize-errors.md) - Consistent error handling

**Success Criteria**:
- ✅ No circular imports
- ✅ Data clumps extracted to proper classes
- ✅ Standardized error handling pattern

### Phase 4: TUI Basic Functionality (Week 7)

**Problem**: TUI doesn't respond to user input

**Specifications**:
- [spec-10-fix-navigation.md](./specs/spec-10-fix-navigation.md) - Enable Tab navigation
- [spec-11-connect-buttons.md](./specs/spec-11-connect-buttons.md) - Make buttons work
- [spec-12-responsive-layout.md](./specs/spec-12-responsive-layout.md) - Handle terminal resize

**Success Criteria**:
- ✅ Tab key navigates between panels
- ✅ Buttons trigger actual actions
- ✅ TUI adapts to terminal size changes

### Phase 5: Integration & Validation (Week 8)

**Problem**: No confidence that components work together

**Specifications**:
- [spec-13-integration-tests.md](./specs/spec-13-integration-tests.md) - Test component interactions
- [spec-14-e2e-workflows.md](./specs/spec-14-e2e-workflows.md) - End-to-end scenarios
- [spec-15-documentation.md](./specs/spec-15-documentation.md) - Update docs to match reality

**Success Criteria**:
- ✅ Integration tests for adapter + engine
- ✅ E2E test for complete order workflow
- ✅ Documentation matches implementation

## Implementation Priority Matrix

| Task | Impact | Effort | Risk | Priority |
|------|--------|--------|------|----------|
| File Splitting | Critical | Low | Low | P0 - Immediate |
| Fix Test Collection | Critical | Low | Low | P0 - Immediate |
| Remove Globals | High | Low | Medium | P1 - High |
| Basic Unit Tests | High | Medium | Low | P1 - High |
| Fix Circular Deps | High | Medium | Medium | P1 - High |
| TUI Navigation | Medium | Low | Low | P2 - Medium |
| Integration Tests | Medium | Medium | Low | P2 - Medium |
| Documentation | Low | Low | Low | P3 - Low |

## What Happens AFTER Foundation is Fixed

Only after all 5 phases are complete should we consider:

1. **Performance Optimization** - Profile and optimize bottlenecks
2. **Advanced Error Handling** - Retry strategies, recovery mechanisms
3. **State Persistence** - SQLite for saving application state
4. **Risk Management** - Basic position limits and checks
5. **Additional Adapters** - Support more brokers/exchanges

## Success Metrics

### Phase 1 Success
- [ ] 0 files over 200 lines
- [ ] 0 global instances
- [ ] 100% public methods documented

### Phase 2 Success
- [ ] pytest runs successfully
- [ ] 20+ passing tests
- [ ] 50% coverage on event_engine, adapters

### Phase 3 Success
- [ ] 0 circular dependencies
- [ ] 0 data clumps over 3 parameters
- [ ] Consistent error handling

### Phase 4 Success
- [ ] TUI fully navigable
- [ ] All buttons functional
- [ ] Responsive to terminal resize

### Phase 5 Success
- [ ] 10+ integration tests
- [ ] 1+ E2E workflow test
- [ ] README accurate

## Anti-Patterns to Avoid

❌ **DO NOT**:
- Add abstraction layers before fixing basics
- Copy Nautilus patterns without understanding need
- Implement production features for research platform
- Add new features before foundation is solid
- Pursue 90% test coverage initially
- Over-architect for hypothetical future needs

✅ **DO**:
- Fix the most painful problems first
- Write simple, readable Python code
- Focus on making existing features work
- Add tests incrementally
- Keep solutions proportional to problems
- Build only what's needed now

## Timeline & Resources

### Realistic Timeline
- **Week 1-2**: Code Health (20 hours)
- **Week 3-4**: Test Infrastructure (20 hours)
- **Week 5-6**: Architecture Cleanup (20 hours)
- **Week 7**: TUI Fixes (10 hours)
- **Week 8**: Integration (10 hours)

**Total**: 80 hours over 8 weeks (part-time development)

### Required Skills
- Python development (intermediate)
- pytest knowledge (basic)
- Refactoring experience (helpful)
- No Rust/Cython/advanced patterns needed

## Conclusion

This plan focuses on fixing Foxtrot's real problems instead of adding unnecessary complexity. The existing plans are trying to turn Foxtrot into Nautilus Trader, but Foxtrot should be Foxtrot - a simple, accessible Python trading platform for research and education.

By following this pragmatic plan, Foxtrot will have a solid foundation in 8 weeks, after which advanced features can be considered if actually needed.

## Next Steps

1. Review and approve this master plan
2. Start with Phase 1 immediately (file splitting is urgent)
3. Track progress using simple checklist
4. Defer all feature requests until Phase 5 complete
5. Reassess advanced features only after foundation solid