"""
Test Ollama LLM Integration
Tests the LLM-powered answer generation
"""
import sys
sys.path.insert(0, 'src')

from pipelines.adaptive_rag import AdaptiveRAGPipeline
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

def test_ollama_integration():
    """Test Ollama LLM integration with the adaptive RAG pipeline"""
    
    print("=" * 80)
    print("🧪 OLLAMA LLM INTEGRATION TEST")
    print("=" * 80)
    
    test_queries = [
        "What is the punishment for murder?",
        "How do I file an FIR?",
        "What is the difference between bail and anticipatory bail?"
    ]
    
    print("\n📦 Testing Rule-Based Generation (Baseline)...")
    print("=" * 80)
    
    pipeline_rulebased = AdaptiveRAGPipeline(use_llm=False)
    
    for i, query in enumerate(test_queries[:1], 1):  # Test one query
        print(f"\nQuery {i}: {query}")
        result = pipeline_rulebased.process_query(query)
        print(f"\n📝 Rule-Based Answer ({len(result.answer)} chars):")
        print(result.answer[:300] + "...")
    
    print("\n\n🤖 Testing LLM-Powered Generation (Ollama)...")
    print("=" * 80)
    
    try:
        pipeline_llm = AdaptiveRAGPipeline(use_llm=True, llm_model="llama3.2:3b")
        
        for i, query in enumerate(test_queries[:1], 1):  # Test one query
            print(f"\nQuery {i}: {query}")
            print("Generating with Ollama mistral:latest...")
            
            result = pipeline_llm.process_query(query)
            
            print(f"\n🎯 LLM-Generated Answer ({len(result.answer)} chars):")
            print(result.answer[:500] + "...")
            print(f"\nProcessing Time: {result.processing_time_ms:.2f}ms")
            print(f"Confidence: {result.confidence:.4f}")
            
    except Exception as e:
        print(f"\n❌ LLM Test Failed: {str(e)}")
        print("\n🔍 Troubleshooting:")
        print("   1. Make sure Ollama is running: ollama serve")
        print("   2. Check if model is pulled: ollama list")
        print("   3. Pull model if needed: ollama pull mistral:latest")
        return False
    
    print("\n" + "=" * 80)
    print("✅ OLLAMA LLM INTEGRATION TEST COMPLETED")
    print("=" * 80)
    return True


if __name__ == "__main__":
    success = test_ollama_integration()
    sys.exit(0 if success else 1)
