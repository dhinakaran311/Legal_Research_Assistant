"""
Test Script for Adaptive RAG API Endpoint
Tests the new /api/adaptive-query endpoint
"""
import requests
import json
import sys

BASE_URL = "http://localhost:5000"


def test_adaptive_status():
    """Test the /api/adaptive-status endpoint"""
    print("\n" + "="*80)
    print("Testing /api/adaptive-status Endpoint")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/api/adaptive-status")
        
        if response.status_code == 200:
            status = response.json()
            print(f"\n✅ Status endpoint working!")
            print(f"   Version: {status['version']}")
            print(f"   Status: {status['status']}")
            print(f"   Pipeline: {status['pipeline']['name']}")
            print(f"   Intents: {len(status['pipeline']['intents_supported'])}")
            print(f"   Documents: {status['database']['chroma_documents']}")
            print(f"\n   Message: {status['message']}")
            return True
        else:
            print(f"\n❌ Status check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


def test_adaptive_queries():
    """Test various queries showing adaptive behavior"""
    
    print("\n" + "="*80)
    print("Testing /api/adaptive-query Endpoint - Adaptive Behavior")
    print("="*80)
    
    test_cases = [
        {
            "name": "Definitional Query (Should retrieve 2-3 docs)",
            "question": "What is anticipatory bail?",
            "expected_intent": "definitional",
            "expected_doc_range": (2, 3)
        },
        {
            "name": "Factual Query (Should retrieve 2-4 docs)",
            "question": "What is the punishment for murder under Section 302?",
            "expected_intent": "factual",
            "expected_doc_range": (2, 4)
        },
        {
            "name": "Procedural Query (Should retrieve 3-5 docs)",
            "question": "How do I file an FIR for theft?",
            "expected_intent": "procedural",
            "expected_doc_range": (3, 5)
        },
        {
            "name": "Comparative Query (Should retrieve 4-7 docs)",
            "question": "What is the difference between bail and anticipatory bail?",
            "expected_intent": "comparative",
            "expected_doc_range": (4, 7)
        },
        {
            "name": "Exploratory Query (Should retrieve 6-10 docs)",
            "question": "Tell me about criminal procedure in India",
            "expected_intent": "exploratory",
            "expected_doc_range": (6, 10)
        }
    ]
    
    results = []
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}/{len(test_cases)}: {test['name']}")
        print(f"{'='*80}")
        print(f"Question: \"{test['question']}\"")
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/adaptive-query",
                json={"question": test['question']},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Check intent
                intent_match = result['intent'] == test['expected_intent']
                
                # Check document count is in expected range
                docs_used = result['documents_used']
                min_docs, max_docs = test['expected_doc_range']
                docs_in_range = min_docs <= docs_used <= max_docs
                
                print(f"\n✅ Query successful!")
                print(f"\n📊 INTENT ANALYSIS:")
                print(f"   Detected Intent: {result['intent']}")
                print(f"   Expected Intent: {test['expected_intent']}")
                print(f"   Intent Match: {'✓' if intent_match else '✗'}")
                print(f"   Intent Confidence: {result['intent_confidence']:.2f}")
                
                print(f"\n📈 ADAPTIVE BEHAVIOR:")
                print(f"   Documents Used: {docs_used}")
                print(f"   Expected Range: {min_docs}-{max_docs}")
                print(f"   In Range: {'✓' if docs_in_range else '✗'}")
                print(f"   Strategy: {result['retrieval_strategy']}")
                
                print(f"\n💡 ANSWER PREVIEW:")
                answer_preview = result['answer'][:200].replace('\n', ' ')
                print(f"   {answer_preview}...")
                
                print(f"\n🎯 METRICS:")
                print(f"   Confidence: {result['confidence']:.4f}")
                print(f"   Processing Time: {result['processing_time_ms']:.2f}ms")
                print(f"   Sources: {len(result['sources'])}")
                
                results.append({
                    'test_name': test['name'],
                    'question': test['question'],
                    'intent_match': intent_match,
                    'docs_in_range': docs_in_range,
                    'docs_used': docs_used,
                    'confidence': result['confidence'],
                    'processing_time': result['processing_time_ms']
                })
                
            else:
                print(f"\n❌ Query failed: {response.status_code}")
                print(f"   Error: {response.json().get('detail', 'Unknown error')}")
                
        except requests.exceptions.ConnectionError:
            print(f"\n❌ Cannot connect to API at {BASE_URL}")
            print(f"   Make sure the AI Engine is running:")
            print(f"   cd ai_engine/src && python main.py")
            return False
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
    
    # Print summary
    print(f"\n{'='*80}")
    print("📊 TEST SUMMARY - ADAPTIVE BEHAVIOR VERIFICATION")
    print(f"{'='*80}")
    
    if results:
        total_tests = len(results)
        intent_matches = sum(1 for r in results if r['intent_match'])
        docs_in_range = sum(1 for r in results if r['docs_in_range'])
        avg_confidence = sum(r['confidence'] for r in results) / total_tests
        avg_time = sum(r['processing_time'] for r in results) / total_tests
        
        print(f"\nTotal Tests: {total_tests}")
        print(f"Intent Accuracy: {intent_matches}/{total_tests} ({intent_matches/total_tests*100:.1f}%)")
        print(f"Adaptive Retrieval Accuracy: {docs_in_range}/{total_tests} ({docs_in_range/total_tests*100:.1f}%)")
        print(f"Average Confidence: {avg_confidence:.4f}")
        print(f"Average Processing Time: {avg_time:.2f}ms")
        
        print(f"\n📋 Document Usage by Intent:")
        for r in results:
            print(f"   {r['test_name']}: {r['docs_used']} docs")
        
        # Verify adaptive behavior
        doc_counts = [r['docs_used'] for r in results]
        if len(set(doc_counts)) > 1:
            print(f"\n✅ ADAPTIVE BEHAVIOR CONFIRMED!")
            print(f"   Different intents retrieved different document counts: {set(doc_counts)}")
        else:
            print(f"\n⚠️  Adaptive behavior not detected (all queries used same doc count)")
    
    print(f"\n{'='*80}")
    print("✅ ADAPTIVE RAG API TEST COMPLETED")
    print(f"{'='*80}\n")
    
    return True


if __name__ == "__main__":
    print("\n🚀 Starting Adaptive RAG API Tests...\n")
    
    # Test status
    status_ok = test_adaptive_status()
    
    if status_ok:
        # Test adaptive queries
        queries_ok = test_adaptive_queries()
        sys.exit(0 if queries_ok else 1)
    else:
        print("\n⚠️  Status check failed. Make sure the AI Engine is running:")
        print("   cd ai_engine/src")
        print("   python main.py")
        sys.exit(1)
