"""Check if ChromaDB documents have actual content"""
import sys
sys.path.insert(0, 'src')

from vectorstore.chroma_client import ChromaClient
from config import settings

client = ChromaClient(
    persist_directory=settings.CHROMA_DB_PATH,
    collection_name=settings.CHROMA_COLLECTION_NAME
)
client.connect()

# Query for Section 420
results = client.query("Section 420 cheating", n_results=3)

print("="*80)
print("CHROMADB CONTENT CHECK")
print("="*80)

if results and 'documents' in results:
    docs = results['documents']
    metas = results['metadatas']
    
    print(f"\nTotal results: {len(docs)}")
    print(f"Type of docs: {type(docs)}")
    print(f"Type of metas: {type(metas)}")
    
    # Handle nested structure
    if isinstance(docs[0], list):
        docs = docs[0]
        metas = metas[0] if metas else []
    
    print(f"\nAfter flattening - docs: {len(docs)}, metas: {len(metas)}")
    
    for i in range(min(len(docs), 3)):  # Show only first 3
        doc = docs[i]
        meta = metas[i] if i < len(metas) else {}
        
        print(f"\n{i+1}. Act: {meta.get('act', 'N/A')} | Section: {meta.get('section', 'N/A')}")
        print(f"   Title: {meta.get('title', 'N/A')}")
        print(f"   Content Length: {len(doc)} chars")
        
        if len(doc) > 0:
            preview = doc[:300]
            print(f"   Content Preview:\n   {preview}...")
        else:
            print("   [PROBLEM] Content is EMPTY!")
        print()
else:
    print("No results found!")

print("="*80)
