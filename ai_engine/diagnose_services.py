
import os
import logging
from dotenv import load_dotenv
import requests

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load env from ai_engine/.env
dotenv_path = os.path.join(os.getcwd(), '.env')
load_dotenv(dotenv_path)

def test_neo4j():
    from neo4j import GraphDatabase
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    pwd = os.getenv("NEO4J_PASSWORD")
    
    print(f"\n--- Testing Neo4j ---")
    print(f"URI: {uri}")
    print(f"User: {user}")
    
    if not uri or not pwd:
        print("Error: NEO4J_URI or NEO4J_PASSWORD missing in .env")
        return

    try:
        driver = GraphDatabase.driver(uri, auth=(user, pwd), connection_timeout=10)
        with driver.session() as session:
            result = session.run("RETURN 1 AS test")
            val = result.single()["test"]
            print(f"Success! Result: {val}")
        driver.close()
    except Exception as e:
        print(f"Neo4j Connection Failed: {e}")

def test_ollama():
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    
    print(f"\n--- Testing Ollama ---")
    print(f"URL: {base_url}")
    print(f"Model: {model}")
    
    try:
        r = requests.get(f"{base_url}/api/tags", timeout=5)
        if r.status_code == 200:
            models = [m['name'] for m in r.json().get('models', [])]
            print(f"Ollama is RUNNING. Available models: {models}")
            if model in models or any(model in m for m in models):
                print(f"Model '{model}' is available.")
            else:
                print(f"Warning: Model '{model}' NOT found in Ollama.")
        else:
            print(f"Ollama returned status {r.status_code}")
    except Exception as e:
        print(f"Ollama Reachability Failed: {e}")

def test_ai_engine():
    url = "http://localhost:5000/api/adaptive-query"
    api_key = os.getenv("INTERNAL_API_KEY")
    
    print(f"\n--- Testing AI Engine API ---")
    print(f"URL: {url}")
    
    try:
        r = requests.post(
            url,
            json={"question": "What is the punishment for murder?"},
            headers={"X-Internal-API-Key": api_key},
            timeout=10 # Fast check
        )
        if r.status_code == 200:
            data = r.json()
            strategy = data.get("retrieval_strategy", {})
            print("Response RECEIVED.")
            print(f"Fields in retrieval_strategy: {list(strategy.keys())}")
            
            required = ["num_documents_requested", "min_relevance_threshold", "num_documents_returned", "intent_reasoning"]
            missing = [f for f in required if f not in strategy]
            if missing:
                print(f"❌ MISSING FIELDS: {missing}")
            else:
                print("✅ ALL LEGACY FIELDS PRESENT.")
        else:
            print(f"AI Engine returned status {r.status_code}: {r.text}")
    except Exception as e:
        print(f"AI Engine Request Failed: {e}")

if __name__ == "__main__":
    test_neo4j()
    test_ollama()
    test_ai_engine()
