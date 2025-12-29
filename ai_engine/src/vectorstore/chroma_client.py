"""
ChromaDB Client for Legal Document Vector Store
Handles initialization, collection management, and document operations
"""
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)


class ChromaClient:
    """
    ChromaDB client for managing legal document embeddings and semantic search
    """
    
    def __init__(
        self,
        persist_directory: str = "./data/chromadb",
        collection_name: str = "legal_documents",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        """
        Initialize ChromaDB client
        
        Args:
            persist_directory: Path to persist ChromaDB data
            collection_name: Name of the collection to use
            embedding_model: Name of the sentence-transformer model
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        
        # Ensure persist directory exists
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = None
        self.collection = None
        self.embedding_function = None
        
        logger.info(f"ChromaClient initialized with persist_directory: {persist_directory}")
    
    def connect(self) -> None:
        """
        Connect to ChromaDB and initialize the collection
        """
        try:
            # Create ChromaDB client with persistence
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Initialize embedding function
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=self.embedding_model
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"description": "Legal documents and case law for semantic search"}
            )
            
            logger.info(f"✅ Connected to ChromaDB collection: {self.collection_name}")
            logger.info(f"📊 Collection contains {self.collection.count()} documents")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to ChromaDB: {str(e)}")
            raise
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> None:
        """
        Add documents to the collection
        
        Args:
            documents: List of document texts
            metadatas: List of metadata dictionaries for each document
            ids: List of unique IDs for each document
        """
        if not self.collection:
            raise RuntimeError("ChromaDB collection not initialized. Call connect() first.")
        
        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"✅ Added {len(documents)} documents to collection")
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
        Query the collection for similar documents
        
        Args:
            query_texts: List of query strings
            n_results: Number of results to return per query
            where: Metadata filter conditions
            where_document: Document content filter conditions
            
        Returns:
            Dictionary containing query results with documents, metadatas, and distances
        """
        if not self.collection:
            raise RuntimeError("ChromaDB collection not initialized. Call connect() first.")
        
        try:
            results = self.collection.query(
                query_texts=query_texts,
                n_results=n_results,
                where=where,
                where_document=where_document
            )
            logger.info(f"✅ Query completed, returned {len(results['ids'][0])} results")
            return results
        except Exception as e:
            logger.error(f"❌ Query failed: {str(e)}")
            raise
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific document by ID
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document data or None if not found
        """
        if not self.collection:
            raise RuntimeError("ChromaDB collection not initialized. Call connect() first.")
        
        try:
            result = self.collection.get(ids=[doc_id])
            if result['ids']:
                return {
                    'id': result['ids'][0],
                    'document': result['documents'][0],
                    'metadata': result['metadatas'][0]
                }
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get document {doc_id}: {str(e)}")
            raise
    
    def update_document(
        self,
        doc_id: str,
        document: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update an existing document
        
        Args:
            doc_id: Document ID to update
            document: New document text (optional)
            metadata: New metadata (optional)
        """
        if not self.collection:
            raise RuntimeError("ChromaDB collection not initialized. Call connect() first.")
        
        try:
            update_params = {'ids': [doc_id]}
            if document:
                update_params['documents'] = [document]
            if metadata:
                update_params['metadatas'] = [metadata]
            
            self.collection.update(**update_params)
            logger.info(f"✅ Updated document {doc_id}")
        except Exception as e:
            logger.error(f"❌ Failed to update document {doc_id}: {str(e)}")
            raise
    
    def delete_documents(self, ids: List[str]) -> None:
        """
        Delete documents from the collection
        
        Args:
            ids: List of document IDs to delete
        """
        if not self.collection:
            raise RuntimeError("ChromaDB collection not initialized. Call connect() first.")
        
        try:
            self.collection.delete(ids=ids)
            logger.info(f"✅ Deleted {len(ids)} documents")
        except Exception as e:
            logger.error(f"❌ Failed to delete documents: {str(e)}")
            raise
    
    def count(self) -> int:
        """
        Get the number of documents in the collection
        
        Returns:
            Number of documents
        """
        if not self.collection:
            raise RuntimeError("ChromaDB collection not initialized. Call connect() first.")
        
        return self.collection.count()
    
    def reset_collection(self) -> None:
        """
        Delete all documents from the collection (use with caution!)
        """
        if not self.collection:
            raise RuntimeError("ChromaDB collection not initialized. Call connect() first.")
        
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"description": "Legal documents and case law for semantic search"}
            )
            logger.warning(f"⚠️ Collection {self.collection_name} has been reset")
        except Exception as e:
            logger.error(f"❌ Failed to reset collection: {str(e)}")
            raise
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get information about the current collection
        
        Returns:
            Dictionary with collection metadata and statistics
        """
        if not self.collection:
            raise RuntimeError("ChromaDB collection not initialized. Call connect() first.")
        
        return {
            'name': self.collection_name,
            'count': self.collection.count(),
            'metadata': self.collection.metadata,
            'embedding_model': self.embedding_model
        }
    
    def disconnect(self) -> None:
        """
        Disconnect from ChromaDB (cleanup)
        """
        self.collection = None
        self.client = None
        logger.info("Disconnected from ChromaDB")


# Singleton instance for global access
_chroma_client_instance: Optional[ChromaClient] = None


def get_chroma_client(
    persist_directory: str = "./data/chromadb",
    collection_name: str = "legal_documents",
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
) -> ChromaClient:
    """
    Get or create a singleton ChromaClient instance
    
    Args:
        persist_directory: Path to persist ChromaDB data
        collection_name: Name of the collection to use
        embedding_model: Name of the sentence-transformer model
        
    Returns:
        ChromaClient instance
    """
    global _chroma_client_instance
    
    if _chroma_client_instance is None:
        _chroma_client_instance = ChromaClient(
            persist_directory=persist_directory,
            collection_name=collection_name,
            embedding_model=embedding_model
        )
        _chroma_client_instance.connect()
    
    return _chroma_client_instance
