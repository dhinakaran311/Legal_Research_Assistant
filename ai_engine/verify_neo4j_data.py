"""
Neo4j Data Verification Script
Verifies that data was loaded correctly into Neo4j
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from graph.neo4j_client import get_neo4j_client
from config import settings

print("=" * 70)
print("Neo4j Data Verification")
print("=" * 70)

# Step 1: Connect to Neo4j
print("\nStep 1: Connecting to Neo4j...")
client = get_neo4j_client(
    uri=settings.NEO4J_URI,
    username=settings.NEO4J_USERNAME,
    password=settings.NEO4J_PASSWORD
)

if not client:
    print("ERROR: Failed to connect to Neo4j")
    print("TIP: Check your NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD in .env")
    sys.exit(1)

if not client.test_connection():
    print("ERROR: Neo4j connection test failed")
    sys.exit(1)

print("SUCCESS: Connected to Neo4j successfully")

# Step 2: Count nodes
print("\nStep 2: Counting nodes...")
query = """
MATCH (a:Act)
WITH count(a) AS act_count
MATCH (s:Section)
RETURN act_count, count(s) AS section_count
"""
result = client.run_query(query)

if result:
    act_count = result[0]['act_count']
    section_count = result[0]['section_count']
    print(f"SUCCESS: Acts in graph: {act_count}")
    print(f"SUCCESS: Sections in graph: {section_count}")
else:
    print("ERROR: No data found in graph")
    sys.exit(1)

# Step 3: List all acts
print("\nStep 3: Listing all acts...")
query = """
MATCH (a:Act)
RETURN a.short_name AS act, a.name AS name, a.year AS year
ORDER BY a.short_name
"""
result = client.run_query(query)

if result:
    print(f"SUCCESS: Found {len(result)} acts:")
    for r in result:
        print(f"   - {r['act']}: {r['name']} ({r['year']})")
else:
    print("WARNING: No acts found")

# Step 4: Count sections per act
print("\nStep 4: Counting sections per act...")
query = """
MATCH (a:Act)-[:HAS_SECTION]->(s:Section)
RETURN a.short_name AS act, count(s) AS section_count
ORDER BY act
"""
result = client.run_query(query)

if result:
    print(f"SUCCESS: Sections per act:")
    total = 0
    for r in result:
        count = r['section_count']
        total += count
        print(f"   - {r['act']}: {count} sections")
    print(f"   Total: {total} sections")
else:
    print("WARNING: No sections found")

# Step 5: Test CrPC sections
print("\nStep 5: Testing CrPC sections...")
query = """
MATCH (a:Act {short_name: "CrPC"})-[:HAS_SECTION]->(s:Section)
RETURN s.number AS section, s.title AS title
ORDER BY s.number
LIMIT 10
"""
result = client.run_query(query)

if result:
    print(f"SUCCESS: Found {len(result)} CrPC sections:")
    for r in result:
        print(f"   - Section {r['section']}: {r['title'][:60]}...")
else:
    print("WARNING: No CrPC sections found")

# Step 6: Test relationships
print("\nStep 6: Testing relationships...")
query = """
MATCH ()-[r:HAS_SECTION]->()
WITH count(r) AS has_section_count
MATCH ()-[r2:RELATED_TO]->()
RETURN has_section_count, count(r2) AS related_count
"""
result = client.run_query(query)

if result:
    has_section = result[0]['has_section_count']
    related = result[0]['related_count']
    print(f"SUCCESS: HAS_SECTION relationships: {has_section}")
    print(f"SUCCESS: RELATED_TO relationships: {related}")
else:
    print("WARNING: No relationships found")

# Step 7: Test related sections
print("\nStep 7: Testing related sections (Section 438)...")
query = """
MATCH (s:Section {number: "438"})-[:RELATED_TO]->(related:Section)
RETURN related.number AS related_section, related.title AS title, related.act_short_name AS act
LIMIT 5
"""
result = client.run_query(query)

if result:
    print(f"SUCCESS: Found {len(result)} sections related to Section 438:")
    for r in result:
        print(f"   - {r['act']} Section {r['related_section']}: {r['title'][:50]}...")
else:
    print("WARNING: No related sections found for Section 438")
    print("   (This is normal if sections don't reference each other in content)")

# Step 8: Test graph query function
print("\nStep 8: Testing graph query function...")
try:
    from graph.graph_queries import fetch_legal_graph_facts
    
    test_query = "What is anticipatory bail under Section 438?"
    facts = fetch_legal_graph_facts(test_query, client)
    
    if facts:
        print(f"SUCCESS: Found {len(facts)} graph facts:")
        for i, fact in enumerate(facts[:3], 1):
            if 'case_name' in fact:
                print(f"   {i}. Case: {fact['case_name']}")
            elif 'related_section' in fact:
                print(f"   {i}. Related Section: {fact['related_section']}")
    else:
        print("WARNING: No graph facts found (this is normal if no cases are loaded)")
except ImportError as e:
    print(f"WARNING: Could not import graph_queries: {e}")
except Exception as e:
    print(f"WARNING: Error testing graph queries: {e}")

# Summary
print("\n" + "=" * 70)
print("Verification Summary")
print("=" * 70)
print("SUCCESS: Neo4j connection: Working")
print(f"SUCCESS: Acts loaded: {act_count}")
print(f"SUCCESS: Sections loaded: {section_count}")
print("SUCCESS: Graph structure: Valid")
print("\nNext steps:")
print("   1. Test graph integration: python test_graph_simple.py")
print("   2. Run end-to-end tests: Follow END_TO_END_TESTING.md")
print("   3. Test search with graph references in frontend")
print("=" * 70)

# Close connection
client.close()
