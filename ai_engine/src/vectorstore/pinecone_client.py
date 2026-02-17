"""
Pinecone Client for Legal Document Vector Store
Uses Pinecone's integrated embedding (llama-text-embed-v2)
No need for local sentence-transformers — Pinecone handles embedding server-side
"""
from pinecone import Pinecone
from typing import List, Dict, Any, Optional
import logging
import os
import time

logger = logging.getLogger(__name__)


class PineconeClient:
    """
    Pinecone client for managing legal document embeddings and semantic search.
    Uses Pinecone's integrated inference (llama-text-embed-v2) for embedding.
    Drop-in replacement for ChromaClient.
    """
    
    def __init__(
        self,
        api_key: str = "",
        index_name: str = "legal-documents",
        namespace: str = "legal_documents"
    ):
        """
        Initialize Pinecone client
        
        Args:
            api_key: Pinecone API key
            index_name: Name of the Pinecone index
            namespace: Namespace within the index
        """
        self.api_key = api_key or os.getenv("PINECONE_API_KEY", "")
        self.index_name = index_name
        self.namespace = namespace
        
        self.pc = None
        self.index = None
        
        logger.info(f"PineconeClient initialized for index: {index_name}")
    
    def connect(self) -> None:
        """Connect to Pinecone and get the index"""
        try:
            self.pc = Pinecone(api_key=self.api_key)
            self.index = self.pc.Index(self.index_name)
            
            # Test connection
            stats = self.index.describe_index_stats()
            total_vectors = stats.get("total_vector_count", 0)
            
            logger.info(f"✅ Connected to Pinecone index: {self.index_name}")
            logger.info(f"📊 Index contains {total_vectors} vectors")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Pinecone: {str(e)}")
            raise
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> None:
        """
        Add documents to Pinecone using integrated embedding.
        Pinecone automatically embeds the text using llama-text-embed-v2.
        
        Args:
            documents: List of document texts
            metadatas: List of metadata dictionaries
            ids: List of unique IDs
        """
        if not self.index:
            raise RuntimeError("Pinecone index not initialized. Call connect() first.")
        
        try:
            # Build records for integrated embedding
            # The "text" field is what Pinecone will embed (configured in index field map)
            records = []
            for doc_id, doc_text, meta in zip(ids, documents, metadatas):
                record = {
                    "_id": doc_id,
                    "text": doc_text,
                }
                # Add metadata fields (flatten for Pinecone)
                # Pinecone metadata values must be string, number, boolean, or list of strings
                for key, value in meta.items():
                    if value is not None:
                        if isinstance(value, (str, int, float, bool)):
                            record[key] = value
                        elif isinstance(value, list):
                            record[key] = value
                        else:
                            record[key] = str(value)
                records.append(record)
            
            # Upsert in batches of 96 (Pinecone limit for integrated embedding)
            batch_size = 96
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                self.index.upsert_records(
                    namespace=self.namespace,
                    records=batch
                )
                logger.info(f"  Upserted batch {i // batch_size + 1} ({len(batch)} records)")
                # Small delay to respect rate limits
                if i + batch_size < len(records):
                    time.sleep(1)
            
            logger.info(f"✅ Added {len(documents)} documents to Pinecone")
        except Exception as e:
            logger.error(f"❌ Failed to add documents: {str(e)}")
            raise
    
    def query(
        self,
        query_texts: List[str],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Query Pinecone for similar documents using integrated embedding.
        Returns results in ChromaDB-compatible format for drop-in replacement.
        
        Args:
            query_texts: List of query strings
            n_results: Number of results to return
            where: Metadata filter (converted to Pinecone filter format)
            where_document: Not used in Pinecone (ignored)
            
        Returns:
            Dictionary in ChromaDB format: {ids, documents, metadatas, distances}
        """
        if not self.index:
            raise RuntimeError("Pinecone index not initialized. Call connect() first.")
        
        try:
            all_ids = []
            all_documents = []
            all_metadatas = []
            all_distances = []
            
            for query_text in query_texts:
                # Build search request
                search_params = {
                    "namespace": self.namespace,
                    "query": {
                        "inputs": {"text": query_text},
                        "top_k": n_results
                    },
                }
                
                # Add metadata filter if provided
                if where:
                    search_params["query"]["filter"] = where
                
                results = self.index.search(**search_params)
                
                # Parse results into ChromaDB-compatible format
                ids = []
                documents = []
                metadatas = []
                distances = []
                
                if results and hasattr(results, 'result') and results.result:
                    hits = results.result.hits if hasattr(results.result, 'hits') else []
                    for hit in hits:
                        hit_id = hit.get('_id', '') if isinstance(hit, dict) else getattr(hit, '_id', '')
                        hit_score = hit.get('_score', 0) if isinstance(hit, dict) else getattr(hit, '_score', 0)
                        hit_fields = hit.get('fields', {}) if isinstance(hit, dict) else getattr(hit, 'fields', {})
                        
                        ids.append(hit_id)
                        # Extract the text from fields
                        doc_text = hit_fields.get('text', '') if isinstance(hit_fields, dict) else ''
                        documents.append(doc_text)
                        
                        # Extract metadata (everything except 'text')
                        meta = {}
                        if isinstance(hit_fields, dict):
                            for k, v in hit_fields.items():
                                if k != 'text':
                                    meta[k] = v
                        metadatas.append(meta)
                        
                        # Convert similarity score to distance (1 - cosine_similarity)
                        distances.append(1.0 - float(hit_score))
                
                all_ids.append(ids)
                all_documents.append(documents)
                all_metadatas.append(metadatas)
                all_distances.append(distances)
            
            logger.info(f"✅ Query completed, returned {len(all_ids[0]) if all_ids else 0} results")
            
            return {
                'ids': all_ids,
                'documents': all_documents,
                'metadatas': all_metadatas,
                'distances': all_distances
            }
            
        except Exception as e:
            logger.error(f"❌ Query failed: {str(e)}")
            raise
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific document by ID"""
        if not self.index:
            raise RuntimeError("Pinecone index not initialized. Call connect() first.")
        
        try:
            result = self.index.fetch(ids=[doc_id], namespace=self.namespace)
            vectors = result.get('vectors', {})
            if doc_id in vectors:
                vec = vectors[doc_id]
                metadata = vec.get('metadata', {})
                return {
                    'id': doc_id,
                    'document': metadata.get('text', ''),
                    'metadata': {k: v for k, v in metadata.items() if k != 'text'}
                }
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get document {doc_id}: {str(e)}")
            raise
    
    def count(self) -> int:
        """Get the number of vectors in the namespace"""
        if not self.index:
            raise RuntimeError("Pinecone index not initialized. Call connect() first.")
        
        stats = self.index.describe_index_stats()
        namespaces = stats.get("namespaces", {})
        ns_stats = namespaces.get(self.namespace, {})
        return ns_stats.get("vector_count", 0)
    
    def delete_documents(self, ids: List[str]) -> None:
        """Delete documents by IDs"""
        if not self.index:
            raise RuntimeError("Pinecone index not initialized. Call connect() first.")
        
        try:
            self.index.delete(ids=ids, namespace=self.namespace)
            logger.info(f"✅ Deleted {len(ids)} documents")
        except Exception as e:
            logger.error(f"❌ Failed to delete documents: {str(e)}")
            raise
    
    def reset_collection(self) -> None:
        """Delete all vectors in the namespace"""
        if not self.index:
            raise RuntimeError("Pinecone index not initialized. Call connect() first.")
        
        try:
            self.index.delete(delete_all=True, namespace=self.namespace)
            logger.warning(f"⚠️ Namespace {self.namespace} has been reset")
        except Exception as e:
            logger.error(f"❌ Failed to reset namespace: {str(e)}")
            raise
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get info about the index"""
        if not self.index:
            raise RuntimeError("Pinecone index not initialized. Call connect() first.")
        
        stats = self.index.describe_index_stats()
        return {
            'name': self.index_name,
            'namespace': self.namespace,
            'count': self.count(),
            'total_vector_count': stats.get("total_vector_count", 0),
        }
    
    def disconnect(self) -> None:
        """Cleanup"""
        self.index = None
        self.pc = None
        logger.info("Disconnected from Pinecone")


# Singleton instance
_pinecone_client_instance: Optional[PineconeClient] = None


def get_pinecone_client(
    api_key: str = "",
    index_name: str = "legal-documents",
    namespace: str = "legal_documents"
) -> PineconeClient:
    """
    Get or create a singleton PineconeClient instance
    """
    global _pinecone_client_instance
    
    if _pinecone_client_instance is None:
        _pinecone_client_instance = PineconeClient(
            api_key=api_key,
            index_name=index_name,
            namespace=namespace
        )
        _pinecone_client_instance.connect()
    
    return _pinecone_client_instance
