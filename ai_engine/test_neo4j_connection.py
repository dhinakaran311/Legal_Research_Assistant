import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

uri = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USERNAME", "neo4j")
password = os.getenv("NEO4J_PASSWORD")

if not uri or not password:
    print("Error: NEO4J_URI or NEO4J_PASSWORD not found in .env")
    exit(1)

print(f"Connecting to: {uri} as {user}...")

try:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session(database="neo4j") as session:
        result = session.run("RETURN 'Connected to Neo4j AuraDB!' AS message")
        print(result.single()["message"])
    driver.close()
except Exception as e:
    print(f"Connection failed: {e}")
