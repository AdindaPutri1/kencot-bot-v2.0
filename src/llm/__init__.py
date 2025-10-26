"""
LLM module — menghubungkan reasoning dengan model eksternal (Gemini/Groq).
"""

from .reasoner import LLMReasoner
from .fallback_handler import FallbackHandler

__all__ = ["LLMReasoner", "FallbackHandler"]
