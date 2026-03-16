"""
Configuration module for AI Engine
Loads environment variables and manages application settings
"""
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "5000"))
    API_RELOAD: bool = os.getenv("API_RELOAD", "True").lower() == "true"
    
    # AI Model Configuration
    MODEL_NAME: str = os.getenv("MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
    
    # Database Configuration
    # Use absolute path for ChromaDB to avoid issues when running from different directories
    CHROMA_DB_PATH: str = os.getenv(
        "CHROMA_DB_PATH", 
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chromadb")
    )
    CHROMA_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "legal_documents")
    
    # Neo4j Configuration
    NEO4J_URI: str = os.getenv("NEO4J_URI", "")
    NEO4J_USERNAME: str = os.getenv("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "")
    
    # Internal API Security
    INTERNAL_API_KEY: str = os.getenv("INTERNAL_API_KEY", "")
    
    # Google Gemini LLM
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    
    # Ollama LLM
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    
    # Pinecone Vector DB
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "legal-documents")
    PINECONE_NAMESPACE: str = os.getenv("PINECONE_NAMESPACE", "legal_documents")
    
    # Application Settings
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = 'ignore'  # Allow extra env variables (for backward compatibility)


# Create global settings instance
settings = Settings()
