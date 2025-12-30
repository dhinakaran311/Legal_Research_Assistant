# Adaptive RAG Pipeline - Module 2.3

## 📖 Overview

The Adaptive RAG Pipeline is an intelligent retrieval system that dynamically adjusts how many legal documents it retrieves based on the **intent** of your question.

Instead of always fetching 5 documents, it:
1. **Detects** what kind of question you're asking
2. **Decides** how many documents you need
3. **Retrieves** only what's necessary
4. **Generates** a focused, structured answer

---

## 🎯 How It Works: The 4 Stages

### **Stage 1: Detect Intent** 🔍

The pipeline analyzes your query to understand what you're looking for:

| Intent Type | Description | Example Query |
|-------------|-------------|---------------|
| **Definitional** | You want a definition | "What is cheating under IPC?" |
| **Factual** | You want specific facts | "What is the punishment for murder?" |
| **Procedural** | You want to know how to do something | "How do I file an FIR?" |
| **Comparative** | You want to compare things | "What's the difference between murder and culpable homicide?" |
| **Temporal** | You want timing information | "When should I file a complaint?" |
| **Exploratory** | You want comprehensive info | "Tell me about contract law" |
| **Unknown** | Intent unclear | Uses default strategy |

**How Detection Works:**
- Keyword pattern matching (fast and efficient)
- Confidence scoring (0.0 - 1.0)
- Top matched keywords tracked for transparency

### **Stage 2: Decide Retrieval Strategy** 📊

Based on the detected intent and confidence, the pipeline decides:

| Intent | Documents Retrieved | Min Relevance | Reasoning |
|--------|-------------------|---------------|-----------|
| **Definitional** | 2-3 docs | 0.5 | Definitions are usually in 1-2 sources |
| **Factual** | 2-4 docs | 0.5 | Facts are specific, need few sources |
| **Procedural** | 3-5 docs | 0.4 | Procedures need step-by-step context |
| **Comparative** | 4-7 docs | 0.4 | Comparisons need multiple perspectives |
| **Temporal** | 2-4 docs | 0.5 | Timing info is usually specific |
| **Exploratory** | 6-10 docs | 0.3 | Broad topics need comprehensive coverage |
| **Unknown** | 3-5 docs | 0.4 | Default moderate approach |

**Adaptive Threshold:**
- High intent confidence (≥0.8) → Use minimum docs (focused)
- Medium confidence (0.6-0.8) → Use middle range
- Low confidence (<0.6) → Use maximum docs (broader search)

### **Stage 3: Retrieve Context** 📚

The pipeline:
1. Queries ChromaDB with your question
2. Retrieves the number of documents determined in Stage 2
3. Filters by minimum relevance threshold
4. Converts distance scores to relevance scores (0-1)
5. Keeps at least 1 document even if all are below threshold

**Relevance Scoring:**
- ChromaDB returns L2 distance (smaller = better)
- Converted to relevance: `relevance = max(0.0, 1.0 - distance/2.0)`
- Scores range from 0.0 (irrelevant) to 1.0 (perfect match)

### **Stage 4: Generate Answer** 💡

The pipeline generates intent-specific answers:

**Definitional Answers:**
```
Based on [source]:

[Definition excerpt]

Related provisions found in N additional source(s).
```

**Factual Answers:**
```
According to [source], Section X of [Act]:

[Factual information]

N other relevant provision(s) also apply.
```

**Procedural Answers:**
```
**Procedure:**

[Step-by-step excerpt]

**Additional Steps/Requirements:**
Refer to N additional source(s) for complete procedure.
```

**Comparative Answers:**
```
**Comparison based on legal provisions:**

1. [Source 1]:
   [Excerpt]

2. [Source 2]:
   [Excerpt]

*N more provisions available for review.*
```

**Exploratory Answers:**
```
**Comprehensive Overview:**

Found N relevant legal provisions:

1. [Provision 1]
   [Excerpt]

2. [Provision 2]
   [Excerpt]

*N additional provisions available.*
```

---

## 📋 Structured Output

The pipeline returns a comprehensive `PipelineResult`:

```json
{
  "question": "What is the punishment for murder?",
  "intent": "factual",
  "intent_confidence": 0.85,
  "answer": "According to Indian Penal Code, Section 302...",
  "sources": [
    {
      "id": "ipc_section_302",
      "title": "Section 302 - Punishment for murder",
      "excerpt": "Whoever commits murder shall be punished...",
      "relevance_score": 0.92,
      "metadata": {
        "act": "Indian Penal Code",
        "section": "302"
      },
      "rank": 1
    }
  ],
  "num_sources_retrieved": 3,
  "retrieval_strategy": {
    "num_documents_requested": 3,
    "min_relevance_threshold": 0.5,
    "num_documents_returned": 3,
    "intent_reasoning": "Matched 2 pattern(s): punishment, section"
  },
  "confidence": 0.88,
  "processing_time_ms": 245.67,
  "metadata": {
    "intent": "factual",
    "intent_confidence": 0.85,
    "keywords_matched": ["punishment", "section"],
    "documents_before_filtering": 3
  }
}
```

---

## 🚀 Usage Example

```python
from pipelines.adaptive_rag import AdaptiveRAGPipeline

# Initialize pipeline
pipeline = AdaptiveRAGPipeline()

# Process a query
result = pipeline.process_query("What is the punishment for murder?")

# Access results
print(f"Intent: {result.intent}")
print(f"Confidence: {result.confidence}")
print(f"Answer: {result.answer}")
print(f"Sources: {len(result.sources)}")

# See retrieval strategy
print(f"Documents requested: {result.retrieval_strategy['num_documents_requested']}")
print(f"Documents returned: {result.retrieval_strategy['num_documents_returned']}")
```

---

## 🎓 Key Features

### ✅ **Efficiency**
- Only retrieves what's needed (2-10 docs instead of always 5)
- Keyword-based intent detection (fast, no LLM needed)
- Single vector search per query

### ✅ **Quality**
- Intent-specific answer generation
- Confidence-based adaptive thresholds
- Relevance filtering to remove low-quality matches
- Structured JSON output for easy integration

### ✅ **Transparency**
- Reports detected intent and confidence
- Shows matched keywords for debugging
- Tracks retrieval strategy decisions
- Includes processing time metrics

### ✅ **Flexibility**
- 7 intent types covering common legal queries
- Adaptive document counts (2-10 range)
- Optional metadata filtering
- Override parameters supported

---

## 🧪 Testing

Run the test script to verify all stages:

```bash
cd ai_engine
python test_adaptive_pipeline.py
```

This tests:
- ✅ Intent detection accuracy
- ✅ Retrieval strategy decisions
- ✅ Document retrieval and filtering
- ✅ Answer generation for each intent type
- ✅ Processing time and confidence scoring

---

## 📊 Performance Metrics

Expected performance (depends on document count and hardware):

- **Processing Time:** 100-500ms per query
- **Intent Detection Accuracy:** 80-95% (keyword-based)
- **Average Documents Retrieved:** 3-5 (vs always 5 in basic RAG)
- **Confidence Scores:** 0.4-0.9 typical range

---

## 🔧 Configuration

The pipeline adapts based on these configurable parameters:

### Intent Patterns
Edit `intent_patterns` in `adaptive_rag.py` to customize keyword matching.

### Retrieval Counts
Modify `intent_retrieval_map` to change document counts per intent.

### Relevance Thresholds
Adjust in `decide_retrieval_strategy()` method:
- High confidence: 0.5
- Medium confidence: 0.4
- Low confidence: 0.3

---

## 🎯 What's Next?

This Adaptive RAG Pipeline is **Module 2.3 complete!**

Future enhancements could include:
- LLM-based intent detection for higher accuracy
- Graph database integration for relationship queries
- Multi-hop reasoning for complex questions
- Query reformulation for better results
- Caching for frequently asked questions

---

## 📚 Files Created

```
ai_engine/
├── src/
│   └── pipelines/
│       ├── __init__.py
│       └── adaptive_rag.py          # Main pipeline (650+ lines)
└── test_adaptive_pipeline.py        # Comprehensive test suite
```

---

**Module 2.3 Status: ✅ COMPLETE**

The Adaptive RAG Pipeline is ready to be integrated into the FastAPI endpoint!
