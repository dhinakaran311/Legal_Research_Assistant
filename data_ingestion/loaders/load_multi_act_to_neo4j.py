"""
Multi-Act Neo4j Graph Loader
Loads scraped JSON files from multiple acts into Neo4j knowledge graph
Creates Act nodes, Section nodes, and relationships between them
"""
import sys
import os
import json
import re
from pathlib import Path
import logging
from typing import Dict, List, Set, Optional

# Add paths for imports
project_root = Path(__file__).parent.parent.parent
ai_engine_src = project_root / "ai_engine" / "src"
data_ingestion_root = project_root / "data_ingestion"
sys.path.insert(0, str(ai_engine_src))

# Import from ai_engine
from graph.neo4j_client import Neo4jClient, get_neo4j_client
from config import settings as ai_config_settings

# Now add data_ingestion to path for its modules
sys.path.insert(0, str(data_ingestion_root))

# Import acts_config directly from the file path to avoid conflict with config module
import importlib.util
acts_config_path = data_ingestion_root / "config" / "acts_config.py"
spec = importlib.util.spec_from_file_location("acts_config", acts_config_path)
acts_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(acts_config)

# Import functions from acts_config
get_act_config = acts_config.get_act_config
get_subcategory = acts_config.get_subcategory
list_all_acts = acts_config.list_all_acts

# Use the correct settings
settings = ai_config_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Storage base directory
STORAGE_BASE_DIR = Path(__file__).parent.parent / "storage" / "acts"


def load_act_json_files(act_key: str) -> list:
    """
    Load all JSON files for a specific act from storage directory
    
    Args:
        act_key: Act key (e.g., "ipc", "crpc")
        
    Returns:
        List of dictionaries with section data
    """
    act_dir = STORAGE_BASE_DIR / act_key.lower()
    
    if not act_dir.exists():
        logger.warning(f"[WARN] Storage directory not found: {act_dir}")
        return []
    
    json_files = list(act_dir.glob("section_*.json"))
    
    if not json_files:
        logger.warning(f"[WARN] No JSON files found in {act_dir}")
        return []
    
    logger.info(f"📁 Found {len(json_files)} JSON files for {act_key.upper()}")
    
    sections = []
    for json_file in sorted(json_files):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                sections.append(data)
                logger.info(f"   ✓ Loaded: {json_file.name}")
        except Exception as e:
            logger.error(f"[FAIL] Failed to load {json_file.name}: {str(e)}")
    
    return sections


def extract_section_references(content: str, act_key: str, current_section: str) -> Set[str]:
    """
    Extract section references from content text
    Looks for patterns like "Section 437", "section 302", "S. 438", etc.
    
    Args:
        content: Section content text
        act_key: Current act key
        current_section: Current section number (to exclude self-references)
        
    Returns:
        Set of section numbers referenced
    """
    references = set()
    
    # Patterns to match section references
    patterns = [
        r'[Ss]ection\s+(\d+[A-Za-z]?)',  # "Section 437" or "section 302"
        r'[Ss]\.\s*(\d+[A-Za-z]?)',      # "S. 438" or "s. 302"
        r'[Ss]ec\.\s*(\d+[A-Za-z]?)',    # "Sec. 437"
        r'[Ss]ec\s+(\d+[A-Za-z]?)',      # "Sec 437"
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            section_num = match.strip()
            # Exclude self-reference and invalid numbers
            if section_num != current_section and section_num:
                references.add(section_num)
    
    return references


def create_act_node(neo4j_client: Neo4jClient, act_key: str) -> bool:
    """
    Create or update Act node in Neo4j
    
    Args:
        neo4j_client: Neo4j client instance
        act_key: Act key (e.g., "ipc", "crpc")
        
    Returns:
        True if successful, False otherwise
    """
    config = get_act_config(act_key)
    if not config:
        logger.error(f"[FAIL] Unknown act: {act_key}")
        return False
    
    act_name = config.get("full_name", act_key.upper())
    short_name = config.get("short_name", act_key.upper())
    year = config.get("year", 0)
    category = config.get("category", "general")
    
    # Create or merge Act node
    query = """
    MERGE (a:Act {short_name: $short_name})
    SET a.name = $name,
        a.year = $year,
        a.category = $category,
        a.act_key = $act_key
    RETURN a.short_name AS short_name
    """
    
    params = {
        "short_name": short_name,
        "name": act_name,
        "year": year,
        "category": category,
        "act_key": act_key.lower()
    }
    
    try:
        result = neo4j_client.run_query(query, params)
        if result:
            logger.info(f"   [PASS] Act node created/updated: {short_name}")
            return True
        else:
            logger.error(f"   [FAIL] Failed to create Act node: {short_name}")
            return False
    except Exception as e:
        logger.error(f"   [FAIL] Error creating Act node: {str(e)}")
        return False


def create_section_node(
    neo4j_client: Neo4jClient,
    section_data: dict,
    act_key: str,
    act_short_name: str
) -> bool:
    """
    Create or update Section node in Neo4j
    
    Args:
        neo4j_client: Neo4j client instance
        section_data: Dictionary with section data from JSON
        act_key: Act key (e.g., "ipc", "crpc")
        act_short_name: Short name of the act (e.g., "IPC", "CrPC")
        
    Returns:
        True if successful, False otherwise
    """
    section_number = section_data.get('section', '')
    title = section_data.get('title', '')
    source_url = section_data.get('source_url', '')
    last_updated = section_data.get('last_updated', '')
    
    # Get subcategory
    subcategory = get_subcategory(act_key, section_number)
    
    # Create unique identifier: act_short_name + section_number
    section_id = f"{act_short_name}_{section_number}"
    
    # Create or merge Section node
    query = """
    MERGE (s:Section {id: $section_id})
    SET s.number = $number,
        s.title = $title,
        s.act_key = $act_key,
        s.act_short_name = $act_short_name,
        s.subcategory = $subcategory,
        s.source_url = $source_url,
        s.last_updated = $last_updated
    RETURN s.id AS id
    """
    
    params = {
        "section_id": section_id,
        "number": section_number,
        "title": title,
        "act_key": act_key.lower(),
        "act_short_name": act_short_name,
        "subcategory": subcategory,
        "source_url": source_url,
        "last_updated": last_updated
    }
    
    try:
        result = neo4j_client.run_query(query, params)
        if result:
            logger.info(f"   [PASS] Section node created/updated: {section_id}")
            return True
        else:
            logger.error(f"   [FAIL] Failed to create Section node: {section_id}")
            return False
    except Exception as e:
        logger.error(f"   [FAIL] Error creating Section node: {str(e)}")
        return False


def create_has_section_relationship(
    neo4j_client: Neo4jClient,
    act_short_name: str,
    section_id: str
) -> bool:
    """
    Create HAS_SECTION relationship between Act and Section
    
    Args:
        neo4j_client: Neo4j client instance
        act_short_name: Short name of the act
        section_id: Section identifier (act_short_name + section_number)
        
    Returns:
        True if successful, False otherwise
    """
    query = """
    MATCH (a:Act {short_name: $act_short_name})
    MATCH (s:Section {id: $section_id})
    MERGE (a)-[r:HAS_SECTION]->(s)
    RETURN r
    """
    
    params = {
        "act_short_name": act_short_name,
        "section_id": section_id
    }
    
    try:
        result = neo4j_client.run_query(query, params)
        if result:
            logger.debug(f"   ✓ HAS_SECTION relationship: {act_short_name} -> {section_id}")
            return True
        else:
            logger.warning(f"   [WARN] Failed to create HAS_SECTION relationship")
            return False
    except Exception as e:
        logger.error(f"   [FAIL] Error creating relationship: {str(e)}")
        return False


def create_section_references(
    neo4j_client: Neo4jClient,
    section_id: str,
    referenced_sections: Set[str],
    act_short_name: str,
    act_key: str
) -> int:
    """
    Create RELATED_TO relationships between sections
    
    Args:
        neo4j_client: Neo4j client instance
        section_id: Source section identifier
        referenced_sections: Set of section numbers referenced
        act_short_name: Short name of the act
        act_key: Act key
        
    Returns:
        Number of relationships created
    """
    if not referenced_sections:
        return 0
    
    relationships_created = 0
    
    for ref_section_num in referenced_sections:
        ref_section_id = f"{act_short_name}_{ref_section_num}"
        
        # Check if referenced section exists in the graph
        check_query = """
        MATCH (s:Section {id: $ref_section_id})
        RETURN s.id AS id
        """
        
        result = neo4j_client.run_query(check_query, {"ref_section_id": ref_section_id})
        
        if result:
            # Create RELATED_TO relationship
            query = """
            MATCH (s1:Section {id: $section_id})
            MATCH (s2:Section {id: $ref_section_id})
            MERGE (s1)-[r:RELATED_TO]->(s2)
            RETURN r
            """
            
            params = {
                "section_id": section_id,
                "ref_section_id": ref_section_id
            }
            
            try:
                result = neo4j_client.run_query(query, params)
                if result:
                    relationships_created += 1
                    logger.debug(f"   ✓ RELATED_TO: {section_id} -> {ref_section_id}")
            except Exception as e:
                logger.debug(f"   [WARN] Could not create relationship: {str(e)}")
    
    return relationships_created


def create_indexes(neo4j_client: Neo4jClient) -> bool:
    """
    Create indexes on Neo4j for better query performance
    
    Args:
        neo4j_client: Neo4j client instance
        
    Returns:
        True if successful, False otherwise
    """
    indexes = [
        "CREATE INDEX IF NOT EXISTS FOR (a:Act) ON (a.short_name)",
        "CREATE INDEX IF NOT EXISTS FOR (s:Section) ON (s.id)",
        "CREATE INDEX IF NOT EXISTS FOR (s:Section) ON (s.number)",
        "CREATE INDEX IF NOT EXISTS FOR (s:Section) ON (s.act_key)",
    ]
    
    try:
        for index_query in indexes:
            neo4j_client.run_query(index_query)
        logger.info("   [PASS] Indexes created/verified")
        return True
    except Exception as e:
        logger.warning(f"   [WARN] Could not create indexes: {str(e)}")
        return False


def load_act_to_neo4j(act_key: str, neo4j_client: Neo4jClient, create_references: bool = True) -> bool:
    """
    Load sections for a specific act into Neo4j
    
    Args:
        act_key: Act key (e.g., "ipc", "crpc")
        neo4j_client: Neo4j client instance
        create_references: Whether to create RELATED_TO relationships from content
        
    Returns:
        True if successful, False otherwise
    """
    config = get_act_config(act_key)
    if not config:
        logger.error(f"[FAIL] Unknown act: {act_key}")
        return False
    
    act_name = config.get("short_name", act_key.upper())
    
    try:
        logger.info(f"\n[LOADING] Loading {act_name} sections into Neo4j...")
        
        # Step 1: Create Act node
        logger.info(f"[STEP 1] Creating Act node...")
        if not create_act_node(neo4j_client, act_key):
            logger.error(f"[FAIL] Failed to create Act node for {act_name}")
            return False
        
        # Step 2: Load JSON files
        logger.info(f"[STEP 2] Loading JSON files...")
        sections = load_act_json_files(act_key)
        
        if not sections:
            logger.warning(f"[WARN] No sections to load for {act_name}. Run scraper first.")
            return False
        
        logger.info(f"[PASS] Loaded {len(sections)} sections")
        
        # Step 3: Create Section nodes and relationships
        logger.info(f"[STEP 3] Creating Section nodes...")
        sections_created = 0
        relationships_created = 0
        reference_relationships = 0
        
        for section in sections:
            section_number = section.get('section', '')
            section_id = f"{act_name}_{section_number}"
            
            # Create Section node
            if create_section_node(neo4j_client, section, act_key, act_name):
                sections_created += 1
                
                # Create HAS_SECTION relationship
                if create_has_section_relationship(neo4j_client, act_name, section_id):
                    relationships_created += 1
                
                # Extract and create section references if enabled
                if create_references:
                    content = section.get('content', '')
                    referenced_sections = extract_section_references(content, act_key, section_number)
                    
                    if referenced_sections:
                        ref_count = create_section_references(
                            neo4j_client,
                            section_id,
                            referenced_sections,
                            act_name,
                            act_key
                        )
                        reference_relationships += ref_count
        
        logger.info(f"[PASS] Created {sections_created} Section nodes")
        logger.info(f"[PASS] Created {relationships_created} HAS_SECTION relationships")
        if create_references:
            logger.info(f"[PASS] Created {reference_relationships} RELATED_TO relationships")
        
        return True
        
    except Exception as e:
        logger.error(f"[FAIL] Failed to load {act_name} data: {str(e)}", exc_info=True)
        return False


def load_all_acts_to_neo4j(act_keys: list = None, create_references: bool = True):
    """
    Main function to load all acts into Neo4j
    
    Args:
        act_keys: List of act keys to load. If None, loads all acts with JSON files.
        create_references: Whether to create RELATED_TO relationships from content
    """
    logger.info("=" * 70)
    logger.info("[START] Loading Multiple Acts into Neo4j Knowledge Graph")
    logger.info("=" * 70)
    
    try:
        # Step 1: Initialize Neo4j client
        logger.info("\n[STEP 1] Initializing Neo4j client...")
        
        neo4j_client = get_neo4j_client(
            uri=settings.NEO4J_URI,
            username=settings.NEO4J_USERNAME,
            password=settings.NEO4J_PASSWORD
        )
        
        if not neo4j_client:
            logger.error("[FAIL] Failed to initialize Neo4j client. Check credentials in .env")
            logger.error("")
            logger.error("[INFO] Troubleshooting:")
            logger.error(f"   1. Verify Neo4j URI: {settings.NEO4J_URI}")
            logger.error("   2. Check if Neo4j AuraDB instance exists and is running")
            logger.error("   3. Verify network connectivity and DNS resolution")
            logger.error("   4. For local Neo4j, use: bolt://localhost:7687")
            logger.error("   5. Check firewall/proxy settings if using AuraDB")
            return False
        
        # Test connection
        if not neo4j_client.test_connection():
            logger.error("[FAIL] Neo4j connection test failed")
            return False
        
        logger.info("[PASS] Neo4j connected")
        
        # Step 2: Create indexes
        logger.info("\n[STEP 2] Creating indexes...")
        create_indexes(neo4j_client)
        
        # Step 3: Determine which acts to load
        if act_keys is None:
            # Find all acts with JSON files
            act_keys = []
            for act_dir in STORAGE_BASE_DIR.iterdir():
                if act_dir.is_dir() and list(act_dir.glob("section_*.json")):
                    act_keys.append(act_dir.name)
            
            if not act_keys:
                logger.error("[FAIL] No act directories found with JSON files. Run scraper first.")
                return False
        
        logger.info(f"\n[STEP 3] Loading acts: {', '.join([a.upper() for a in act_keys])}")
        
        # Step 4: Load each act
        results = {}
        total_sections = 0
        total_relationships = 0
        
        for act_key in act_keys:
            config = get_act_config(act_key)
            if not config:
                logger.warning(f"[WARN] Skipping unknown act: {act_key}")
                continue
            
            logger.info(f"\n{'=' * 70}")
            logger.info(f"[ACT] Processing Act: {config.get('full_name', act_key)}")
            logger.info(f"{'=' * 70}")
            
            success = load_act_to_neo4j(act_key, neo4j_client, create_references)
            results[act_key] = success
            
            if success:
                sections = load_act_json_files(act_key)
                total_sections += len(sections)
        
        # Step 5: Summary
        logger.info(f"\n{'=' * 70}")
        logger.info("[SUMMARY] Final Status")
        logger.info("=" * 70)
        
        # Count nodes and relationships
        count_query = """
        MATCH (a:Act)
        WITH count(a) AS act_count
        MATCH (s:Section)
        WITH act_count, count(s) AS section_count
        MATCH ()-[r:HAS_SECTION]->()
        WITH act_count, section_count, count(r) AS has_section_count
        MATCH ()-[r2:RELATED_TO]->()
        RETURN act_count, section_count, has_section_count, count(r2) AS related_count
        """
        
        count_result = neo4j_client.run_query(count_query)
        if count_result:
            stats = count_result[0]
            logger.info(f"   Acts in graph: {stats.get('act_count', 0)}")
            logger.info(f"   Sections in graph: {stats.get('section_count', 0)}")
            logger.info(f"   HAS_SECTION relationships: {stats.get('has_section_count', 0)}")
            logger.info(f"   RELATED_TO relationships: {stats.get('related_count', 0)}")
        
        successful_acts = sum(1 for v in results.values() if v)
        logger.info(f"   Acts loaded: {successful_acts}/{len(results)}")
        logger.info(f"   Sections processed: {total_sections}")
        
        # Step 6: Test query
        logger.info(f"\n[STEP 4] Testing graph query...")
        test_query = """
        MATCH (a:Act {short_name: "CrPC"})-[:HAS_SECTION]->(s:Section)
        RETURN a.short_name AS act, count(s) AS section_count
        LIMIT 1
        """
        
        test_result = neo4j_client.run_query(test_query)
        if test_result:
            logger.info(f"   [PASS] Test query successful")
            result = test_result[0]
            logger.info(f"      {result.get('act')}: {result.get('section_count')} sections")
        
        logger.info("\n" + "=" * 70)
        logger.info("[SUCCESS] Multi-act data loaded into Neo4j successfully!")
        logger.info("=" * 70)
        
        return True
        
    except Exception as e:
        logger.error(f"\n[FAIL] Failed to load multi-act data: {str(e)}", exc_info=True)
        return False
    finally:
        # Close Neo4j connection
        if 'neo4j_client' in locals() and neo4j_client is not None:
            neo4j_client.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Load multiple Indian Acts into Neo4j")
    parser.add_argument(
        "--acts",
        nargs="+",
        help="Specific acts to load (default: all acts with JSON files)"
    )
    parser.add_argument(
        "--no-references",
        action="store_true",
        help="Skip creating RELATED_TO relationships from content"
    )
    
    args = parser.parse_args()
    
    create_refs = not args.no_references
    
    success = load_all_acts_to_neo4j(args.acts, create_references=create_refs)
    sys.exit(0 if success else 1)
