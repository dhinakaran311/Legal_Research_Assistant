"""
Vector store module for Pinecone and ChromaDB integration.
Imports are lazy so a broken/missing Pinecone install never crashes
a ChromaDB-only startup.
"""
from .chroma_client import ChromaClient

__all__ = ["ChromaClient", "PineconeClient"]


def __getattr__(name: str):
    if name == "PineconeClient":
        from .pinecone_client import PineconeClient  # noqa: PLC0415
        return PineconeClient
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
