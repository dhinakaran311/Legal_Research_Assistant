# Neo4j Graph Loader - Multi-Act Data

Loads scraped legal act data into Neo4j knowledge graph for relationship mapping and cross-references.

## Overview

This loader creates a knowledge graph structure:
- **Act Nodes**: Represent legal acts (IPC, CrPC, Evidence Act, etc.)
- **Section Nodes**: Represent individual sections within acts
- **Relationships**:
  - `HAS_SECTION`: Act → Section (every section belongs to an act)
  - `RELATED_TO`: Section → Section (sections that reference each other)

## Prerequisites

1. **Neo4j Running**
   - Docker: `docker run -p 7474:7474 -p 7687:7687 neo4j:latest`
   - Neo4j Desktop: Start your database
   - Cloud: Neo4j AuraDB

2. **Environment Variables**
   - Configure in `ai_engine/.env`:
     ```env
     NEO4J_URI=bolt://localhost:7687
     NEO4J_USERNAME=neo4j
     NEO4J_PASSWORD=your_password
     ```

3. **Scraped Data**
   - JSON files must exist in `storage/acts/{act_key}/`
   - Run `python sources/multi_act_scraper.py` first if needed

## Usage

### Load All Acts

```bash
cd data_ingestion
python loaders/load_multi_act_to_neo4j.py
```

### Load Specific Acts

```bash
python loaders/load_multi_act_to_neo4j.py --acts crpc ipc evidence
```

### Skip Reference Extraction (Faster)

```bash
# Only creates Act and Section nodes, no RELATED_TO relationships
python loaders/load_multi_act_to_neo4j.py --no-references
```

## What Gets Created

### Act Nodes

Properties:
- `name`: Full act name (e.g., "Code of Criminal Procedure, 1973")
- `short_name`: Short name (e.g., "CrPC")
- `year`: Year of enactment
- `category`: Category (e.g., "criminal_procedure")
- `act_key`: Lowercase key (e.g., "crpc")

### Section Nodes

Properties:
- `id`: Unique identifier (e.g., "CrPC_438")
- `number`: Section number (e.g., "438")
- `title`: Section title
- `act_key`: Act key (e.g., "crpc")
- `act_short_name`: Act short name (e.g., "CrPC")
- `subcategory`: Subcategory (e.g., "bail")
- `source_url`: Source URL from IndiaCode
- `last_updated`: Last updated year

### Relationships

1. **HAS_SECTION**
   - From: Act node
   - To: Section node
   - Meaning: Section belongs to this Act

2. **RELATED_TO**
   - From: Section node
   - To: Section node
   - Meaning: Section references or relates to another section
   - Created by: Extracting section references from content text

## Example Queries

### Count Nodes

```cypher
MATCH (a:Act)
WITH count(a) AS act_count
MATCH (s:Section)
RETURN act_count, count(s) AS section_count
```

### Find All Sections in an Act

```cypher
MATCH (a:Act {short_name: "CrPC"})-[:HAS_SECTION]->(s:Section)
RETURN s.number AS section, s.title AS title
ORDER BY s.number
```

### Find Related Sections

```cypher
MATCH (s:Section {number: "438"})-[:RELATED_TO]->(related:Section)
RETURN related.number AS related_section, related.title AS title
```

### Find Sections by Subcategory

```cypher
MATCH (s:Section {subcategory: "bail"})
RETURN s.number AS section, s.title AS title, s.act_short_name AS act
```

### Find Cross-Act Relationships

```cypher
MATCH (s1:Section)-[:RELATED_TO]->(s2:Section)
WHERE s1.act_short_name <> s2.act_short_name
RETURN s1.act_short_name + " " + s1.number AS from_section,
       s2.act_short_name + " " + s2.number AS to_section
```

## Reference Detection

The loader automatically detects section references in content using regex patterns:
- "Section 437"
- "section 302"
- "S. 438"
- "Sec. 437"

When a reference is found, a `RELATED_TO` relationship is created (if the referenced section exists in the graph).

## Indexes

The loader automatically creates indexes for performance:
- `Act.short_name`
- `Section.id`
- `Section.number`
- `Section.act_key`

## Troubleshooting

### Connection Failed

**Error:** `❌ Failed to initialize Neo4j client`

**Solutions:**
1. Verify Neo4j is running: `docker ps` or check Neo4j Desktop
2. Check `NEO4J_URI` in `ai_engine/.env` (should be `bolt://localhost:7687` for local)
3. Verify credentials match Neo4j database
4. Test connection: Open Neo4j Browser at http://localhost:7474

### No Sections Found

**Error:** `⚠️  No JSON files found`

**Solutions:**
1. Run scraper first: `python sources/multi_act_scraper.py`
2. Verify JSON files exist in `storage/acts/{act_key}/`
3. Check file naming: Should be `section_XXX.json`

### Import Errors

**Error:** `ModuleNotFoundError` or import errors

**Solutions:**
1. Verify `ai_engine/src` is accessible
2. Check Python path setup in script
3. Ensure all dependencies installed: `pip install neo4j`

### No Relationships Created

**Issue:** `RELATED_TO` relationships count is 0

**Solutions:**
1. This is normal if sections don't reference each other in content
2. Check if `--no-references` flag was used
3. Verify content in JSON files contains section references
4. Some sections may not have references in their text

## Integration with AI Engine

The Neo4j graph is used by the AI Engine for:
- Finding related sections during search
- Cross-referencing between acts
- Building graph-based context for answers
- Discovering legal relationships

The graph queries are handled by `ai_engine/src/graph/graph_queries.py` and integrated into the Adaptive RAG pipeline.

## Next Steps

After loading data into Neo4j:

1. **Verify Graph Structure**: Use Neo4j Browser to explore relationships
2. **Test Graph Queries**: Use the example queries above
3. **Integrate with Search**: Graph references will appear in search results
4. **Add More Relationships**: Manually add case citations, principles, etc.

## Related Files

- **Loader Script**: `data_ingestion/loaders/load_multi_act_to_neo4j.py`
- **Neo4j Client**: `ai_engine/src/graph/neo4j_client.py`
- **Graph Queries**: `ai_engine/src/graph/graph_queries.py`
- **Sample Data Script**: `ai_engine/scripts/setup_neo4j_sample.cypher`
