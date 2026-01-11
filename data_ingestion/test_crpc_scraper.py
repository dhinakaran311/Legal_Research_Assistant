"""
Test Script for CrPC Scraper and Loader
Validates scraping, JSON structure, cleaning, and ChromaDB loading
"""
import sys
import json
from pathlib import Path
import logging

# Add paths for imports
project_root = Path(__file__).parent
data_ingestion_root = project_root
ai_engine_src = project_root.parent / "ai_engine" / "src"
sys.path.insert(0, str(data_ingestion_root))
sys.path.insert(0, str(ai_engine_src))

from preprocess.text_cleaner import clean_legal_text, validate_cleaned_text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

STORAGE_DIR = Path(__file__).parent / "storage" / "acts" / "crpc"


def test_json_structure():
    """Test that JSON files have correct structure"""
    logger.info("=" * 70)
    logger.info("📋 Test 1: JSON Structure Validation")
    logger.info("=" * 70)
    
    if not STORAGE_DIR.exists():
        logger.error(f"❌ Storage directory not found: {STORAGE_DIR}")
        logger.error("   Run scraper first: python sources/indiacode_scraper.py")
        return False
    
    json_files = list(STORAGE_DIR.glob("section_*.json"))
    
    if not json_files:
        logger.error(f"❌ No JSON files found in {STORAGE_DIR}")
        logger.error("   Run scraper first: python sources/indiacode_scraper.py")
        return False
    
    logger.info(f"📁 Found {len(json_files)} JSON files")
    
    required_fields = ['act', 'section', 'title', 'content', 'source', 'source_url']
    all_valid = True
    
    for json_file in sorted(json_files):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check required fields
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                logger.error(f"❌ {json_file.name}: Missing fields: {missing_fields}")
                all_valid = False
            else:
                logger.info(f"   ✅ {json_file.name}: Valid structure")
                
                # Check content length
                content = data.get('content', '')
                if len(content) < 50:
                    logger.warning(f"   ⚠️  {json_file.name}: Content too short ({len(content)} chars)")
                else:
                    logger.info(f"      Content length: {len(content)} chars")
        
        except json.JSONDecodeError as e:
            logger.error(f"❌ {json_file.name}: Invalid JSON - {str(e)}")
            all_valid = False
        except Exception as e:
            logger.error(f"❌ {json_file.name}: Error - {str(e)}")
            all_valid = False
    
    logger.info("=" * 70)
    return all_valid


def test_text_cleaning():
    """Test text cleaning functions"""
    logger.info("=" * 70)
    logger.info("🧹 Test 2: Text Cleaning Validation")
    logger.info("=" * 70)
    
    json_files = list(STORAGE_DIR.glob("section_*.json"))
    
    if not json_files:
        logger.error("❌ No JSON files to test. Run scraper first.")
        return False
    
    all_valid = True
    
    # Test with first file
    test_file = json_files[0]
    
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        section_number = data.get('section', '')
        raw_content = data.get('content', '')
        
        logger.info(f"📄 Testing with: {test_file.name}")
        logger.info(f"   Section: {section_number}")
        logger.info(f"   Raw content length: {len(raw_content)} chars")
        
        # Clean text
        cleaned_content = clean_legal_text(raw_content, section_number)
        
        logger.info(f"   Cleaned content length: {len(cleaned_content)} chars")
        
        # Validate cleaned text
        is_valid = validate_cleaned_text(cleaned_content)
        
        if is_valid:
            logger.info(f"   ✅ Text cleaning successful and valid")
            
            # Show sample
            sample = cleaned_content[:200] + "..." if len(cleaned_content) > 200 else cleaned_content
            logger.info(f"\n   Sample cleaned text:")
            logger.info(f"   {sample}")
        else:
            logger.error(f"   ❌ Cleaned text validation failed")
            all_valid = False
    
    except Exception as e:
        logger.error(f"❌ Error testing text cleaning: {str(e)}")
        all_valid = False
    
    logger.info("=" * 70)
    return all_valid


def test_chromadb_integration():
    """Test ChromaDB loading and querying"""
    logger.info("=" * 70)
    logger.info("🗄️  Test 3: ChromaDB Integration Validation")
    logger.info("=" * 70)
    
    try:
        from vectorstore.chroma_client import ChromaClient
        from config import settings
        
        # Initialize client
        logger.info("📝 Initializing ChromaDB client...")
        chroma_client = ChromaClient(
            persist_directory=settings.CHROMA_DB_PATH,
            collection_name=settings.CHROMA_COLLECTION_NAME,
            embedding_model=settings.MODEL_NAME
        )
        chroma_client.connect()
        
        doc_count = chroma_client.count()
        logger.info(f"✅ ChromaDB connected")
        logger.info(f"   Total documents: {doc_count}")
        
        # Check for CrPC sections
        logger.info("\n📝 Checking for CrPC documents...")
        test_query = "anticipatory bail"
        results = chroma_client.query(
            query_texts=[test_query],
            n_results=5,
            where={"act": "CrPC"}
        )
        
        crpc_results = results['ids'][0]
        
        if crpc_results:
            logger.info(f"   ✅ Found {len(crpc_results)} CrPC documents")
            for i, doc_id in enumerate(crpc_results[:3]):
                distance = results['distances'][0][i]
                logger.info(f"      {i+1}. {doc_id} (distance: {distance:.4f})")
        else:
            logger.warning(f"   ⚠️  No CrPC documents found in ChromaDB")
            logger.warning(f"      Run loader: python loaders/load_crpc_data.py")
            return False
        
        logger.info("=" * 70)
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {str(e)}")
        logger.error("   Make sure ai_engine/src is accessible")
        return False
    except Exception as e:
        logger.error(f"❌ ChromaDB test failed: {str(e)}")
        return False


def run_all_tests():
    """Run all tests"""
    logger.info("\n" + "=" * 70)
    logger.info("🧪 CrPC Scraper and Loader Test Suite")
    logger.info("=" * 70)
    logger.info("")
    
    results = {
        "JSON Structure": test_json_structure(),
        "Text Cleaning": test_text_cleaning(),
        "ChromaDB Integration": test_chromadb_integration()
    }
    
    logger.info("\n" + "=" * 70)
    logger.info("📊 Test Results Summary")
    logger.info("=" * 70)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"   {test_name}: {status}")
    
    all_passed = all(results.values())
    
    logger.info("=" * 70)
    
    if all_passed:
        logger.info("✅ All tests passed!")
    else:
        logger.warning("⚠️  Some tests failed. Check logs above.")
    
    logger.info("=" * 70)
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
