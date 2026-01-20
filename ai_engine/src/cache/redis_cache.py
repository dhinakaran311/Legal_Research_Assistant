"""
Redis Cache Manager for AI Engine
Implements caching layer for query embeddings, search results, and graph facts
"""
import redis
import json
import hashlib
import logging
from typing import Any, Optional, List, Dict
import pickle

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache manager with TTL support"""
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        decode_responses: bool = False  # False for binary data (pickled objects)
    ):
        """
        Initialize Redis cache
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password (optional)
            decode_responses: Whether to decode responses to strings
        """
        self.host = host
        self.port = port
        self.db = db
        
        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=decode_responses,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            
            # Test connection
            self.client.ping()
            logger.info(f"[PASS] Redis cache connected: {host}:{port}")
            self.enabled = True
            
        except Exception as e:
            logger.warning(f"[WARN] Redis not available: {str(e)}")
            logger.warning("[WARN] Caching disabled, proceeding without cache")
            self.client = None
            self.enabled = False
    
    def _generate_key(self, prefix: str, data: str) -> str:
        """
        Generate cache key from prefix and data
        
        Args:
            prefix: Key prefix (e.g., 'embedding', 'search', 'graph')
            data: Data to hash
            
        Returns:
            Cache key
        """
        hash_obj = hashlib.md5(data.encode('utf-8'))
        return f"{prefix}:{hash_obj.hexdigest()}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if not self.enabled:
            return None
        
        try:
            value = self.client.get(key)
            if value:
                # Unpickle the value
                return pickle.loads(value)
            return None
        except Exception as e:
            logger.debug(f"Cache get error: {str(e)}")
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600
    ) -> bool:
        """
        Set value in cache with TTL
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            # Pickle the value
            pickled_value = pickle.dumps(value)
            self.client.setex(key, ttl, pickled_value)
            return True
        except Exception as e:
            logger.debug(f"Cache set error: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.enabled:
            return False
        
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.debug(f"Cache delete error: {str(e)}")
            return False
    
    def clear_all(self) -> bool:
        """Clear all cache entries (use with caution!)"""
        if not self.enabled:
            return False
        
        try:
            self.client.flushdb()
            logger.info("[INFO] Cache cleared")
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        if not self.enabled:
            return {
                "enabled": False,
                "message": "Cache disabled"
            }
        
        try:
            info = self.client.info()
            return {
                "enabled": True,
                "used_memory": info.get('used_memory_human', 'N/A'),
                "total_keys": self.client.dbsize(),
                "hits": info.get('keyspace_hits', 0),
                "misses": info.get('keyspace_misses', 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get('keyspace_hits', 0),
                    info.get('keyspace_misses', 0)
                )
            }
        except Exception as e:
            logger.error(f"Cache stats error: {str(e)}")
            return {"enabled": False, "error": str(e)}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate"""
        total = hits + misses
        if total == 0:
            return 0.0
        return (hits / total) * 100


# Global cache instance
_cache_instance: Optional[RedisCache] = None


def get_cache(
    host: str = 'localhost',
    port: int = 6379,
    db: int = 0,
    force_reload: bool = False
) -> RedisCache:
    """
    Get or create Redis cache singleton
    
    Args:
        host: Redis host
        port: Redis port
        db: Redis database number
        force_reload: Force recreation of cache instance
        
    Returns:
        RedisCache instance
    """
    global _cache_instance
    
    if _cache_instance is None or force_reload:
        _cache_instance = RedisCache(host=host, port=port, db=db)
    
    return _cache_instance


# Cache key prefixes
class CachePrefix:
    """Cache key prefixes for different data types"""
    EMBEDDING = "emb"
    SEARCH_RESULT = "search"
    GRAPH_FACT = "graph"
    INTENT = "intent"
    

# Cache TTL (Time To Live) in seconds
class CacheTTL:
    """TTL values for different cache types"""
    EMBEDDING = 3600  # 1 hour (embeddings rarely change)
    SEARCH_RESULT = 1800  # 30 minutes
    GRAPH_FACT = 3600  # 1 hour
    INTENT = 3600  # 1 hour
