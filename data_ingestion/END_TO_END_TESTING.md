# 🧪 End-to-End Testing Guide - Multi-Act System

Complete guide to test the multi-act scraping and loading system with AI Engine, Backend, and Frontend.

## 📋 Prerequisites

Before starting, ensure:
- ✅ Python dependencies installed (`data_ingestion/requirements.txt`)
- ✅ AI Engine dependencies installed (`ai_engine/requirements.txt`)
- ✅ Backend dependencies installed (`backend/package.json`)
- ✅ Frontend dependencies installed (`frontend/package.json`)
- ✅ Environment variables configured (see below)

## 🎯 Step-by-Step Testing

### **Step 1: Prepare Data (Optional)**

If you haven't scraped data yet, do this first:

```powershell
# Navigate to data_ingestion
cd data_ingestion

# Scrape all acts (or specific acts)
python sources/multi_act_scraper.py

# Or scrape specific acts only
python sources/multi_act_scraper.py --acts crpc ipc

# Load scraped data into ChromaDB
python loaders/load_multi_act_data.py

# Or load specific acts
python loaders/load_multi_act_data.py --acts crpc ipc
```

**Expected Output:**
- ✅ JSON files created in `storage/acts/{act_key}/`
- ✅ Documents loaded into ChromaDB
- ✅ Success message with document count

**Note:** If you already have data loaded, you can skip this step.

---

### **Step 2: Verify Environment Variables**

Ensure these files exist and are configured:

#### **AI Engine** (`ai_engine/.env`):
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

#### **Backend** (`backend/.env`):
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/legal_assistant
AI_ENGINE_URL=http://localhost:5000
INTERNAL_API_KEY=legal-ai-secret-key-2024
PORT=4000
NODE_ENV=development
JWT_SECRET=your-jwt-secret-key-here
```

**Important:** `INTERNAL_API_KEY` must be **identical** in both files.

#### **Frontend** (`frontend/.env.local`):
```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:4000
NEXT_PUBLIC_GRAPHQL_URL=http://localhost:4000/graphql
```

---

### **Step 3: Start All Services**

Open **3 separate terminal windows** (PowerShell or Command Prompt):

#### **Terminal 1: AI Engine**

```powershell
cd ai_engine

# Activate virtual environment
.\.ven\Scripts\Activate

# Use startup script (recommended)
.\start_server.ps1

# OR manually:
# $env:PYTHONPATH = "src"
# python -m uvicorn src.main:app --host 0.0.0.0 --port 5000 --reload
```

**Verify:**
- Open http://localhost:5000/health in browser
- Should see: `{"status":"healthy","service":"ai-engine",...}`

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

#### **Terminal 2: Backend**

```powershell
cd backend
npm run dev
```

**Verify:**
- Open http://localhost:4000/graphql in browser
- Should see GraphQL Playground interface

**Expected Output:**
```
Server is running on http://localhost:4000
GraphQL endpoint: http://localhost:4000/graphql
```

---

#### **Terminal 3: Frontend**

```powershell
cd frontend
npm run dev
```

**Verify:**
- Open http://localhost:3000 in browser
- Should see login page

**Expected Output:**
```
▲ Next.js 14.x.x
- Local:        http://localhost:3000
- Ready in X.Xs
```

---

### **Step 4: Test Search Functionality**

Once all services are running:

#### **4.1: Login/Signup**

1. Open http://localhost:3000
2. Click **"Sign Up"** or **"Login"**
3. Create an account or login with existing credentials

#### **4.2: Search Test Queries**

After logging in, try these test queries to verify multi-act data:

**IPC Queries:**
- "What is the punishment for murder?"
- "What is Section 302 of IPC?"
- "What is the definition of cheating under IPC?"

**CrPC Queries:**
- "What is anticipatory bail?"
- "When can police arrest without warrant?"
- "What is Section 438 of CrPC?"

**Evidence Act Queries:**
- "What is burden of proof?"
- "What is estoppel?"
- "What is Section 101 of Evidence Act?"

**Contract Act Queries:**
- "What are the requirements for a valid contract?"
- "What is free consent?"
- "What is Section 10 of Contract Act?"

**Constitution Queries:**
- "What are fundamental rights?"
- "What is Article 21?"
- "What is the right to equality?"

**Cross-Act Queries:**
- "What is bail under criminal law?"
- "What are my rights if arrested?"
- "How to prove a case in court?"

#### **4.3: Verify Search Results**

For each query, check:
- ✅ **Answer:** Should be relevant and accurate
- ✅ **Sources:** Should include relevant sections from appropriate acts
- ✅ **Metadata:** Should show act name (IPC, CrPC, etc.), section number
- ✅ **Graph References:** Should show related sections/cases (if Neo4j configured)
- ✅ **Confidence Score:** Should be displayed

---

### **Step 5: Verify Data in ChromaDB**

To verify data is loaded correctly:

```powershell
# Navigate to ai_engine
cd ai_engine

# Activate virtual environment
.\.ven\Scripts\Activate

# Set PYTHONPATH
$env:PYTHONPATH = "src"

# Run Python to check data
python
```

```python
from vectorstore.chroma_client import ChromaClient
from config import settings

# Connect to ChromaDB
client = ChromaClient(
    persist_directory=settings.CHROMA_DB_PATH,
    collection_name=settings.CHROMA_COLLECTION_NAME,
    embedding_model=settings.MODEL_NAME
)
client.connect()

# Get document count
count = client.count()
print(f"Total documents: {count}")

# Query for IPC documents
results = client.query(
    query_texts=["murder"],
    n_results=5,
    where={"act": "IPC"}
)

print(f"\nIPC documents found: {len(results['ids'][0])}")
for i, doc_id in enumerate(results['ids'][0]):
    print(f"  {i+1}. {doc_id}")

# Query for CrPC documents
results = client.query(
    query_texts=["bail"],
    n_results=5,
    where={"act": "CrPC"}
)

print(f"\nCrPC documents found: {len(results['ids'][0])}")
for i, doc_id in enumerate(results['ids'][0]):
    print(f"  {i+1}. {doc_id}")

# Exit
exit()
```

**Expected Output:**
- Total documents should be > 0 (based on what you loaded)
- IPC queries should return `ipc_section_*` documents
- CrPC queries should return `crpc_section_*` documents

---

### **Step 6: Test via GraphQL Playground**

You can also test directly via GraphQL:

1. Open http://localhost:4000/graphql
2. Paste this query:

```graphql
query SearchTest {
  search(query: "What is anticipatory bail?", use_llm: false) {
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
        category
        subcategory
      }
    }
    graph_references {
      section
      section_title
      act_name
      relationship
    }
    documents_used
    confidence
    processing_time_ms
  }
}
```

3. Click "Play" button
4. Verify results show CrPC Section 438 (Anticipatory Bail)

---

## ✅ Testing Checklist

Use this checklist to verify everything is working:

- [ ] **Data Loaded:**
  - [ ] JSON files exist in `data_ingestion/storage/acts/{act_key}/`
  - [ ] ChromaDB documents loaded successfully
  - [ ] Document count matches expected (check logs)

- [ ] **Services Running:**
  - [ ] AI Engine: http://localhost:5000/health returns healthy
  - [ ] Backend: http://localhost:4000/graphql shows Playground
  - [ ] Frontend: http://localhost:3000 shows login page

- [ ] **Authentication:**
  - [ ] Can sign up new account
  - [ ] Can login with credentials
  - [ ] Redirected to search page after login

- [ ] **Search Functionality:**
  - [ ] IPC queries return IPC sections
  - [ ] CrPC queries return CrPC sections
  - [ ] Evidence Act queries return Evidence sections
  - [ ] Contract Act queries return Contract sections
  - [ ] Constitution queries return Constitution articles
  - [ ] Cross-act queries return relevant results from multiple acts
  - [ ] Sources show correct metadata (act, section, title)
  - [ ] Answer is relevant and accurate

- [ ] **Data Verification:**
  - [ ] ChromaDB query returns documents
  - [ ] Document IDs match pattern: `{act}_section_{number}`
  - [ ] Metadata includes act, section, category, subcategory

---

## 🐛 Troubleshooting

### **Issue: No search results**

**Solutions:**
1. Check if data is loaded in ChromaDB (Step 5)
2. Verify ChromaDB path in `ai_engine/.env` matches actual location
3. Check AI Engine logs for errors
4. Verify collection name is `legal_documents`

### **Issue: Wrong act in results**

**Solutions:**
1. Verify metadata when loading: `python loaders/load_multi_act_data.py`
2. Check ChromaDB metadata: `where={"act": "IPC"}` should return IPC docs
3. Verify document IDs: Should be `{act}_section_{number}`

### **Issue: AI Engine not responding**

**Solutions:**
1. Check AI Engine terminal for errors
2. Verify PYTHONPATH is set: `$env:PYTHONPATH = "src"`
3. Test health endpoint: `curl http://localhost:5000/health`
4. Check if ChromaDB is accessible

### **Issue: Backend can't connect to AI Engine**

**Solutions:**
1. Verify `AI_ENGINE_URL=http://localhost:5000` in `backend/.env`
2. Verify `INTERNAL_API_KEY` matches in both `.env` files
3. Check if AI Engine is running (Terminal 1)
4. Test AI Engine directly: `curl http://localhost:5000/health`

### **Issue: Frontend can't connect to Backend**

**Solutions:**
1. Verify `NEXT_PUBLIC_BACKEND_URL=http://localhost:4000` in `frontend/.env.local`
2. Check if Backend is running (Terminal 2)
3. Test GraphQL endpoint: http://localhost:4000/graphql

---

## 🎉 Success Criteria

You've successfully tested the system if:

1. ✅ All services start without errors
2. ✅ Can login/signup successfully
3. ✅ Search queries return relevant results
4. ✅ Results include sections from multiple acts (IPC, CrPC, etc.)
5. ✅ Sources show correct metadata
6. ✅ Answers are relevant and accurate
7. ✅ ChromaDB contains expected documents

---

## 📝 Next Steps

After successful testing:

1. **Expand Data:** Scrape more sections from each act
2. **Add More Acts:** Add GST Act, Income Tax Act, etc.
3. **Neo4j Integration:** Create graph relationships between sections
4. **Fine-tune Search:** Adjust retrieval parameters for better results
5. **User Feedback:** Collect feedback to improve search quality

---

## 📚 Related Documentation

- **Data Ingestion:** `data_ingestion/README.md`
- **Multi-Act Setup:** `data_ingestion/POPULAR_ACTS.md`
- **Quick Start:** `data_ingestion/QUICK_START.md`
- **Service Startup:** `START_ALL_SERVICES.md`
- **Search Feature:** `frontend/SEARCH_FEATURE.md`

---

**Status:** ✅ Ready for end-to-end testing!
