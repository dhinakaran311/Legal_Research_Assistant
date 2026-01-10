"""
Verify INTERNAL_API_KEY Configuration
Checks if AI Engine and Backend have matching API keys
"""
import os
from pathlib import Path
from dotenv import load_dotenv

def verify_api_keys():
    """Verify that AI Engine and Backend have matching INTERNAL_API_KEY"""
    
    print("=" * 60)
    print("🔐 INTERNAL_API_KEY Verification")
    print("=" * 60)
    print()
    
    # Paths
    project_root = Path(__file__).parent
    ai_engine_env = project_root / "ai_engine" / ".env"
    backend_env = project_root / "backend" / ".env"
    
    # Load AI Engine .env
    ai_engine_key = None
    if ai_engine_env.exists():
        load_dotenv(ai_engine_env)
        ai_engine_key = os.getenv("INTERNAL_API_KEY")
        print(f"✅ AI Engine .env found: {ai_engine_env}")
        if ai_engine_key:
            print(f"   INTERNAL_API_KEY: {ai_engine_key[:20]}...{ai_engine_key[-10:]}")
        else:
            print("   ⚠️  INTERNAL_API_KEY not set or empty")
    else:
        print(f"❌ AI Engine .env not found: {ai_engine_env}")
        print("   Create this file with INTERNAL_API_KEY")
    
    print()
    
    # Load Backend .env
    backend_key = None
    if backend_env.exists():
        # Clear previous env vars
        for key in list(os.environ.keys()):
            if key.startswith("INTERNAL_API_KEY"):
                del os.environ[key]
        
        load_dotenv(backend_env)
        backend_key = os.getenv("INTERNAL_API_KEY")
        print(f"✅ Backend .env found: {backend_env}")
        if backend_key:
            print(f"   INTERNAL_API_KEY: {backend_key[:20]}...{backend_key[-10:]}")
        else:
            print("   ⚠️  INTERNAL_API_KEY not set or empty")
    else:
        print(f"❌ Backend .env not found: {backend_env}")
        print("   Create this file with INTERNAL_API_KEY")
    
    print()
    print("=" * 60)
    
    # Verification
    if not ai_engine_key or not backend_key:
        print("⚠️  VERIFICATION FAILED")
        print()
        if not ai_engine_key:
            print("   ❌ AI Engine INTERNAL_API_KEY is missing")
        if not backend_key:
            print("   ❌ Backend INTERNAL_API_KEY is missing")
        print()
        print("💡 Solution:")
        print("   1. Create .env files in both ai_engine/ and backend/")
        print("   2. Set INTERNAL_API_KEY in both files")
        print("   3. Make sure they match exactly")
        return False
    
    if ai_engine_key == backend_key:
        print("✅ VERIFICATION PASSED")
        print()
        print("   Both AI Engine and Backend have matching API keys")
        print(f"   Key length: {len(ai_engine_key)} characters")
        print()
        print("   🎉 Configuration is correct!")
        return True
    else:
        print("❌ VERIFICATION FAILED")
        print()
        print("   API keys do NOT match!")
        print()
        print("   AI Engine key:  " + ai_engine_key[:30] + "...")
        print("   Backend key:    " + backend_key[:30] + "...")
        print()
        print("💡 Solution:")
        print("   1. Copy the same INTERNAL_API_KEY to both .env files")
        print("   2. Make sure there are no extra spaces or quotes")
        print("   3. Restart both services after updating")
        return False

if __name__ == "__main__":
    verify_api_keys()
