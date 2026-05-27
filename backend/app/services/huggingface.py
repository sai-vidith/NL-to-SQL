"""
Hugging Face Inference API client wrapper for text embeddings and fallback generation models.
"""

from __future__ import annotations

import httpx
import structlog
from typing import Any
from app.core.config import get_settings
from app.core.exceptions import LLMError

logger = structlog.get_logger(__name__)
settings = get_settings()

class HuggingFaceClient:
    """
    Client for interacting with Hugging Face Serverless Inference API.
    Can be used as a backup/alternative embedding source or for open-source model inference.
    """
    def __init__(self) -> None:
        self.api_key = settings.huggingface_api_key
        self.embedding_model = settings.huggingface_embedding_model
        self.api_url = f"https://api-inference.huggingface.co/models/{self.embedding_model}"
        
        self.headers = {}
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

    async def get_embedding(self, text: str) -> list[float]:
        """
        Generate vector embeddings using a Hugging Face model (default: all-mpnet-base-v2).
        Returns a list of 768 floats.
        """
        payload = {"inputs": text, "options": {"wait_for_model": True}}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.api_url, json=payload, headers=self.headers)
                
                if response.status_code == 200:
                    result = response.json()
                    # Inference API typically returns a list of floats (1D) or a nested list
                    if isinstance(result, list):
                        if isinstance(result[0], list):
                            return [float(x) for x in result[0]]
                        return [float(x) for x in result]
                    raise LLMError(f"Unexpected response format from Hugging Face: {result}")
                else:
                    logger.warning("huggingface.embedding_failed_api_status", status=response.status_code, text=response.text)
                    # Return local fallback mock embedding of 768 dimensions
                    return [0.0] * 768
        except Exception as e:
            logger.error("huggingface.embedding_exception", error=str(e))
            # Graceful fallback to prevent application crash
            return [0.0] * 768

    async def generate_sql_fallback(self, prompt: str, model_id: str = "Qwen/Qwen2.5-Coder-7B-Instruct") -> str | None:
        """
        Attempt to generate SQL query using open-source Hugging Face models if Gemini fails.
        """
        if not self.api_key:
            logger.warning("huggingface.missing_api_key_skipping_generation")
            return None
            
        url = f"https://api-inference.huggingface.co/models/{model_id}"
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 512,
                "temperature": 0.1,
                "return_full_text": False
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=self.headers)
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list) and "generated_text" in result[0]:
                        return result[0]["generated_text"].strip()
                    elif isinstance(result, dict) and "generated_text" in result:
                        return result["generated_text"].strip()
                return None
        except Exception as e:
            logger.error("huggingface.text_generation_failed", error=str(e))
            return None
