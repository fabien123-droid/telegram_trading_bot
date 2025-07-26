#!/usr/bin/env python3
"""
Script de test pour vérifier les imports
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test all critical imports"""
    
    print("🧪 Test des imports...")
    
    try:
        print("1. Test import core.config...")
        from core.config import get_settings, validate_required_settings
        print("   ✅ core.config OK")
        
        # Test de la configuration
        settings = get_settings()
        print(f"   📋 Bot token présent: {bool(settings.telegram_bot_token)}")
        print(f"   📋 Database URL: {settings.database_url}")
        
    except Exception as e:
        print(f"   ❌ core.config ÉCHEC: {e}")
        return False
    
    try:
        print("2. Test import core.main...")
        from core.main import main
        print("   ✅ core.main OK")
    except Exception as e:
        print(f"   ❌ core.main ÉCHEC: {e}")
        return False
    
    try:
        print("3. Test import database.database...")
        from database.database import init_database, close_database
        print("   ✅ database.database OK")
    except Exception as e:
        print(f"   ❌ database.database ÉCHEC: {e}")
        return False
    
    try:
        print("4. Test import database.models...")
        from database.models import Base, User
        print("   ✅ database.models OK")
    except Exception as e:
        print(f"   ❌ database.models ÉCHEC: {e}")
        return False
    
    print("\n🎉 Tous les imports critiques fonctionnent !")
    return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
