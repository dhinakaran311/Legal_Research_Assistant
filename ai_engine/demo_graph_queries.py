"""
Graph Queries Demo - Showcase Neo4j Graph Capabilities for Legal Research
Demonstrates:
1. Graph queries to find related sections
2. Legal research queries using the AI Engine
3. Cross-referencing between acts
4. Enhanced search with graph context
"""
import sys
sys.path.insert(0, 'src')

from graph.neo4j_client import get_neo4j_client
from graph.graph_queries import fetch_legal_graph_facts, build_graph_context
from pipelines.adaptive_rag import AdaptiveRAGPipeline
from config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def demo_1_find_related_sections():
    """Demo 1: Graph queries to find related sections"""
    print_section("DEMO 1: Finding Related Sections Using Graph Queries")
    
    client = get_neo4j_client()
    if not client:
        print("❌ Neo4j connection failed")
        return
    
    # Example 1: Find sections related to Section 438 (Anticipatory Bail)
    print("\n📋 Example 1: Find sections related to Section 438 (Anticipatory Bail)")
    query = """
    MATCH (s:Section {number: "438"})-[:RELATED_TO]->(related:Section)
    RETURN related.number AS section, related.title AS title, related.act_short_name AS act
    ORDER BY related.number
    LIMIT 10
    """
    results = client.run_query(query)
    if results:
        for i, r in enumerate(results, 1):
            print(f"   {i}. Section {r['section']} ({r['act']}): {r['title']}")
    else:
        print("   No related sections found")
    
    # Example 2: Find all sections in an act
    print("\n📋 Example 2: Find all sections in Motor Vehicles Act (MVA)")
    query = """
    MATCH (a:Act {short_name: "MVA"})-[:HAS_SECTION]->(s:Section)
    RETURN s.number AS section, s.title AS title
    ORDER BY toInteger(s.number)
    LIMIT 10
    """
    results = client.run_query(query)
    if results:
        for i, r in enumerate(results, 1):
            print(f"   {i}. Section {r['section']}: {r['title']}")
    else:
        print("   No sections found")
    
    # Example 3: Find sections across multiple acts
    print("\n📋 Example 3: Find bail-related sections across all acts")
    query = """
    MATCH (s:Section)
    WHERE toLower(s.title) CONTAINS 'bail' OR toLower(s.title) CONTAINS 'arrest'
    RETURN s.act_short_name AS act, s.number AS section, s.title AS title
    ORDER BY s.act_short_name, toInteger(s.number)
    LIMIT 10
    """
    results = client.run_query(query)
    if results:
        for i, r in enumerate(results, 1):
            print(f"   {i}. {r['act']} Section {r['section']}: {r['title']}")
    else:
        print("   No bail-related sections found")

def demo_2_legal_research_queries():
    """Demo 2: Legal research queries using the AI Engine"""
    print_section("DEMO 2: Legal Research Queries with AI Engine + Graph")
    
    # Initialize pipeline with graph support
    client = get_neo4j_client()
    if not client:
        print("❌ Neo4j connection failed")
        return
    
    pipeline = AdaptiveRAGPipeline(neo4j_client=client, use_llm=False)
    
    # Example queries
    test_queries = [
        "What is anticipatory bail under Section 438?",
        "What are the provisions for driving license in Motor Vehicles Act?",
        "What is the penalty for dishonor of cheque?",
        "What are the tax deductions available under Income Tax Act?",
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        print("-" * 80)
        
        result = pipeline.process_query(query)
        
        print(f"   Intent: {result.intent.value}")
        print(f"   Documents Retrieved: {result.num_sources_retrieved}")
        print(f"   Graph References: {len(result.graph_references)}")
        print(f"   Processing Time: {result.processing_time_ms:.0f}ms")
        
        if result.graph_references:
            print(f"\n   📊 Graph References Found:")
            for i, ref in enumerate(result.graph_references[:3], 1):
                if 'section' in ref:
                    print(f"      {i}. Section {ref.get('section', 'N/A')} - {ref.get('section_title', 'N/A')}")
                if 'act_name' in ref:
                    print(f"         Act: {ref.get('act_name', 'N/A')}")
        
        if result.sources:
            print(f"\n   📄 Top Source:")
            top_source = result.sources[0]
            print(f"      Act: {top_source.get('metadata', {}).get('act', 'N/A')}")
            print(f"      Section: {top_source.get('metadata', {}).get('section', 'N/A')}")
            print(f"      Title: {top_source.get('metadata', {}).get('title', 'N/A')}")

def demo_3_cross_referencing():
    """Demo 3: Cross-referencing between acts"""
    print_section("DEMO 3: Cross-Referencing Between Acts")
    
    client = get_neo4j_client()
    if not client:
        print("❌ Neo4j connection failed")
        return
    
    # Example 1: Find all acts with similar concepts
    print("\n📋 Example 1: Find all acts dealing with 'penalty' or 'punishment'")
    query = """
    MATCH (s:Section)
    WHERE toLower(s.title) CONTAINS 'penalty' OR toLower(s.title) CONTAINS 'punishment'
    WITH s.act_short_name AS act, count(s) AS section_count
    RETURN act, section_count
    ORDER BY section_count DESC
    LIMIT 10
    """
    results = client.run_query(query)
    if results:
        for i, r in enumerate(results, 1):
            print(f"   {i}. {r['act']}: {r['section_count']} sections")
    
    # Example 2: Find sections across acts by category
    print("\n📋 Example 2: Find tax-related sections across all acts")
    query = """
    MATCH (s:Section)
    WHERE s.subcategory CONTAINS 'tax' OR s.subcategory CONTAINS 'deduction'
    RETURN s.act_short_name AS act, s.number AS section, s.title AS title
    ORDER BY s.act_short_name
    LIMIT 10
    """
    results = client.run_query(query)
    if results:
        for i, r in enumerate(results, 1):
            print(f"   {i}. {r['act']} Section {r['section']}: {r['title']}")
    
    # Example 3: Compare sections across acts
    print("\n📋 Example 3: Find 'registration' sections across different acts")
    query = """
    MATCH (s:Section)
    WHERE toLower(s.title) CONTAINS 'registration' OR toLower(s.title) CONTAINS 'register'
    RETURN s.act_short_name AS act, s.number AS section, s.title AS title
    ORDER BY s.act_short_name, toInteger(s.number)
    LIMIT 10
    """
    results = client.run_query(query)
    if results:
        for i, r in enumerate(results, 1):
            print(f"   {i}. {r['act']} Section {r['section']}: {r['title']}")

def demo_4_enhanced_search():
    """Demo 4: Enhanced search with graph context"""
    print_section("DEMO 4: Enhanced Search with Graph Context")
    
    client = get_neo4j_client()
    if not client:
        print("❌ Neo4j connection failed")
        return
    
    pipeline = AdaptiveRAGPipeline(neo4j_client=client, use_llm=False)
    
    # Example: Complex query that benefits from graph
    complex_queries = [
        {
            "query": "What are the legal provisions for divorce in Hindu Marriage Act?",
            "description": "Uses graph to find related sections and cross-references"
        },
        {
            "query": "What is the procedure for retrenchment of employees?",
            "description": "Finds related sections in Industrial Disputes Act"
        },
        {
            "query": "What are the consumer rights under Consumer Protection Act?",
            "description": "Graph helps find jurisdiction and appeal sections"
        }
    ]
    
    for example in complex_queries:
        print(f"\n🔍 Query: {example['query']}")
        print(f"   Description: {example['description']}")
        print("-" * 80)
        
        # Get graph facts first
        graph_facts = fetch_legal_graph_facts(example['query'], client)
        print(f"   Graph Facts Found: {len(graph_facts)}")
        
        if graph_facts:
            print(f"   Graph Context:")
            context = build_graph_context(graph_facts)
            # Print first few lines of context
            lines = context.split('\n')[:10]
            for line in lines:
                if line.strip():
                    print(f"      {line}")
        
        # Process through pipeline
        result = pipeline.process_query(example['query'])
        
        print(f"\n   Results:")
        print(f"      Vector Search Results: {result.num_sources_retrieved}")
        print(f"      Graph Enrichment: {len(result.graph_references)} references")
        print(f"      Combined Answer Length: {len(result.answer)} characters")

def demo_5_graph_statistics():
    """Demo 5: Graph statistics and overview"""
    print_section("DEMO 5: Graph Statistics and Overview")
    
    client = get_neo4j_client()
    if not client:
        print("❌ Neo4j connection failed")
        return
    
    # Overall statistics
    print("\n📊 Overall Graph Statistics:")
    query = """
    MATCH (a:Act)
    WITH count(a) AS act_count
    MATCH (s:Section)
    WITH act_count, count(s) AS section_count
    MATCH ()-[r:HAS_SECTION]->()
    WITH act_count, section_count, count(r) AS has_section_count
    MATCH ()-[r2:RELATED_TO]->()
    RETURN act_count, section_count, has_section_count, count(r2) AS related_count
    """
    results = client.run_query(query)
    if results:
        stats = results[0]
        print(f"   Total Acts: {stats['act_count']}")
        print(f"   Total Sections: {stats['section_count']}")
        print(f"   HAS_SECTION Relationships: {stats['has_section_count']}")
        print(f"   RELATED_TO Relationships: {stats['related_count']}")
    
    # Acts breakdown
    print("\n📊 Acts Breakdown:")
    query = """
    MATCH (a:Act)-[:HAS_SECTION]->(s:Section)
    RETURN a.short_name AS act, a.name AS name, count(s) AS section_count
    ORDER BY section_count DESC
    """
    results = client.run_query(query)
    if results:
        for i, r in enumerate(results, 1):
            print(f"   {i}. {r['act']} ({r['name']}): {r['section_count']} sections")

def main():
    """Run all demos"""
    print("\n" + "="*80)
    print("  LEGAL RESEARCH ASSISTANT - GRAPH QUERIES DEMONSTRATION")
    print("="*80)
    print("\nThis demo showcases the Neo4j knowledge graph capabilities:")
    print("  1. Graph queries to find related sections")
    print("  2. Legal research queries using the AI Engine")
    print("  3. Cross-referencing between acts")
    print("  4. Enhanced search with graph context")
    print("  5. Graph statistics and overview")
    
    try:
        # Test connection first
        client = get_neo4j_client()
        if not client or not client.test_connection():
            print("\n❌ Failed to connect to Neo4j. Please check your connection settings.")
            return
        
        print("\n✅ Connected to Neo4j successfully!")
        
        # Run all demos
        demo_5_graph_statistics()
        demo_1_find_related_sections()
        demo_3_cross_referencing()
        demo_2_legal_research_queries()
        demo_4_enhanced_search()
        
        print_section("DEMO COMPLETE")
        print("\n✅ All graph capabilities demonstrated successfully!")
        print("\nThe graph is now ready for:")
        print("  • Graph queries to find related sections")
        print("  • Legal research queries using the AI Engine")
        print("  • Cross-referencing between acts")
        print("  • Enhanced search with graph context")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
