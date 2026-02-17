"""
Migration Script: ChromaDB -> Pinecone
Reads all documents from local ChromaDB and uploads to Pinecone
using Pinecone's integrated embedding (llama-text-embed-v2)
"""
import sys
import os
import time

sys.path.insert(0, 'src')

from dotenv import load_dotenv
load_dotenv()

from vectorstore.chroma_client import ChromaClient
from vectorstore.pinecone_client import PineconeClient
from config import settings


def migrate():
    print("=" * 60)
    print("  ChromaDB -> Pinecone Migration")
    print("=" * 60)
    
    # 1. Connect to local ChromaDB
    print("\n[1/4] Connecting to local ChromaDB...")
    chroma = ChromaClient(
        persist_directory=settings.CHROMA_DB_PATH,
        collection_name=settings.CHROMA_COLLECTION_NAME,
        embedding_model=settings.MODEL_NAME
    )
    chroma.connect()
    
    total_docs = chroma.count()
    print(f"  Found {total_docs} documents in ChromaDB")
    
    if total_docs == 0:
        print("  No documents to migrate!")
        return
    
    # 2. Read all documents from ChromaDB
    print("\n[2/4] Reading all documents from ChromaDB...")
    # ChromaDB get() returns all documents
    all_docs = chroma.collection.get(
        include=["documents", "metadatas"]
    )
    
    ids = all_docs['ids']
    documents = all_docs['documents']
    metadatas = all_docs['metadatas']
    
    print(f"  Read {len(ids)} documents")
    
    # Show sample
    if documents:
        print(f"\n  Sample document (first 200 chars):")
        print(f"  ID: {ids[0]}")
        print(f"  Text: {documents[0][:200]}...")
        print(f"  Metadata: {metadatas[0]}")
    
    # 3. Connect to Pinecone
    print("\n[3/4] Connecting to Pinecone...")
    pinecone = PineconeClient(
        api_key=settings.PINECONE_API_KEY,
        index_name=settings.PINECONE_INDEX_NAME,
        namespace=settings.PINECONE_NAMESPACE
    )
    pinecone.connect()
    
    existing_count = pinecone.count()
    print(f"  Pinecone currently has {existing_count} vectors")
    
    # 4. Upload to Pinecone
    print(f"\n[4/4] Uploading {len(ids)} documents to Pinecone...")
    print("  (Pinecone will embed using llama-text-embed-v2)")
    
    # Upload in batches
    batch_size = 96  # Pinecone integrated embedding limit
    total_batches = (len(ids) + batch_size - 1) // batch_size
    
    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i:i + batch_size]
        batch_docs = documents[i:i + batch_size]
        batch_metas = metadatas[i:i + batch_size]
        batch_num = i // batch_size + 1
        
        print(f"  Batch {batch_num}/{total_batches} ({len(batch_ids)} documents)...")
        
        pinecone.add_documents(
            documents=batch_docs,
            metadatas=batch_metas,
            ids=batch_ids
        )
        
        # Delay between batches to respect rate limits
        if i + batch_size < len(ids):
            time.sleep(2)
    
    # Wait for indexing
    print("\n  Waiting 10s for Pinecone to index vectors...")
    time.sleep(10)
    
    # Verify
    final_count = pinecone.count()
    print(f"\n{'=' * 60}")
    print(f"  Migration complete!")
    print(f"  Pinecone now has {final_count} vectors")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    migrate()
