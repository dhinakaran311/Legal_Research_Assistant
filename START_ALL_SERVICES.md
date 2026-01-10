# 🚀 Start All Services Guide

This guide shows you how to start all services needed for the Legal Research Assistant.

## 📋 Services Required

1. **PostgreSQL** - Database (if using Docker)
2. **Neo4j** - Graph Database (if using Docker)
3. **ChromaDB** - Vector Database (if using Docker)
4. **Backend** (Node.js) - Port 4000
5. **AI Engine** (Python FastAPI) - Port 5000
6. **Frontend** (Next.js) - Port 3000

---

## 🎯 Quick Start (3 Terminal Windows)

### **Terminal 1: Start AI Engine**

```powershell
cd ai_engine

# Activate virtual environment
.\.ven\Scripts\Activate

# Set PYTHONPATH and start server
$env:PYTHONPATH = "src"
python -m uvicorn src.main:app --host 0.0.0.0 --port 5000 --reload
```

**Or use the startup script:**
```powershell
cd ai_engine
.\start_server.ps1
```

**Verify it's running:**
- Open http://localhost:5000/health in browser
- Should see: `{"status":"healthy","service":"ai-engine","version":"2.1.0","environment":"development"}`

---

### **Terminal 2: Start Backend**

```powershell
cd backend
npm run dev
```

**Verify it's running:**
- Open http://localhost:4000/graphql in browser
- Should see GraphQL Playground interface

---

### **Terminal 3: Start Frontend**

```powershell
cd frontend
npm run dev
```

**Verify it's running:**
- Open http://localhost:3000 in browser
- Should see login page

---

## 🔧 Environment Setup

### **1. AI Engine Environment Variables**

Create `ai_engine/.env` file:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=5000
API_RELOAD=True

# Database Configuration
CHROMA_DB_PATH=./data/chromadb
CHROMA_COLLECTION_NAME=legal_documents
MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

# Internal API Security
INTERNAL_API_KEY=your-secret-api-key-here

# Application Settings
DEBUG=True
LOG_LEVEL=INFO
```

**Important:** Set `INTERNAL_API_KEY` to a secret value (e.g., `legal-ai-secret-key-2024`)

---

### **2. Backend Environment Variables**

Create `backend/.env` file:

```env
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/legal_assistant

# AI Engine
AI_ENGINE_URL=http://localhost:5000
INTERNAL_API_KEY=your-secret-api-key-here

# Server
PORT=4000
NODE_ENV=development

# JWT Secret (for authentication)
JWT_SECRET=your-jwt-secret-key-here
```

**Important:** 
- Set `INTERNAL_API_KEY` to the **same value** as in AI Engine `.env`
- Set `DATABASE_URL` with your PostgreSQL credentials

---

### **3. Frontend Environment Variables**

Create `frontend/.env.local` file:

```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:4000
NEXT_PUBLIC_GRAPHQL_URL=http://localhost:4000/graphql
```

---

## ✅ Verification Checklist

Before testing the search, verify all services:

- [ ] **AI Engine Running**
  - URL: http://localhost:5000/health
  - Expected: `{"status":"healthy"}`

- [ ] **Backend Running**
  - URL: http://localhost:4000/graphql
  - Expected: GraphQL Playground opens

- [ ] **Frontend Running**
  - URL: http://localhost:3000
  - Expected: Login page appears

- [ ] **Environment Variables Set**
  - [ ] AI Engine `.env` file exists with `INTERNAL_API_KEY`
  - [ ] Backend `.env` file exists with same `INTERNAL_API_KEY`
  - [ ] Frontend `.env.local` file exists

---

## 🐛 Troubleshooting

### **Error: "AI Engine is not running"**

**Solution:**
1. Check if AI Engine is running on port 5000:
   ```powershell
   # Test health endpoint
   curl http://localhost:5000/health
   ```

2. Check AI Engine terminal for errors

3. Verify PYTHONPATH is set:
   ```powershell
   cd ai_engine
   $env:PYTHONPATH = "src"
   python -m uvicorn src.main:app --host 0.0.0.0 --port 5000 --reload
   ```

### **Error: "AI Engine authentication failed"**

**Solution:**
1. Check `INTERNAL_API_KEY` in both:
   - `ai_engine/.env`
   - `backend/.env`

2. Make sure they match exactly

3. Restart both services after changing `.env` files

### **Error: "Cannot connect to database"**

**Solution:**
1. Start PostgreSQL (if using Docker):
   ```powershell
   cd docker
   docker-compose up postgres -d
   ```

2. Check DATABASE_URL in `backend/.env`

3. Run Prisma migrations:
   ```powershell
   cd backend
   npx prisma migrate dev
   ```

### **Error: "Port already in use"**

**Solution:**
1. Find what's using the port:
   ```powershell
   # For port 5000
   netstat -ano | findstr :5000
   ```

2. Stop the process or use a different port

---

## 🎯 Testing the Search

Once all services are running:

1. **Open Frontend:** http://localhost:3000
2. **Login/Signup:** Create an account or login
3. **Search:** Enter "What is the punishment for murder?"
4. **Check Results:** Should see answer with sources

---

## 📝 Service URLs

| Service | URL | Status Check |
|---------|-----|--------------|
| Frontend | http://localhost:3000 | Login page |
| Backend | http://localhost:4000 | GraphQL Playground |
| AI Engine | http://localhost:5000 | /health endpoint |
| GraphQL | http://localhost:4000/graphql | Playground UI |

---

## 🚀 Quick Start Script (Future)

For convenience, you can create a script to start all services:

```powershell
# start-all.ps1 (create in project root)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd ai_engine; .\start_server.ps1"
Start-Sleep -Seconds 3
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; npm run dev"
Start-Sleep -Seconds 3
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"
```

---

**Status:** ✅ All services ready to start!
