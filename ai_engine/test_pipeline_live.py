import sys
import os
import logging

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from agents.agentic_pipeline import AgenticPipeline
from llm.ollama_generator import get_ollama_generator

# Setup logging
logging.basicConfig(level=logging.INFO)

def test_live_pipeline():
    print("Testing AgenticPipeline (v2) with Ollama...")
    
    # Initialize real LLM
    llm = get_ollama_generator(model_name="llama3.2:3b")
    
    # Mock Chroma for now (since we just want to test pipeline logic + LLM)
    class MockChroma:
        def query(self, **kwargs):
            return {
                "ids": [["id1"]],
                "documents": [["Section 302 of the Indian Penal Code (IPC) specifies the punishment for murder. It states that whoever commits murder shall be punished with death or imprisonment for life, and shall also be liable to fine."]],
                "metadatas": [[{"act": "IPC", "section": "302"}]],
                "distances": [[0.1]]
            }
        def upsert(self, **kwargs):
            print(f"ChromaDB Upsert called for {len(kwargs.get('ids', []))} docs")
            return None

    # Instantiate pipeline
    pipeline = AgenticPipeline(
        chroma_client=MockChroma(),
        llm=llm
    )
    
    # Run a query
    query = "What is the punishment for murder according to IPC 302?"
    print(f"\nRunning query: {query}")
    
    result = pipeline.run(query)
    
    print("\n--- Pipeline Result ---")
    print(f"Intent: {result.intent}")
    print(f"Answer: {result.answer}")
    print(f"Used LLM: {result.metadata.get('used_llm')}")
    print(f"Processing Time: {result.processing_time_ms} ms")
    print("------------------------\n")

if __name__ == "__main__":
    test_live_pipeline()
