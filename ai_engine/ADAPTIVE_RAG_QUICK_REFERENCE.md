# 📊 Adaptive RAG Pipeline - Quick Reference

## 🔄 Pipeline Flow

```
User Query
    ↓
┌──────────────────────────────────────┐
│  STAGE 1: DETECT INTENT              │
│  - Analyze keywords                  │
│  - Match to 7 intent types           │
│  - Calculate confidence (0-1)        │
└──────────────────────────────────────┘
    ↓
┌──────────────────────────────────────┐
│  STAGE 2: DECIDE STRATEGY            │
│  - Map intent → doc count (2-10)     │
│  - Set relevance threshold           │
│  - Apply confidence adjustments      │
└──────────────────────────────────────┘
    ↓
┌──────────────────────────────────────┐
│  STAGE 3: RETRIEVE CONTEXT           │
│  - Query ChromaDB vector store       │
│  - Get N documents                   │
│  - Filter by relevance threshold     │
│  - Convert distances to scores       │
└──────────────────────────────────────┘
    ↓
┌──────────────────────────────────────┐
│  STAGE 4: GENERATE ANSWER            │
│  - Build intent-specific answer      │
│  - Structure sources with metadata   │
│  - Calculate overall confidence      │
│  - Return structured JSON            │
└──────────────────────────────────────┘
    ↓
Structured PipelineResult
```

## 🎯 Intent Types & Retrieval Counts

| Intent | Docs | Example |
|--------|------|---------|
| 🔤 **Definitional** | 2-3 | "What is X?" |
| 📌 **Factual** | 2-4 | "What is the punishment for X?" |
| 📝 **Procedural** | 3-5 | "How do I file X?" |
| ⚖️ **Comparative** | 4-7 | "Difference between X and Y?" |
| ⏰ **Temporal** | 2-4 | "When should I X?" |
| 🔍 **Exploratory** | 6-10 | "Tell me about X" |
| ❓ **Unknown** | 3-5 | Default strategy |

## 📈 Adaptive Logic

```
High Confidence (≥0.8)
    → Use MINIMUM docs
    → Threshold: 0.5
    → Focused search
    
Medium Confidence (0.6-0.8)
    → Use MIDDLE range
    → Threshold: 0.4
    → Balanced search
    
Low Confidence (<0.6)
    → Use MAXIMUM docs
    → Threshold: 0.3
    → Broad search
```

## 🔑 Key Classes

```python
# Intent Analysis Result
IntentAnalysis(
    intent: QueryIntent,
    confidence: float,
    reasoning: str,
    keywords_matched: List[str]
)

# Retrieval Strategy
RetrievalStrategy(
    num_documents: int,
    min_relevance_threshold: float,
    use_metadata_filter: bool,
    metadata_filter: Optional[Dict]
)

# Final Result
PipelineResult(
    question: str,
    intent: QueryIntent,
    intent_confidence: float,
    answer: str,
    sources: List[Dict],
    num_sources_retrieved: int,
    retrieval_strategy: Dict,
    confidence: float,
    processing_time_ms: float,
    metadata: Dict
)
```

## ⚡ Quick Start

```python
from pipelines.adaptive_rag import AdaptiveRAGPipeline

# Initialize
pipeline = AdaptiveRAGPipeline()

# Process query
result = pipeline.process_query("What is the punishment for murder?")

# Use results
print(f"Intent: {result.intent}")              # factual
print(f"Docs: {len(result.sources)}")          # 2-4
print(f"Confidence: {result.confidence}")       # 0.XX
print(f"Answer: {result.answer}")               # Structured answer
```

## 🧪 Testing

```bash
cd ai_engine
python test_adaptive_pipeline.py
```

## 📁 Files

```
ai_engine/src/pipelines/
├── __init__.py
└── adaptive_rag.py (650+ lines)

ai_engine/
├── test_adaptive_pipeline.py
└── ADAPTIVE_RAG_PIPELINE.md
```

## ✅ Module 2.3 Complete!

**Implemented:**
- ✅ 4-stage adaptive pipeline
- ✅ 7 intent types with keyword detection
- ✅ Dynamic retrieval (2-10 docs based on intent)
- ✅ Confidence-based thresholds
- ✅ Intent-specific answer generation
- ✅ Structured JSON output
- ✅ Comprehensive test suite
- ✅ Full documentation

**Next Steps:**
- Integrate with FastAPI endpoint `/api/adaptive-query`
- Add request/response models
- Deploy and test with real queries
