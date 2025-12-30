"""
Test Script for Adaptive RAG Pipeline
Tests all 4 stages with various query types
"""
import sys
sys.path.insert(0, 'src')

from pipelines.adaptive_rag import AdaptiveRAGPipeline, QueryIntent
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

def test_pipeline():
    """Test the Adaptive RAG Pipeline with various query types"""
    
    print("=" * 80)
    print("🧪 ADAPTIVE RAG PIPELINE TEST")
    print("=" * 80)
    
    # Initialize pipeline
    print("\n📦 Initializing pipeline...")
    pipeline = AdaptiveRAGPipeline()
    
    # Test queries representing different intents
    test_queries = [
        {
            "query": "What is the punishment for murder?",
            "expected_intent": QueryIntent.FACTUAL,
            "description": "Factual query about specific punishment"
        },
        {
            "query": "How do I file an FIR?",
            "expected_intent": QueryIntent.PROCEDURAL,
            "description": "Procedural query about process"
        },
        {
            "query": "What is the difference between murder and culpable homicide?",
            "expected_intent": QueryIntent.COMPARATIVE,
            "description": "Comparative query between two concepts"
        },
        {
            "query": "What is cheating under IPC?",
            "expected_intent": QueryIntent.DEFINITIONAL,
            "description": "Definitional query"
        },
        {
            "query": "Tell me about contract law in India",
            "expected_intent": QueryIntent.EXPLORATORY,
            "description": "Exploratory broad query"
        },
        {
            "query": "When should I file a complaint?",
            "expected_intent": QueryIntent.TEMPORAL,
            "description": "Temporal query about timing"
        }
    ]
    
    results_summary = []
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n{'=' * 80}")
        print(f"🔍 TEST {i}/{len(test_queries)}: {test['description']}")
        print(f"{'=' * 80}")
        print(f"Query: \"{test['query']}\"")
        print(f"Expected Intent: {test['expected_intent'].value}")
        
        try:
            # Process query through pipeline
            result = pipeline.process_query(test['query'])
            
            # Display results
            print(f"\n✅ PIPELINE COMPLETED")
            print(f"   Processing Time: {result.processing_time_ms:.2f}ms")
            print(f"\n📊 INTENT ANALYSIS:")
            print(f"   Detected Intent: {result.intent.value}")
            print(f"   Intent Confidence: {result.intent_confidence:.2f}")
            print(f"   Intent Match: {'✓' if result.intent == test['expected_intent'] else '✗'}")
            print(f"   Keywords Matched: {', '.join(result.metadata['keywords_matched'][:3])}")
            
            print(f"\n📈 RETRIEVAL STRATEGY:")
            print(f"   Documents Requested: {result.retrieval_strategy['num_documents_requested']}")
            print(f"   Documents Returned: {result.retrieval_strategy['num_documents_returned']}")
            print(f"   Min Relevance Threshold: {result.retrieval_strategy['min_relevance_threshold']:.2f}")
            print(f"   Reasoning: {result.retrieval_strategy['intent_reasoning']}")
            
            print(f"\n📚 SOURCES:")
            print(f"   Total Sources: {len(result.sources)}")
            for j, source in enumerate(result.sources[:3], 1):
                print(f"\n   {j}. {source['title'][:60]}...")
                print(f"      Relevance: {source['relevance_score']:.4f}")
                print(f"      Act: {source['metadata'].get('act', 'N/A')}")
                print(f"      Section: {source['metadata'].get('section', 'N/A')}")
            
            print(f"\n💡 ANSWER:")
            answer_preview = result.answer[:300].replace('\n', '\n   ')
            print(f"   {answer_preview}...")
            
            print(f"\n🎯 CONFIDENCE: {result.confidence:.4f}")
            
            # Save summary
            results_summary.append({
                'test_number': i,
                'query': test['query'],
                'expected_intent': test['expected_intent'].value,
                'detected_intent': result.intent.value,
                'intent_match': result.intent == test['expected_intent'],
                'intent_confidence': result.intent_confidence,
                'num_sources': len(result.sources),
                'confidence': result.confidence,
                'processing_time_ms': result.processing_time_ms
            })
            
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            results_summary.append({
                'test_number': i,
                'query': test['query'],
                'error': str(e)
            })
    
    # Print summary
    print(f"\n{'=' * 80}")
    print("📊 TEST SUMMARY")
    print(f"{'=' * 80}")
    
    successful = [r for r in results_summary if 'error' not in r]
    failed = [r for r in results_summary if 'error' in r]
    
    print(f"\nTotal Tests: {len(test_queries)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    if successful:
        intent_matches = sum(1 for r in successful if r.get('intent_match', False))
        avg_confidence = sum(r['confidence'] for r in successful) / len(successful)
        avg_time = sum(r['processing_time_ms'] for r in successful) / len(successful)
        avg_sources = sum(r['num_sources'] for r in successful) / len(successful)
        
        print(f"\n📈 Performance Metrics:")
        print(f"   Intent Detection Accuracy: {intent_matches}/{len(successful)} ({intent_matches/len(successful)*100:.1f}%)")
        print(f"   Average Confidence: {avg_confidence:.4f}")
        print(f"   Average Processing Time: {avg_time:.2f}ms")
        print(f"   Average Sources Retrieved: {avg_sources:.1f}")
    
    # Save detailed results to JSON
    with open('pipeline_test_results.json', 'w') as f:
        json.dump(results_summary, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: pipeline_test_results.json")
    print(f"\n{'=' * 80}")
    print("✅ ADAPTIVE RAG PIPELINE TEST COMPLETED")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    test_pipeline()
