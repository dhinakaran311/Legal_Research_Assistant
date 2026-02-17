"""
Google Gemini LLM Generator
Handles communication with Google Gemini API for answer generation
Uses the new google-genai SDK
"""
import logging
import time
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class GeminiGenerator:
    """
    Generator class for Google Gemini API integration
    Uses Gemini for natural language answer generation
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 120
    ):
        """
        Initialize Gemini Generator
        
        Args:
            model_name: Gemini model name (loaded from config if not provided)
            api_key: Gemini API key (loaded from config if not provided)
            timeout: Request timeout in seconds
        """
        from config import settings
        
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL
        self.timeout = timeout
        self._client = None
        
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not set. Add it to your .env file or pass it directly."
            )
        
        logger.info(f"GeminiGenerator initialized with model: {self.model_name}")
    
    def _get_client(self):
        """Lazy-load the Gemini client"""
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client
    
    def check_health(self) -> bool:
        """
        Check if Gemini API is accessible
        
        Returns:
            True if Gemini is healthy, False otherwise
        """
        try:
            from google.genai import types
            client = self._get_client()
            response = client.models.generate_content(
                model=self.model_name,
                contents="Say 'ok'",
                config=types.GenerateContentConfig(
                    max_output_tokens=10,
                    temperature=0.0,
                )
            )
            if response and response.text:
                logger.info(f"✅ Gemini is healthy, model {self.model_name} is available")
                return True
            else:
                logger.error("❌ Gemini returned empty response")
                return False
        except Exception as e:
            logger.error(f"❌ Gemini health check failed: {str(e)}")
            return False
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.3,
        **kwargs
    ) -> str:
        """
        Generate text using Gemini API
        
        Args:
            prompt: The prompt to generate from
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            **kwargs: Additional parameters
            
        Returns:
            Generated text
            
        Raises:
            Exception: If generation fails
        """
        try:
            from google.genai import types
            
            start_time = time.time()
            logger.debug(f"Generating with Gemini, prompt length: {len(prompt)} chars")
            
            client = self._get_client()
            
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    top_p=kwargs.get('top_p', 0.9),
                    top_k=kwargs.get('top_k', 40),
                )
            )
            
            if response and response.text:
                generated_text = response.text
                elapsed = time.time() - start_time
                logger.info(f"✅ Generated {len(generated_text)} chars in {elapsed:.2f}s")
                return generated_text.strip()
            else:
                error_msg = "Gemini returned empty response"
                if response and hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                    error_msg = f"Gemini blocked the prompt: {response.prompt_feedback}"
                logger.error(f"❌ {error_msg}")
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"❌ Gemini generation failed: {str(e)}")
            raise
    
    def generate_with_context(
        self,
        question: str,
        context_documents: list,
        system_prompt: Optional[str] = None,
        max_tokens: int = 512
    ) -> str:
        """
        Generate answer with context documents
        
        Args:
            question: User's question
            context_documents: List of context documents
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated answer
        """
        context_text = self._format_context(context_documents)
        
        if system_prompt:
            prompt = f"{system_prompt}\n\n"
        else:
            prompt = ""
        
        prompt += f"Context:\n{context_text}\n\n"
        prompt += f"Question: {question}\n\n"
        prompt += "Answer:"
        
        return self.generate(prompt, max_tokens=max_tokens)
    
    def _format_context(self, documents: list) -> str:
        """
        Format context documents into a clean string
        """
        context_parts = []
        
        for i, doc in enumerate(documents, 1):
            if isinstance(doc, dict):
                text = doc.get('content', doc.get('text', doc.get('document', str(doc))))
            else:
                text = str(doc)
            
            if len(text) > 500:
                text = text[:500] + "..."
            
            context_parts.append(f"[Document {i}]\n{text}")
        
        return "\n\n".join(context_parts)
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the Gemini model
        """
        return {
            "model": self.model_name,
            "provider": "Google Gemini",
            "status": "configured"
        }


# Singleton instance
_gemini_instance: Optional[GeminiGenerator] = None


def get_gemini_generator(
    model_name: Optional[str] = None,
    api_key: Optional[str] = None
) -> GeminiGenerator:
    """
    Get or create singleton Gemini generator
    """
    global _gemini_instance
    
    if _gemini_instance is None:
        _gemini_instance = GeminiGenerator(model_name=model_name, api_key=api_key)
    
    return _gemini_instance
