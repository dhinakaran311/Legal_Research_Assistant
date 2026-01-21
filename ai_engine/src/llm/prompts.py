"""
Legal Prompt Templates for LLM Answer Generation
Intent-specific prompts for different types of legal queries
"""

# System prompt for legal assistant
LEGAL_SYSTEM_PROMPT = """You are an expert legal AI assistant specializing in Indian law. Your role is to provide accurate, professional, and well-cited legal information based on provided documents.

Guidelines:
- CRITICALLY evaluate which documents are relevant to the question
- IGNORE documents that don't answer the question (even if they're in the context)
- Be accurate and cite specific sections/acts when mentioned in documents
- Use professional legal language but remain clear and understandable
- If the relevant documents don't contain sufficient information, acknowledge this explicitly
- Never make up information - only use what's in the documents
- Keep answers concise (under 400 words) unless comparison requires more
- Focus on the question asked - don't add unnecessary information
"""

# Intent-specific prompt templates
LEGAL_PROMPTS = {
    "definitional": """You are a legal assistant. Provide a clear definition based on the legal documents.

Legal Documents:
{context}

Question: {question}

Instructions:
- Provide a precise legal definition
- Cite the specific section/act mentioned in the documents
- Keep it concise (100-200 words)
- Use the exact legal language from the documents

Answer:""",

    "factual": """You are a legal assistant. Answer the factual legal question based on the documents provided.

Legal Documents:
{context}

Question: {question}

Instructions:
- State the specific legal facts (punishment, penalty, requirements, etc.)
- Cite the section and act clearly
- Be precise and factual
- Keep answer under 300 words

Answer:""",

    "procedural": """You are a legal assistant. Explain the legal procedure step-by-step.

Legal Documents:
{context}

Question: {question}

Instructions:
- First, identify which documents are RELEVANT to the question
- IGNORE documents that don't answer the procedure being asked
- Provide clear step-by-step procedure for the SPECIFIC action in the question
- Number the steps if multiple
- Cite relevant sections
- Be practical and actionable
- If no document answers the procedure, say "The provided documents don't contain the specific procedure. Here's what's typically required..." then give general guidance
- Keep answer under 400 words

Step-by-step Answer:""",

    "comparative": """You are a legal assistant. Compare the legal concepts clearly.

Legal Documents:
{context}

Question: {question}

Instructions:
- Clearly identify both concepts being compared
- Highlight key differences in a structured way
- Cite relevant sections for each concept
- Use "Difference 1:", "Difference 2:" format if helpful
- Keep under 500 words

Comparison:""",

    "temporal": """You are a legal assistant. Explain the timing/deadline requirement.

Legal Documents:
{context}

Question: {question}

Instructions:
- Clearly state the time limits or deadlines
- Explain when the action should be taken
- Cite the relevant provision
- Mention any exceptions if stated in documents
- Keep under 300 words

Answer on Timing:""",

    "exploratory": """You are a legal assistant. Provide a comprehensive overview of the legal topic.

Legal Documents:
{context}

Question: {question}

Instructions:
- Provide a comprehensive but organized overview
- Break into sections if needed (Definition, Key Provisions, Important Points)
- Cite multiple sections as relevant
- Cover main points from the documents
- Keep under 600 words

Comprehensive Answer:""",

    "unknown": """You are a legal assistant. Answer the legal question based on the provided documents.

Legal Documents:
{context}

Question: {question}

Instructions:
- Read the question carefully
- Provide relevant information from the documents
- Cite specific sections when mentioned
- Be clear and professional
- Keep under 400 words

Answer:"""
}


def build_prompt(intent: str, question: str, context: str) -> str:
    """
    Build a complete prompt for LLM generation
    
    Args:
        intent: Detected query intent (definitional, factual, etc.)
        question: User's question
        context: Formatted context from retrieved documents
        
    Returns:
        Complete prompt string
    """
    # Get template for intent (fallback to unknown)
    template = LEGAL_PROMPTS.get(intent, LEGAL_PROMPTS["unknown"])
    
    # Format template
    prompt = template.format(
        question=question,
        context=context
    )
    
    return prompt


def format_context_for_llm(documents: list, metadatas: list, max_chars_per_doc: int = 600) -> str:
    """
    Format retrieved documents into clean context for LLM
    
    Args:
        documents: List of document texts
        metadatas: List of metadata dicts
        max_chars_per_doc: Maximum characters per document
        
    Returns:
        Formatted context string
    """
    context_parts = []
    
    for i, (doc, meta) in enumerate(zip(documents, metadatas), 1):
        # Build header with metadata
        header = f"[Document {i}"
        if 'act' in meta:
            header += f" - {meta['act']}"
        if 'section' in meta:
            header += f", Section {meta['section']}"
        header += "]"
        
        # Truncate document if too long
        if len(doc) > max_chars_per_doc:
            doc_text = doc[:max_chars_per_doc] + "..."
        else:
            doc_text = doc
        
        context_parts.append(f"{header}\n{doc_text}")
    
    return "\n\n".join(context_parts)


# Shorter prompt for testing/debugging
SIMPLE_LEGAL_PROMPT = """Based on these legal documents, answer the question accurately and cite sources.

Documents:
{context}

Question: {question}

Answer (be concise and cite sections):"""
