# 🚀 Deployment Guide — Legal Research Assistant

Deploy all 3 services for **FREE** using Vercel + Render + Neon + Neo4j AuraDB.

```
┌──────────────────┐     ┌──────────────────────┐     ┌──────────────────────┐
│   Vercel (Free)  │────▶│   Render (Free)      │────▶│   Render (Free)      │
│   Frontend       │     │   Backend            │     │   AI Engine          │
│   Next.js        │     │   Node.js/Express    │     │   Python/FastAPI     │
│   Port: auto     │     │   Port: auto         │     │   Port: auto         │
└──────────────────┘     └────────┬─────────────┘     └────────┬─────────────┘
                                  │                            │
                         ┌────────▼─────────────┐    ┌────────▼──────────────┐
                         │  Neon (Free)         │    │  Neo4j AuraDB (Free)  │
                         │  PostgreSQL 15       │    │  Knowledge Graph      │
                         │  500MB free          │    │  + ChromaDB (local)   │
                         └──────────────────────┘    └───────────────────────┘
```

---

## Prerequisites

Before starting, generate your secrets. Run these in PowerShell:

```powershell
# Generate JWT_SECRET (copy the output)
node -e "console.log(require('crypto').randomBytes(64).toString('hex'))"

# Generate INTERNAL_API_KEY (copy the output)
node -e "console.log(require('crypto').randomBytes(32).toString('base64url'))"
```

**Save both values — you'll need them in Steps 3 and 4.**

---

## Step 1: PostgreSQL Database — Neon

1. Go to **[neon.tech](https://neon.tech)** → Sign up (GitHub login works)
2. Create a new project — Neon will auto-create a database called `neondb`
3. Or use the CLI: `npx neonctl@latest init`
4. Once created, go to your **Dashboard → Connection Details**
5. **Copy the connection string** — it looks like:
   ```
   postgresql://neondb_owner:abc123@ep-cool-name-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
6. **(Optional)** To rename the database to `lsa_db`, go to **Databases** tab → Create new database `lsa_db`, then update the connection string to end with `/lsa_db?sslmode=require`

> ✅ Save this as your `DATABASE_URL`

---

## Step 2: Neo4j — AuraDB (You Already Have This)

You already have a Neo4j AuraDB instance. Your credentials:
```
URI:      neo4j+s://6db506f2.databases.neo4j.io
Username: neo4j
Password: <your_existing_password>
```

If you need a new one: [neo4j.com/cloud/aura-free](https://neo4j.com/cloud/aura-free/) → Create free instance

---

## Step 3: AI Engine — Render

1. Go to **[render.com](https://render.com)** → Sign up → **Connect your GitHub**
2. Click **"New +"** → **"Web Service"**
3. Select your **`Legal_Research_Assistant`** repository
4. Configure the service:

| Setting | Value |
|---------|-------|
| **Name** | `legal-ai-engine` |
| **Region** | Oregon (US West) or closest |
| **Root Directory** | `ai_engine` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn src.main:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | `Free` |
5. **Click "Advanced" → "Add Environment Variable"** and add **ALL** of these:

| Key | Value | Notes |
|-----|-------|-------|
| `API_HOST` | `0.0.0.0` | Required |
| `API_PORT` | `5000` | Required |
| `CHROMA_DB_PATH` | `./data/chromadb` | Local ChromaDB storage |
| `CHROMA_COLLECTION_NAME` | `legal_documents` | Collection name |
| `MODEL_NAME` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model |
| `NEO4J_URI` | `neo4j+s://6db506f2.databases.neo4j.io` | Your AuraDB URI |
| `NEO4J_USERNAME` | `neo4j` | AuraDB username |
| `NEO4J_PASSWORD` | `<your_neo4j_password>` | AuraDB password |
| `INTERNAL_API_KEY` | `<paste_your_generated_key>` | 🔑 From prerequisites |
| `GEMINI_API_KEY` | `<your_gemini_api_key>` | 🔑 Google Gemini API key |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model name |
| `DEBUG` | `False` | Production mode |
| `LOG_LEVEL` | `INFO` | Logging level |
| `PYTHONPATH` | `src` | Required for imports |

6. Click **"Create Web Service"**
7. Wait for deploy → **Copy the URL** (e.g., `https://legal-ai-engine.onrender.com`)

> ✅ Save this URL as your `AI_ENGINE_URL`

---

## Step 4: Backend — Render

1. In Render → **"New +"** → **"Web Service"**
2. Select same **`Legal_Research_Assistant`** repository
3. Configure:

| Setting | Value |
|---------|-------|
| **Name** | `legal-backend` |
| **Region** | Same region as AI Engine |
| **Root Directory** | `backend` |
| **Runtime** | `Node` |
| **Build Command** | `npm ci && npx prisma generate && npx prisma migrate deploy` |
| **Start Command** | `npm start` |
| **Instance Type** | `Free` |

4. **Click "Advanced" → "Add Environment Variable"** and add **ALL** of these:

| Key | Value | Notes |
|-----|-------|-------|
| `DATABASE_URL` | `postgresql://user:pass@ep-xxx.neon.tech/lsa_db?sslmode=require` | 🔑 From Step 1 (Neon) |
| `AI_ENGINE_URL` | `https://legal-ai-engine.onrender.com` | 🔑 From Step 3 |
| `INTERNAL_API_KEY` | `<same_key_as_ai_engine>` | 🔑 **MUST match AI Engine's key exactly** |
| `PORT` | `4000` | Server port |
| `NODE_ENV` | `production` | Production mode |
| `JWT_SECRET` | `<paste_your_64_char_hex>` | 🔑 From prerequisites — **this signs all login tokens** |
| `JWT_EXPIRES_IN` | `7d` | Token valid for 7 days |

5. Click **"Create Web Service"**
6. Wait for deploy → **Copy the URL** (e.g., `https://legal-backend.onrender.com`)

> ✅ Save this URL as your `BACKEND_URL`

### ⚠️ Critical Notes on JWT_SECRET
- This key **signs and verifies all user login tokens**
- If you change it after deployment, **all existing users get logged out**
- **Never** commit it to GitHub — only set it in Render's environment variables
- Use the 128-character hex string generated in the Prerequisites step

---

## Step 5: Frontend — Vercel

1. Go to **[vercel.com](https://vercel.com)** → Sign up with GitHub
2. Click **"Add New Project"** → Import **`Legal_Research_Assistant`**
3. Configure:

| Setting | Value |
|---------|-------|
| **Framework Preset** | Next.js (auto-detected) |
| **Root Directory** | `frontend` |
| **Build Command** | `npm run build` (default) |
| **Output Directory** | `.next` (default) |

4. **Expand "Environment Variables"** and add:

| Key | Value | Notes |
|-----|-------|-------|
| `NEXT_PUBLIC_BACKEND_URL` | `https://legal-backend.onrender.com` | 🔑 From Step 4 |
| `NEXT_PUBLIC_GRAPHQL_URL` | `https://legal-backend.onrender.com/graphql` | 🔑 Same backend + `/graphql` |

5. Click **"Deploy"**
6. Your app is live! (e.g., `https://legal-research-assistant.vercel.app`)

---

## Step 6: Load Data into Databases

After all services are deployed, load your legal data from your **local machine**:

### Load Neo4j Data (One-Time)
```powershell
cd data_ingestion

# Activate Python environment
..\ai_engine\.ven\Scripts\Activate

# Set Neo4j credentials
$env:NEO4J_URI = "neo4j+s://6db506f2.databases.neo4j.io"
$env:NEO4J_USERNAME = "neo4j"
$env:NEO4J_PASSWORD = "<your_password>"

# Scrape legal documents (skip if already scraped)
python sources/multi_act_scraper.py

# Load into Neo4j AuraDB
python loaders/load_multi_act_to_neo4j.py
```

### Load ChromaDB Data
ChromaDB runs locally on the AI Engine server. You need to trigger data loading via the deployed service:

```powershell
# SSH into Render or use Render's shell:
# Render Dashboard → legal-ai-engine → Shell tab
cd /app
python load_sample_data.py
```

> If you already loaded data into Neo4j locally, it's already in AuraDB (cloud) — no extra steps needed.

---

## Step 7: Verify Deployment

### Test Each Service

```powershell
# 1. AI Engine health check
curl https://legal-ai-engine.onrender.com/health

# 2. Backend GraphQL
curl https://legal-backend.onrender.com/graphql

# 3. Frontend
# Open in browser: https://your-app.vercel.app
```

### Test the Full Flow

1. Open your Vercel URL → You'll see the **Login page**
2. Click **"Sign up"** → Create account with name, email, password
3. You'll be redirected to **Search page**
4. Try: **"What is the punishment for murder?"**
5. If you get results → ✅ **Deployment is complete!**

---

## Complete Environment Variables Summary

### Where Each Secret Goes

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SECRET                    WHERE TO ADD IT        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  JWT_SECRET ──────────────────────────▶ Render (Backend only)       │
│  (signs login tokens)                    ENV: JWT_SECRET            │
│                                                                     │
│  INTERNAL_API_KEY ────────────────────▶ Render (Backend)            │
│  (Backend ↔ AI Engine auth)          AND Render (AI Engine)         │
│  ⚠️ MUST be identical in both!          ENV: INTERNAL_API_KEY      │
│                                                                     │
│  DATABASE_URL ────────────────────────▶ Render (Backend only)       │
│  (PostgreSQL connection)                 ENV: DATABASE_URL          │
│                                                                     │
│  NEO4J_PASSWORD ──────────────────────▶ Render (AI Engine only)     │
│  (Graph database)                        ENV: NEO4J_PASSWORD        │
│                                                                     │
│  NEXT_PUBLIC_BACKEND_URL ─────────────▶ Vercel (Frontend only)      │
│  (API endpoint)                          ENV: NEXT_PUBLIC_BACKEND_URL│
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### ⚡ Quick Copy-Paste Checklist

**Render → AI Engine (11 env vars):**
```env
API_HOST=0.0.0.0
API_PORT=5000
CHROMA_DB_PATH=./data/chromadb
CHROMA_COLLECTION_NAME=legal_documents
MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
NEO4J_URI=neo4j+s://6db506f2.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=<your_neo4j_password>
INTERNAL_API_KEY=<your_generated_api_key>
GEMINI_API_KEY=<your_gemini_api_key>
GEMINI_MODEL=gemini-2.0-flash
DEBUG=False
LOG_LEVEL=INFO
```

**Render → Backend (7 env vars):**
```env
DATABASE_URL=<your_neon_connection_string>
AI_ENGINE_URL=https://legal-ai-engine.onrender.com
INTERNAL_API_KEY=<same_key_as_ai_engine>
PORT=4000
NODE_ENV=production
JWT_SECRET=<your_generated_64_char_hex>
JWT_EXPIRES_IN=7d
```

**Vercel → Frontend (2 env vars):**
```env
NEXT_PUBLIC_BACKEND_URL=https://legal-backend.onrender.com
NEXT_PUBLIC_GRAPHQL_URL=https://legal-backend.onrender.com/graphql
```

---

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Login fails / "Not authorized" | `JWT_SECRET` not set on Render Backend | Add `JWT_SECRET` env var in Render |
| Search returns no results | AI Engine has no data | Load ChromaDB data via Render Shell |
| "Internal Server Error" on search | `INTERNAL_API_KEY` mismatch | Ensure **same key** in both Backend and AI Engine |
| CORS errors in browser | Backend doesn't allow frontend origin | Add frontend Vercel URL to CORS whitelist in `backend/src/index.js` |
| Database connection error | Wrong `DATABASE_URL` | Copy exact string from Neon dashboard (include `?sslmode=require`) |
| AI Engine timeout (30s+) | Render free tier cold start | Normal — first request takes ~30s after inactivity |
| Neo4j connection failed | Using `bolt://` instead of `neo4j+s://` | AuraDB requires `neo4j+s://` protocol |
| Frontend shows blank page | Env vars not prefixed with `NEXT_PUBLIC_` | Must use `NEXT_PUBLIC_BACKEND_URL` (not `BACKEND_URL`) |

---

## Cost Summary

| Service | Platform | Cost |
|---------|----------|------|
| Frontend | Vercel | **Free** (100GB bandwidth/mo) |
| Backend | Render | **Free** (750 hrs/mo, sleeps after 15min) |
| AI Engine | Render | **Free** (750 hrs/mo, sleeps after 15min) |
| PostgreSQL | Neon | **Free** (500MB, 100 hrs compute/mo) |
| Neo4j | AuraDB | **Free** (200K nodes, 400K relationships) |
| **Total** | | **$0/month** |

---

**Built with ❤️ for the Indian legal community**
