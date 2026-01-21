"""
Test script to diagnose retrieval quality issues
"""
import sys
sys.path.insert(0, 'src')

from pipelines.adaptive_rag import AdaptiveRAGPipeline
from graph.neo4j_client import get_neo4j_client
from config import settings

def test_query_retrieval(query: str, use_llm: bool = False):
    """Test what documents are retrieved for a query"""
    
    print(f"\n{'='*80}")
    print(f"TESTING QUERY: {query}")
    print(f"LLM Enabled: {use_llm}")
    print(f"{'='*80}\n")
    
    # Initialize pipeline
    neo4j = get_neo4j_client()
    pipeline = AdaptiveRAGPipeline(use_llm=use_llm, neo4j_client=neo4j)
    
    result = pipeline.process_query(query, use_llm=use_llm, max_docs=5)
    
    print(f"Intent: {result.intent}")
    print(f"Documents Retrieved: {result.num_sources_retrieved}")
    print(f"Confidence: {result.confidence}")
    print(f"Processing Time: {result.processing_time_ms}ms")
    
    if hasattr(result, 'metadata') and result.metadata and 'cache_hit' in result.metadata:
        print(f"Cache Hit: {result.metadata['cache_hit']}")
    
    print(f"\n{'='*80}")
    print("TOP DOCUMENTS RETRIEVED:")
    print(f"{'='*80}\n")
    
    for i, doc in enumerate(result.sources[:5], 1):
        meta = doc.get('metadata', {})
        print(f"{i}. Act: {meta.get('act', 'N/A')} | Section: {meta.get('section', 'N/A')}")
        print(f"   Title: {meta.get('title', 'N/A')}")
        
        content = doc.get('content', '')
        content_preview = content[:200] if len(content) > 200 else content
        print(f"   Content Preview: {content_preview}...")
        print(f"   Content Length: {len(content)} chars\n")
    
    print(f"{'='*80}")
    print("ANSWER GENERATED:")
    print(f"{'='*80}\n")
    
    answer = result.answer if hasattr(result, 'answer') else ''
    answer_preview = answer[:500] if len(answer) > 500 else answer
    print(answer_preview)
    if len(answer) > 500:
        print("\n... (truncated)")
    
    print(f"\n{'='*80}\n")
    
    return result


if __name__ == "__main__":
    # Test the problematic query
    test_queries = [
        "How to file a complaint for cheating?",
        "What is Section 420 IPC?",
        "Procedure to file FIR for fraud"
    ]
    
    for query in test_queries:
        test_query_retrieval(query, use_llm=False)
        print("\n\n")
