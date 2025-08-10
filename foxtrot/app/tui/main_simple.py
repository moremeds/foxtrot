#!/usr/bin/env python3
"""
Simple TUI entry point without import-time dependencies.

This module provides a clean entry point for the TUI application,
avoiding circular imports and module-level initialization issues.
"""

def run_tui():
    """
    Run the Foxtrot TUI application with proper initialization order.
    
    This function handles all imports and initialization at runtime
    to avoid circular dependency issues.
    """
    import sys
    import os
    from pathlib import Path
    
    # Ensure we can import foxtrot
    project_root = Path(__file__).parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Step 1: Basic setup
    print("Starting Foxtrot TUI...")
    print("=" * 50)
    
    try:
        # Step 2: Import core components (these should be safe)
        print("Importing EventEngine...")
        from foxtrot.core.event_engine import EventEngine
        print("✓ EventEngine imported")
        
        print("Importing MainEngine...")
        from foxtrot.server.engine import MainEngine
        print("✓ MainEngine imported")
        
        # Step 3: Create the engines
        print("Creating EventEngine...")
        event_engine = EventEngine()
        print("✓ EventEngine created")
        
        print("Creating MainEngine...")
        main_engine = MainEngine(event_engine)
        print("✓ MainEngine created")
        print("✓ Trading engines initialized")
        
        # Step 4: Import TUI components AFTER engines are ready
        # This avoids any circular dependencies
        from foxtrot.app.tui.main_app import FoxtrotTUIApp
        
        # Step 5: Create the TUI application
        print("Creating TUI application...")
        app = FoxtrotTUIApp(main_engine, event_engine)
        print("✓ TUI application created")
        
        # Step 6: Display startup info
        print("\nFoxtrot TUI Ready!")
        print("Press Ctrl+Q to quit")
        print("Press F1 for help")
        print("=" * 50)
        
        # Step 7: Run the application
        app.run()
        
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("\nPlease ensure all dependencies are installed:")
        print("  uv sync")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n\nShutdown requested by user")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ Failed to start TUI: {e}")
        
        # Optional: show traceback in debug mode
        if os.environ.get("TEXTUAL_DEBUG") == "1":
            import traceback
            traceback.print_exc()
        
        sys.exit(1)


def main():
    """
    Main entry point that can be called from scripts.
    
    This wrapper function ensures clean initialization.
    """
    # Avoid any module-level imports or initialization
    run_tui()


if __name__ == "__main__":
    main()