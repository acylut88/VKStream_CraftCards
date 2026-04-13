#!/usr/bin/env python
import sys
try:
    from database import DatabaseManager
    print("✅ Database module loaded")
    
    from main import db, engine
    print("✅ Main module loaded")
    
    from api import app
    print("✅ API module loaded")
    
    print("\n✅ All Phase 2 modules imported successfully!")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
