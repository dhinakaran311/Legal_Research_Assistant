# Graph Usage Guide - Legal Research Assistant

## Overview

The Neo4j knowledge graph is now fully integrated and ready for use! This guide shows you how to leverage the graph for legal research.

## Graph Statistics

- **19 Acts** loaded
- **168 Sections** in the graph
- **168 HAS_SECTION relationships**
- **1 RELATED_TO relationship** (will grow as more references are extracted)

## Use Cases

### 1. Graph Queries to Find Related Sections

**Example: Find all sections in an act**
```cypher
MATCH (a:Act {short_name: "CrPC"})-[:HAS_SECTION]->(s:Section)
RETURN s.number AS section, s.title AS title
ORDER BY toInteger(s.number)
```

**Example: Find sections related to a specific section**
```cypher
MATCH (s:Section {number: "438"})-[:RELATED_TO]->(related:Section)
RETURN related.number AS section, related.title AS title
```

**Example: Find sections by topic across all acts**
```cypher
MATCH (s:Section)
WHERE toLower(s.title) CONTAINS 'bail'
RETURN s.act_short_name AS act, s.number AS section, s.title AS title
```

### 2. Legal Research Queries Using the AI Engine

The AI Engine automatically uses the graph when processing queries:

**Via API:**
```bash
POST http://localhost:5000/api/adaptive-query
{
  "question": "What is anticipatory bail under Section 438?",
  "use_llm": false,
  "max_docs": 5
}
```

**Via Python:**
```python
from pipelines.adaptive_rag import AdaptiveRAGPipeline
from graph.neo4j_client import get_neo4j_client

client = get_neo4j_client()
pipeline = AdaptiveRAGPipeline(neo4j_client=client, use_llm=False)

result = pipeline.process_query("What is anticipatory bail?")
print(f"Graph References: {len(result.graph_references)}")
print(f"Sources: {result.num_sources_retrieved}")
```

### 3. Cross-Referencing Between Acts

**Example: Find all acts with similar concepts**
```cypher
MATCH (s:Section)
WHERE toLower(s.title) CONTAINS 'penalty' OR toLower(s.title) CONTAINS 'punishment'
WITH s.act_short_name AS act, count(s) AS section_count
RETURN act, section_count
ORDER BY section_count DESC
```

**Example: Compare sections across acts**
```cypher
MATCH (s:Section)
WHERE toLower(s.title) CONTAINS 'registration'
RETURN s.act_short_name AS act, s.number AS section, s.title AS title
ORDER BY s.act_short_name
```

**Example: Find tax-related sections across all acts**
```cypher
MATCH (s:Section)
WHERE s.subcategory CONTAINS 'tax' OR s.subcategory CONTAINS 'deduction'
RETURN s.act_short_name AS act, s.number AS section, s.title AS title
```

### 4. Enhanced Search with Graph Context

The graph automatically enriches search results:

1. **Vector Search** (ChromaDB) finds semantically similar documents
2. **Graph Enrichment** (Neo4j) adds:
   - Related sections
   - Cross-references
   - Section relationships
   - Act-level context

**Example Query Flow:**
```
User Query: "What is anticipatory bail?"
    ↓
1. Vector Search → Finds Section 438 content from ChromaDB
    ↓
2. Graph Query → Finds:
   - Related sections (437, 436)
   - Case citations (if available)
   - Cross-act references
    ↓
3. Combined Answer → Enhanced with graph context
```

## Available Acts in Graph

1. **CrPC** - Code of Criminal Procedure, 1973
2. **IPC** - Indian Penal Code, 1860
3. **CPC** - Code of Civil Procedure, 1908
4. **Evidence** - Indian Evidence Act, 1872
5. **Contract** - Indian Contract Act, 1872
6. **Companies** - Companies Act, 2013
7. **Constitution** - Constitution of India, 1950
8. **MVA** - Motor Vehicles Act, 1988
9. **ITA** - Income Tax Act, 1961
10. **GST** - Central Goods and Services Tax Act, 2017
11. **CPA** - Consumer Protection Act, 2019
12. **RPA** - Representation of the People Act, 1951
13. **IT Act** - Information Technology Act, 2000
14. **RTI** - Right to Information Act, 2005
15. **TPA** - Transfer of Property Act, 1882
16. **NIA** - Negotiable Instruments Act, 1881
17. **IDA** - Industrial Disputes Act, 1947
18. **HMA** - Hindu Marriage Act, 1955
19. **FSSA** - Food Safety and Standards Act, 2006

## Testing the Graph

Run the test script to verify all capabilities:

```bash
cd ai_engine
python test_graph_capabilities.py
```

This tests:
- ✅ Neo4j connection
- ✅ Graph queries
- ✅ Cross-referencing
- ✅ Topic-based search
- ✅ Graph statistics
- ✅ Graph query functions
- ✅ Pipeline integration

## Graph Query Functions

### `fetch_legal_graph_facts(question, neo4j_client)`
Automatically extracts graph facts from a legal question:
- Detects section numbers
- Finds related sections
- Retrieves case citations (if available)
- Maps legal concepts to sections

### `build_graph_context(graph_data)`
Formats graph facts into readable context for LLM or display.

## Example Queries

### Query 1: Find bail-related sections
```python
query = """
MATCH (s:Section)
WHERE toLower(s.title) CONTAINS 'bail'
RETURN s.act_short_name AS act, s.number AS section, s.title AS title
"""
results = client.run_query(query)
```

### Query 2: Get all sections in an act
```python
query = """
MATCH (a:Act {short_name: "MVA"})-[:HAS_SECTION]->(s:Section)
RETURN s.number AS section, s.title AS title
ORDER BY toInteger(s.number)
"""
results = client.run_query(query)
```

### Query 3: Find sections by category
```python
query = """
MATCH (s:Section)
WHERE s.subcategory = 'bail'
RETURN s.act_short_name AS act, s.number AS section, s.title AS title
"""
results = client.run_query(query)
```

## Integration with AI Engine

The graph is automatically used when:
1. Processing queries via `/api/adaptive-query`
2. Using `AdaptiveRAGPipeline` with `neo4j_client` parameter
3. Graph facts are included in `result.graph_references`

**Response Structure:**
```python
{
    "question": "...",
    "answer": "...",
    "sources": [...],  # From ChromaDB
    "graph_references": [...],  # From Neo4j
    "intent": "...",
    "confidence": 0.95
}
```

## Next Steps

1. **Add more relationships**: Extract section references from content to create more RELATED_TO relationships
2. **Add case law**: Load case citations to create Case nodes and INTERPRETS relationships
3. **Expand queries**: Add more pattern matching in `graph_queries.py`
4. **Performance tuning**: Add more indexes for common query patterns

## Troubleshooting

**Issue: Graph queries return empty results**
- Check if sections exist: `MATCH (s:Section) RETURN count(s)`
- Verify relationships: `MATCH ()-[r:HAS_SECTION]->() RETURN count(r)`

**Issue: Pipeline not using graph**
- Ensure `neo4j_client` is passed to `AdaptiveRAGPipeline`
- Check `use_graph` parameter is True (default)

**Issue: Connection errors**
- Verify Neo4j credentials in `.env`
- Check AuraDB instance is running
- Test connection: `client.test_connection()`

## Summary

✅ **Graph is ready and working!**

The knowledge graph provides:
- **19 acts** with **168 sections**
- **Automatic graph enrichment** for all queries
- **Cross-act referencing** capabilities
- **Enhanced search** with graph context
- **Scalable architecture** for adding more data

Start using it now for powerful legal research!
