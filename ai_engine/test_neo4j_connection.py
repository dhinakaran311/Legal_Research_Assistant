from neo4j import GraphDatabase
import os

uri = os.getenv("NEO4J_URI", "neo4j+s://6db506f2.databases.neo4j.io")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "zvhdxV75jqge_cm992yU7uRqiCFQsmZtuA51r59xMmw")

driver = GraphDatabase.driver(uri, auth=(user, password))

with driver.session(database="neo4j") as session:
    result = session.run("RETURN 'Connected to Neo4j AuraDB!' AS message")
    print(result.single()["message"])
