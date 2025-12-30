"""
Ollama LLM Generator
Handles communication with Ollama for answer generation
"""
import requests
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class OllamaGenerator:
    """
    Generator class for Ollama LLM integration
    Uses llama3.2:3b for natural language answer generation
    """
    
    def __init__(
        self,
        model_name: str = "llama3.2:3b",
        base_url: str = "http://localhost:11434",
        timeout: int = 120  # Increased for cold starts
    ):
        """
        Initialize Ollama Generator
        
        Args:
            model_name: Name of the Ollama model to use
            base_url: Base URL of Ollama server
            timeout: Request timeout in seconds
        """
        self.model_name = model_name
        self.base_url = base_url
        self.timeout = timeout
        
        logger.info(f"OllamaGenerator initialized with model: {model_name}")
    
    def check_health(self) -> bool:
        """
        Check if Ollama server is running and model is available
        
        Returns:
            True if Ollama is healthy, False otherwise
        """
        try:
            # Check if server is running
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                
                if self.model_name in model_names:
                    logger.info(f"✅ Ollama is healthy, model {self.model_name} is available")
                    return True
                else:
                    logger.warning(f"⚠️ Model {self.model_name} not found. Available: {model_names}")
                    logger.warning(f"   Run: ollama pull {self.model_name}")
                    return False
            else:
                logger.error(f"❌ Ollama server returned status {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ Cannot connect to Ollama at {self.base_url}")
            logger.error(f"   Make sure Ollama is running: ollama serve")
            return False
        except Exception as e:
            logger.error(f"❌ Ollama health check failed: {str(e)}")
            return False
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.3,
        **kwargs
    ) -> str:
        """
        Generate text using Ollama
        
        Args:
            prompt: The prompt to generate from
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0.0-1.0)
                - Lower (0.1-0.3) = More focused, factual (good for legal)
                - Higher (0.7-0.9) = More creative, diverse
            **kwargs: Additional Ollama parameters
            
        Returns:
            Generated text
            
        Raises:
            Exception: If generation fails
        """
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
                "top_p": kwargs.get('top_p', 0.9),
                "top_k": kwargs.get('top_k', 40),
            }
        }
        
        try:
            logger.debug(f"Generating with Ollama, prompt length: {len(prompt)} chars")
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get("response", "")
                
                # Log metrics
                total_duration = result.get("total_duration", 0) / 1e9  # Convert to seconds
                logger.info(f"✅ Generated {len(generated_text)} chars in {total_duration:.2f}s")
                
                return generated_text.strip()
            else:
                error_msg = f"Ollama returned status {response.status_code}: {response.text}"
                logger.error(f"❌ {error_msg}")
                raise Exception(error_msg)
                
        except requests.exceptions.Timeout:
            error_msg = f"Ollama request timed out after {self.timeout}s"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
        except requests.exceptions.ConnectionError:
            error_msg = f"Cannot connect to Ollama at {self.base_url}"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
        except Exception as e:
            logger.error(f"❌ Ollama generation failed: {str(e)}")
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
        # Build context from documents
        context_text = self._format_context(context_documents)
        
        # Build full prompt
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
        
        Args:
            documents: List of document strings or dicts
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, doc in enumerate(documents, 1):
            if isinstance(doc, dict):
                # Extract text from dict
                text = doc.get('content', doc.get('text', doc.get('document', str(doc))))
            else:
                text = str(doc)
            
            # Limit length per document
            if len(text) > 500:
                text = text[:500] + "..."
            
            context_parts.append(f"[Document {i}]\n{text}")
        
        return "\n\n".join(context_parts)
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model
        
        Returns:
            Dictionary with model information
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/show",
                json={"name": self.model_name},
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Status {response.status_code}"}
                
        except Exception as e:
            return {"error": str(e)}


# Singleton instance
_ollama_instance: Optional[OllamaGenerator] = None


def get_ollama_generator(
    model_name: str = "llama3.2:3b",
    base_url: str = "http://localhost:11434"
) -> OllamaGenerator:
    """
    Get or create singleton Ollama generator
    
    Args:
        model_name: Name of the Ollama model
        base_url: Base URL of Ollama server
        
    Returns:
        OllamaGenerator instance
    """
    global _ollama_instance
    
    if _ollama_instance is None:
        _ollama_instance = OllamaGenerator(model_name=model_name, base_url=base_url)
    
    return _ollama_instance
