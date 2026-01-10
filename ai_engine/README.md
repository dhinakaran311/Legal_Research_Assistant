# Legal AI Engine 🤖

AI microservice for legal research and retrieval, built with FastAPI.

## 📋 Overview

This is the AI Engine component of the Legal Research Assistant project. It handles:
- Legal question understanding
- Document retrieval from vector database (ChromaDB)
- Graph-based verification (Neo4j)
- Grounded, explainable responses

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd ai_engine
pip install -r requirements.txt
```

### 2. Configure Environment

Edit the `.env` file with your settings:
- API port (default: 5000)
- Database credentials
- Model configuration

### 3. Run the Server

**Option 1: Using PowerShell script (Recommended for Windows):**
```powershell
.\start_server.ps1
```

**Option 2: Using batch file:**
```cmd
start_server.bat
```

**Option 3: Manual start (from ai_engine directory):**
```powershell
# Set PYTHONPATH and run
$env:PYTHONPATH = "src"
uvicorn src.main:app --host 0.0.0.0 --port 5000 --reload
```

**Option 4: Run from src directory:**
```bash
cd src
uvicorn main:app --host 0.0.0.0 --port 5000 --reload
```

## 📡 API Endpoints

### Health Check
```
GET /health
```
Returns the health status of the AI engine.

### Root
```
GET /
```
Basic information and links to documentation.

### Query Processing
```
POST /api/query
```
Process a legal question and retrieve relevant information.

**Request Body:**
```json
{
  "question": "What are the requirements for a valid contract?",
  "max_results": 5,
  "include_graph": true
}
```

**Response:**
```json
{
  "question": "What are the requirements for a valid contract?",
  "answer": "...",
  "sources": [...],
  "confidence": 0.85,
  "processing_time_ms": 245.5
}
```

### Status
```
GET /api/status
```
Get current status of AI engine modules.

## 📁 Project Structure

```
ai_engine/
├── src/
│   ├── main.py           # FastAPI application
│   ├── config.py         # Configuration management
│   └── routes/
│       └── query.py      # Query endpoints
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables
└── README.md            # This file
```

## 🧪 Testing

Access the interactive API documentation:
- **Swagger UI**: http://localhost:5000/docs
- **ReDoc**: http://localhost:5000/redoc

### Test Health Endpoint
```bash
curl http://localhost:5000/health
```

### Test Query Endpoint
```bash
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is contract law?"}'
```

## 🔧 Configuration

Key environment variables in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `API_PORT` | Server port | 5000 |
| `API_HOST` | Server host | 0.0.0.0 |
| `DEBUG` | Debug mode | True |
| `MODEL_NAME` | Embedding model | all-MiniLM-L6-v2 |
| `CHROMA_DB_PATH` | ChromaDB storage path | ./data/chromadb |
| `NEO4J_URI` | Neo4j connection URI | bolt://localhost:7687 |

## 📦 Current Status

✅ **Module 2.1 - AI Engine Base** (Complete)
- FastAPI application setup
- Health endpoint
- Query endpoint structure
- Environment configuration

⏳ **Upcoming Modules**
- 2.2 - ChromaDB Integration
- 2.3 - Neo4j Graph Integration
- 2.4 - LangChain Integration
- 2.5 - Full AI Pipeline

## 🔗 Integration with Backend

The Node.js backend can communicate with this AI engine:

```javascript
// Example backend integration
const response = await fetch('http://localhost:5000/api/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    question: userQuestion,
    max_results: 5
  })
});

const result = await response.json();
```

## 📝 Notes

- Current `/api/query` endpoint returns dummy data
- AI logic will be implemented in subsequent modules
- Database connections are configured but not yet utilized

## 🛠️ Tech Stack

- **FastAPI** - Modern Python web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation
- **python-dotenv** - Environment management

---

**Phase**: 2.1 - AI Engine Base  
**Status**: ✅ Complete  
**Next**: Module 2.2 - ChromaDB Integration
