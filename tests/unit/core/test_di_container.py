"""
Unit tests for the Dependency Injection Container.

Tests registration, resolution, and override functionality.
"""

import pytest
from unittest.mock import MagicMock

from foxtrot.core.di_container import DIContainer


class TestService:
    """Test service class."""
    def __init__(self, value: str = "default"):
        self.value = value
        
    def get_value(self) -> str:
        return self.value


class DependentService:
    """Service that depends on TestService."""
    def __init__(self, test_service: TestService):
        self.test_service = test_service
        
    def use_dependency(self) -> str:
        return f"Using: {self.test_service.get_value()}"


class TestDIContainer:
    """Test suite for DIContainer."""
    
    @pytest.fixture
    def container(self):
        """Create a fresh container for each test."""
        return DIContainer()
    
    def test_register_factory(self, container):
        """Test factory registration and object creation."""
        # Counter to track factory calls
        call_count = 0
        
        def factory():
            nonlocal call_count
            call_count += 1
            return TestService(f"instance_{call_count}")
        
        # Register factory
        container.register_factory(TestService, factory)
        
        # Create instances
        instance1 = container.create(TestService)
        instance2 = container.create(TestService)
        
        # Each create should call factory
        assert call_count == 2
        assert instance1.get_value() == "instance_1"
        assert instance2.get_value() == "instance_2"
        assert instance1 is not instance2
    
    def test_register_singleton(self, container):
        """Test singleton registration."""
        # Create and register singleton
        singleton = TestService("singleton_value")
        container.register_singleton(TestService, singleton)
        
        # Get singleton multiple times
        instance1 = container.get_singleton(TestService)
        instance2 = container.get_singleton(TestService)
        
        # Should be the same instance
        assert instance1 is instance2
        assert instance1 is singleton
        assert instance1.get_value() == "singleton_value"
    
    def test_override_for_testing(self, container):
        """Test override functionality for testing."""
        # Register original factory
        container.register_factory(TestService, lambda: TestService("original"))
        
        # Create normal instance
        original = container.create(TestService)
        assert original.get_value() == "original"
        
        # Override with mock
        mock_service = MagicMock(spec=TestService)
        mock_service.get_value.return_value = "mocked"
        container.override(TestService, mock_service)
        
        # Create should now return override
        overridden = container.create(TestService)
        assert overridden is mock_service
        assert overridden.get_value() == "mocked"
    
    def test_clear_override(self, container):
        """Test clearing overrides."""
        # Register factory
        container.register_factory(TestService, lambda: TestService("original"))
        
        # Override
        mock_service = MagicMock(spec=TestService)
        container.override(TestService, mock_service)
        
        # Verify override works
        assert container.create(TestService) is mock_service
        
        # Clear override
        container.clear_override(TestService)
        
        # Should return to original factory
        instance = container.create(TestService)
        assert instance is not mock_service
        assert instance.get_value() == "original"
    
    def test_clear_all_overrides(self, container):
        """Test clearing all overrides at once."""
        # Register multiple factories
        container.register_factory(TestService, lambda: TestService("original"))
        container.register_factory(DependentService, 
                                 lambda: DependentService(TestService("dep")))
        
        # Override both
        mock1 = MagicMock(spec=TestService)
        mock2 = MagicMock(spec=DependentService)
        container.override(TestService, mock1)
        container.override(DependentService, mock2)
        
        # Verify overrides
        assert container.create(TestService) is mock1
        assert container.create(DependentService) is mock2
        
        # Clear all
        container.clear_all_overrides()
        
        # Both should return to original
        service = container.create(TestService)
        dependent = container.create(DependentService)
        
        assert service is not mock1
        assert dependent is not mock2
        assert service.get_value() == "original"
    
    def test_create_without_registration(self, container):
        """Test creating object without registration raises error."""
        # Should raise KeyError when not registered
        with pytest.raises(KeyError):
            container.create(TestService)
    
    def test_get_singleton_without_registration(self, container):
        """Test getting singleton without registration returns None."""
        # Should return None when not registered
        result = container.get_singleton(TestService)
        assert result is None
    
    def test_factory_with_arguments(self, container):
        """Test factory that accepts arguments."""
        def factory(value: str = "default"):
            return TestService(value)
        
        container.register_factory(TestService, factory)
        
        # Create with default
        default_instance = container.create(TestService)
        assert default_instance.get_value() == "default"
        
        # Create with custom value
        custom_instance = container.create(TestService, value="custom")
        assert custom_instance.get_value() == "custom"
    
    def test_singleton_replacement(self, container):
        """Test replacing a singleton."""
        # Register first singleton
        singleton1 = TestService("first")
        container.register_singleton(TestService, singleton1)
        assert container.get_singleton(TestService).get_value() == "first"
        
        # Replace with new singleton
        singleton2 = TestService("second")
        container.register_singleton(TestService, singleton2)
        assert container.get_singleton(TestService).get_value() == "second"
    
    def test_multiple_types(self, container):
        """Test registering multiple different types."""
        # Register different types
        container.register_factory(TestService, lambda: TestService("test"))
        container.register_factory(DependentService, 
                                 lambda: DependentService(TestService("dep")))
        
        # Create instances
        service = container.create(TestService)
        dependent = container.create(DependentService)
        
        # Verify they work independently
        assert service.get_value() == "test"
        assert dependent.use_dependency() == "Using: dep"
    
    def test_override_singleton(self, container):
        """Test that override works with singletons."""
        # Register singleton
        singleton = TestService("singleton")
        container.register_singleton(TestService, singleton)
        
        # Override should take precedence
        override = TestService("override")
        container.override(TestService, override)
        
        # Both create and get_singleton should return override
        assert container.create(TestService) is override
        assert container.get_singleton(TestService) is override
    
    def test_factory_exception_propagation(self, container):
        """Test that factory exceptions are propagated."""
        def failing_factory():
            raise ValueError("Factory failed")
        
        container.register_factory(TestService, failing_factory)
        
        # Exception should propagate
        with pytest.raises(ValueError, match="Factory failed"):
            container.create(TestService)
    
    def test_complex_factory(self, container):
        """Test factory that creates complex objects."""
        def complex_factory():
            # Create dependencies
            test_service = TestService("complex")
            return DependentService(test_service)
        
        container.register_factory(DependentService, complex_factory)
        
        # Create and verify
        dependent = container.create(DependentService)
        assert dependent.use_dependency() == "Using: complex"
    
    def test_stateful_factory(self, container):
        """Test factory with state."""
        class StatefulFactory:
            def __init__(self):
                self.counter = 0
                
            def create(self):
                self.counter += 1
                return TestService(f"instance_{self.counter}")
        
        factory = StatefulFactory()
        container.register_factory(TestService, factory.create)
        
        # Create multiple instances
        instance1 = container.create(TestService)
        instance2 = container.create(TestService)
        instance3 = container.create(TestService)
        
        # Verify state is maintained
        assert instance1.get_value() == "instance_1"
        assert instance2.get_value() == "instance_2"
        assert instance3.get_value() == "instance_3"