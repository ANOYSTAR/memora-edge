"""
Classification Agent — Predicts importance, category, and privacy labels.
Uses the local LLM (Ollama) for intelligent classification.
"""
import json
import re
from typing import Dict, Any, Optional, Tuple

import httpx

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import OLLAMA_HOST, OLLAMA_MODEL


CLASSIFICATION_PROMPT = """You are a memory classification AI. Analyze the following text and classify it.

TEXT: "{text}"

Respond with ONLY a JSON object (no markdown, no explanation):
{{
  "importance": "critical|high|medium|low",
  "importance_score": 0.0-1.0,
  "privacy": "local_only|sync_allowed",
  "category": "personal|work|maintenance|research|health"
}}

Rules:
- "critical" = safety, security, urgent issues (score 0.9-1.0)
- "high" = important deadlines, key decisions (score 0.7-0.89)
- "medium" = general useful information (score 0.4-0.69)
- "low" = casual, trivial info (score 0.1-0.39)
- "local_only" = contains passwords, private data, health info, financial details
- "sync_allowed" = safe to sync to cloud
- Choose the best category for the content

JSON:"""


class ClassificationAgent:
    """Classifies memories using the local LLM for importance, privacy, and category."""

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=60.0)
        return self._client

    async def classify(self, text: str) -> Dict[str, Any]:
        """
        Classify a memory text using the local LLM.
        Returns importance, importance_score, privacy, and category.
        Falls back to rule-based classification if LLM is unavailable.
        """
        try:
            return await self._llm_classify(text)
        except Exception as e:
            print(f"LLM classification failed, using fallback: {e}")
            return self._rule_based_classify(text)

    async def _llm_classify(self, text: str) -> Dict[str, Any]:
        """Use Ollama LLM for classification."""
        client = await self._get_client()
        prompt = CLASSIFICATION_PROMPT.format(text=text)

        response = await client.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 150,
                }
            }
        )
        response.raise_for_status()
        
        result_text = response.json().get("response", "")
        
        # Extract JSON from response
        json_match = re.search(r'\{[^}]+\}', result_text, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            return self._validate_classification(parsed)
        
        raise ValueError(f"Could not parse LLM response: {result_text}")

    def _rule_based_classify(self, text: str) -> Dict[str, Any]:
        """Fallback rule-based classification when LLM is unavailable."""
        text_lower = text.lower()
        
        # Importance
        critical_keywords = ["urgent", "emergency", "critical", "danger", "safety", "leak", "failure", "broken"]
        high_keywords = ["important", "deadline", "meeting", "inspection", "review", "priority"]
        low_keywords = ["maybe", "sometime", "just", "random", "fyi"]
        
        if any(k in text_lower for k in critical_keywords):
            importance = "critical"
            importance_score = 0.95
        elif any(k in text_lower for k in high_keywords):
            importance = "high"
            importance_score = 0.75
        elif any(k in text_lower for k in low_keywords):
            importance = "low"
            importance_score = 0.25
        else:
            importance = "medium"
            importance_score = 0.5
        
        # Privacy
        private_keywords = ["password", "secret", "private", "ssn", "credit card", "bank", "salary"]
        privacy = "local_only" if any(k in text_lower for k in private_keywords) else "sync_allowed"
        
        # Category
        if any(k in text_lower for k in ["machine", "generator", "maintenance", "repair", "inspection", "equipment"]):
            category = "maintenance"
        elif any(k in text_lower for k in ["work", "office", "project", "team", "meeting", "deadline"]):
            category = "work"
        elif any(k in text_lower for k in ["health", "doctor", "medicine", "symptom", "hospital"]):
            category = "health"
        elif any(k in text_lower for k in ["research", "study", "paper", "experiment", "data"]):
            category = "research"
        else:
            category = "personal"
        
        return {
            "importance": importance,
            "importance_score": importance_score,
            "privacy": privacy,
            "category": category,
        }

    def _validate_classification(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize classification output."""
        valid_importance = ["critical", "high", "medium", "low"]
        valid_privacy = ["local_only", "sync_allowed"]
        valid_category = ["personal", "work", "maintenance", "research", "health"]
        
        importance = data.get("importance", "medium").lower()
        if importance not in valid_importance:
            importance = "medium"
        
        importance_score = float(data.get("importance_score", 0.5))
        importance_score = max(0.0, min(1.0, importance_score))
        
        privacy = data.get("privacy", "sync_allowed").lower()
        if privacy not in valid_privacy:
            privacy = "sync_allowed"
        
        category = data.get("category", "personal").lower()
        if category not in valid_category:
            category = "personal"
        
        return {
            "importance": importance,
            "importance_score": round(importance_score, 2),
            "privacy": privacy,
            "category": category,
        }

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
