#!/usr/bin/env python3
"""
Minimal TUI application for testing.

This is a bare-bones TUI to isolate the recursion issue.
"""

def run_minimal_tui():
    """Run a minimal TUI without any complex components."""
    import sys
    from pathlib import Path
    
    # Add project to path
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    print("Starting Minimal TUI Test...")
    print("=" * 50)
    
    # Test 1: Import Textual
    print("1. Importing Textual...")
    try:
        from textual.app import App
        from textual.widgets import Static
        print("   ✓ Textual imported")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return
    
    # Test 2: Create minimal app
    print("2. Creating minimal Textual app...")
    
    class MinimalApp(App):
        """A minimal Textual application."""
        
        def compose(self):
            """Create the app layout."""
            yield Static("Minimal TUI is working!")
    
    try:
        app = MinimalApp()
        print("   ✓ App created")
    except RecursionError as e:
        print(f"   ✗ RecursionError: {e}")
        import traceback
        traceback.print_exc()
        return
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return
    
    # Test 3: Import our engines
    print("3. Testing engine imports...")
    try:
        from foxtrot.core.event_engine import EventEngine
        from foxtrot.server.engine import MainEngine
        print("   ✓ Engines imported")
        
        event_engine = EventEngine()
        main_engine = MainEngine(event_engine)
        print("   ✓ Engines created")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return
    
    # Test 4: Create app with engines
    print("4. Creating app with engines...")
    
    class AppWithEngines(App):
        """App that takes engines as parameters."""
        
        def __init__(self, main_engine, event_engine, **kwargs):
            super().__init__(**kwargs)
            self.main_engine = main_engine
            self.event_engine = event_engine
            
        def compose(self):
            """Create the app layout."""
            yield Static("App with engines is working!")
    
    try:
        app2 = AppWithEngines(main_engine, event_engine)
        print("   ✓ App with engines created")
    except RecursionError as e:
        print(f"   ✗ RecursionError: {e}")
        import traceback
        traceback.print_exc()
        return
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return
    
    # Test 5: Import FoxtrotTUIApp
    print("5. Testing FoxtrotTUIApp import...")
    try:
        from foxtrot.app.tui.main_app import FoxtrotTUIApp
        print("   ✓ FoxtrotTUIApp imported")
    except RecursionError as e:
        print(f"   ✗ RecursionError during import: {e}")
        return
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return
    
    # Test 6: Create FoxtrotTUIApp
    print("6. Creating FoxtrotTUIApp...")
    try:
        app3 = FoxtrotTUIApp(main_engine, event_engine)
        print("   ✓ FoxtrotTUIApp created")
    except RecursionError as e:
        print(f"   ✗ RecursionError during creation: {e}")
        import traceback
        traceback.print_exc()
        return
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return
    
    print("\n✅ All tests passed!")
    print("\nWould run app.run() here, but skipping to avoid blocking")
    # app3.run()  # Uncomment to actually run the app


if __name__ == "__main__":
    run_minimal_tui()