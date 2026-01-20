"""
Test Multiple Queries - Comprehensive Search Quality Test
Tests the improved AI Engine with 166 documents across various legal topics
"""
import sys
sys.path.insert(0, 'src')

from pipelines.adaptive_rag import AdaptiveRAGPipeline
from graph.neo4j_client import get_neo4j_client
import time

# Test queries covering different acts and intents
TEST_QUERIES = [
    # Criminal Law (CrPC, IPC)
    {
        "query": "What is anticipatory bail?",
        "expected_act": "CrPC",
        "intent": "definitional"
    },
    {
        "query": "What is the punishment for murder under Section 302?",
        "expected_act": "IPC",
        "intent": "factual"
    },
    {
        "query": "How to file an FIR?",
        "expected_act": "CrPC",
        "intent": "procedural"
    },
    
    # Contract Law
    {
        "query": "What are the essential elements of a valid contract?",
        "expected_act": "Contract Act",
        "intent": "definitional"
    },
    {
        "query": "What is the difference between void and voidable contracts?",
        "expected_act": "Contract Act",
        "intent": "comparative"
    },
    
    # Motor Vehicles
    {
        "query": "What are the penalties for drunk driving?",
        "expected_act": "MVA",
        "intent": "factual"
    },
    {
        "query": "How to get a driving license in India?",
        "expected_act": "MVA",
        "intent": "procedural"
    },
    
    # Income Tax
    {
        "query": "What deductions are available under Section 80C?",
        "expected_act": "Income Tax",
        "intent": "factual"
    },
    
    # Consumer Protection
    {
        "query": "How to file a consumer complaint?",
        "expected_act": "Consumer Protection",
        "intent": "procedural"
    },
    
    # Property Law
    {
        "query": "What is a mortgage under Transfer of Property Act?",
        "expected_act": "TPA",
        "intent": "definitional"
    },
    
    # Evidence
    {
        "query": "What is hearsay evidence?",
        "expected_act": "Evidence",
        "intent": "definitional"
    },
    
    # Information Technology
    {
        "query": "What are cyber crimes under IT Act?",
        "expected_act": "IT Act",
        "intent": "exploratory"
    },
    
    # GST
    {
        "query": "What is the GST rate on services?",
        "expected_act": "GST",
        "intent": "factual"
    },
    
    # Right to Information
    {
        "query": "How to file an RTI application?",
        "expected_act": "RTI",
        "intent": "procedural"
    },
    
    # General Legal
    {
        "query": "Tell me about fundamental rights in India",
        "expected_act": "Constitution",
        "intent": "exploratory"
    }
]

def run_query_test(pipeline, test_case, test_num):
    """Run a single query test"""
    query = test_case["query"]
    expected_act = test_case["expected_act"]
    expected_intent = test_case["intent"]
    
    print(f"\n{'='*80}")
    print(f"TEST {test_num}: {query}")
    print(f"{'='*80}")
    print(f"Expected Act: {expected_act}")
    print(f"Expected Intent: {expected_intent}")
    print()
    
    start_time = time.time()
    
    try:
        result = pipeline.process_query(query)
        elapsed_ms = (time.time() - start_time) * 1000
        
        # Results
        print(f"[RESULT] Intent Detected: {result.intent.value}")
        print(f"[RESULT] Sources Retrieved: {result.num_sources_retrieved}")
        print(f"[RESULT] Graph References: {len(result.graph_references)}")
        print(f"[RESULT] Processing Time: {elapsed_ms:.0f}ms")
        print(f"[RESULT] Confidence: {result.confidence:.2f}")
        
        # Check intent match
        intent_match = "PASS" if result.intent.value == expected_intent else "FAIL"
        print(f"\n[CHECK] Intent Match: {intent_match} (Expected: {expected_intent}, Got: {result.intent.value})")
        
        # Show sources
        print(f"\n[SOURCES] Top {len(result.sources)} sources:")
        for i, source in enumerate(result.sources[:3], 1):
            metadata = source.get('metadata', {})
            act = metadata.get('act', 'Unknown')
            section = metadata.get('section', 'N/A')
            title = metadata.get('title', 'N/A')
            print(f"  {i}. {act} Section {section}: {title[:60]}...")
        
        # Check if expected act is in sources
        acts_found = [s.get('metadata', {}).get('act', '') for s in result.sources]
        act_match = "PASS" if any(expected_act.lower() in act.lower() for act in acts_found) else "FAIL"
        print(f"\n[CHECK] Act Found: {act_match} (Expected: {expected_act})")
        
        # Show answer preview
        print(f"\n[ANSWER] {result.answer[:200]}...")
        
        # Performance rating
        if elapsed_ms < 500:
            perf_rating = "Excellent"
        elif elapsed_ms < 1000:
            perf_rating = "Good"
        elif elapsed_ms < 2000:
            perf_rating = "Fair"
        else:
            perf_rating = "Slow"
        
        print(f"\n[PERFORMANCE] {perf_rating} ({elapsed_ms:.0f}ms)")
        
        return {
            "success": True,
            "query": query,
            "intent_match": intent_match == "PASS",
            "act_match": act_match == "PASS",
            "processing_time": elapsed_ms,
            "sources": len(result.sources),
            "confidence": result.confidence
        }
        
    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        print(f"[ERROR] Query failed: {str(e)}")
        print(f"[PERFORMANCE] Failed ({elapsed_ms:.0f}ms)")
        
        return {
            "success": False,
            "query": query,
            "error": str(e),
            "processing_time": elapsed_ms
        }

def main():
    print("\n" + "="*80)
    print("  LEGAL AI ENGINE - COMPREHENSIVE QUERY TEST")
    print("  Testing with 166 documents across 19 acts")
    print("="*80)
    
    # Initialize pipeline
    print("\n[SETUP] Initializing pipeline...")
    neo4j_client = get_neo4j_client()
    pipeline = AdaptiveRAGPipeline(neo4j_client=neo4j_client, use_llm=False)
    print("[SETUP] Pipeline ready")
    
    # Run tests
    results = []
    for i, test_case in enumerate(TEST_QUERIES, 1):
        result = run_query_test(pipeline, test_case, i)
        results.append(result)
        
        # Brief pause to avoid overwhelming the system
        time.sleep(0.5)
    
    # Summary
    print("\n" + "="*80)
    print("  TEST SUMMARY")
    print("="*80)
    
    successful = sum(1 for r in results if r["success"])
    total = len(results)
    
    intent_matches = sum(1 for r in results if r.get("intent_match", False))
    act_matches = sum(1 for r in results if r.get("act_match", False))
    
    avg_time = sum(r["processing_time"] for r in results) / len(results) if results else 0
    avg_sources = sum(r.get("sources", 0) for r in results if r["success"]) / successful if successful > 0 else 0
    avg_confidence = sum(r.get("confidence", 0) for r in results if r["success"]) / successful if successful > 0 else 0
    
    print(f"\n[RESULTS]")
    print(f"  Total Queries: {total}")
    print(f"  Successful: {successful} ({successful/total*100:.0f}%)" if total > 0 else "  Successful: 0 (0%)")
    print(f"  Failed: {total - successful}")
    print()
    print(f"[ACCURACY]")
    if successful > 0:
        print(f"  Intent Detection: {intent_matches}/{successful} ({intent_matches/successful*100:.0f}%)")
        print(f"  Act Detection: {act_matches}/{successful} ({act_matches/successful*100:.0f}%)")
    else:
        print(f"  Intent Detection: N/A (no successful queries)")
        print(f"  Act Detection: N/A (no successful queries)")
    print()
    print(f"[PERFORMANCE]")
    print(f"  Average Processing Time: {avg_time:.0f}ms")
    print(f"  Average Sources Retrieved: {avg_sources:.1f}")
    print(f"  Average Confidence: {avg_confidence:.2f}")
    
    # Performance breakdown
    fast_queries = sum(1 for r in results if r["processing_time"] < 500)
    good_queries = sum(1 for r in results if 500 <= r["processing_time"] < 1000)
    fair_queries = sum(1 for r in results if 1000 <= r["processing_time"] < 2000)
    slow_queries = sum(1 for r in results if r["processing_time"] >= 2000)
    
    print()
    print(f"[SPEED DISTRIBUTION]")
    print(f"  Excellent (<500ms): {fast_queries} ({fast_queries/total*100:.0f}%)")
    print(f"  Good (500-1000ms): {good_queries} ({good_queries/total*100:.0f}%)")
    print(f"  Fair (1-2s): {fair_queries} ({fair_queries/total*100:.0f}%)")
    print(f"  Slow (>2s): {slow_queries} ({slow_queries/total*100:.0f}%)")
    
    print("\n" + "="*80)
    print("  ALL TESTS COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
