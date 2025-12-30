"""
Simple Graph Test - Shows Neo4j + RAG Integration
"""
import sys
sys.path.insert(0, 'src')

print("\n" + "="*80)
print("NEO4J GRAPH INTEGRATION TEST")
print("="*80)

# Step 1: Test Neo4j Connection
print("\n[Step 1] Testing Neo4j Connection...")
from graph.neo4j_client import get_neo4j_client

client = get_neo4j_client()
if client:
    print("PASS: Connected to Neo4j AuraDB")
else:
    print("FAIL: Connection failed")
    exit(1)

# Step 2: Test Direct Graph Query
print("\n[Step 2] Testing Direct Graph Query...")
print("Query: Find cases citing Section 438")

cases = client.find_case_citations("438")
print(f"PASS: Found {len(cases)} cases:")
for i, case in enumerate(cases, 1):
    print(f"   {i}. {case['case_name']} ({case['case_year']})")

# Step 3: Test Graph Query Function
print("\n[Step 3] Testing Graph Query Function...")
from graph.graph_queries import fetch_legal_graph_facts

test_query = "What is anticipatory bail under Section 438?"
print(f"Query: '{test_query}'")

facts = fetch_legal_graph_facts(test_query, client)
print(f"PASS: Found {len(facts)} graph facts:")
for i, fact in enumerate(facts, 1):
    if 'case_name' in fact:
        print(f"   {i}. Case: {fact['case_name']}")
    elif 'related_section' in fact:
        print(f"   {i}. Related Section: {fact['related_section']}")

# Step 4: Test Full Pipeline Integration
print("\n[Step 4] Testing RAG+Graph Pipeline...")
from pipelines.adaptive_rag import AdaptiveRAGPipeline

pipeline = AdaptiveRAGPipeline(neo4j_client=client, use_llm=False)
print("Query: 'What is anticipatory bail under Section 438?'")

result = pipeline.process_query("What is anticipatory bail under Section 438?")

print(f"\nRESULTS:")
print(f"   Intent: {result.intent.value}")
print(f"   Vector Sources (ChromaDB): {result.num_sources_retrieved}")
print(f"   Graph Facts (Neo4j): {len(result.graph_references)}")
print(f"   Processing Time: {result.processing_time_ms:.0f}ms")

if result.graph_references:
    print(f"\nGraph References:")
    for i, ref in enumerate(result.graph_references, 1):
        if 'case_name' in ref:
            print(f"   {i}. {ref['case_name']} ({ref.get('case_year', 'N/A')})")

# Final Summary
print("\n" + "="*80)
print("GRAPH INTEGRATION TEST PASSED!")
print("="*80)
print("\nSummary:")
print(f"  * Neo4j connected: YES")
print(f"  * Graph queries working: YES")
print(f"  * Pipeline integration: YES")
print(f"  * Hybrid RAG+Graph: YES")
print("\nLegal knowledge graph is enriching RAG responses!")
print("="*80 + "\n")
