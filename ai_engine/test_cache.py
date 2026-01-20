"""
Test Redis Caching Performance
Compares query performance with and without caching
"""
import sys
sys.path.insert(0, 'src')

from pipelines.adaptive_rag import AdaptiveRAGPipeline
from graph.neo4j_client import get_neo4j_client
import time

def test_cache_performance():
    print("\n" + "="*80)
    print("  REDIS CACHE PERFORMANCE TEST")
    print("="*80)
    
    # Initialize pipeline with cache
    print("\n[SETUP] Initializing pipeline with Redis cache...")
    neo4j_client = get_neo4j_client()
    pipeline = AdaptiveRAGPipeline(neo4j_client=neo4j_client, use_llm=False, use_cache=True)
    
    if pipeline.use_cache:
        print("[PASS] Redis caching enabled")
        stats = pipeline.cache.get_stats()
        print(f"[INFO] Cache status: {stats}")
    else:
        print("[WARN] Redis caching not available")
        return
    
    # Test query
    test_query = "What is anticipatory bail?"
    
    # Clear cache first
    print(f"\n[TEST] Clearing cache...")
    pipeline.cache.clear_all()
    
    # First run (cache miss)
    print(f"\n[TEST 1] First run (cache miss)")
    print(f"Query: {test_query}")
    start = time.time()
    result1 = pipeline.process_query(test_query)
    time1 = (time.time() - start) * 1000
    
    print(f"[RESULT] Processing Time: {time1:.0f}ms")
    print(f"[RESULT] Intent: {result1.intent.value}")
    print(f"[RESULT] Sources: {result1.num_sources_retrieved}")
    print(f"[RESULT] Cache Hit: {result1.metadata.get('cache_hit', False)}")
    
    # Second run (cache hit)
    print(f"\n[TEST 2] Second run (cache hit)")
    print(f"Query: {test_query}")
    start = time.time()
    result2 = pipeline.process_query(test_query)
    time2 = (time.time() - start) * 1000
    
    print(f"[RESULT] Processing Time: {time2:.0f}ms")
    print(f"[RESULT] Intent: {result2.intent.value}")
    print(f"[RESULT] Sources: {result2.num_sources_retrieved}")
    print(f"[RESULT] Cache Hit: {result2.metadata.get('cache_hit', False)}")
    
    # Calculate speedup
    speedup = time1 / time2 if time2 > 0 else 0
    time_saved = time1 - time2
    
    print(f"\n{'='*80}")
    print("  PERFORMANCE COMPARISON")
    print("="*80)
    print(f"\nFirst Run (No Cache):  {time1:.0f}ms")
    print(f"Second Run (Cached):   {time2:.0f}ms")
    print(f"\nTime Saved:            {time_saved:.0f}ms ({(time_saved/time1*100):.1f}%)")
    print(f"Speedup:               {speedup:.1f}x faster")
    
    # Test multiple queries
    print(f"\n{'='*80}")
    print("  MULTIPLE QUERY TEST")
    print("="*80)
    
    queries = [
        "What is the punishment for murder?",
        "How to file an FIR?",
        "What are the essential elements of a contract?"
    ]
    
    total_uncached = 0
    total_cached = 0
    
    for i, query in enumerate(queries, 1):
        print(f"\n[TEST {i}] {query}")
        
        # Clear cache
        cache_key = pipeline.cache._generate_key("search", query)
        pipeline.cache.delete(cache_key)
        
        # Uncached
        start = time.time()
        pipeline.process_query(query)
        uncached_time = (time.time() - start) * 1000
        total_uncached += uncached_time
        
        # Cached
        start = time.time()
        pipeline.process_query(query)
        cached_time = (time.time() - start) * 1000
        total_cached += cached_time
        
        speedup = uncached_time / cached_time if cached_time > 0 else 0
        print(f"  Uncached: {uncached_time:.0f}ms | Cached: {cached_time:.0f}ms | Speedup: {speedup:.1f}x")
    
    # Summary
    avg_uncached = total_uncached / len(queries)
    avg_cached = total_cached / len(queries)
    avg_speedup = avg_uncached / avg_cached if avg_cached > 0 else 0
    
    print(f"\n{'='*80}")
    print("  SUMMARY")
    print("="*80)
    print(f"\nAverage Uncached Time: {avg_uncached:.0f}ms")
    print(f"Average Cached Time:   {avg_cached:.0f}ms")
    print(f"Average Speedup:       {avg_speedup:.1f}x faster")
    print(f"Time Saved per Query:  {(avg_uncached - avg_cached):.0f}ms")
    
    # Cache stats
    stats = pipeline.cache.get_stats()
    print(f"\n[CACHE STATS]")
    print(f"  Total Keys: {stats.get('total_keys', 0)}")
    print(f"  Memory Used: {stats.get('used_memory', 'N/A')}")
    print(f"  Hit Rate: {stats.get('hit_rate', 0):.1f}%")
    
    print("\n" + "="*80)
    print("  TEST COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    test_cache_performance()
