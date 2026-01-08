"""
Narration Engine for DIET_APP
Generates fact-based commentary and recommendations using local LLM with strict guard-rails.
"""
import json
import re
from typing import Dict, List, Optional, Any
from datetime import date, timedelta
import logging

from core.storage import Storage
from core.metrics import MetricsEngine
from core.kpi_engine import KPIEngine
from core.red_flags import RedFlagsEngine
from core.llm.client import OllamaClient

logger = logging.getLogger(__name__)


class NarrationEngine:
    """
    Generates natural language summaries based on computed metrics.
    CRITICAL: LLM cannot invent new numbers - only narrate existing facts.
    """

    def __init__(
        self,
        storage: Storage,
        ollama_client: Optional[OllamaClient] = None,
        bmr_kcal: float = 2000.0,
        target_weight_kg: float = 75.0
    ):
        """
        Initialize NarrationEngine.

        Args:
            storage: Data storage instance
            ollama_client: Ollama client (optional, will create default if None)
            bmr_kcal: Basal Metabolic Rate in kcal/day
            target_weight_kg: Target weight in kg
        """
        self.storage = storage
        self.ollama_client = ollama_client or OllamaClient()
        self.bmr_kcal = bmr_kcal
        self.target_weight_kg = target_weight_kg

        self.metrics = MetricsEngine(storage, bmr_kcal=bmr_kcal)
        self.kpis = KPIEngine(storage, target_weight_kg=target_weight_kg, bmr_kcal=bmr_kcal)
        self.red_flags = RedFlagsEngine(storage, bmr_kcal=bmr_kcal)

    def _extract_facts(self, days: int = 30) -> Dict[str, Any]:
        """
        Extract structured facts from metrics, KPIs, and red flags.
        These facts are the ONLY data the LLM can reference.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary of facts
        """
        kpis = self.kpis.compute_all_kpis(days=days)
        flags = self.red_flags.detect_all_flags(days=days)
        summary = self.metrics.get_summary_stats(days=days)

        facts = {
            'period': {
                'days': days,
                'start_date': (date.today() - timedelta(days=days)).isoformat(),
                'end_date': date.today().isoformat()
            },
            'summary': {
                'total_entries': summary.get('total_entries', 0),
                'coverage_percent': summary.get('coverage_pct', 0.0),
                'current_weight_kg': summary.get('current_weight_kg'),
                'weight_change_kg': summary.get('weight_change_kg'),
                'avg_weight_kg': summary.get('avg_weight_kg'),
                'current_bodyfat_pct': summary.get('current_bodyfat_pct'),
                'bodyfat_change_pp': summary.get('bodyfat_change_pp'),
                'avg_calories_in': summary.get('avg_calories_in'),
                'avg_calories_sport': summary.get('avg_calories_sport'),
                'avg_net_balance': summary.get('avg_net_balance'),
            },
            'kpis': [
                {
                    'id': kpi.id,
                    'name': kpi.name,
                    'value': kpi.value,
                    'unit': kpi.unit,
                    'is_good': bool(kpi.is_good) if kpi.is_good is not None else None,
                    'explanation': kpi.explanation
                }
                for kpi in kpis
            ],
            'red_flags': [
                {
                    'id': flag.id,
                    'severity': flag.severity,
                    'category': flag.category,
                    'title': flag.title,
                    'description': flag.description,
                    'recommendation': flag.recommendation
                }
                for flag in flags
            ],
            'target_weight_kg': self.target_weight_kg,
            'bmr_kcal': self.bmr_kcal
        }

        return facts

    def _build_system_prompt(self) -> str:
        """Build system prompt with strict guard-rails."""
        return """You are a diet and fitness analytics assistant. Your role is to provide concise, factual commentary based ONLY on the provided metrics.

CRITICAL RULES:
1. DO NOT invent, calculate, or mention ANY numbers not explicitly provided in the facts
2. DO NOT provide medical advice or diagnoses
3. DO NOT make up trends or patterns not shown in the data
4. Keep responses concise (2-4 paragraphs maximum)
5. Focus on actionable insights based on the KPIs and red flags
6. Use a professional, analytical tone (CFO-grade)
7. If data is incomplete, acknowledge it - don't guess

Your response should:
- Summarize the overall trend (weight, body composition)
- Highlight key KPIs (good and bad)
- Mention critical red flags with recommendations
- Provide 1-3 concrete, actionable suggestions based on the data"""

    def _build_narration_prompt(self, facts: Dict[str, Any]) -> str:
        """
        Build user prompt with facts for narration.

        Args:
            facts: Extracted facts dictionary

        Returns:
            Formatted prompt string
        """
        facts_json = json.dumps(facts, indent=2, default=str)

        prompt = f"""Analyze the following diet and training data and provide a brief summary with recommendations.

FACTS (DO NOT add any numbers not listed here):
{facts_json}

Provide a concise analysis covering:
1. Overall progress towards target weight ({facts['target_weight_kg']} kg)
2. Key performance indicators (mention 2-3 most important)
3. Critical red flags (if any) and their implications
4. 1-3 actionable recommendations

Keep it factual, professional, and under 200 words."""

        return prompt

    def generate_summary(self, days: int = 30, temperature: float = 0.3) -> Dict[str, Any]:
        """
        Generate a fact-based summary narration.

        Args:
            days: Number of days to analyze
            temperature: LLM temperature (lower = more deterministic)

        Returns:
            Dict with 'summary', 'facts', 'available', 'error'
        """
        result = {
            'summary': None,
            'facts': None,
            'available': False,
            'error': None,
            'model': None,
            'duration_ms': None
        }

        # Extract facts first (always works)
        try:
            facts = self._extract_facts(days=days)
            result['facts'] = facts
        except Exception as e:
            logger.error(f"Failed to extract facts: {e}")
            result['error'] = f"Failed to extract metrics: {str(e)}"
            return result

        # Check if LLM is available
        if not self.ollama_client.is_available():
            result['error'] = "Ollama is not available. Please ensure Ollama is running."
            return result

        # Generate narration
        try:
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_narration_prompt(facts)

            response = self.ollama_client.generate(
                prompt=user_prompt,
                system=system_prompt,
                temperature=temperature,
                max_tokens=500
            )

            result['summary'] = response['response'].strip()
            result['available'] = True
            result['model'] = response.get('model')
            result['duration_ms'] = response.get('duration_ms')

            # Validate: check for hallucinated numbers
            validation_warning = self._validate_no_hallucinations(result['summary'], facts)
            if validation_warning:
                logger.warning(f"Possible hallucination detected: {validation_warning}")
                result['validation_warning'] = validation_warning

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            result['error'] = f"Failed to generate summary: {str(e)}"

        return result

    def _validate_no_hallucinations(self, text: str, facts: Dict[str, Any]) -> Optional[str]:
        """
        Check if LLM response contains numbers not in the facts.
        This is a simple heuristic check, not foolproof.

        Args:
            text: LLM generated text
            facts: Original facts dictionary

        Returns:
            Warning message if suspicious numbers found, None otherwise
        """
        # Extract all numbers from the LLM response
        llm_numbers = set(re.findall(r'\b\d+\.?\d*\b', text))

        # Extract all numbers from facts (convert to strings)
        facts_str = json.dumps(facts)
        fact_numbers = set(re.findall(r'\b\d+\.?\d*\b', facts_str))

        # Find numbers in LLM output not in facts
        new_numbers = llm_numbers - fact_numbers

        # Filter out common safe numbers (years, percentages like 100)
        safe_numbers = {'2025', '2026', '100', '0', '1', '2', '3'}
        suspicious = new_numbers - safe_numbers

        if suspicious:
            return f"Response contains numbers not in facts: {suspicious}"

        return None

    def generate_recommendation(
        self,
        focus: str = "general",
        days: int = 30,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        Generate focused recommendations.

        Args:
            focus: Focus area ('general', 'weight', 'calories', 'consistency')
            days: Number of days to analyze
            temperature: LLM temperature

        Returns:
            Dict with 'recommendation', 'facts', 'available', 'error'
        """
        result = {
            'recommendation': None,
            'facts': None,
            'available': False,
            'error': None
        }

        try:
            facts = self._extract_facts(days=days)
            result['facts'] = facts
        except Exception as e:
            result['error'] = f"Failed to extract metrics: {str(e)}"
            return result

        if not self.ollama_client.is_available():
            result['error'] = "Ollama is not available."
            return result

        focus_prompts = {
            'general': "Provide 3 actionable recommendations to improve overall progress.",
            'weight': "Focus on weight trend and provide recommendations for better weight management.",
            'calories': "Analyze calorie balance and suggest adjustments to intake/expenditure.",
            'consistency': "Review data consistency and suggest ways to maintain better tracking habits."
        }

        try:
            system_prompt = self._build_system_prompt()
            facts_json = json.dumps(facts, indent=2, default=str)

            user_prompt = f"""Based on these facts:
{facts_json}

{focus_prompts.get(focus, focus_prompts['general'])}

Provide specific, actionable advice based ONLY on the metrics shown. Keep it under 150 words."""

            response = self.ollama_client.generate(
                prompt=user_prompt,
                system=system_prompt,
                temperature=temperature,
                max_tokens=400
            )

            result['recommendation'] = response['response'].strip()
            result['available'] = True
            result['model'] = response.get('model')
            result['duration_ms'] = response.get('duration_ms')

        except Exception as e:
            result['error'] = f"Failed to generate recommendation: {str(e)}"

        return result
