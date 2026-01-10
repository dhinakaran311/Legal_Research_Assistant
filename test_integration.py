"""
Test Backend → AI Engine Integration
GraphQL search query test
"""
import requests
import json

GRAPHQL_URL = "http://localhost:4000/graphql"

def test_graphql_search():
    """Test GraphQL search query"""
    
    # GraphQL query
    query = """
    query {
      search(query: "What is anticipatory bail under Section 438?") {
        question
        intent
        intent_confidence
        answer
        sources {
          content
          relevance_score
        }
        graph_references {
          case_name
          case_year
          section
        }
        confidence
        processing_time_ms
      }
    }
    """
    
    print("=" * 80)
    print("🧪 TESTING BACKEND → AI ENGINE INTEGRATION")
    print("=" * 80)
    
    print("\n📤 Sending GraphQL query to backend...")
    print(f"URL: {GRAPHQL_URL}")
    print(f"Query: search(query: 'What is anticipatory bail...')")
    
    try:
        response = requests.post(
            GRAPHQL_URL,
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if "errors" in data:
                print("❌ GraphQL Errors:")
                for error in data["errors"]:
                    print(f"   - {error['message']}")
                return False
            
            result = data["data"]["search"]
            
            print("\n✅ SUCCESS! Integration Working!")
            print("=" * 80)
            print(f"Intent: {result['intent']}")
            print(f"Confidence: {result['intent_confidence']:.2f}")
            print(f"Sources: {len(result['sources'])}")
            print(f"Graph Facts: {len(result['graph_references'])}")
            print(f"Processing Time: {result['processing_time_ms']:.0f}ms")
            
            print(f"\n📝 Answer Preview:")
            print(result['answer'][:200] + "...")
            
            if result['graph_references']:
                print(f"\n📚 Graph References:")
                for ref in result['graph_references'][:2]:
                    if 'case_name' in ref and ref['case_name']:
                        print(f"   - {ref['case_name']} ({ref.get('case_year', 'N/A')})")
            
            print("\n" + "=" * 80)
            print("✅ BACKEND ↔ AI ENGINE INTEGRATION TEST PASSED!")
            print("=" * 80)
            return True
            
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error - Is the backend running?")
        print("   Start with: cd backend && npm run dev")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_graphql_search()
    exit(0 if success else 1)
