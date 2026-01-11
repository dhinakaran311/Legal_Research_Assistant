"""
ChromaDB Loader for CrPC Data
Loads scraped CrPC JSON files into ChromaDB for semantic search
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
sys.path.insert(0, str(data_ingestion_root))

from vectorstore.chroma_client import ChromaClient
from config import settings
from preprocess.text_cleaner import clean_legal_text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Storage directory
STORAGE_DIR = Path(__file__).parent.parent / "storage" / "acts" / "crpc"


def load_crpc_json_files() -> list:
    """
    Load all CrPC JSON files from storage directory
    
    Returns:
        List of dictionaries with section data
    """
    if not STORAGE_DIR.exists():
        logger.error(f"❌ Storage directory not found: {STORAGE_DIR}")
        return []
    
    json_files = list(STORAGE_DIR.glob("section_*.json"))
    
    if not json_files:
        logger.warning(f"⚠️  No JSON files found in {STORAGE_DIR}")
        return []
    
    logger.info(f"📁 Found {len(json_files)} JSON files")
    
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


def create_chromadb_metadata(section_data: dict) -> dict:
    """
    Create ChromaDB metadata from section data
    
    Args:
        section_data: Dictionary from JSON file
        
    Returns:
        Metadata dictionary for ChromaDB
    """
    section_number = section_data.get('section', '')
    
    # Determine subcategory based on section
    subcategory_map = {
        '41': 'arrest_without_warrant',
        '41A': 'arrest_procedures',
        '41D': 'arrest_procedures',
        '50': 'arrest_procedures',
        '50A': 'arrest_procedures',
        '154': 'information_to_police',
        '156': 'investigation',
        '436': 'bail',
        '437': 'bail',
        '438': 'bail'
    }
    
    subcategory = subcategory_map.get(section_number, 'general_procedure')
    
    metadata = {
        "act": "CrPC",
        "section": section_number,
        "source": section_data.get("source", "IndiaCode"),
        "category": "criminal_procedure",
        "subcategory": subcategory,
        "title": section_data.get("title", ""),
        "source_url": section_data.get("source_url", ""),
        "last_updated": section_data.get("last_updated", "")
    }
    
    return metadata


def prepare_documents_for_chromadb(sections: list) -> tuple:
    """
    Prepare documents, metadatas, and IDs for ChromaDB
    
    Args:
        sections: List of section data dictionaries
        
    Returns:
        Tuple of (documents, metadatas, ids)
    """
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
        metadata = create_chromadb_metadata(section)
        
        # Create ID
        doc_id = f"crpc_section_{section_number}"
        
        documents.append(document_text)
        metadatas.append(metadata)
        ids.append(doc_id)
        
        logger.info(f"   ✓ Prepared: {doc_id} ({title[:50]}...)")
    
    return documents, metadatas, ids


def load_crpc_to_chromadb():
    """
    Main function to load CrPC sections into ChromaDB
    """
    logger.info("=" * 70)
    logger.info("🚀 Loading CrPC Sections into ChromaDB")
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
        
        # Step 2: Load JSON files
        logger.info(f"\n📝 Step 2: Loading CrPC JSON files...")
        sections = load_crpc_json_files()
        
        if not sections:
            logger.error("❌ No sections to load. Run scraper first.")
            return False
        
        logger.info(f"✅ Loaded {len(sections)} sections")
        
        # Step 3: Prepare documents
        logger.info(f"\n📝 Step 3: Preparing documents for ChromaDB...")
        documents, metadatas, ids = prepare_documents_for_chromadb(sections)
        
        logger.info(f"✅ Prepared {len(documents)} documents")
        
        # Check for duplicates
        logger.info(f"\n📝 Step 4: Checking for existing documents...")
        existing_ids = []
        for doc_id in ids:
            existing_doc = chroma_client.get_document(doc_id)
            if existing_doc:
                existing_ids.append(doc_id)
                logger.info(f"   ⚠️  Document {doc_id} already exists (will be skipped)")
        
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
        
        # Step 4: Add to ChromaDB
        if documents:
            logger.info(f"\n📝 Step 5: Adding documents to ChromaDB...")
            chroma_client.add_documents(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"✅ Successfully added {len(documents)} documents")
        else:
            logger.info(f"\n⚠️  No new documents to add (all already exist)")
        
        # Step 5: Summary
        new_count = chroma_client.count()
        logger.info(f"\n📊 Final Status:")
        logger.info(f"   Total documents in collection: {new_count}")
        logger.info(f"   Documents added: {len(documents) if documents else 0}")
        
        # Test query
        logger.info(f"\n📝 Step 6: Testing search with sample query...")
        test_query = "What is anticipatory bail?"
        results = chroma_client.query(
            query_texts=[test_query],
            n_results=2,
            where={"act": "CrPC"}
        )
        
        if results['ids'][0]:
            logger.info(f"   ✅ Test query successful")
            logger.info(f"   Top result: {results['ids'][0][0]}")
            logger.info(f"   Distance: {results['distances'][0][0]:.4f}")
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ CrPC data loaded successfully!")
        logger.info("=" * 70)
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Failed to load CrPC data: {str(e)}", exc_info=True)
        return False


if __name__ == "__main__":
    success = load_crpc_to_chromadb()
    sys.exit(0 if success else 1)
