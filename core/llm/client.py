"""
Ollama Client for DIET_APP
Provides a simple wrapper around Ollama API for local LLM inference.
"""
import requests
import json
import time
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with local Ollama instance."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2:latest"):
        """
        Initialize Ollama client.

        Args:
            base_url: Ollama API base URL (default: http://localhost:11434)
            model: Model name to use (default: llama3.2:latest)
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self._available = None

    def is_available(self) -> bool:
        """
        Check if Ollama is available and running.

        Returns:
            True if Ollama is available, False otherwise
        """
        if self._available is not None:
            return self._available

        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            self._available = response.status_code == 200
            return self._available
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")
            self._available = False
            return False

    def list_models(self) -> List[str]:
        """
        List available models in Ollama.

        Returns:
            List of model names
        """
        if not self.is_available():
            return []

        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            data = response.json()
            return [model['name'] for model in data.get('models', [])]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Generate completion from Ollama.

        Args:
            prompt: User prompt
            system: System prompt (optional)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate (optional)
            stream: Whether to stream response (not implemented)

        Returns:
            Dict with 'response', 'tokens', 'duration_ms'

        Raises:
            RuntimeError: If Ollama is not available
            requests.RequestException: If API call fails
        """
        if not self.is_available():
            raise RuntimeError("Ollama is not available. Please ensure Ollama is running.")

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }

        if system:
            payload["system"] = system

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        start_time = time.time()

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120  # 2 minutes timeout for generation
            )
            response.raise_for_status()
            data = response.json()

            duration_ms = int((time.time() - start_time) * 1000)

            return {
                'response': data.get('response', ''),
                'model': data.get('model', self.model),
                'total_duration': data.get('total_duration', 0),
                'load_duration': data.get('load_duration', 0),
                'prompt_eval_count': data.get('prompt_eval_count', 0),
                'eval_count': data.get('eval_count', 0),
                'duration_ms': duration_ms,
                'tokens_generated': data.get('eval_count', 0),
            }

        except requests.exceptions.Timeout:
            raise RuntimeError("Ollama request timed out after 120 seconds")
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API error: {e}")
            raise

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Chat completion with Ollama.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Dict with 'response', 'tokens', 'duration_ms'
        """
        if not self.is_available():
            raise RuntimeError("Ollama is not available. Please ensure Ollama is running.")

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        start_time = time.time()

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            data = response.json()

            duration_ms = int((time.time() - start_time) * 1000)

            return {
                'response': data.get('message', {}).get('content', ''),
                'model': data.get('model', self.model),
                'total_duration': data.get('total_duration', 0),
                'load_duration': data.get('load_duration', 0),
                'prompt_eval_count': data.get('prompt_eval_count', 0),
                'eval_count': data.get('eval_count', 0),
                'duration_ms': duration_ms,
                'tokens_generated': data.get('eval_count', 0),
            }

        except requests.exceptions.Timeout:
            raise RuntimeError("Ollama request timed out after 120 seconds")
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API error: {e}")
            raise
