"""
Graph Module
Handles Neo4j knowledge graph operations for legal relationships
"""

from .neo4j_client import Neo4jClient, get_neo4j_client
from .graph_queries import fetch_legal_graph_facts, build_graph_context

__all__ = [
    'Neo4jClient',
    'get_neo4j_client',
    'fetch_legal_graph_facts',
    'build_graph_context'
]
