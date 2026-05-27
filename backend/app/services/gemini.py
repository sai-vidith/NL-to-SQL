"""
Gemini API client wrapper for SQL generation, schema embeddings,
intent classification, and natural language result summaries.
"""

from __future__ import annotations

import json
import structlog
from typing import Any

from google import genai
from google.genai import types
from app.core.config import get_settings
from app.core.exceptions import LLMError

logger = structlog.get_logger(__name__)
settings = get_settings()

class GeminiClient:
    def __init__(self) -> None:
        api_key = settings.gemini_api_key
        # Fallback to empty client or dummy check if API key is blank/mock
        if not api_key or api_key == "mock-key":
            logger.warning("gemini.client", status="missing_api_key_using_mock_fallback")
            self.client = None
        else:
            self.client = genai.Client(api_key=api_key)

    async def get_embedding(self, text: str) -> list[float]:
        """
        Generate high-quality vector embeddings using Google's embedding model.
        Falls back to Hugging Face embeddings if Gemini is not configured.
        Returns a 768-dimension float list.
        """
        if not self.client:
            # Fallback to Hugging Face client embeddings
            from app.services.huggingface import HuggingFaceClient
            hf_client = HuggingFaceClient()
            logger.info("gemini.get_embedding", status="using_huggingface_fallback")
            return await hf_client.get_embedding(text)
            
        try:
            response = self.client.models.embed_content(
                model=settings.gemini_embedding_model,
                contents=text,
            )
            return response.embeddings[0].values
        except Exception as e:
            logger.error("gemini.embedding_failed", error=str(e))
            raise LLMError(f"Failed to generate embeddings: {e}")


    async def generate_sql(self, prompt: str) -> str:
        """
        Ask Gemini to write optimal SQL query matching prompt rules.
        """
        if not self.client:
            # Local deterministic fallback logic
            return "SELECT * FROM biz_orders LIMIT 5;"

        try:
            response = self.client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,  # Low temperature for highly deterministic SQL code
                ),
            )
            sql_text = response.text.strip()
            # Strip markdown tags if present
            if sql_text.startswith("```sql"):
                sql_text = sql_text[6:]
            if sql_text.endswith("```"):
                sql_text = sql_text[:-3]
            return sql_text.strip()
        except Exception as e:
            logger.error("gemini.sql_generation_failed", error=str(e))
            raise LLMError(f"Failed to generate SQL query: {e}")

    async def generate_summary(self, question: str, sql: str, results_preview: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Asks Gemini to summarize the SQL output data structures and suggest
        corresponding Chart styles.
        """
        if not self.client:
            # Return basic summary format
            return {
                "summary": "Data retrieved successfully. Showing records from business tables.",
                "chart_recommendation": {
                    "chart_type": "bar",
                    "x_column": "month" if results_preview and "month" in results_preview[0] else "",
                    "y_column": "revenue" if results_preview and "revenue" in results_preview[0] else "",
                    "title": "Query Trend Analysis"
                }
            }

        prompt = f"""
        Given the SQL query results below, provide a concise natural language summary and recommendation.

        ORIGINAL QUESTION: {question}
        SQL EXECUTED: {sql}
        RESULTS PREVIEW: {json.dumps(results_preview[:10], default=str)}
        TOTAL ROWS: {len(results_preview)}

        Instructions:
        1. Start with a direct answer to the question.
        2. Highlight key insights (highest/lowest values, growth rates, etc.) in a conversational way.
        3. Recommend a chart visual: "bar", "line", "pie", or "none" (if visual isn't helpful).
        4. Return your output EXACTLY as a JSON object containing two keys: "summary" (str) and "chart_recommendation" (object with keys: chart_type, x_column, y_column, title).
        """

        try:
            response = self.client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error("gemini.summary_failed", error=str(e))
            return {
                "summary": "Database metrics computed successfully.",
                "chart_recommendation": {"chart_type": "none", "x_column": "", "y_column": "", "title": ""}
            }
