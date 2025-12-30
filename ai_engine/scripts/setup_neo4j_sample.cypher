// Neo4j Sample Legal Data Setup (Simplified - No Indexes)
// Insert this data into Neo4j to test graph integration
// Run in Neo4j Browser (https://console.neo4j.io)

// Create Acts
MERGE (crpc:Act {name: "Criminal Procedure Code", year: 1973, short_name: "CrPC"})
MERGE (ipc:Act {name: "Indian Penal Code", year: 1860, short_name: "IPC"})

// Create Sections
MERGE (s438:Section {
  number: "438",
  title: "Direction for grant of bail to person apprehending arrest",
  common_name: "Anticipatory Bail"
})

MERGE (s437:Section {
  number: "437",
  title: "When bail may be taken in case of non-bailable offence",
  common_name: "Regular Bail"
})

MERGE (s302:Section {
  number: "302",
  title: "Punishment for Murder",
  common_name: "Murder"
})

MERGE (s300:Section {
  number: "300",
  title: "Murder",
  common_name: "Definition of Murder"
})

// Create Principles
MERGE (anticipatory_bail:Principle {
  name: "Anticipatory Bail",
  description: "Bail granted in anticipation of arrest"
})

MERGE (regular_bail:Principle {
  name: "Regular Bail",
  description: "Bail after arrest"
})

// Create Landmark Cases
MERGE (gurbaksh:Case {
  name: "Gurbaksh Singh Sibbia vs State of Punjab",
  year: 1980,
  court: "Supreme Court",
  citation: "AIR 1980 SC 1632"
})

MERGE (arnesh:Case {
  name: "Arnesh Kumar vs State of Bihar",
  year: 2014,
  court: "Supreme Court",
  citation: "AIR 2014 SC 2756"
})

// Create Relationships

// Act → Section
MERGE (crpc)-[:HAS_SECTION]->(s438)
MERGE (crpc)-[:HAS_SECTION]->(s437)
MERGE (ipc)-[:HAS_SECTION]->(s302)
MERGE (ipc)-[:HAS_SECTION]->(s300)

// Section → Principle
MERGE (s438)-[:DEFINES]->(anticipatory_bail)
MERGE (s437)-[:DEFINES]->(regular_bail)

// Section relationships
MERGE (s438)-[:RELATED_TO]->(s437)
MERGE (s302)-[:REFERENCES]->(s300)

// Case → Section (INTERPRETS)
MERGE (gurbaksh)-[:INTERPRETS]->(s438)
MERGE (arnesh)-[:INTERPRETS]->(s438)

// Case → Principle (ESTABLISHES)
MERGE (gurbaksh)-[:ESTABLISHES]->(anticipatory_bail)

// Verify Data
RETURN "Data loaded successfully!" AS status;
