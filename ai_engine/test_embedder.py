"""
Test script for Embedder
Run this to verify text-to-vector conversion is working correctly
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from embeddings.embedder import Embedder, get_embedder
import logging
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def test_embedder():
    """Test Embedder functionality"""
    
    logger.info("=" * 60)
    logger.info("Testing Embedder")
    logger.info("=" * 60)
    
    try:
        # Test 1: Initialize and load model
        logger.info("\n📝 Test 1: Initializing embedder...")
        embedder = Embedder(model_name="sentence-transformers/all-MiniLM-L6-v2")
        embedder.load_model()
        logger.info("✅ Embedder initialized successfully")
        
        # Test 2: Get model info
        logger.info("\n📝 Test 2: Getting model information...")
        info = embedder.get_model_info()
        logger.info(f"✅ Model Info:")
        logger.info(f"  Model Name: {info['model_name']}")
        logger.info(f"  Loaded: {info['loaded']}")
        logger.info(f"  Embedding Dimension: {info['embedding_dimension']}")
        logger.info(f"  Device: {info['device']}")
        logger.info(f"  Max Sequence Length: {info['max_seq_length']}")
        
        # Test 3: Encode single text
        logger.info("\n📝 Test 3: Encoding single legal text...")
        sample_text = "A contract requires offer, acceptance, and consideration to be valid."
        embedding = embedder.encode_single(sample_text)
        logger.info(f"✅ Encoded text to embedding:")
        logger.info(f"  Text: {sample_text}")
        logger.info(f"  Embedding shape: {embedding.shape}")
        logger.info(f"  Embedding type: {type(embedding)}")
        logger.info(f"  First 5 values: {embedding[:5]}")
        
        # Test 4: Encode batch of texts
        logger.info("\n📝 Test 4: Encoding batch of legal texts...")
        sample_texts = [
            "A contract requires offer, acceptance, and consideration to be valid.",
            "The statute of limitations for breach of contract is typically 6 years.",
            "Negligence requires duty, breach, causation, and damages.",
            "The plaintiff must prove all elements of the tort to prevail."
        ]
        embeddings = embedder.encode_batch(sample_texts, show_progress_bar=True)
        logger.info(f"✅ Encoded {len(sample_texts)} texts:")
        logger.info(f"  Embeddings shape: {embeddings.shape}")
        logger.info(f"  Expected shape: ({len(sample_texts)}, {info['embedding_dimension']})")
        
        # Test 5: Calculate similarity
        logger.info("\n📝 Test 5: Calculating similarity between embeddings...")
        sim_1_2 = embedder.similarity(embeddings[0], embeddings[1])
        sim_1_3 = embedder.similarity(embeddings[0], embeddings[2])
        sim_1_1 = embedder.similarity(embeddings[0], embeddings[0])
        
        logger.info(f"✅ Similarity scores:")
        logger.info(f"  Contract vs Contract (same): {sim_1_1:.4f}")
        logger.info(f"  Contract vs Statute of Limitations: {sim_1_2:.4f}")
        logger.info(f"  Contract vs Negligence: {sim_1_3:.4f}")
        
        # Test 6: Preprocess legal text
        logger.info("\n📝 Test 6: Testing legal text preprocessing...")
        messy_text = "This    is   a    legal   document   with   excessive    whitespace."
        preprocessed = embedder.preprocess_legal_text(messy_text)
        logger.info(f"✅ Preprocessed text:")
        logger.info(f"  Original: '{messy_text}'")
        logger.info(f"  Preprocessed: '{preprocessed}'")
        
        # Test 7: Test singleton pattern
        logger.info("\n📝 Test 7: Testing singleton pattern...")
        embedder2 = get_embedder()
        logger.info(f"✅ Singleton working: Same instance = {embedder2 is not None}")
        logger.info(f"  Model loaded: {embedder2.get_model_info()['loaded']}")
        
        # Test 8: Embed legal documents with preprocessing
        logger.info("\n📝 Test 8: Embedding legal documents with preprocessing...")
        legal_docs = [
            "Section 1: The parties agree to the following terms and conditions.",
            "Section 2: Payment shall be made within 30 days of invoice date.",
            "Section 3: This agreement may be terminated with 60 days notice."
        ]
        doc_embeddings = embedder.embed_legal_documents(
            legal_docs,
            preprocess=True,
            show_progress_bar=True
        )
        logger.info(f"✅ Embedded {len(legal_docs)} legal documents:")
        logger.info(f"  Embeddings shape: {doc_embeddings.shape}")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ All tests passed successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"\n❌ Test failed: {str(e)}", exc_info=True)
        return False
    
    return True


if __name__ == "__main__":
    success = test_embedder()
    sys.exit(0 if success else 1)
