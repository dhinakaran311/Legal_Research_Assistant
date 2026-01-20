"""
Adaptive RAG Pipeline for Legal AI
Dynamically adjusts retrieval strategy based on query intent

Pipeline Stages:
1. Detect Intent - Classify user query to understand the type of question
2. Decide Retrieval Strategy - Determine optimal number of documents to retrieve
3. Retrieve Context - Fetch relevant documents from vector store
4. Generate Answer - Create structured response with sources
"""

from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import logging
import re
import time
from dataclasses import dataclass

from vectorstore.chroma_client import ChromaClient
from embeddings.embedder import Embedder
from config import settings

# Optional LLM imports (lazy loaded)
try:
    from llm.ollama_generator import OllamaGenerator
    from llm.prompts import build_prompt, format_context_for_llm
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    logger.warning("LLM module not available, using rule-based generation only")

# Optional Graph imports (lazy loaded)
try:
    from graph.graph_queries import fetch_legal_graph_facts, build_graph_context
    GRAPH_AVAILABLE = True
except ImportError:
    GRAPH_AVAILABLE = False
    logger.warning("Graph module not available, proceeding without graph enrichment")

# Optional Cache imports (lazy loaded)
try:
    from cache import get_cache, CachePrefix, CacheTTL
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    logger.warning("Cache module not available, proceeding without caching")

logger = logging.getLogger(__name__)


class QueryIntent(str, Enum):
    """Types of query intents for legal questions"""
    FACTUAL = "factual"           # Single fact: "What is the punishment for X?"
    PROCEDURAL = "procedural"     # How-to: "How do I file X?"
    COMPARATIVE = "comparative"   # Comparison: "What's the difference between X and Y?"
    EXPLORATORY = "exploratory"   # Broad: "Tell me about X"
    DEFINITIONAL = "definitional" # Definition: "What is X?"
    TEMPORAL = "temporal"         # Time-based: "When should I X?"
    UNKNOWN = "unknown"           # Cannot determine intent


@dataclass
class IntentAnalysis:
    """Result of intent detection"""
    intent: QueryIntent
    confidence: float
    reasoning: str
    keywords_matched: List[str]


@dataclass
class RetrievalStrategy:
    """Strategy for document retrieval"""
    num_documents: int
    min_relevance_threshold: float
    use_metadata_filter: bool
    metadata_filter: Optional[Dict[str, Any]] = None


@dataclass
class RetrievedContext:
    """Retrieved documents with metadata"""
    documents: List[str]
    metadatas: List[Dict[str, Any]]
    distances: List[float]
    ids: List[str]
    relevance_scores: List[float]


@dataclass
class PipelineResult:
    """Final result from the adaptive RAG pipeline"""
    question: str
    graph_references: List[Dict[str, Any]]  # NEW: Graph facts from Neo4j
    intent: QueryIntent
    intent_confidence: float
    answer: str
    sources: List[Dict[str, Any]]
    num_sources_retrieved: int
    retrieval_strategy: Dict[str, Any]
    confidence: float
    processing_time_ms: float
    metadata: Dict[str, Any]


class AdaptiveRAGPipeline:
    """
    Adaptive RAG Pipeline that dynamically adjusts retrieval based on query intent
    
    Features:
    - Intent-aware query classification
    - Dynamic document retrieval (2-10 docs based on intent)
    - Confidence-based filtering
    - Structured JSON output
    """
    
    def __init__(
        self,
        chroma_client: Optional[ChromaClient] = None,
        embedder: Optional[Embedder] = None,
        neo4j_client = None,
        use_llm: bool = False,
        llm_model: str = "llama3.2:3b",
        use_cache: bool = True
    ):
        """
        Initialize the Adaptive RAG Pipeline
        
        Args:
            chroma_client: Optional ChromaDB client (will create if not provided)
            embedder: Optional embedder instance (will create if not provided)
            neo4j_client: Optional Neo4j client for graph enrichment (will skip if not provided)
            use_llm: Whether to use LLM for answer generation (default: False)
            llm_model: Name of the Ollama model to use (default: llama3.2:3b)
            use_cache: Whether to use Redis caching (default: True)
        """
        self.chroma_client = chroma_client
        self.embedder = embedder
        self.neo4j_client = neo4j_client
        self.use_graph = neo4j_client is not None and GRAPH_AVAILABLE
        self.use_llm = use_llm and LLM_AVAILABLE
        self.llm_model = llm_model
        self.llm_generator = None  # Lazy loaded
        
        # Initialize cache
        self.use_cache = use_cache and CACHE_AVAILABLE
        self.cache = None
        if self.use_cache:
            try:
                self.cache = get_cache()
                if self.cache.enabled:
                    logger.info("[CACHE] Redis caching enabled")
                else:
                    self.use_cache = False
                    logger.info("[CACHE] Redis not available, caching disabled")
            except Exception as e:
                self.use_cache = False
                logger.warning(f"[CACHE] Failed to initialize cache: {str(e)}")
        
        if use_llm and not LLM_AVAILABLE:
            logger.warning("LLM requested but not available, falling back to rule-based generation")
        
        if neo4j_client and not GRAPH_AVAILABLE:
            logger.warning("Graph enrichment requested but graph module not available")
        
        # Intent detection patterns (ordered by priority - specific to generic)
        # Patterns are checked in order, with multi-word patterns prioritized
        self.intent_patterns = {
            # COMPARATIVE - Must check BEFORE definitional (has "difference")
            QueryIntent.COMPARATIVE: {
                'keywords': ['difference between', 'compare', 'versus', 'vs', 'vs.', 
                           'distinction between', 'contrast', 'better than', 'worse than',
                           'similar to', 'compared to'],
                'weight': 1.0,
                'priority': 1,  # Highest priority
                'multi_word': True
            },
            # EXPLORATORY - Check BEFORE factual (has "tell me about")
            QueryIntent.EXPLORATORY: {
                'keywords': ['tell me about', 'tell me everything', 'explain everything about',
                           'overview of', 'all about', 'comprehensive guide',
                           'detailed information', 'everything about'],
                'weight': 1.0,
                'priority': 2,
                'multi_word': True
            },
            # PROCEDURAL - Check BEFORE definitional
            QueryIntent.PROCEDURAL: {
                'keywords': ['how to', 'how do i', 'how can i', 'steps to', 'procedure to',
                           'process of', 'file', 'apply for', 'register', 'obtain', 'submit'],
                'weight': 0.95,
                'priority': 3,
                'multi_word': True
            },
            # FACTUAL - Specific legal queries (punishment, section, etc.)
            QueryIntent.FACTUAL: {
                'keywords': ['punishment for', 'penalty for', 'sentence for', 
                           'imprisonment for', 'fine for', 'consequences of',
                           'section', 'article', 'provision', 'clause'],
                'weight': 0.9,
                'priority': 4,
                'multi_word': False
            },
            # TEMPORAL - Time-based queries
            QueryIntent.TEMPORAL: {
                'keywords': ['when should', 'when can', 'when to', 'deadline for',
                           'time limit', 'duration', 'period', 'within', 'before', 'after'],
                'weight': 0.85,
                'priority': 5,
                'multi_word': False
            },
            # DEFINITIONAL - Generic "what is" (lowest priority)
            QueryIntent.DEFINITIONAL: {
                'keywords': ['what is', 'what are', 'define', 'definition of', 
                           'meaning of', 'means'],
                'weight': 0.7,
                'priority': 6,  # Lowest priority
                'multi_word': False,
                # Exclude if these patterns present (avoid false positives)
                'exclude_if': ['punishment', 'difference', 'compare', 'penalty']
            }
        }
        
        # Intent to retrieval count mapping
        self.intent_retrieval_map = {
            QueryIntent.DEFINITIONAL: (2, 3),      # Simple definitions need fewer docs
            QueryIntent.FACTUAL: (2, 4),           # Specific facts need moderate docs
            QueryIntent.PROCEDURAL: (3, 5),        # Procedures need more context
            QueryIntent.COMPARATIVE: (4, 7),       # Comparisons need multiple perspectives
            QueryIntent.TEMPORAL: (2, 4),          # Time-based queries are specific
            QueryIntent.EXPLORATORY: (6, 10),      # Broad queries need comprehensive docs
            QueryIntent.UNKNOWN: (3, 5)            # Default moderate retrieval
        }
        
        logger.info(
            f"AdaptiveRAGPipeline initialized (LLM: {'enabled' if self.use_llm else 'disabled'}, "
            f"Graph: {'enabled' if self.use_graph else 'disabled'})"
        )
    
    def _ensure_clients(self) -> None:
        """Ensure ChromaDB and Embedder clients are initialized"""
        if self.chroma_client is None:
            self.chroma_client = ChromaClient(
                persist_directory=settings.CHROMA_DB_PATH,
                collection_name=settings.CHROMA_COLLECTION_NAME,
                embedding_model=settings.MODEL_NAME
            )
            self.chroma_client.connect()
            logger.info("ChromaDB client initialized")
        
        if self.embedder is None:
            self.embedder = Embedder(model_name=settings.MODEL_NAME)
            self.embedder.load_model()
            logger.info("Embedder initialized")
    
    # ==================== STAGE 1: DETECT INTENT ====================
    
    def detect_intent(self, query: str) -> IntentAnalysis:
        """
        Stage 1: Detect the intent of the user's query
        
        Args:
            query: User's question
            
        Returns:
            IntentAnalysis with detected intent and confidence
        """
        query_lower = query.lower()
        
        # Sort intents by priority (1 = highest, 6 = lowest)
        sorted_intents = sorted(
            self.intent_patterns.items(),
            key=lambda x: x[1].get('priority', 99)
        )
        
        intent_scores = {}
        matched_keywords = {}
        
        # Check each intent in priority order
        for intent, pattern_data in sorted_intents:
            keywords = pattern_data['keywords']
            weight = pattern_data['weight']
            matches = []
            
            # Check for exclusion patterns (for definitional)
            if 'exclude_if' in pattern_data:
                exclude_keywords = pattern_data['exclude_if']
                # If any exclusion keyword is found, skip this intent
                if any(excl in query_lower for excl in exclude_keywords):
                    logger.debug(f"Skipping {intent} due to exclusion pattern")
                    continue
            
            # Match keywords
            for keyword in keywords:
                if keyword in query_lower:
                    matches.append(keyword)
            
            if matches:
                # Calculate score
                # For multi-word patterns, exact match gets higher score
                if pattern_data.get('multi_word', False):
                    # Give bonus for longer matches
                    match_lengths = [len(m.split()) for m in matches]
                    avg_length = sum(match_lengths) / len(match_lengths)
                    score = (len(matches) / len(keywords)) * weight * (1 + avg_length * 0.1)
                else:
                    score = (len(matches) / len(keywords)) * weight
                
                intent_scores[intent] = score
                matched_keywords[intent] = matches
        
        # Determine best intent
        if intent_scores:
            # Get intent with highest score
            best_intent = max(intent_scores, key=intent_scores.get)
            best_score = intent_scores[best_intent]
            
            # Calculate confidence based on score and priority
            # Higher priority intents get confidence boost
            priority = self.intent_patterns[best_intent].get('priority', 6)
            priority_boost = (7 - priority) * 0.05  # 0.30 boost for priority 1, 0.05 for priority 6
            
            confidence = min(best_score + priority_boost, 0.95)  # Cap at 0.95
            keywords_found = matched_keywords[best_intent]
            reasoning = f"Matched {len(keywords_found)} pattern(s): {', '.join(keywords_found[:3])}"
        else:
            # Fallback for unknown intent
            best_intent = QueryIntent.UNKNOWN
            confidence = 0.3
            keywords_found = []
            reasoning = "No clear intent pattern detected, using default strategy"
        
        logger.info(f"Intent detected: {best_intent} (confidence: {confidence:.2f})")
        
        return IntentAnalysis(
            intent=best_intent,
            confidence=confidence,
            reasoning=reasoning,
            keywords_matched=keywords_found
        )
    
    # ==================== STAGE 2: DECIDE RETRIEVAL STRATEGY ====================
    
    def decide_retrieval_strategy(
        self,
        intent_analysis: IntentAnalysis,
        query: str
    ) -> RetrievalStrategy:
        """
        Stage 2: Decide the optimal retrieval strategy based on intent
        
        Args:
            intent_analysis: Result from intent detection
            query: Original user query
            
        Returns:
            RetrievalStrategy with number of documents and thresholds
        """
        intent = intent_analysis.intent
        confidence = intent_analysis.confidence
        
        # Get base retrieval range for this intent
        min_docs, max_docs = self.intent_retrieval_map[intent]
        
        # Adjust based on confidence
        # Higher confidence → use minimum docs (more focused)
        # Lower confidence → use maximum docs (broader search)
        if confidence >= 0.8:
            num_documents = min_docs
            min_relevance = 0.5
        elif confidence >= 0.6:
            num_documents = (min_docs + max_docs) // 2
            min_relevance = 0.4
        else:
            num_documents = max_docs
            min_relevance = 0.3
        
        # Detect if query mentions specific acts/sections for metadata filtering
        use_metadata_filter = False
        metadata_filter = None
        
        # Check for IPC/CrPC/Act mentions
        act_pattern = r'\b(IPC|CrPC|CPC|Indian Penal Code|Criminal Procedure Code|Civil Procedure Code)\b'
        section_pattern = r'\bsection\s+\d+\b'
        
        if re.search(act_pattern, query, re.IGNORECASE):
            use_metadata_filter = True
            # Could add actual filter logic here
        
        logger.info(
            f"Retrieval strategy: {num_documents} docs, "
            f"threshold: {min_relevance}, "
            f"metadata filter: {use_metadata_filter}"
        )
        
        return RetrievalStrategy(
            num_documents=num_documents,
            min_relevance_threshold=min_relevance,
            use_metadata_filter=use_metadata_filter,
            metadata_filter=metadata_filter
        )
    
    # ==================== STAGE 3: RETRIEVE CONTEXT ====================
    
    def retrieve_context(
        self,
        query: str,
        strategy: RetrievalStrategy
    ) -> RetrievedContext:
        """
        Stage 3: Retrieve relevant documents from vector store
        
        Args:
            query: User's question
            strategy: Retrieval strategy from stage 2
            
        Returns:
            RetrievedContext with retrieved documents and metadata
        """
        self._ensure_clients()
        
        # Query ChromaDB
        results = self.chroma_client.query(
            query_texts=[query],
            n_results=strategy.num_documents,
            where=strategy.metadata_filter
        )
        
        # Extract results
        if not results['ids'][0]:
            logger.warning("No documents retrieved")
            return RetrievedContext(
                documents=[],
                metadatas=[],
                distances=[],
                ids=[],
                relevance_scores=[]
            )
        
        documents = results['documents'][0]
        metadatas = results['metadatas'][0]
        distances = results['distances'][0]
        ids = results['ids'][0]
        
        # Convert distances to relevance scores (0-1, higher is better)
        # ChromaDB uses L2 distance, smaller is better
        relevance_scores = [max(0.0, 1.0 - (dist / 2.0)) for dist in distances]
        
        # Filter by minimum relevance threshold
        filtered_data = []
        for i, score in enumerate(relevance_scores):
            if score >= strategy.min_relevance_threshold:
                filtered_data.append((documents[i], metadatas[i], distances[i], ids[i], score))
        
        # If filtering removed too many, keep at least 1
        if not filtered_data and documents:
            filtered_data.append((
                documents[0], metadatas[0], distances[0], ids[0], relevance_scores[0]
            ))
        
        # Unpack filtered data
        if filtered_data:
            docs, metas, dists, doc_ids, scores = zip(*filtered_data)
            logger.info(f"Retrieved {len(docs)} documents (filtered from {len(documents)})")
        else:
            docs, metas, dists, doc_ids, scores = [], [], [], [], []
            logger.warning("All documents filtered out by relevance threshold")
        
        return RetrievedContext(
            documents=list(docs),
            metadatas=list(metas),
            distances=list(dists),
            ids=list(doc_ids),
            relevance_scores=list(scores)
        )
    
    # ==================== STAGE 4: GENERATE ANSWER ====================
    
    def generate_answer(
        self,
        query: str,
        context: RetrievedContext,
        intent_analysis: IntentAnalysis
    ) -> Tuple[str, float, List[Dict[str, Any]]]:
        """
        Stage 4: Generate a structured answer from retrieved context
        
        Uses LLM if enabled, otherwise falls back to rule-based generation
        
        Args:
            query: User's question
            context: Retrieved documents from stage 3
            intent_analysis: Intent analysis from stage 1
            
        Returns:
            Tuple of (answer_text, confidence, sources_list)
        """
        if not context.documents:
            return (
                "No relevant legal provisions found for your query. Please try rephrasing your question or being more specific.",
                0.0,
                []
            )
        
        # Build sources list (needed for both methods)
        sources = self._build_sources_list(context)
        
        # Decide whether to use LLM or rule-based
        if self.use_llm:
            try:
                answer = self._generate_llm_answer(query, context, intent_analysis)
                logger.info("Generated answer using LLM")
            except Exception as e:
                logger.warning(f"LLM generation failed, falling back to rule-based: {str(e)}")
                answer = self._generate_rulebased_answer(query, sources, intent_analysis)
        else:
            answer = self._generate_rulebased_answer(query, sources, intent_analysis)
        
        # Calculate overall confidence
        top_source = sources[0]
        confidence = (top_source['relevance_score'] + intent_analysis.confidence) / 2
        confidence = round(confidence, 4)
        
        logger.info(f"Generated answer with confidence: {confidence}")
        
        return answer, confidence, sources
    
    def _build_sources_list(self, context: RetrievedContext) -> List[Dict[str, Any]]:
        """Build sources list from retrieved context"""
        sources = []
        for i, (doc_id, document, metadata, score) in enumerate(zip(
            context.ids,
            context.documents,
            context.metadatas,
            context.relevance_scores
        )):
            # Extract title from document (first line or ID)
            title = document.split('\n')[0] if '\n' in document else doc_id
            title = title[:100]  # Limit title length
            
            # Create excerpt
            excerpt = document[:300] + "..." if len(document) > 300 else document
            
            sources.append({
                'id': doc_id,
                'title': title,
                'excerpt': excerpt,
                'relevance_score': round(score, 4),
                'metadata': metadata,
                'rank': i + 1
            })
        return sources
    
    def _ensure_llm_generator(self) -> None:
        """Lazy load Ollama generator"""
        if self.llm_generator is None:
            logger.info(f"Initializing Ollama generator with model: {self.llm_model}")
            self.llm_generator = OllamaGenerator(model_name=self.llm_model)
            
            # Check health
            if not self.llm_generator.check_health():
                raise Exception("Ollama health check failed")
    
    def _generate_llm_answer(
        self,
        query: str,
        context: RetrievedContext,
        intent_analysis: IntentAnalysis
    ) -> str:
        """Generate answer using Ollama LLM"""
        self._ensure_llm_generator()
        
        # Format context for LLM
        context_text = format_context_for_llm(
            context.documents,
            context.metadatas,
            max_chars_per_doc=600
        )
        
        # Build prompt based on intent
        prompt = build_prompt(
            intent=intent_analysis.intent.value,
            question=query,
            context=context_text
        )
        
        # Generate with Ollama
        answer = self.llm_generator.generate(
            prompt=prompt,
            max_tokens=512,
            temperature=0.3  # Lower temperature for factual legal answers
        )
        
        return answer
    
    def _generate_rulebased_answer(
        self,
        query: str,
        sources: List[Dict[str, Any]],
        intent_analysis: IntentAnalysis
    ) -> str:
        """Generate answer using rule-based approach"""
        top_source = sources[0]
        intent = intent_analysis.intent
        
        # Build answer based on intent
        if intent == QueryIntent.DEFINITIONAL:
            answer = self._generate_definitional_answer(query, top_source, sources)
        elif intent == QueryIntent.FACTUAL:
            answer = self._generate_factual_answer(query, top_source, sources)
        elif intent == QueryIntent.PROCEDURAL:
            answer = self._generate_procedural_answer(query, top_source, sources)
        elif intent == QueryIntent.COMPARATIVE:
            answer = self._generate_comparative_answer(query, sources)
        elif intent == QueryIntent.EXPLORATORY:
            answer = self._generate_exploratory_answer(query, sources)
        else:
            answer = self._generate_default_answer(query, top_source, sources)
        
        return answer
    
    def _generate_definitional_answer(
        self,
        query: str,
        top_source: Dict[str, Any],
        all_sources: List[Dict[str, Any]]
    ) -> str:
        """Generate answer for definitional queries"""
        answer = f"Based on {top_source['metadata'].get('source', 'legal documents')}:\n\n"
        answer += top_source['excerpt']
        
        if len(all_sources) > 1:
            answer += f"\n\nRelated provisions found in {len(all_sources) - 1} additional source(s)."
        
        return answer
    
    def _generate_factual_answer(
        self,
        query: str,
        top_source: Dict[str, Any],
        all_sources: List[Dict[str, Any]]
    ) -> str:
        """Generate answer for factual queries"""
        metadata = top_source['metadata']
        answer = f"According to {metadata.get('source', 'legal documents')}"
        
        if 'section' in metadata:
            answer += f", Section {metadata['section']}"
        if 'act' in metadata:
            answer += f" of {metadata['act']}"
        
        answer += ":\n\n" + top_source['excerpt']
        
        if len(all_sources) > 1:
            answer += f"\n\n{len(all_sources) - 1} other relevant provision(s) also apply."
        
        return answer
    
    def _generate_procedural_answer(
        self,
        query: str,
        top_source: Dict[str, Any],
        all_sources: List[Dict[str, Any]]
    ) -> str:
        """Generate answer for procedural queries"""
        answer = f"**Procedure:**\n\n{top_source['excerpt']}"
        
        if len(all_sources) > 1:
            answer += f"\n\n**Additional Steps/Requirements:**\n"
            answer += f"Refer to {len(all_sources) - 1} additional source(s) for complete procedure."
        
        return answer
    
    def _generate_comparative_answer(
        self,
        query: str,
        all_sources: List[Dict[str, Any]]
    ) -> str:
        """Generate answer for comparative queries"""
        answer = "**Comparison based on legal provisions:**\n\n"
        
        for i, source in enumerate(all_sources[:3], 1):  # Top 3 sources
            title = source['metadata'].get('source', f'Source {i}')
            answer += f"**{i}. {title}:**\n{source['excerpt'][:200]}...\n\n"
        
        if len(all_sources) > 3:
            answer += f"*{len(all_sources) - 3} more provisions available for review.*"
        
        return answer
    
    def _generate_exploratory_answer(
        self,
        query: str,
        all_sources: List[Dict[str, Any]]
    ) -> str:
        """Generate answer for exploratory queries"""
        answer = "**Comprehensive Overview:**\n\n"
        answer += f"Found {len(all_sources)} relevant legal provisions:\n\n"
        
        for i, source in enumerate(all_sources[:4], 1):  # Top 4 sources
            title = source['metadata'].get('source', f'Provision {i}')
            answer += f"**{i}. {title}**\n{source['excerpt'][:250]}...\n\n"
        
        if len(all_sources) > 4:
            answer += f"*{len(all_sources) - 4} additional provisions available.*"
        
        return answer
    
    def _generate_default_answer(
        self,
        query: str,
        top_source: Dict[str, Any],
        all_sources: List[Dict[str, Any]]
    ) -> str:
        """Generate default answer for unknown intent"""
        answer = f"**Relevant Legal Information:**\n\n{top_source['excerpt']}"
        
        if len(all_sources) > 1:
            answer += f"\n\nFound {len(all_sources)} relevant provision(s)."
        
        return answer
    
    # ==================== MAIN PIPELINE ====================
    
    def process_query(self, query: str, **kwargs) -> PipelineResult:
        """
        Main pipeline: Process a query through all 4 stages with caching
        
        Args:
            query: User's legal question
            **kwargs: Additional options (max_docs, force_intent, bypass_cache, etc.)
            
        Returns:
            PipelineResult with structured answer and metadata
        """
        start_time = time.time()
        
        logger.info(f"Processing query: {query}")
        
        # Check cache first (unless bypassed)
        bypass_cache = kwargs.get('bypass_cache', False)
        cache_key = None
        
        if self.use_cache and not bypass_cache:
            cache_key = self.cache._generate_key(CachePrefix.SEARCH_RESULT, query)
            cached_result = self.cache.get(cache_key)
            
            if cached_result:
                logger.info("[CACHE HIT] Returning cached result")
                # Update processing time to show cache speed
                cached_result.processing_time_ms = (time.time() - start_time) * 1000
                cached_result.metadata['cache_hit'] = True
                return cached_result
        
        logger.info("[CACHE MISS] Processing query")
        
        # STAGE 1: Detect Intent
        intent_analysis = self.detect_intent(query)
        
        # STAGE 2: Decide Retrieval Strategy
        retrieval_strategy = self.decide_retrieval_strategy(intent_analysis, query)
        
        # Allow override of num_documents if provided
        if 'max_docs' in kwargs:
            retrieval_strategy.num_documents = kwargs['max_docs']
        
        # STAGE 3: Retrieve Context
        context = self.retrieve_context(query, retrieval_strategy)
        
        # STAGE 3.5: Graph Enrichment (if Neo4j available)
        graph_facts = []
        if self.use_graph:
            try:
                graph_facts = fetch_legal_graph_facts(query, self.neo4j_client)
                logger.info(f"Graph enrichment: {len(graph_facts)} facts retrieved")
            except Exception as e:
                logger.warning(f"Graph enrichment failed: {str(e)}, proceeding without graph")
        
        # STAGE 4: Generate Answer
        answer, confidence, sources = self.generate_answer(
            query, context, intent_analysis
        )
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # ms
        
        # Build result
        result = PipelineResult(
            question=query,
            graph_references=graph_facts,  # Include graph facts
            intent=intent_analysis.intent,
            intent_confidence=round(intent_analysis.confidence, 4),
            answer=answer,
            sources=sources,
            num_sources_retrieved=len(context.documents),
            retrieval_strategy={
                'num_documents_requested': retrieval_strategy.num_documents,
                'min_relevance_threshold': retrieval_strategy.min_relevance_threshold,
                'num_documents_returned': len(sources),
                'intent_reasoning': intent_analysis.reasoning
            },
            confidence=confidence,
            processing_time_ms=round(processing_time, 2),
            metadata={
                'intent': intent_analysis.intent.value,
                'intent_confidence': intent_analysis.confidence,
                'keywords_matched': intent_analysis.keywords_matched,
                'documents_before_filtering': len(context.documents),
                'graph_facts_found': len(graph_facts),  # NEW
                'cache_hit': False
            }
        )
        
        # Cache the result
        if self.use_cache and cache_key:
            try:
                self.cache.set(cache_key, result, ttl=CacheTTL.SEARCH_RESULT)
                logger.info("[CACHE] Result cached successfully")
            except Exception as e:
                logger.debug(f"[CACHE] Failed to cache result: {str(e)}")
        
        logger.info(
            f"Pipeline completed: intent={result.intent}, "
            f"sources={len(result.sources)}, "
            f"graph_facts={len(graph_facts)}, "
            f"time={result.processing_time_ms:.2f}ms"
        )
        
        return result
