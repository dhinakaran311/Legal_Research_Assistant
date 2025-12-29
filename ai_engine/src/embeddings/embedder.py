"""
Text Embedder for Legal Documents
Converts text to vector embeddings using sentence-transformers
"""
from sentence_transformers import SentenceTransformer
from typing import List, Union, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)


class Embedder:
    """
    Text embedding service using sentence-transformers
    Converts legal text into dense vector representations for semantic search
    """
    
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: Optional[str] = None
    ):
        """
        Initialize the embedder with a sentence-transformer model
        
        Args:
            model_name: Name of the sentence-transformer model to use
            device: Device to run the model on ('cuda', 'cpu', or None for auto-detect)
        """
        self.model_name = model_name
        self.device = device
        self.model = None
        self.embedding_dimension = None
        
        logger.info(f"Embedder initialized with model: {model_name}")
    
    def load_model(self) -> None:
        """
        Load the sentence-transformer model
        """
        try:
            logger.info(f"Loading model: {self.model_name}...")
            self.model = SentenceTransformer(self.model_name, device=self.device)
            self.embedding_dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"✅ Model loaded successfully")
            logger.info(f"📊 Embedding dimension: {self.embedding_dimension}")
        except Exception as e:
            logger.error(f"❌ Failed to load model: {str(e)}")
            raise
    
    def encode(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        show_progress_bar: bool = False,
        normalize_embeddings: bool = True
    ) -> np.ndarray:
        """
        Convert text(s) to vector embeddings
        
        Args:
            texts: Single text string or list of text strings
            batch_size: Batch size for encoding
            show_progress_bar: Whether to show progress bar during encoding
            normalize_embeddings: Whether to normalize embeddings to unit length
            
        Returns:
            numpy array of embeddings (shape: [num_texts, embedding_dim])
        """
        if not self.model:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        # Convert single string to list
        if isinstance(texts, str):
            texts = [texts]
        
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress_bar,
                normalize_embeddings=normalize_embeddings,
                convert_to_numpy=True
            )
            
            logger.info(f"✅ Encoded {len(texts)} text(s) to embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"❌ Failed to encode texts: {str(e)}")
            raise
    
    def encode_single(
        self,
        text: str,
        normalize_embeddings: bool = True
    ) -> np.ndarray:
        """
        Convenience method to encode a single text
        
        Args:
            text: Text string to encode
            normalize_embeddings: Whether to normalize embedding to unit length
            
        Returns:
            1D numpy array of embedding
        """
        embeddings = self.encode(
            texts=[text],
            batch_size=1,
            show_progress_bar=False,
            normalize_embeddings=normalize_embeddings
        )
        return embeddings[0]
    
    def encode_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress_bar: bool = True,
        normalize_embeddings: bool = True
    ) -> np.ndarray:
        """
        Encode a batch of texts with progress tracking
        
        Args:
            texts: List of text strings
            batch_size: Batch size for encoding
            show_progress_bar: Whether to show progress bar
            normalize_embeddings: Whether to normalize embeddings
            
        Returns:
            2D numpy array of embeddings (shape: [num_texts, embedding_dim])
        """
        return self.encode(
            texts=texts,
            batch_size=batch_size,
            show_progress_bar=show_progress_bar,
            normalize_embeddings=normalize_embeddings
        )
    
    def similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (0 to 1)
        """
        # Normalize if not already normalized
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 > 0:
            embedding1 = embedding1 / norm1
        if norm2 > 0:
            embedding2 = embedding2 / norm2
        
        similarity = np.dot(embedding1, embedding2)
        return float(similarity)
    
    def get_model_info(self) -> dict:
        """
        Get information about the loaded model
        
        Returns:
            Dictionary with model information
        """
        if not self.model:
            return {
                'model_name': self.model_name,
                'loaded': False
            }
        
        return {
            'model_name': self.model_name,
            'loaded': True,
            'embedding_dimension': self.embedding_dimension,
            'device': str(self.model.device),
            'max_seq_length': self.model.max_seq_length
        }
    
    def preprocess_legal_text(self, text: str) -> str:
        """
        Preprocess legal text before embedding
        
        Args:
            text: Raw legal text
            
        Returns:
            Preprocessed text
        """
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Truncate if too long (model has max sequence length)
        if self.model and len(text) > self.model.max_seq_length * 4:
            # Rough estimate: 4 chars per token
            max_chars = self.model.max_seq_length * 4
            text = text[:max_chars]
            logger.warning(f"Text truncated to {max_chars} characters")
        
        return text
    
    def embed_legal_documents(
        self,
        documents: List[str],
        preprocess: bool = True,
        batch_size: int = 32,
        show_progress_bar: bool = True
    ) -> np.ndarray:
        """
        Embed legal documents with optional preprocessing
        
        Args:
            documents: List of legal document texts
            preprocess: Whether to preprocess texts
            batch_size: Batch size for encoding
            show_progress_bar: Whether to show progress bar
            
        Returns:
            2D numpy array of embeddings
        """
        if preprocess:
            documents = [self.preprocess_legal_text(doc) for doc in documents]
        
        return self.encode_batch(
            texts=documents,
            batch_size=batch_size,
            show_progress_bar=show_progress_bar
        )


# Singleton instance for global access
_embedder_instance: Optional[Embedder] = None


def get_embedder(
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    device: Optional[str] = None,
    force_reload: bool = False
) -> Embedder:
    """
    Get or create a singleton Embedder instance
    
    Args:
        model_name: Name of the sentence-transformer model
        device: Device to run the model on
        force_reload: Force reload the model even if already loaded
        
    Returns:
        Embedder instance
    """
    global _embedder_instance
    
    if _embedder_instance is None or force_reload:
        _embedder_instance = Embedder(model_name=model_name, device=device)
        _embedder_instance.load_model()
    
    return _embedder_instance
