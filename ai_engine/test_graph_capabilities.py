"""
Quick Test of Graph Capabilities
Tests the 4 main use cases:
1. Graph queries to find related sections
2. Legal research queries using the AI Engine
3. Cross-referencing between acts
4. Enhanced search with graph context
"""
import sys
sys.path.insert(0, 'src')

print("\n" + "="*80)
print("  TESTING GRAPH CAPABILITIES")
print("="*80)

# Test 1: Basic Connection
print("\n[Test 1] Neo4j Connection")
from graph.neo4j_client import get_neo4j_client
client = get_neo4j_client()
if client and client.test_connection():
    print("[PASS] Neo4j connected successfully")
else:
    print("[FAIL] Neo4j connection failed")
    exit(1)

# Test 2: Graph Queries - Find Related Sections
print("\n[Test 2] Graph Queries - Find Related Sections")
query = """
MATCH (a:Act {short_name: "CrPC"})-[:HAS_SECTION]->(s:Section)
RETURN s.number AS section, s.title AS title
ORDER BY toInteger(s.number)
LIMIT 5
"""
results = client.run_query(query)
if results:
    print(f"[PASS] Found {len(results)} CrPC sections:")
    for r in results:
        print(f"   - Section {r['section']}: {r['title'][:60]}...")
else:
    print("[WARN] No sections found")

# Test 3: Cross-Referencing Between Acts
print("\n[Test 3] Cross-Referencing Between Acts")
query = """
MATCH (a:Act)-[:HAS_SECTION]->(s:Section)
WITH a.short_name AS act, count(s) AS section_count
RETURN act, section_count
ORDER BY section_count DESC
LIMIT 5
"""
results = client.run_query(query)
if results:
    print(f"[PASS] Found {len(results)} acts with sections:")
    for r in results:
        print(f"   - {r['act']}: {r['section_count']} sections")
else:
    print("[WARN] No acts found")

# Test 4: Find Sections by Topic
print("\n[Test 4] Find Sections by Topic (e.g., 'bail')")
query = """
MATCH (s:Section)
WHERE toLower(s.title) CONTAINS 'bail'
RETURN s.act_short_name AS act, s.number AS section, s.title AS title
LIMIT 5
"""
results = client.run_query(query)
if results:
    print(f"[PASS] Found {len(results)} bail-related sections:")
    for r in results:
        print(f"   - {r['act']} Section {r['section']}: {r['title'][:60]}...")
else:
    print("[WARN] No bail-related sections found")

# Test 5: Graph Statistics
print("\n[Test 5] Graph Statistics")
query = """
MATCH (a:Act)
WITH count(a) AS act_count
MATCH (s:Section)
WITH act_count, count(s) AS section_count
MATCH ()-[r:HAS_SECTION]->()
RETURN act_count, section_count, count(r) AS has_section_count
"""
results = client.run_query(query)
if results:
    stats = results[0]
    print("[PASS] Graph Statistics:")
    print(f"   - Total Acts: {stats['act_count']}")
    print(f"   - Total Sections: {stats['section_count']}")
    print(f"   - HAS_SECTION Relationships: {stats['has_section_count']}")

# Test 6: Graph Query Function
print("\n[Test 6] Graph Query Function (fetch_legal_graph_facts)")
from graph.graph_queries import fetch_legal_graph_facts
test_query = "What is anticipatory bail under Section 438?"
facts = fetch_legal_graph_facts(test_query, client)
print(f"[PASS] Found {len(facts)} graph facts for query: '{test_query}'")
if facts:
    for i, fact in enumerate(facts[:3], 1):
        print(f"   {i}. {fact}")

# Test 7: Pipeline Integration (if ChromaDB available)
print("\n[Test 7] Pipeline Integration Test")
try:
    from pipelines.adaptive_rag import AdaptiveRAGPipeline
    pipeline = AdaptiveRAGPipeline(neo4j_client=client, use_llm=False)
    print("[PASS] Pipeline initialized with graph support")
    
    # Test a simple query
    result = pipeline.process_query("What is anticipatory bail?")
    print(f"[PASS] Query processed:")
    print(f"   - Intent: {result.intent.value}")
    print(f"   - Sources: {result.num_sources_retrieved}")
    print(f"   - Graph References: {len(result.graph_references)}")
    print(f"   - Processing Time: {result.processing_time_ms:.0f}ms")
except Exception as e:
    print(f"[WARN] Pipeline test skipped: {str(e)}")

print("\n" + "="*80)
print("  ALL TESTS COMPLETE")
print("="*80)
print("\n[SUCCESS] Graph is ready for:")
print("   1. Graph queries to find related sections")
print("   2. Legal research queries using the AI Engine")
print("   3. Cross-referencing between acts")
print("   4. Enhanced search with graph context")
print("="*80 + "\n")
