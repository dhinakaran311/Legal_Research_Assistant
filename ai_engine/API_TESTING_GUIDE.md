# API Testing Guide for Adaptive RAG

## 🚀 Quick Start

### 1. Start the FastAPI Server

```bash
cd ai_engine/src
python main.py
```

The server will start at: `http://localhost:5000`

### 2. Test with Python Script

```bash
cd ai_engine
python test_adaptive_api.py
```

### 3. Test with curl

```bash
# Test status
curl http://localhost:5000/api/adaptive-status

# Test query
curl -X POST http://localhost:5000/api/adaptive-query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the punishment for murder?"}'
```

---

## 📡 API Endpoints

### **POST /api/adaptive-query**

Process a legal query using the Adaptive RAG Pipeline.

**Request:**
```json
{
  "question": "What is anticipatory bail?",
  "max_docs": 5  // Optional: override adaptive retrieval
}
```

**Response:**
```json
{
  "question": "What is anticipatory bail?",
  "intent": "definitional",
  "intent_confidence": 0.85,
  "answer": "Based on legal documents...",
  "sources": [
    {
      "id": "doc_id",
      "title": "Section 438 CrPC",
      "excerpt": "...",
      "relevance_score": 0.92,
      "metadata": {"act": "CrPC", "section": "438"},
      "rank": 1
    }
  ],
  "documents_used": 2,
  "retrieval_strategy": {
    "num_documents_requested": 2,
    "min_relevance_threshold": 0.5,
    "num_documents_returned": 2,
    "intent_reasoning": "Matched pattern: what is"
  },
  "confidence": 0.88,
  "processing_time_ms": 245.67,
  "metadata": {
    "intent": "definitional",
    "intent_confidence": 0.85,
    "keywords_matched": ["what is"]
  }
}
```

### **GET /api/adaptive-status**

Get the status of the Adaptive RAG Pipeline.

**Response:**
```json
{
  "status": "operational",
  "version": "2.3.0",
  "pipeline": {
    "name": "Adaptive RAG",
    "intents_supported": [
      "definitional", "factual", "procedural",
      "comparative", "temporal", "exploratory", "unknown"
    ],
    "adaptive_retrieval_range": "2-10 documents",
    "confidence_based_thresholds": true
  },
  "database": {
    "chroma_documents": 5,
    "collection": "legal_documents",
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
  },
  "message": "Adaptive RAG Pipeline ready with 5 legal documents."
}
```

---

## 🧪 Test Examples

### Example 1: Definitional Query (2-3 docs)
```bash
curl -X POST http://localhost:5000/api/adaptive-query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is cheating under IPC?"}'
```

**Expected:** `documents_used: 2-3`

### Example 2: Factual Query (2-4 docs)
```bash
curl -X POST http://localhost:5000/api/adaptive-query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the punishment for murder?"}'
```

**Expected:** `documents_used: 2-4`

### Example 3: Procedural Query (3-5 docs)
```bash
curl -X POST http://localhost:5000/api/adaptive-query \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I file an FIR?"}'
```

**Expected:** `documents_used: 3-5`

### Example 4: Comparative Query (4-7 docs)
```bash
curl -X POST http://localhost:5000/api/adaptive-query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the difference between bail and anticipatory bail?"}'
```

**Expected:** `documents_used: 4-7`

### Example 5: Exploratory Query (6-10 docs)
```bash
curl -X POST http://localhost:5000/api/adaptive-query \
  -H "Content-Type: application/json" \
  -d '{"question": "Tell me about criminal procedure in India"}'
```

**Expected:** `documents_used: 6-10`

---

## 🎯 Verifying Adaptive Behavior

To confirm the pipeline is adaptive:

1. **Test multiple query types** (definitional, factual, procedural, etc.)
2. **Check `documents_used` varies** based on intent
3. **Verify `retrieval_strategy`** matches intent

Example verification:
```python
# Definitional: documents_used = 2
# Procedural: documents_used = 4
# Exploratory: documents_used = 8

# ✅ Adaptive behavior confirmed!
```

---

## 📊 Interactive Testing with Swagger UI

FastAPI automatically generates interactive docs:

**Open in browser:**
```
http://localhost:5000/docs
```

Features:
- ✅ Try queries directly in browser
- ✅ See request/response schemas
- ✅ No need for curl/Postman

---

## 🐛 Troubleshooting

### Server won't start
```bash
# Check if port 5000 is in use
netstat -ano | findstr :5000

# Kill process or change port in config.py
```

### Import errors
```bash
# Make sure you're in the virtual environment
.ven\Scripts\activate

# Check dependencies
pip install -r requirements.txt
```

### No documents found
```bash
# Load sample data
cd ai_engine
python load_sample_data.py
```

---

## 📝 Legacy Endpoint

The old `/api/query` endpoint still works for backwards compatibility.

**Difference:**
- `/api/query` - Fixed retrieval (always 5 docs)
- `/api/adaptive-query` - Adaptive retrieval (2-10 docs based on intent)

---

## ✅ Success Criteria

Your API is working correctly if:

1. ✅ `/api/adaptive-status` returns "operational"
2. ✅ Different intents retrieve different document counts
3. ✅ Intent detection accuracy ≥ 80%
4. ✅ Confidence scores are reasonable (0.3-0.9)
5. ✅ Processing time < 500ms (after model warmup)

---

**Ready to test!** 🚀
