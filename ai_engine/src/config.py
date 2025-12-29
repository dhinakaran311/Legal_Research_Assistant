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
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")
    
    # Application Settings
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()
