# AI Engine Optimization Plan

**Date:** January 20, 2026  
**Current Status:** Functional but not optimized  
**Target:** High-performance production system

---

## Current Performance Analysis

### Baseline Metrics
```
Query Processing Time: 200-500ms (without LLM), 2-10s (with LLM)
Memory Usage: ~500 MB (without LLM), ~2 GB (with LLM)
Database Size: 0.85 MB
Document Count: 61 (expected: 168)
Concurrent Requests: Limited (no async)
Cache Hit Rate: 0% (no caching)
```

### Identified Bottlenecks

#### 1. **No Caching Layer** 🔴 CRITICAL
- **Issue:** Every query hits database and recomputes embeddings
- **Impact:** High latency, wasted resources
- **Current:** No caching at all
- **Target:** 80%+ cache hit rate

#### 2. **Client Recreation** 🔴 CRITICAL
- **Issue:** ChromaDB client recreated on every request
- **Location:** `routes/query.py` line 62-68
- **Impact:** Connection overhead, memory waste
- **Current:** New connection per request
- **Target:** Singleton with connection pooling

#### 3. **Missing Documents** 🟡 MEDIUM
- **Issue:** Only 61/168 documents loaded (36%)
- **Impact:** Incomplete search results
- **Current:** 61 documents
- **Target:** 168 documents

#### 4. **No Async Operations** 🟡 MEDIUM
- **Issue:** All operations are synchronous
- **Impact:** Poor concurrency, blocking I/O
- **Current:** Synchronous only
- **Target:** Async for I/O operations

#### 5. **No Rate Limiting** 🟡 MEDIUM
- **Issue:** No protection against abuse
- **Impact:** Potential DoS, resource exhaustion
- **Current:** Unlimited requests
- **Target:** Rate limiting middleware

#### 6. **Embedding Model Loading** 🟢 LOW
- **Issue:** Model loaded on every embedder creation
- **Impact:** Slow cold starts
- **Current:** Lazy loading exists but not optimized
- **Target:** Pre-warmed singleton

#### 7. **No Query Optimization** 🟢 LOW
- **Issue:** No query rewriting or optimization
- **Impact:** Suboptimal retrievals
- **Current:** Raw queries
- **Target:** Query expansion, synonym handling

---

## Optimization Strategy

### Phase 1: Critical Performance (Immediate)
**Time:** 2-3 hours  
**Impact:** 5-10x performance improvement

#### 1.1 Add Redis Caching Layer
```python
# Cache structure:
- Query embeddings: 1 hour TTL
- Search results: 30 min TTL
- Graph facts: 1 hour TTL
- Intent detection: 1 hour TTL
```

**Expected Improvements:**
- Cache hit rate: 70-80%
- Latency reduction: 80-90% for cached queries
- Memory: +100 MB (Redis)

#### 1.2 Fix Client Singleton Pattern
```python
# Ensure singletons for:
- ChromaDB client (global, not per-request)
- Neo4j client (already singleton, optimize pool)
- Embedder (pre-warm on startup)
```

**Expected Improvements:**
- Connection overhead: -95%
- Memory usage: -60%
- Cold start time: -80%

#### 1.3 Add Connection Pooling
```python
# Optimize:
- Neo4j: Increase pool from 50 to 100
- ChromaDB: Persistent connections
- HTTP keep-alive for all external calls
```

**Expected Improvements:**
- Concurrent requests: 10x increase
- Latency: -20%

---

### Phase 2: Data Completeness (Medium Priority)
**Time:** 1 hour  
**Impact:** Better search quality

#### 2.1 Load Missing Documents
```bash
# Current: 61 documents
# Expected: 168 documents
# Missing: 107 documents (64%)
```

**Action:**
1. Re-run data ingestion pipeline
2. Verify all acts are loaded
3. Update ChromaDB collection

**Expected Improvements:**
- Search recall: +64%
- Answer quality: Significant improvement

---

### Phase 3: Async & Concurrency (Medium Priority)
**Time:** 3-4 hours  
**Impact:** Better scalability

#### 3.1 Convert to Async Operations
```python
# Make async:
- Database queries (ChromaDB, Neo4j)
- Embedding generation (batch)
- LLM calls (streaming)
- API endpoints (FastAPI async)
```

**Expected Improvements:**
- Concurrent requests: 50-100x
- Throughput: 10x
- Resource utilization: +40%

#### 3.2 Add Request Queuing
```python
# Queue system:
- Background task queue (Celery/RQ)
- Priority queues for different intents
- Rate limiting per user
```

**Expected Improvements:**
- System stability: High
- Resource protection: Complete

---

### Phase 4: Advanced Optimizations (Low Priority)
**Time:** 4-6 hours  
**Impact:** Incremental improvements

#### 4.1 Query Optimization
```python
# Add:
- Query expansion with synonyms
- Legal term normalization
- Spelling correction
- Query rewriting
```

#### 4.2 Model Optimization
```python
# Optimize:
- Quantize embedding model (FP32 -> FP16)
- Use faster embedding models
- Implement vector compression
- Add approximate nearest neighbors
```

#### 4.3 Monitoring & Profiling
```python
# Add:
- Prometheus metrics
- Request tracing
- Performance profiling
- Error tracking (Sentry)
```

---

## Implementation Roadmap

### Week 1: Critical Optimizations
```
Day 1-2: Add Redis caching
Day 3: Fix singleton patterns
Day 4: Load missing documents
Day 5: Testing & validation
```

### Week 2: Async & Scale
```
Day 1-2: Convert to async
Day 3: Add rate limiting
Day 4-5: Testing & load testing
```

### Week 3: Advanced Features
```
Day 1-2: Query optimization
Day 3-4: Monitoring setup
Day 5: Documentation & deployment
```

---

## Expected Performance After Optimization

### Target Metrics
```
Query Processing Time:
  - Cached queries: 10-50ms (10x faster)
  - Uncached queries: 100-200ms (2x faster)
  - With LLM: 1-3s (3x faster)

Memory Usage:
  - Base: ~300 MB (40% reduction)
  - With cache: ~400 MB (20% reduction)
  - With LLM: ~1.5 GB (25% reduction)

Throughput:
  - Concurrent requests: 100-500 (50x increase)
  - Requests/second: 50-200 (20x increase)

Cache Performance:
  - Cache hit rate: 70-80%
  - Cache memory: ~100 MB
  - Cache latency: <10ms

Resource Efficiency:
  - CPU usage: -40%
  - Memory efficiency: +50%
  - Network bandwidth: -60%
```

---

## Quick Wins (Start Today)

### 1. Add Response Caching (30 minutes)
```python
# Simple in-memory cache with TTL
from functools import lru_cache
import time

# Cache query results
```

### 2. Fix ChromaDB Client (15 minutes)
```python
# Use singleton from routes/adaptive_query.py pattern
# Remove client recreation in routes/query.py
```

### 3. Pre-warm Models (10 minutes)
```python
# Add to lifespan in main.py
# Load embedder and connect ChromaDB on startup
```

### 4. Add Request Logging (20 minutes)
```python
# Track query times, cache hits, errors
# Use for baseline performance measurement
```

**Total Time:** 75 minutes  
**Expected Improvement:** 3-5x on common queries

---

## Technology Stack Recommendations

### Caching Layer
- **Option 1:** Redis (recommended)
  - Fast, distributed
  - TTL support
  - Pub/sub for cache invalidation
- **Option 2:** In-memory (simple start)
  - `cachetools` library
  - No external dependencies
  - Limited to single instance

### Async Framework
- **FastAPI** (already using) ✓
- **httpx** for async HTTP
- **asyncio** for concurrent operations

### Monitoring
- **Prometheus** + **Grafana** (metrics)
- **Sentry** (error tracking)
- **OpenTelemetry** (tracing)

---

## Cost-Benefit Analysis

| Optimization | Time | Complexity | Impact | Priority |
|--------------|------|------------|--------|----------|
| Redis Caching | 2h | Medium | HIGH | 🔴 Critical |
| Fix Singletons | 30min | Low | HIGH | 🔴 Critical |
| Load Documents | 1h | Low | HIGH | 🔴 Critical |
| Async Operations | 3h | High | MEDIUM | 🟡 Medium |
| Rate Limiting | 1h | Low | MEDIUM | 🟡 Medium |
| Query Optimization | 2h | Medium | LOW | 🟢 Low |
| Monitoring | 4h | Medium | LOW | 🟢 Low |

---

## Success Criteria

### Phase 1 Success
- ✅ Cache hit rate > 70%
- ✅ Average latency < 100ms (cached)
- ✅ All 168 documents loaded
- ✅ Memory usage < 400 MB

### Phase 2 Success
- ✅ Handle 100 concurrent requests
- ✅ Throughput > 50 req/sec
- ✅ Rate limiting active

### Phase 3 Success
- ✅ Query optimization active
- ✅ Monitoring dashboard live
- ✅ 99.9% uptime

---

## Next Steps

1. **Immediate:** Start with quick wins (75 minutes)
2. **Today:** Implement Redis caching (2 hours)
3. **Tomorrow:** Load missing documents (1 hour)
4. **This Week:** Complete Phase 1

**Ready to start optimization? Let's begin with the quick wins!**
