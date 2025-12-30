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
    
    # Pattern 3: Specific legal concepts (extensible)
    concept_queries = {
        'bail': '438',  # Map to Section 438
        'murder': '302',  # Map to Section 302
        'cheating': '420',  # Map to Section 420
    }
    
    for concept, section in concept_queries.items():
        if concept in question_lower and section not in [f.get('section', '') for f in graph_facts]:
            facts = neo4j_client.find_case_citations(section)
            if facts:
                graph_facts.extend(facts)
                logger.info(f"Found {len(facts)} facts for concept '{concept}' (Section {section})")
    
    # Remove duplicates (by case_name + section)
    unique_facts = []
    seen = set()
    
    for fact in graph_facts:
        identifier = f"{fact.get('case_name', '')}_{fact.get('section', '')}"
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
