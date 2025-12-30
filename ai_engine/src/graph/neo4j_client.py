"""
Neo4j Client - Optimized for Legal Knowledge Graph
Features: Connection pooling, singleton pattern, parameterized queries, session management
"""
from neo4j import GraphDatabase, Session
from typing import List, Dict, Any, Optional
import logging
import os

# Import settings for env variables
try:
    from config import settings
    HAS_SETTINGS = True
except ImportError:
    HAS_SETTINGS = False

logger = logging.getLogger(__name__)


class Neo4jClient:
    """
    Optimized Neo4j client for legal knowledge graph
    
    Features:
    - Connection pooling via neo4j-driver
    - Singleton pattern for resource efficiency
    - Parameterized queries for security
    - Automatic session management
    - Health checks and error handling
    """
    
    def __init__(
        self,
        uri: str,
        username: str,
        password: str,
        max_connection_pool_size: int = 50,
        connection_timeout: int = 30
    ):
        """
        Initialize Neo4j client with connection pooling
        
        Args:
            uri: Neo4j connection URI (e.g., neo4j+s://xxx.databases.neo4j.io)
            username: Neo4j username
            password: Neo4j password
            max_connection_pool_size: Max connections in pool (default: 50)
            connection_timeout: Connection timeout in seconds (default: 30)
        """
        self.uri = uri
        self.username = username
        
        # Initialize driver with connection pooling
        self.driver = GraphDatabase.driver(
            uri,
            auth=(username, password),
            max_connection_pool_size=max_connection_pool_size,
            connection_timeout=connection_timeout
        )
        
        logger.info(f"Neo4jClient initialized: {uri}")
    
    def test_connection(self) -> bool:
        """
        Test Neo4j connection health
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 AS test")
                value = result.single()["test"]
                
                if value == 1:
                    logger.info("✅ Neo4j connection successful")
                    return True
                else:
                    logger.error("❌ Neo4j connection test failed")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Neo4j connection failed: {str(e)}")
            return False
    
    def run_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute Cypher query with parameters (prevents injection)
        
        Args:
            query: Cypher query string
            params: Query parameters (optional)
            
        Returns:
            List of result records as dictionaries
        """
        try:
            with self.driver.session() as session:
                result = session.run(query, params or {})
                records = [record.data() for record in result]
                
                logger.debug(f"Query executed: {len(records)} results")
                return records
                
        except Exception as e:
            logger.error(f"Query failed: {str(e)}")
            logger.error(f"Query: {query}")
            return []
    
    def run_write_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute write query (CREATE, MERGE, DELETE) with transaction
        
        Args:
            query: Cypher write query
            params: Query parameters
            
        Returns:
            Query summary statistics
        """
        try:
            with self.driver.session() as session:
                result = session.run(query, params or {})
                summary = result.consume()
                
                stats = {
                    "nodes_created": summary.counters.nodes_created,
                    "relationships_created": summary.counters.relationships_created,
                    "properties_set": summary.counters.properties_set
                }
                
                logger.info(f"Write query executed: {stats}")
                return stats
                
        except Exception as e:
            logger.error(f"Write query failed: {str(e)}")
            return {}
    
    def close(self):
        """Close driver and release resources"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j driver closed")
    
    def __enter__(self):
        """Context manager support"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.close()
    
    # Optimized query methods for common patterns
    
    def find_section_relationships(
        self,
        section_number: str,
        max_depth: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Find all relationships for a legal section (optimized with index)
        
        Args:
            section_number: Section number (e.g., "438")
            max_depth: Maximum relationship depth (default: 2)
            
        Returns:
            List of related nodes and relationships
        """
        # Optimized query using index on Section.number
        query = """
        MATCH path = (s:Section {number: $section_number})-[*1..{max_depth}]-(related)
        RETURN 
            s.number AS section,
            s.title AS section_title,
            type(relationships(path)[0]) AS relationship_type,
            labels(related)[0] AS related_type,
            properties(related) AS related_properties
        LIMIT 50
        """
        
        # Format query with max_depth
        query = query.replace("{max_depth}", str(max_depth))
        
        return self.run_query(query, {"section_number": section_number})
    
    def find_case_citations(
        self,
        section_number: str
    ) -> List[Dict[str, Any]]:
        """
        Find cases citing a specific section (indexed lookup)
        
        Args:
            section_number: Section number
            
        Returns:
            List of cases with citation details
        """
        query = """
        MATCH (c:Case)-[:INTERPRETS]->(s:Section {number: $section_number})
        OPTIONAL MATCH (s)-[:PART_OF]->(a:Act)
        RETURN 
            c.name AS case_name,
            c.year AS case_year,
            s.number AS section,
            s.title AS section_title,
            a.name AS act_name
        ORDER BY c.year DESC
        LIMIT 20
        """
        
        return self.run_query(query, {"section_number": section_number})
    
    def find_related_provisions(
        self,
        section_number: str
    ) -> List[Dict[str, Any]]:
        """
        Find provisions related to a section (via REFERENCES, RELATED_TO)
        
        Args:
            section_number: Section number
            
        Returns:
            List of related provisions
        """
        query = """
        MATCH (s:Section {number: $section_number})-[r:REFERENCES|RELATED_TO]-(related:Section)
        OPTIONAL MATCH (related)-[:PART_OF]->(a:Act)
        RETURN 
            related.number AS related_section,
            related.title AS related_title,
            type(r) AS relationship,
            a.name AS act_name
        LIMIT 10
        """
        
        return self.run_query(query, {"section_number": section_number})


# Singleton instance
_neo4j_instance: Optional[Neo4jClient] = None


def get_neo4j_client(
    uri: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None
) -> Optional[Neo4jClient]:
    """
    Get or create singleton Neo4j client
    
    Args:
        uri: Neo4j URI (from env if not provided)
        username: Neo4j username (from env if not provided)
        password: Neo4j password (from env if not provided)
        
    Returns:
        Neo4jClient instance or None if credentials missing
    """
    global _neo4j_instance
    
    if _neo4j_instance is None:
        # Get from settings/environment if not provided
        if HAS_SETTINGS:
            uri = uri or settings.NEO4J_URI
            username = username or settings.NEO4J_USERNAME
            password = password or settings.NEO4J_PASSWORD
        else:
            uri = uri or os.getenv("NEO4J_URI")
            username = username or os.getenv("NEO4J_USERNAME", "neo4j")
            password = password or os.getenv("NEO4J_PASSWORD")
        
        if not uri or not password:
            logger.warning("Neo4j credentials missing, graph features disabled")
            return None
        
        try:
            _neo4j_instance = Neo4jClient(uri, username, password)
            
            # Test connection
            if not _neo4j_instance.test_connection():
                logger.error("Neo4j connection test failed")
                _neo4j_instance = None
                
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j client: {str(e)}")
            _neo4j_instance = None
    
    return _neo4j_instance
