"""
Q&A Engine for DIET_APP
Enables interactive questions over diet and training data using local LLM.
"""
import json
from typing import Dict, List, Optional, Any
from datetime import date, timedelta
import logging

from core.storage import Storage
from core.metrics import MetricsEngine
from core.kpi_engine import KPIEngine
from core.red_flags import RedFlagsEngine
from core.llm.client import OllamaClient

logger = logging.getLogger(__name__)


class QAEngine:
    """
    Question-answering engine over diet/training data.
    Uses structured data retrieval + LLM for natural language Q&A.
    """

    def __init__(
        self,
        storage: Storage,
        ollama_client: Optional[OllamaClient] = None,
        bmr_kcal: float = 2000.0,
        target_weight_kg: float = 75.0
    ):
        """
        Initialize QAEngine.

        Args:
            storage: Data storage instance
            ollama_client: Ollama client (optional)
            bmr_kcal: Basal Metabolic Rate
            target_weight_kg: Target weight
        """
        self.storage = storage
        self.ollama_client = ollama_client or OllamaClient()
        self.bmr_kcal = bmr_kcal
        self.target_weight_kg = target_weight_kg

        self.metrics = MetricsEngine(storage, bmr_kcal=bmr_kcal)
        self.kpis = KPIEngine(storage, target_weight_kg=target_weight_kg, bmr_kcal=bmr_kcal)
        self.red_flags = RedFlagsEngine(storage, bmr_kcal=bmr_kcal)

    def _retrieve_context(self, question: str, days: int = 90) -> Dict[str, Any]:
        """
        Retrieve relevant context for answering a question.
        Uses keyword matching and retrieves relevant metrics.

        Args:
            question: User question
            days: Number of days of data to include

        Returns:
            Context dictionary with relevant data
        """
        question_lower = question.lower()

        # Determine what data to retrieve based on keywords
        include_kpis = any(word in question_lower for word in [
            'kpi', 'performance', 'indicator', 'trend', 'progress',
            'improvement', 'worse', 'better'
        ])

        include_flags = any(word in question_lower for word in [
            'flag', 'red', 'warning', 'issue', 'problem', 'wrong',
            'alert', 'anomaly'
        ])

        include_weight = any(word in question_lower for word in [
            'weight', 'kg', 'mass', 'lose', 'gain', 'reduction'
        ])

        include_calories = any(word in question_lower for word in [
            'calorie', 'kcal', 'eat', 'intake', 'sport', 'exercise',
            'deficit', 'surplus', 'balance'
        ])

        include_bodyfat = any(word in question_lower for word in [
            'fat', 'bodyfat', 'body fat', 'bf%', 'composition', 'lean'
        ])

        # Get summary stats (always)
        summary = self.metrics.get_summary_stats(days=days)

        context = {
            'period_days': days,
            'summary': summary,
            'target_weight_kg': self.target_weight_kg,
            'bmr_kcal': self.bmr_kcal
        }

        # Add KPIs if relevant
        if include_kpis or 'all' in question_lower:
            kpis = self.kpis.compute_all_kpis(days=days)
            context['kpis'] = [
                {
                    'id': kpi.id,
                    'name': kpi.name,
                    'value': kpi.value,
                    'unit': kpi.unit,
                    'is_good': kpi.is_good,
                    'explanation': kpi.explanation
                }
                for kpi in kpis
            ]

        # Add red flags if relevant
        if include_flags or 'all' in question_lower:
            flags = self.red_flags.detect_all_flags(days=days)
            context['red_flags'] = [
                {
                    'id': flag.id,
                    'severity': flag.severity,
                    'title': flag.title,
                    'description': flag.description,
                    'recommendation': flag.recommendation
                }
                for flag in flags
            ]

        # Add detailed daily data if asking about specific metrics
        if include_weight or include_calories or include_bodyfat:
            from datetime import date
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            entries = self.storage.get_all(start_date=start_date, end_date=end_date)
            if entries:
                context['daily_data_sample'] = {
                    'num_entries': len(entries),
                    'first_date': entries[0].date.isoformat() if entries else None,
                    'last_date': entries[-1].date.isoformat() if entries else None,
                    'has_bodyfat': any(e.bodyfat_pct is not None for e in entries)
                }

        return context

    def _build_system_prompt(self) -> str:
        """Build system prompt for Q&A."""
        return """You are a data analysis assistant for diet and training tracking.
Answer user questions based ONLY on the provided context data.

RULES:
1. Only use facts from the provided context
2. If the answer is not in the context, say "I don't have enough data to answer that"
3. Cite specific metrics, dates, and values when answering
4. Keep answers concise (2-3 sentences)
5. Do not provide medical advice
6. Do not invent or calculate new numbers

Format your answers to be clear and actionable."""

    def ask(
        self,
        question: str,
        days: int = 90,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """
        Ask a question about the user's diet and training data.

        Args:
            question: Natural language question
            days: Number of days to include in context
            temperature: LLM temperature (lower = more factual)

        Returns:
            Dict with 'answer', 'context', 'available', 'error'
        """
        result = {
            'answer': None,
            'question': question,
            'context': None,
            'available': False,
            'error': None,
            'model': None,
            'duration_ms': None
        }

        # Retrieve context
        try:
            context = self._retrieve_context(question, days=days)
            result['context'] = context
        except Exception as e:
            logger.error(f"Failed to retrieve context: {e}")
            result['error'] = f"Failed to retrieve data: {str(e)}"
            return result

        # Check if LLM is available
        if not self.ollama_client.is_available():
            result['error'] = "Ollama is not available. Please ensure Ollama is running."
            # Provide fallback based on keywords
            result['answer'] = self._fallback_answer(question, context)
            return result

        # Generate answer using LLM
        try:
            system_prompt = self._build_system_prompt()
            context_json = json.dumps(context, indent=2, default=str)

            user_prompt = f"""Context (your diet/training data):
{context_json}

User question: {question}

Provide a concise, factual answer based only on the context above. Cite specific metrics and dates."""

            response = self.ollama_client.generate(
                prompt=user_prompt,
                system=system_prompt,
                temperature=temperature,
                max_tokens=300
            )

            result['answer'] = response['response'].strip()
            result['available'] = True
            result['model'] = response.get('model')
            result['duration_ms'] = response.get('duration_ms')

        except Exception as e:
            logger.error(f"LLM Q&A failed: {e}")
            result['error'] = f"Failed to generate answer: {str(e)}"
            # Provide fallback
            result['answer'] = self._fallback_answer(question, context)

        return result

    def _fallback_answer(self, question: str, context: Dict[str, Any]) -> str:
        """
        Provide a simple rule-based answer when LLM is unavailable.

        Args:
            question: User question
            context: Retrieved context

        Returns:
            Simple answer string
        """
        question_lower = question.lower()
        summary = context.get('summary', {})

        # Weight-related questions
        if 'weight' in question_lower:
            current = summary.get('current_weight_kg')
            change = summary.get('weight_change_kg')
            if current is not None:
                msg = f"Current weight: {current:.1f} kg"
                if change is not None:
                    msg += f", change: {change:+.1f} kg over {context['period_days']} days"
                return msg
            return "No weight data available."

        # Calorie-related questions
        if 'calorie' in question_lower or 'kcal' in question_lower:
            avg_in = summary.get('avg_calories_in')
            avg_net = summary.get('avg_net_balance')
            if avg_in is not None:
                msg = f"Average intake: {avg_in:.0f} kcal/day"
                if avg_net is not None:
                    msg += f", NET balance: {avg_net:+.0f} kcal/day"
                return msg
            return "No calorie data available."

        # Red flags
        if 'problem' in question_lower or 'issue' in question_lower or 'flag' in question_lower:
            flags = context.get('red_flags', [])
            if flags:
                critical = [f for f in flags if f['severity'] == 'critical']
                if critical:
                    return f"Critical issues: {critical[0]['title']}. {critical[0]['recommendation']}"
                return f"Found {len(flags)} red flag(s): {flags[0]['title']}"
            return "No red flags detected in this period."

        # Default
        entries = summary.get('total_entries', 0)
        coverage = summary.get('coverage_pct', 0)
        return f"Analyzed {entries} entries over {context['period_days']} days (coverage: {coverage:.0f}%). Please ask a more specific question or ensure Ollama is running for detailed analysis."

    def chat(
        self,
        messages: List[Dict[str, str]],
        days: int = 90,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """
        Multi-turn conversation about data.

        Args:
            messages: List of message dicts with 'role' and 'content'
            days: Number of days for context
            temperature: LLM temperature

        Returns:
            Dict with 'response', 'available', 'error'
        """
        result = {
            'response': None,
            'available': False,
            'error': None
        }

        if not self.ollama_client.is_available():
            result['error'] = "Ollama is not available."
            return result

        try:
            # Get context and prepend to messages
            context = self._retrieve_context(messages[-1]['content'], days=days)
            context_json = json.dumps(context, indent=2, default=str)

            system_message = {
                'role': 'system',
                'content': self._build_system_prompt() + f"\n\nCurrent context:\n{context_json}"
            }

            chat_messages = [system_message] + messages

            response = self.ollama_client.chat(
                messages=chat_messages,
                temperature=temperature,
                max_tokens=300
            )

            result['response'] = response['response']
            result['available'] = True
            result['model'] = response.get('model')
            result['duration_ms'] = response.get('duration_ms')

        except Exception as e:
            logger.error(f"Chat failed: {e}")
            result['error'] = f"Chat failed: {str(e)}"

        return result
