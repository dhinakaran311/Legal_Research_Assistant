"""
Multi-Act ChromaDB Loader
Loads scraped JSON files from multiple acts into ChromaDB for semantic search
"""
import sys
import os
import json
from pathlib import Path
import logging

# Add paths for imports
project_root = Path(__file__).parent.parent.parent
ai_engine_src = project_root / "ai_engine" / "src"
data_ingestion_root = project_root / "data_ingestion"
sys.path.insert(0, str(ai_engine_src))

# Import from ai_engine first (before adding data_ingestion to path)
from vectorstore.chroma_client import ChromaClient
from config import settings as ai_config_settings

# Now add data_ingestion to path for its modules
sys.path.insert(0, str(data_ingestion_root))

from preprocess.text_cleaner import clean_legal_text

# Import acts_config directly from the file path to avoid conflict with config module
import importlib.util
acts_config_path = data_ingestion_root / "config" / "acts_config.py"
spec = importlib.util.spec_from_file_location("acts_config", acts_config_path)
acts_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(acts_config)

# Import functions from acts_config
ACT_CONFIGS = acts_config.ACT_CONFIGS
get_act_config = acts_config.get_act_config
get_subcategory = acts_config.get_subcategory
list_all_acts = acts_config.list_all_acts

# Use the correct settings
settings = ai_config_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Storage base directory
STORAGE_BASE_DIR = Path(__file__).parent.parent / "storage" / "acts"


def load_act_json_files(act_key: str) -> list:
    """
    Load all JSON files for a specific act from storage directory
    
    Args:
        act_key: Act key (e.g., "ipc", "crpc")
        
    Returns:
        List of dictionaries with section data
    """
    act_dir = STORAGE_BASE_DIR / act_key.lower()
    
    if not act_dir.exists():
        logger.warning(f"⚠️  Storage directory not found: {act_dir}")
        return []
    
    json_files = list(act_dir.glob("section_*.json"))
    
    if not json_files:
        logger.warning(f"⚠️  No JSON files found in {act_dir}")
        return []
    
    logger.info(f"📁 Found {len(json_files)} JSON files for {act_key.upper()}")
    
    sections = []
    for json_file in sorted(json_files):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                sections.append(data)
                logger.info(f"   ✓ Loaded: {json_file.name}")
        except Exception as e:
            logger.error(f"❌ Failed to load {json_file.name}: {str(e)}")
    
    return sections


def create_chromadb_metadata(section_data: dict, act_key: str) -> dict:
    """
    Create ChromaDB metadata from section data
    
    Args:
        section_data: Dictionary from JSON file
        act_key: Act key (e.g., "ipc", "crpc")
        
    Returns:
        Metadata dictionary for ChromaDB
    """
    config = get_act_config(act_key)
    section_number = section_data.get('section', '')
    
    # Get subcategory
    subcategory = get_subcategory(act_key, section_number)
    
    metadata = {
        "act": config.get("short_name", act_key.upper()),
        "section": section_number,
        "source": section_data.get("source", "IndiaCode"),
        "category": config.get("category", "general"),
        "subcategory": subcategory,
        "title": section_data.get("title", ""),
        "source_url": section_data.get("source_url", ""),
        "last_updated": section_data.get("last_updated", "")
    }
    
    return metadata


def prepare_documents_for_chromadb(sections: list, act_key: str) -> tuple:
    """
    Prepare documents, metadatas, and IDs for ChromaDB
    
    Args:
        sections: List of section data dictionaries
        act_key: Act key (e.g., "ipc", "crpc")
        
    Returns:
        Tuple of (documents, metadatas, ids)
    """
    config = get_act_config(act_key)
    act_short_name = config.get("short_name", act_key.upper())
    
    documents = []
    metadatas = []
    ids = []
    
    for section in sections:
        section_number = section.get('section', '')
        
        # Clean the content
        raw_content = section.get('content', '')
        cleaned_content = clean_legal_text(raw_content, section_number)
        
        # Create document text (title + content for better search)
        title = section.get('title', f'Section {section_number}')
        document_text = f"{title}\n\n{cleaned_content}"
        
        # Create metadata
        metadata = create_chromadb_metadata(section, act_key)
        
        # Create ID (format: act_section_XXX)
        doc_id = f"{act_key.lower()}_section_{section_number}"
        
        documents.append(document_text)
        metadatas.append(metadata)
        ids.append(doc_id)
        
        logger.info(f"   ✓ Prepared: {doc_id} ({title[:50]}...)")
    
    return documents, metadatas, ids


def load_act_to_chromadb(act_key: str, chroma_client: ChromaClient) -> bool:
    """
    Load sections for a specific act into ChromaDB
    
    Args:
        act_key: Act key (e.g., "ipc", "crpc")
        chroma_client: ChromaDB client instance
        
    Returns:
        True if successful, False otherwise
    """
    config = get_act_config(act_key)
    if not config:
        logger.error(f"❌ Unknown act: {act_key}")
        return False
    
    act_name = config.get("short_name", act_key.upper())
    
    try:
        logger.info(f"\n📝 Loading {act_name} sections...")
        
        # Load JSON files
        sections = load_act_json_files(act_key)
        
        if not sections:
            logger.warning(f"⚠️  No sections to load for {act_name}. Run scraper first.")
            return False
        
        logger.info(f"✅ Loaded {len(sections)} sections")
        
        # Prepare documents
        logger.info(f"📝 Preparing documents for ChromaDB...")
        documents, metadatas, ids = prepare_documents_for_chromadb(sections, act_key)
        
        logger.info(f"✅ Prepared {len(documents)} documents")
        
        # Check for duplicates
        logger.info(f"📝 Checking for existing documents...")
        existing_ids = []
        for doc_id in ids:
            existing_doc = chroma_client.get_document(doc_id)
            if existing_doc:
                existing_ids.append(doc_id)
        
        # Filter out existing documents
        if existing_ids:
            new_documents = []
            new_metadatas = []
            new_ids = []
            
            for i, doc_id in enumerate(ids):
                if doc_id not in existing_ids:
                    new_documents.append(documents[i])
                    new_metadatas.append(metadatas[i])
                    new_ids.append(doc_id)
            
            documents = new_documents
            metadatas = new_metadatas
            ids = new_ids
            
            logger.info(f"   📊 Skipping {len(existing_ids)} existing documents")
            logger.info(f"   📊 Adding {len(documents)} new documents")
        
        # Add to ChromaDB
        if documents:
            logger.info(f"📝 Adding documents to ChromaDB...")
            chroma_client.add_documents(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"✅ Successfully added {len(documents)} {act_name} documents")
        else:
            logger.info(f"⚠️  No new {act_name} documents to add (all already exist)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to load {act_name} data: {str(e)}", exc_info=True)
        return False


def load_all_acts_to_chromadb(act_keys: list = None):
    """
    Main function to load all acts into ChromaDB
    
    Args:
        act_keys: List of act keys to load. If None, loads all acts with JSON files.
    """
    logger.info("=" * 70)
    logger.info("🚀 Loading Multiple Acts into ChromaDB")
    logger.info("=" * 70)
    
    try:
        # Step 1: Initialize ChromaDB client
        logger.info("\n📝 Step 1: Initializing ChromaDB client...")
        chroma_client = ChromaClient(
            persist_directory=settings.CHROMA_DB_PATH,
            collection_name=settings.CHROMA_COLLECTION_NAME,
            embedding_model=settings.MODEL_NAME
        )
        chroma_client.connect()
        
        existing_count = chroma_client.count()
        logger.info(f"✅ ChromaDB connected")
        logger.info(f"   Collection: {settings.CHROMA_COLLECTION_NAME}")
        logger.info(f"   Existing documents: {existing_count}")
        
        # Step 2: Determine which acts to load
        if act_keys is None:
            # Find all acts with JSON files
            act_keys = []
            for act_dir in STORAGE_BASE_DIR.iterdir():
                if act_dir.is_dir() and (act_dir / "section_*.json").glob("*"):
                    act_keys.append(act_dir.name)
            
            if not act_keys:
                logger.error("❌ No act directories found with JSON files. Run scraper first.")
                return False
        
        logger.info(f"\n📝 Step 2: Loading acts: {', '.join([a.upper() for a in act_keys])}")
        
        # Step 3: Load each act
        results = {}
        total_added = 0
        
        for act_key in act_keys:
            config = get_act_config(act_key)
            if not config:
                logger.warning(f"⚠️  Skipping unknown act: {act_key}")
                continue
            
            logger.info(f"\n{'=' * 70}")
            logger.info(f"📚 Processing Act: {config.get('full_name', act_key)}")
            logger.info(f"{'=' * 70}")
            
            success = load_act_to_chromadb(act_key, chroma_client)
            results[act_key] = success
            
            if success:
                sections = load_act_json_files(act_key)
                total_added += len(sections)
        
        # Step 4: Summary
        new_count = chroma_client.count()
        logger.info(f"\n{'=' * 70}")
        logger.info("📊 Final Status")
        logger.info("=" * 70)
        logger.info(f"   Total documents in collection: {new_count}")
        logger.info(f"   Documents processed: {total_added}")
        
        successful_acts = sum(1 for v in results.values() if v)
        logger.info(f"   Acts loaded: {successful_acts}/{len(results)}")
        
        # Step 5: Test query
        logger.info(f"\n📝 Step 3: Testing search with sample query...")
        test_query = "What is anticipatory bail?"
        results = chroma_client.query(
            query_texts=[test_query],
            n_results=3,
            where={"act": "CrPC"}
        )
        
        if results['ids'][0]:
            logger.info(f"   ✅ Test query successful")
            for i, doc_id in enumerate(results['ids'][0][:3]):
                distance = results['distances'][0][i]
                logger.info(f"      {i+1}. {doc_id} (distance: {distance:.4f})")
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ Multi-act data loaded successfully!")
        logger.info("=" * 70)
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Failed to load multi-act data: {str(e)}", exc_info=True)
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Load multiple Indian Acts into ChromaDB")
    parser.add_argument(
        "--acts",
        nargs="+",
        help="Specific acts to load (default: all acts with JSON files)"
    )
    
    args = parser.parse_args()
    
    success = load_all_acts_to_chromadb(args.acts)
    sys.exit(0 if success else 1)
