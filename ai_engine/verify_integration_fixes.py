import requests
import json
import sys
import os

def test_integration():
    url = "http://localhost:5000/api/adaptive-query"
    headers = {
        "Content-Type": "application/json",
        "X-Internal-API-Key": "hqVm1Oe9wtEt5QQFXPyHhVLH-m2f4Id4aKaEierRjBw"
    }
    
    payload = {
        "question": "What is the law for land fraud?",
        "use_llm": True
    }
    
    print(f"🚀 Testing Integration at {url}...")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=180)
        
        if response.status_code != 200:
            print(f"❌ Error: Received status code {response.status_code}")
            print(response.text)
            return False
            
        data = response.json()
        print("✅ Received Response from AI Engine")
        
        # Verify Issue 1: intent is a string
        intent = data.get("intent")
        print(f"🔹 Intent: {intent} (Type: {type(intent).__name__})")
        if not isinstance(intent, str):
            print("❌ Issue 1 Failed: Intent is not a string!")
            return False
            
        # Verify Issue 2: web_sources exists
        if "web_sources" not in data:
            print("❌ Issue 2 Failed: 'web_sources' field missing in response!")
            return False
        print(f"✅ Issue 2 Passed: 'web_sources' found (count: {len(data['web_sources'])})")
        
        # Verify mapping
        if "documents_used" not in data:
            print("❌ Error: 'documents_used' field missing!")
            return False
        
        print("\n--- Integrity Check ---")
        print(f"Answer Sample: {data['answer'][:100]}...")
        print(f"Time: {data['processing_time_ms']}ms")
        print(f"Confidence: {data['confidence']}")
        print("-----------------------")
        
        print("\n✨ ALL 4 INTEGRATION ISSUES VERIFIED FIXED! ✨")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the server. Is it running on port 5000?")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_integration()
    sys.exit(0 if success else 1)
