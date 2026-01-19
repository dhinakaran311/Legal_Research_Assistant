# Legal Research Assistant

An AI-powered legal research platform for Indian law, enabling intelligent search through legal documents using natural language queries with hybrid RAG (Retrieval-Augmented Generation) and knowledge graph integration.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-20.x-green.svg)](https://nodejs.org/)
[![Next.js](https://img.shields.io/badge/Next.js-14.x-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Overview

Legal Research Assistant is a comprehensive legal search system that combines:
- **Vector Search** (ChromaDB) for semantic document retrieval
- **Knowledge Graphs** (Neo4j) for legal relationship mapping
- **Adaptive RAG Pipeline** for intent-aware query processing
- **LLM Integration** (Ollama) for natural language answer generation

The system supports **7 major Indian Acts** with **63+ popular sections**, including IPC, CrPC, Evidence Act, Contract Act, CPC, Companies Act, and Constitution.

---

## Screenshots

### Authentication Pages
<div align="center">
  <img src="images/login.png" alt="Login Page" width="45%">
  <img src="images/signin.png" alt="Sign Up Page" width="45%">
</div>

### Main Interface
<div align="center">
  <img src="images/home_page.png" alt="Home Page - Search Interface" width="90%">
</div>

---

## Features

### Intelligent Search
- **Natural Language Queries**: Ask legal questions in plain English
- **Intent Detection**: Automatically classifies query types (factual, procedural, comparative, etc.)
- **Adaptive Retrieval**: Dynamically adjusts document retrieval based on query intent
- **Hybrid Search**: Combines vector search (ChromaDB) + knowledge graph (Neo4j)

### Multi-Act Support
- **7 Indian Acts**: IPC, CrPC, Evidence Act, Contract Act, CPC, Companies Act, Constitution
- **63+ Sections**: Popular sections from each act
- **Graph Relationships**: Cross-references between sections and acts
- **Case Citations**: Landmark cases linked to sections

### AI-Powered Answers
- **Rule-Based Generation**: Fast, predictable answers (default)
- **LLM-Powered Generation**: Natural, synthesized answers using Ollama (optional)
- **Source Citations**: Every answer includes source documents with metadata
- **Graph References**: Related sections and cases from knowledge graph

### Modern Architecture
- **Microservices Design**: Separate services for Frontend, Backend, and AI Engine
- **GraphQL API**: Flexible query interface
- **REST API**: Standard HTTP endpoints
- **JWT Authentication**: Secure user authentication

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│                    (Next.js - Port 3000)                    │
│              - Search Interface                              │
│              - Authentication                                │
│              - Results Display                               │
└───────────────────────┬─────────────────────────────────────┘
                        │ GraphQL / REST
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                        Backend                               │
│                 (Node.js/Express - Port 4000)                │
│              - GraphQL API (Apollo Server)                   │
│              - REST API                                       │
│              - JWT Authentication                            │
│              - PostgreSQL (User Data)                        │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTP + API Key
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                      AI Engine                               │
│                  (Python/FastAPI - Port 5000)                │
│              - Adaptive RAG Pipeline                         │
│              - Intent Detection                              │
│              - Answer Generation (Rule-based / LLM)          │
└───────────────┬───────────────────────┬─────────────────────┘
                │                       │
                ▼                       ▼
    ┌──────────────────┐    ┌──────────────────┐
    │    ChromaDB      │    │      Neo4j       │
    │  (Vector Store)  │    │ (Knowledge Graph)│
    │  - Embeddings    │    │  - Relationships │
    │  - Documents     │    │  - Cross-refs     │
    └──────────────────┘    └──────────────────┘
```

---

## Tech Stack

### Frontend
- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Apollo Client** - GraphQL client

### Backend
- **Node.js 20** - Runtime
- **Express.js 5** - Web framework
- **Apollo Server** - GraphQL server
- **Prisma** - ORM for PostgreSQL
- **JWT** - Authentication

### AI Engine
- **Python 3.11** - Runtime
- **FastAPI** - Web framework
- **ChromaDB** - Vector database
- **Neo4j** - Graph database
- **Sentence Transformers** - Embeddings
- **Ollama** - LLM integration (optional)

### Databases
- **PostgreSQL 15** - User data and sessions
- **ChromaDB** - Vector embeddings
- **Neo4j 5** - Knowledge graph

---

## Prerequisites

Before you begin, ensure you have:

- **Python 3.11+** installed
- **Node.js 20.x** installed
- **PostgreSQL 15** (or Docker)
- **Neo4j 5** (or Docker, or Neo4j AuraDB)
- **Git** installed
- **Ollama** (optional, for LLM features)

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/dhinakaran311/Legal_Research_Assistant.git
cd Legal_Research_Assistant
```

### 2. Install Dependencies

#### AI Engine
```powershell
cd ai_engine
python -m venv .ven
.\.ven\Scripts\Activate
pip install -r requirements.txt
```

#### Backend
```powershell
cd backend
npm install
```

#### Frontend
```powershell
cd frontend
npm install
```

#### Data Ingestion
```powershell
cd data_ingestion
pip install -r requirements.txt
```

### 3. Configure Environment Variables

#### AI Engine (`ai_engine/.env`)
```env
API_HOST=0.0.0.0
API_PORT=5000
CHROMA_DB_PATH=./data/chromadb
CHROMA_COLLECTION_NAME=legal_documents
MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
INTERNAL_API_KEY=legal-ai-secret-key-2024
DEBUG=True
LOG_LEVEL=INFO
```

#### Backend (`backend/.env`)
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/legal_assistant
AI_ENGINE_URL=http://localhost:5000
INTERNAL_API_KEY=legal-ai-secret-key-2024
PORT=4000
NODE_ENV=development
JWT_SECRET=your-jwt-secret-key-here
```

#### Frontend (`frontend/.env.local`)
```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:4000
NEXT_PUBLIC_GRAPHQL_URL=http://localhost:4000/graphql
```

**Important:** `INTERNAL_API_KEY` must be **identical** in both `ai_engine/.env` and `backend/.env`.

### 4. Set Up Databases

#### PostgreSQL
```powershell
# Create database
createdb legal_assistant

# Run migrations
cd backend
npx prisma migrate dev
```

#### Neo4j
- **Option 1:** Use Neo4j AuraDB (cloud) - Update `NEO4J_URI` in `.env`
- **Option 2:** Use Docker:
  ```powershell
  docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:5
  ```

### 5. Load Data

#### Scrape Legal Documents
```powershell
cd data_ingestion
python sources/multi_act_scraper.py
```

#### Load into ChromaDB
```powershell
python loaders/load_multi_act_data.py
```

#### Load into Neo4j
```powershell
python loaders/load_multi_act_to_neo4j.py
```

### 6. Start Services

Open **3 separate terminal windows**:

#### Terminal 1: AI Engine
```powershell
cd ai_engine
.\.ven\Scripts\Activate
$env:PYTHONPATH = "src"
python -m uvicorn src.main:app --host 0.0.0.0 --port 5000 --reload
```

**Verify:** http://localhost:5000/health

#### Terminal 2: Backend
```powershell
cd backend
npm run dev
```

**Verify:** http://localhost:4000/graphql

#### Terminal 3: Frontend
```powershell
cd frontend
npm run dev
```

**Verify:** http://localhost:3000

---

## Execution Flow

### Complete System Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    USER QUERY FLOW                           │
└─────────────────────────────────────────────────────────────┘

1. User enters query in Frontend
   "What is anticipatory bail?"
   │
   ▼
2. Frontend sends GraphQL query to Backend
   POST /graphql
   { query: "What is anticipatory bail?", use_llm: false }
   │
   ▼
3. Backend authenticates request
   - Validates JWT token
   - Checks user session
   │
   ▼
4. Backend forwards to AI Engine
   POST /api/adaptive-query
   Headers: X-Internal-API-Key
   Body: { question: "...", use_llm: false }
   │
   ▼
5. AI Engine: Intent Detection
   - Analyzes query type (definitional, factual, etc.)
   - Calculates confidence score
   - Determines retrieval strategy
   │
   ▼
6. AI Engine: Document Retrieval
   ├─→ ChromaDB: Vector search for relevant sections
   │   Returns: Top 3-5 documents with relevance scores
   │
   └─→ Neo4j: Graph query for related sections/cases
       Returns: Related sections, landmark cases
   │
   ▼
7. AI Engine: Answer Generation
   ├─→ Rule-based (if use_llm: false)
   │   - Formats answer from top document
   │   - Adds citations
   │
   └─→ LLM-powered (if use_llm: true)
       - Sends context to Ollama
       - Generates natural language answer
       - Synthesizes multiple sources
   │
   ▼
8. AI Engine returns structured response
   {
     answer: "Anticipatory bail is...",
     sources: [...],
     graph_references: [...],
     intent: "definitional",
     confidence: 0.95
   }
   │
   ▼
9. Backend transforms and returns to Frontend
   - Maps AI Engine response to GraphQL schema
   - Adds user context if needed
   │
   ▼
10. Frontend displays results
    - Main answer
    - Source documents with citations
    - Graph references (related sections/cases)
    - Confidence score
```

### Data Loading Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA INGESTION FLOW                       │
└─────────────────────────────────────────────────────────────┘

1. Scrape Legal Documents
   python sources/multi_act_scraper.py
   │
   ├─→ Scrapes from IndiaCode
   ├─→ Saves JSON files: storage/acts/{act}/section_*.json
   └─→ Rate limiting: 2 seconds between requests
   │
   ▼
2. Load into ChromaDB
   python loaders/load_multi_act_data.py
   │
   ├─→ Reads JSON files
   ├─→ Cleans text
   ├─→ Generates embeddings
   └─→ Stores in ChromaDB with metadata
   │
   ▼
3. Load into Neo4j
   python loaders/load_multi_act_to_neo4j.py
   │
   ├─→ Creates Act nodes
   ├─→ Creates Section nodes
   ├─→ Creates HAS_SECTION relationships
   └─→ Creates RELATED_TO relationships (from content analysis)
   │
   ▼
4. Verify Data
   python ai_engine/verify_neo4j_data.py
   - Checks node counts
   - Tests graph queries
   - Verifies relationships
```

---

## Usage Examples

### Search via Frontend

1. **Open:** http://localhost:3000
2. **Login/Signup:** Create account or login
3. **Search:** Enter query (e.g., "What is anticipatory bail?")
4. **Toggle LLM:** Check "Use LLM" for better quality (slower)
5. **View Results:** See answer, sources, and graph references

### Search via GraphQL

```graphql
query SearchLegal {
  search(query: "What is the punishment for murder?", use_llm: false) {
    question
    intent
    intent_confidence
    answer
    sources {
      content
      relevance_score
      metadata {
        act
        section
        title
      }
    }
    graph_references {
      section
      section_title
      act_name
      relationship
    }
    confidence
    processing_time_ms
  }
}
```

### Search via REST API

```bash
curl -X POST http://localhost:5000/api/adaptive-query \
  -H "Content-Type: application/json" \
  -H "X-Internal-API-Key: legal-ai-secret-key-2024" \
  -d '{
    "question": "What is anticipatory bail?",
    "use_llm": false
  }'
```

---

## Project Structure

```
Legal_Research_Assistant/
├── ai_engine/              # AI Engine service (Python/FastAPI)
│   ├── src/
│   │   ├── pipelines/      # Adaptive RAG pipeline
│   │   ├── vectorstore/    # ChromaDB client
│   │   ├── graph/          # Neo4j client
│   │   ├── llm/            # Ollama integration
│   │   └── routes/         # API endpoints
│   ├── data/               # ChromaDB data
│   └── requirements.txt
│
├── backend/                # Backend service (Node.js/Express)
│   ├── src/
│   │   ├── graphql/        # GraphQL schema & resolvers
│   │   ├── services/        # AI Engine client
│   │   └── routes/          # REST API routes
│   ├── prisma/             # Database schema
│   └── package.json
│
├── frontend/               # Frontend (Next.js)
│   ├── app/                # Next.js app directory
│   ├── components/         # React components
│   ├── lib/                # Utilities & GraphQL client
│   └── package.json
│
├── data_ingestion/          # Data scraping & loading
│   ├── sources/             # Scrapers
│   ├── loaders/             # ChromaDB & Neo4j loaders
│   ├── config/              # Act configurations
│   ├── storage/             # Scraped JSON files
│   └── requirements.txt
│
├── docker/                  # Docker configurations
│   └── docker-compose.yml
│
└── docs/                    # Documentation
    ├── architecture-diagrams/
    └── api-reference/
```

---

## Testing

### Verify Services

```powershell
# AI Engine
curl http://localhost:5000/health

# Backend
curl http://localhost:4000/graphql

# Frontend
curl http://localhost:3000
```

### Verify Data

```powershell
# Check ChromaDB
cd ai_engine
python -c "from vectorstore.chroma_client import ChromaClient; from config import settings; c = ChromaClient(settings.CHROMA_DB_PATH, settings.CHROMA_COLLECTION_NAME); c.connect(); print(f'Documents: {c.count()}')"

# Check Neo4j
python verify_neo4j_data.py
```

### Test Queries

**IPC Queries:**
- "What is the punishment for murder?"
- "What is Section 302 of IPC?"

**CrPC Queries:**
- "What is anticipatory bail?"
- "When can police arrest without warrant?"

**Evidence Act Queries:**
- "What is burden of proof?"
- "What is estoppel?"

---

## Configuration

### Supported Acts

- **IPC** - Indian Penal Code (11 sections)
- **CrPC** - Code of Criminal Procedure (9 sections)
- **Evidence Act** - Indian Evidence Act (10 sections)
- **Contract Act** - Indian Contract Act (9 sections)
- **CPC** - Code of Civil Procedure (9 sections)
- **Companies Act** - Companies Act 2013 (7 sections)
- **Constitution** - Constitution of India (8 sections)

**Total: 63+ sections across 7 acts**

### LLM Configuration

To enable LLM-powered answers:

1. **Install Ollama:**
   ```powershell
   # Download from https://ollama.ai
   ```

2. **Pull Model:**
   ```powershell
   ollama pull llama3.2:3b
   ```

3. **Enable in Query:**
   - Frontend: Check "Use LLM" checkbox
   - GraphQL: Set `use_llm: true`
   - API: Set `use_llm: true` in request

---

## Documentation

- **[Data Ingestion Guide](data_ingestion/README.md)** - Scraping and loading data
- **[End-to-End Testing](data_ingestion/END_TO_END_TESTING.md)** - Complete testing guide
- **[Start Services](START_ALL_SERVICES.md)** - Service startup instructions
- **[Neo4j Loader](data_ingestion/loaders/NEO4J_LOADER_README.md)** - Graph data loading
- **[LLM Guide](ENABLE_LLM_GUIDE.md)** - Enabling Ollama LLM
- **[AI Engine README](ai_engine/README.md)** - AI Engine documentation
- **[Frontend README](frontend/README.md)** - Frontend documentation

---

## Development Status

### Completed
- [x] Backend API (GraphQL + REST)
- [x] AI Engine with Adaptive RAG Pipeline
- [x] Frontend application (Next.js)
- [x] Multi-act data scraping
- [x] ChromaDB integration
- [x] Neo4j knowledge graph integration
- [x] User authentication
- [x] LLM integration (Ollama)

### In Progress
- [ ] Additional acts (GST Act, Income Tax Act)
- [ ] Court judgments scraping
- [ ] Law Commission reports
- [ ] Advanced graph relationships

### Planned
- [ ] Search history
- [ ] Saved searches
- [ ] Export results
- [ ] Admin dashboard
- [ ] Performance optimization

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **IndiaCode** - Source for legal acts and sections
- **ChromaDB** - Vector database for embeddings
- **Neo4j** - Knowledge graph database
- **Ollama** - Local LLM integration
- **Sentence Transformers** - Embedding models

---

## Support

For issues, questions, or contributions:
- **GitHub Issues:** [Create an issue](https://github.com/dhinakaran311/Legal_Research_Assistant/issues)
- **Documentation:** See `docs/` directory for detailed guides

---

## Roadmap

- [ ] Expand to 20+ Indian Acts
- [ ] Add 500+ sections
- [ ] Integrate court judgments
- [ ] Add case law analysis
- [ ] Implement citation network
- [ ] Add multi-language support
- [ ] Deploy to production

---

**Built with love for the Indian legal community**
