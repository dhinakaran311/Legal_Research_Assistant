"""
Graph Queries - Legal-specific graph query logic with optimized Cypher patterns
"""
from typing import List, Dict, Any, Optional
import logging
import re

logger = logging.getLogger(__name__)


def fetch_legal_graph_facts(
    question: str,
    neo4j_client
) -> List[Dict[str, Any]]:
    """
    Fetch relevant legal relationships from Neo4j based on question
    
    Uses optimized, indexed queries for common legal patterns.
    
    Args:
        question: User's legal question
        neo4j_client: Neo4jClient instance
        
    Returns:
        List of graph facts (cases, sections, relationships)
    """
    if not neo4j_client:
        logger.debug("Neo4j client not available, skipping graph enrichment")
        return []
    
    question_lower = question.lower()
    graph_facts = []
    
    # Pattern 1: Anticipatory Bail / Section 438
    if any(term in question_lower for term in ['anticipatory bail', 'section 438', 's.438', 's 438']):
        logger.info("Detected Section 438 query, fetching graph relationships")
        
        # Optimized query using indexed Section.number
        facts = neo4j_client.find_case_citations("438")
        if facts:
            graph_facts.extend(facts)
            logger.info(f"Found {len(facts)} case citations for Section 438")
        
        # Also get related sections
        related = neo4j_client.find_related_provisions("438")
        if related:
            graph_facts.extend(related)
    
    # Pattern 2: Section number detection (e.g., "section 302", "s.302")
    section_pattern = r'section\s+(\d+)|s\.?\s*(\d+)'
    section_match = re.search(section_pattern, question_lower)
    
    if section_match:
        section_num = section_match.group(1) or section_match.group(2)
        logger.info(f"Detected section number: {section_num}")
        
        # Fetch relationships for this section
        facts = neo4j_client.find_case_citations(section_num)
        if facts:
            graph_facts.extend(facts)
            logger.info(f"Found {len(facts)} case citations for Section {section_num}")
    
    # Pattern 3: Specific legal concepts → section mappings (extensible)
    concept_queries = {
        'bail':          ('438', 'CrPC'),
        'anticipatory':  ('438', 'CrPC'),
        'arrest':        ('41',  'CrPC'),
        'fir':           ('154', 'CrPC'),
        'murder':        ('302', 'IPC'),
        'homicide':      ('300', 'IPC'),
        'rape':          ('376', 'IPC'),
        'cheating':      ('420', 'IPC'),
        'defamation':    ('499', 'IPC'),
        'intimidation':  ('506', 'IPC'),
        'cheque':        ('138', 'NIA'),
        'dishonour':     ('138', 'NIA'),
        'negotiable':    ('138', 'NIA'),
        'divorce':       ('13',  'HMA'),
        'retrenchment':  ('25',  'IDA'),
        'consumer':      ('35',  'CPA'),
        'cyber':         ('66',  'IT'),
        'hacking':       ('43',  'IT'),
        'rti':           ('6',   'RTI'),
        'information':   ('6',   'RTI'),
        'tax':           ('139', 'ITA'),
        'income tax':    ('139', 'ITA'),
        'contract':      ('10',  'Contract'),
        'agreement':     ('10',  'Contract'),
        'transfer':      ('5',   'TPA'),
        'property':      ('54',  'TPA'),
        'mortgage':      ('58',  'TPA'),
        'lease':         ('105', 'TPA'),
    }

    already_seen_sections = {f.get('section', '') for f in graph_facts}

    for concept, (section_num, act_key) in concept_queries.items():
        if concept not in question_lower:
            continue
        if section_num in already_seen_sections:
            continue

        # First try: find landmark cases for this section
        facts = neo4j_client.find_case_citations(section_num)
        if facts:
            graph_facts.extend(facts)
            already_seen_sections.add(section_num)
            logger.info(f"Found {len(facts)} case citations for concept '{concept}' (Section {section_num})")
            continue

        # Fallback: fetch the section node directly and return it as a graph fact
        try:
            section_info = neo4j_client.run_query("""
                MATCH (s:Section {number: $num, act_short_name: $act})
                RETURN s.number       AS section,
                       s.title        AS section_title,
                       s.common_name  AS common_name,
                       s.act_name     AS act_name,
                       s.act_short_name AS act_short_name
            """, {"num": section_num, "act": act_key})

            if section_info:
                info = section_info[0]
                graph_facts.append({
                    "section":       info.get("section", section_num),
                    "section_title": info.get("section_title", ""),
                    "common_name":   info.get("common_name", ""),
                    "act_name":      info.get("act_name", ""),
                    "act_short_name":info.get("act_short_name", act_key),
                    "source":        "section_node",
                })
                already_seen_sections.add(section_num)
                logger.info(f"Fetched section node for concept '{concept}' (§{section_num} {act_key})")
        except Exception as e:
            logger.warning(f"Section fallback failed for '{concept}': {e}")

    # Also enrich with related provisions for any sections we found
    for section_num in list(already_seen_sections):
        related = neo4j_client.find_related_provisions(section_num)
        if related:
            for r in related:
                identifier = f"_{r.get('related_section', '')}"
                if identifier not in {f"_{f.get('related_section', '')}" for f in graph_facts}:
                    graph_facts.append(r)

    # Remove duplicates (by case_name + section)
    unique_facts = []
    seen = set()

    for fact in graph_facts:
        identifier = f"{fact.get('case_name', '')}_{fact.get('section', '')}_{fact.get('related_section', '')}"
        if identifier not in seen:
            unique_facts.append(fact)
            seen.add(identifier)

    logger.info(f"Returning {len(unique_facts)} unique graph facts")
    return unique_facts


def build_graph_context(graph_data: List[Dict[str, Any]]) -> str:
    """
    Convert graph facts into formatted context text for LLM
    
    Args:
        graph_data: List of graph facts from fetch_legal_graph_facts()
        
    Returns:
        Formatted context string
    """
    if not graph_data:
        return ""
    
    context = "\n\n--- Legal References from Knowledge Graph ---\n"
    
    # Group by type
    cases = []
    related_sections = []
    
    for item in graph_data:
        if 'case_name' in item and item.get('case_name'):
            cases.append(item)
        elif 'related_section' in item:
            related_sections.append(item)
    
    # Format case citations
    if cases:
        context += "\n**Case Law Citations:**\n"
        for case in cases[:5]:  # Limit to top 5
            case_name = case.get('case_name', 'Unknown Case')
            case_year = case.get('case_year', '')
            section = case.get('section', '')
            section_title = case.get('section_title', '')
            act = case.get('act_name', '')
            
            citation = f"- **{case_name}**"
            if case_year:
                citation += f" ({case_year})"
            citation += f" - Interprets Section {section}"
            if section_title:
                citation += f" ({section_title})"
            if act:
                citation += f" of {act}"
            
            context += citation + "\n"
    
    # Format related provisions
    if related_sections:
        context += "\n**Related Provisions:**\n"
        for rel in related_sections[:3]:  # Limit to top 3
            rel_section = rel.get('related_section', '')
            rel_title = rel.get('related_title', '')
            relationship = rel.get('relationship', 'related_to').replace('_', ' ')
            act = rel.get('act_name', '')
            
            relation = f"- Section {rel_section}"
            if rel_title:
                relation += f" ({rel_title})"
            if act:
                relation += f" of {act}"
            relation += f" - {relationship}"
            
            context += relation + "\n"
    
    context += "---\n"
    
    return context


# Helper functions for specific graph patterns

def extract_section_number(text: str) -> Optional[str]:
    """
    Extract section number from text
    
    Args:
        text: Input text
        
    Returns:
        Section number or None
    """
    pattern = r'section\s+(\d+)|s\.?\s*(\d+)'
    match = re.search(pattern, text.lower())
    
    if match:
        return match.group(1) or match.group(2)
    
    return None


def detect_legal_intent(question: str) -> str:
    """
    Detect if question is asking for graph-relevant information
    
    Args:
        question: User's question
        
    Returns:
        Intent type: 'case_law', 'amendment', 'relationship', 'none'
    """
    q_lower = question.lower()
    
    if any(term in q_lower for term in ['case', 'judgment', 'precedent', 'ruling']):
        return 'case_law'
    elif any(term in q_lower for term in ['amendment', 'changed', 'modified', 'updated']):
        return 'amendment'
    elif any(term in q_lower for term in ['related', 'similar', 'connected', 'reference']):
        return 'relationship'
    else:
        return 'none'
