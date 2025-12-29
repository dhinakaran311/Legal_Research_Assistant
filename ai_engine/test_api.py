"""
Test script for the updated /api/query endpoint
Tests semantic search with real legal queries
"""
import requests
import json
import sys

# API endpoint
BASE_URL = "http://localhost:5000"

def test_query_endpoint():
    """Test the /api/query endpoint with various legal questions"""
    
    print("=" * 70)
    print("Testing /api/query Endpoint")
    print("=" * 70)
    
    # Test queries
    test_queries = [
        {
            "question": "What is the punishment for murder?",
            "max_results": 3
        },
        {
            "question": "How do I file an FIR?",
            "max_results": 2
        },
        {
            "question": "What are the requirements for a valid contract?",
            "max_results": 3
        },
        {
            "question": "What is cheating under IPC?",
            "max_results": 2
        },
        {
            "question": "What damages can I claim for breach of contract?",
            "max_results": 2
        }
    ]
    
    for i, query_data in enumerate(test_queries, 1):
        print(f"\n{'='*70}")
        print(f"Test Query {i}: {query_data['question']}")
        print(f"{'='*70}")
        
        try:
            # Send POST request
            response = requests.post(
                f"{BASE_URL}/api/query",
                json=query_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"\n✅ Query successful!")
                print(f"   Processing Time: {result['processing_time_ms']:.2f}ms")
                print(f"   Confidence: {result['confidence']:.4f}")
                print(f"   Sources Found: {len(result['sources'])}")
                
                print(f"\n📝 Answer:")
                print(f"   {result['answer'][:200]}...")
                
                print(f"\n📚 Top Sources:")
                for j, source in enumerate(result['sources'][:3], 1):
                    print(f"\n   {j}. {source['title']}")
                    print(f"      ID: {source['id']}")
                    print(f"      Relevance: {source['relevance_score']:.4f}")
                    print(f"      Act: {source['metadata'].get('act', 'N/A')}")
                    print(f"      Section: {source['metadata'].get('section', 'N/A')}")
                
            else:
                print(f"\n❌ Query failed with status {response.status_code}")
                print(f"   Error: {response.json().get('detail', 'Unknown error')}")
                
        except requests.exceptions.ConnectionError:
            print(f"\n❌ Cannot connect to API at {BASE_URL}")
            print(f"   Make sure the AI Engine is running:")
            print(f"   cd ai_engine/src")
            print(f"   python main.py")
            return False
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            return False
    
    print(f"\n{'='*70}")
    print("✅ All query tests completed!")
    print(f"{'='*70}")
    return True


def test_status_endpoint():
    """Test the /api/status endpoint"""
    
    print(f"\n{'='*70}")
    print("Testing /api/status Endpoint")
    print(f"{'='*70}")
    
    try:
        response = requests.get(f"{BASE_URL}/api/status")
        
        if response.status_code == 200:
            status = response.json()
            
            print(f"\n✅ Status endpoint working!")
            print(f"   Version: {status['version']}")
            print(f"   Status: {status['status']}")
            print(f"   VectorDB: {status['modules']['vectordb']}")
            print(f"   Documents Indexed: {status['database']['chroma_documents']}")
            print(f"   Collection: {status['database']['collection']}")
            print(f"\n   Message: {status['message']}")
            return True
        else:
            print(f"\n❌ Status check failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


if __name__ == "__main__":
    print("\n🚀 Starting API Tests...\n")
    
    # Test status first
    status_ok = test_status_endpoint()
    
    if status_ok:
        # Test queries
        query_ok = test_query_endpoint()
        sys.exit(0 if query_ok else 1)
    else:
        print("\n⚠️  Status check failed. Make sure the AI Engine is running.")
        sys.exit(1)
