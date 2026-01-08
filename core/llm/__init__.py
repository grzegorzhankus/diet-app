"""
LLM integration module for DIET_APP
Provides local LLM narration, Q&A, and benchmarking with Ollama.
"""
from core.llm.client import OllamaClient
from core.llm.narration import NarrationEngine
from core.llm.qa_engine import QAEngine
from core.llm.benchmark import LLMBenchmark

__all__ = ['OllamaClient', 'NarrationEngine', 'QAEngine', 'LLMBenchmark']
