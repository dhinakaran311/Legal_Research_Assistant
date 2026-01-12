"""
Diagnostic script to test Neo4j loader setup
Run this before running the main loader to identify issues
"""
import sys
from pathlib import Path

# Add paths for imports
project_root = Path(__file__).parent.parent.parent
ai_engine_src = project_root / "ai_engine" / "src"
data_ingestion_root = project_root / "data_ingestion"
sys.path.insert(0, str(ai_engine_src))
sys.path.insert(0, str(data_ingestion_root))

print("=" * 70)
print("🔍 Neo4j Loader Diagnostic Test")
print("=" * 70)

# Test 1: Check Python version
print("\n1️⃣  Python Version:")
print(f"   Python {sys.version}")

# Test 2: Check if Neo4j package is installed
print("\n2️⃣  Neo4j Package:")
try:
    import neo4j
    print(f"   ✅ neo4j package installed: {neo4j.__version__}")
except ImportError:
    print("   ❌ neo4j package NOT installed")
    print("   💡 Install with: pip install neo4j")

# Test 3: Check if ai_engine modules can be imported
print("\n3️⃣  AI Engine Imports:")
try:
    from graph.neo4j_client import Neo4jClient, get_neo4j_client
    print("   ✅ Neo4jClient imported successfully")
except ImportError as e:
    print(f"   ❌ Failed to import Neo4jClient: {e}")
    print(f"   💡 Check if ai_engine/src exists and has graph/neo4j_client.py")

try:
    from config import settings
    print("   ✅ Settings imported successfully")
    print(f"   📍 CHROMA_DB_PATH: {settings.CHROMA_DB_PATH}")
except ImportError as e:
    print(f"   ❌ Failed to import settings: {e}")

# Test 4: Check Neo4j configuration
print("\n4️⃣  Neo4j Configuration:")
try:
    from config import settings
    neo4j_uri = settings.NEO4J_URI
    neo4j_user = settings.NEO4J_USERNAME
    neo4j_pass = settings.NEO4J_PASSWORD
    
    if neo4j_uri:
        print(f"   ✅ NEO4J_URI: {neo4j_uri}")
    else:
        print("   ⚠️  NEO4J_URI not set (empty)")
    
    if neo4j_user:
        print(f"   ✅ NEO4J_USERNAME: {neo4j_user}")
    else:
        print("   ⚠️  NEO4J_USERNAME not set")
    
    if neo4j_pass:
        print(f"   ✅ NEO4J_PASSWORD: {'*' * len(neo4j_pass)} (hidden)")
    else:
        print("   ❌ NEO4J_PASSWORD not set")
        print("   💡 Set NEO4J_PASSWORD in ai_engine/.env")
except Exception as e:
    print(f"   ❌ Error checking configuration: {e}")

# Test 5: Check if Neo4j connection works
print("\n5️⃣  Neo4j Connection Test:")
try:
    from graph.neo4j_client import get_neo4j_client
    from config import settings
    
    if not settings.NEO4J_URI or not settings.NEO4J_PASSWORD:
        print("   ⚠️  Skipping connection test (credentials missing)")
    else:
        client = get_neo4j_client(
            uri=settings.NEO4J_URI,
            username=settings.NEO4J_USERNAME,
            password=settings.NEO4J_PASSWORD
        )
        
        if client:
            if client.test_connection():
                print("   ✅ Neo4j connection successful!")
            else:
                print("   ❌ Neo4j connection test failed")
                print("   💡 Check if Neo4j is running and credentials are correct")
        else:
            print("   ❌ Failed to create Neo4j client")
            print("   💡 Check Neo4j credentials in ai_engine/.env")
except Exception as e:
    print(f"   ❌ Connection test error: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Check if storage directory exists
print("\n6️⃣  Storage Directory:")
storage_dir = Path(__file__).parent.parent / "storage" / "acts"
if storage_dir.exists():
    print(f"   ✅ Storage directory exists: {storage_dir}")
    
    # Count JSON files
    json_files = list(storage_dir.glob("**/section_*.json"))
    print(f"   📊 Found {len(json_files)} JSON files")
    
    # List acts with files
    acts_with_files = {}
    for json_file in json_files:
        act_key = json_file.parent.name
        if act_key not in acts_with_files:
            acts_with_files[act_key] = 0
        acts_with_files[act_key] += 1
    
    if acts_with_files:
        print("   📚 Acts with JSON files:")
        for act, count in acts_with_files.items():
            print(f"      - {act.upper()}: {count} files")
    else:
        print("   ⚠️  No JSON files found")
        print("   💡 Run scraper first: python sources/multi_act_scraper.py")
else:
    print(f"   ❌ Storage directory not found: {storage_dir}")
    print("   💡 Run scraper first to create JSON files")

# Test 7: Check acts_config
print("\n7️⃣  Acts Configuration:")
try:
    import importlib.util
    acts_config_path = data_ingestion_root / "config" / "acts_config.py"
    spec = importlib.util.spec_from_file_location("acts_config", acts_config_path)
    acts_config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(acts_config)
    
    get_act_config = acts_config.get_act_config
    list_all_acts = acts_config.list_all_acts
    
    acts = list_all_acts()
    print(f"   ✅ Acts config loaded: {len(acts)} acts configured")
    print(f"   📚 Acts: {', '.join([a.upper() for a in acts])}")
except Exception as e:
    print(f"   ❌ Failed to load acts_config: {e}")

print("\n" + "=" * 70)
print("✅ Diagnostic complete!")
print("=" * 70)
print("\n💡 If all tests pass, you can run:")
print("   python loaders/load_multi_act_to_neo4j.py")
