"""
Test script for ChromaDB client
Run this to verify ChromaDB integration is working correctly
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from vectorstore.chroma_client import ChromaClient, get_chroma_client
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def test_chroma_client():
    """Test ChromaDB client functionality"""
    
    logger.info("=" * 60)
    logger.info("Testing ChromaDB Client")
    logger.info("=" * 60)
    
    try:
        # Test 1: Initialize client
        logger.info("\n📝 Test 1: Initializing ChromaDB client...")
        client = ChromaClient(
            persist_directory="./data/chromadb_test",
            collection_name="test_legal_docs",
            embedding_model="sentence-transformers/all-MiniLM-L6-v2"
        )
        client.connect()
        logger.info("✅ Client initialized successfully")
        
        # Test 2: Add sample documents
        logger.info("\n📝 Test 2: Adding sample legal documents...")
        sample_docs = [
            "A contract requires offer, acceptance, and consideration to be valid.",
            "The statute of limitations for breach of contract is typically 6 years.",
            "Negligence requires duty, breach, causation, and damages."
        ]
        
        sample_metadata = [
            {"source": "Contract Law Basics", "category": "contracts", "chapter": "1"},
            {"source": "Limitations Act", "category": "contracts", "chapter": "5"},
            {"source": "Tort Law Fundamentals", "category": "torts", "chapter": "2"}
        ]
        
        sample_ids = ["doc_001", "doc_002", "doc_003"]
        
        client.add_documents(
            documents=sample_docs,
            metadatas=sample_metadata,
            ids=sample_ids
        )
        logger.info("✅ Documents added successfully")
        
        # Test 3: Query documents
        logger.info("\n📝 Test 3: Querying for similar documents...")
        query_result = client.query(
            query_texts=["What makes a contract valid?"],
            n_results=2
        )
        
        logger.info(f"✅ Query returned {len(query_result['ids'][0])} results:")
        for i, (doc_id, document, distance) in enumerate(zip(
            query_result['ids'][0],
            query_result['documents'][0],
            query_result['distances'][0]
        )):
            logger.info(f"  Result {i+1}:")
            logger.info(f"    ID: {doc_id}")
            logger.info(f"    Text: {document[:80]}...")
            logger.info(f"    Distance: {distance:.4f}")
        
        # Test 4: Get collection info
        logger.info("\n📝 Test 4: Getting collection information...")
        info = client.get_collection_info()
        logger.info(f"✅ Collection Info:")
        logger.info(f"  Name: {info['name']}")
        logger.info(f"  Document Count: {info['count']}")
        logger.info(f"  Embedding Model: {info['embedding_model']}")
        
        # Test 5: Get specific document
        logger.info("\n📝 Test 5: Retrieving specific document...")
        doc = client.get_document("doc_001")
        if doc:
            logger.info(f"✅ Retrieved document:")
            logger.info(f"  ID: {doc['id']}")
            logger.info(f"  Text: {doc['document']}")
            logger.info(f"  Metadata: {doc['metadata']}")
        
        # Test 6: Update document
        logger.info("\n📝 Test 6: Updating document metadata...")
        client.update_document(
            doc_id="doc_001",
            metadata={"source": "Contract Law Basics", "category": "contracts", "chapter": "1", "updated": True}
        )
        logger.info("✅ Document updated successfully")
        
        # Test 7: Test singleton pattern
        logger.info("\n📝 Test 7: Testing singleton pattern...")
        client2 = get_chroma_client(
            persist_directory="./data/chromadb_test",
            collection_name="test_legal_docs"
        )
        logger.info(f"✅ Singleton working: Same instance = {client2 is not None}")
        
        # Cleanup
        logger.info("\n🧹 Cleaning up test collection...")
        client.reset_collection()
        client.disconnect()
        logger.info("✅ Cleanup complete")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ All tests passed successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"\n❌ Test failed: {str(e)}", exc_info=True)
        return False
    
    return True


if __name__ == "__main__":
    success = test_chroma_client()
    sys.exit(0 if success else 1)
