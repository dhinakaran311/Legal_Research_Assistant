"""
Data Loader Script
Loads sample legal documents into ChromaDB for development and testing
"""
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.vectorstore.chroma_client import get_chroma_client
from src.embeddings.embedder import get_embedder
from src.data.sample_legal_data import SAMPLE_LEGAL_DOCUMENTS
from src.config import settings
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def load_sample_data():
    """
    Load sample legal documents into ChromaDB
    """
    logger.info("=" * 70)
    logger.info("Loading Sample Legal Data into ChromaDB")
    logger.info("=" * 70)
    
    try:
        # Initialize components
        logger.info("\n📝 Step 1: Initializing ChromaDB client and embedder...")
        chroma_client = get_chroma_client(
            persist_directory=settings.CHROMA_DB_PATH,
            collection_name=settings.CHROMA_COLLECTION_NAME,
            embedding_model=settings.MODEL_NAME
        )
        logger.info(f"✅ ChromaDB client initialized")
        logger.info(f"   Collection: {settings.CHROMA_COLLECTION_NAME}")
        logger.info(f"   Persist Directory: {settings.CHROMA_DB_PATH}")
        
        # Check existing documents
        existing_count = chroma_client.count()
        logger.info(f"\n📊 Current collection status:")
        logger.info(f"   Existing documents: {existing_count}")
        
        # Prepare documents for ingestion
        logger.info(f"\n📝 Step 2: Preparing {len(SAMPLE_LEGAL_DOCUMENTS)} legal documents...")
        
        documents = []
        metadatas = []
        ids = []
        
        for doc in SAMPLE_LEGAL_DOCUMENTS:
            # Combine title and content for better semantic search
            full_text = f"{doc['title']}\n\n{doc['content']}"
            documents.append(full_text)
            metadatas.append(doc['metadata'])
            ids.append(doc['id'])
            
            logger.info(f"   ✓ {doc['id']}: {doc['title'][:60]}...")
        
        # Add documents to ChromaDB
        logger.info(f"\n📝 Step 3: Adding documents to ChromaDB...")
        chroma_client.add_documents(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        new_count = chroma_client.count()
        logger.info(f"✅ Documents added successfully!")
        logger.info(f"   Total documents in collection: {new_count}")
        
        # Display collection info
        logger.info(f"\n📊 Collection Information:")
        info = chroma_client.get_collection_info()
        logger.info(f"   Name: {info['name']}")
        logger.info(f"   Document Count: {info['count']}")
        logger.info(f"   Embedding Model: {info['embedding_model']}")
        
        # Test query
        logger.info(f"\n📝 Step 4: Testing semantic search...")
        test_queries = [
            "What is the punishment for murder?",
            "How to file an FIR?",
            "What makes a contract valid?"
        ]
        
        for query in test_queries:
            logger.info(f"\n   Query: '{query}'")
            results = chroma_client.query(
                query_texts=[query],
                n_results=2
            )
            
            if results['ids'][0]:
                logger.info(f"   Top Result: {results['ids'][0][0]}")
                logger.info(f"   Distance: {results['distances'][0][0]:.4f}")
                logger.info(f"   Snippet: {results['documents'][0][0][:100]}...")
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ Sample data loaded successfully!")
        logger.info("=" * 70)
        logger.info("\n💡 Next Steps:")
        logger.info("   1. Test queries via the API endpoint")
        logger.info("   2. Add more legal documents as needed")
        logger.info("   3. For production: Use data_ingestion/ pipeline")
        logger.info("=" * 70)
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Failed to load sample data: {str(e)}", exc_info=True)
        return False


def clear_collection():
    """
    Clear all documents from the collection (use with caution!)
    """
    logger.warning("⚠️  Clearing all documents from collection...")
    
    try:
        chroma_client = get_chroma_client(
            persist_directory=settings.CHROMA_DB_PATH,
            collection_name=settings.CHROMA_COLLECTION_NAME
        )
        
        chroma_client.reset_collection()
        logger.info("✅ Collection cleared successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to clear collection: {str(e)}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Load sample legal data into ChromaDB")
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing collection before loading"
    )
    
    args = parser.parse_args()
    
    if args.clear:
        logger.info("Clearing existing collection...")
        clear_collection()
    
    success = load_sample_data()
    sys.exit(0 if success else 1)
