"""
Quick test to verify ChromaDB has data
"""
import sys
sys.path.insert(0, 'src')

from src.vectorstore.chroma_client import ChromaClient

client = ChromaClient(persist_directory="./data/chromadb", collection_name="legal_documents")
client.connect()

count = client.count()
print(f"Document count: {count}")

if count > 0:
    info = client.get_collection_info()
    print(f"Collection info: {info}")
    
    # Try a query
    results = client.query(query_texts=["murder"], n_results=2)
    print(f"Query results: {results['ids']}")
else:
    print("Collection is empty!")
