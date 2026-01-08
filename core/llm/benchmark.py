"""
LLM Benchmark Module for DIET_APP
Benchmarks local LLM performance on DGX Spark for diet/training narration tasks.
"""
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import logging

from core.llm.client import OllamaClient
from core.storage import Storage
from core.llm.narration import NarrationEngine

logger = logging.getLogger(__name__)


class LLMBenchmark:
    """
    Benchmark LLM performance for DIET_APP use cases.
    Measures: tokens/s, latency, time-to-first-token, quality (heuristic).
    """

    def __init__(
        self,
        ollama_client: Optional[OllamaClient] = None,
        storage: Optional[Storage] = None
    ):
        """
        Initialize benchmark.

        Args:
            ollama_client: Ollama client to benchmark
            storage: Storage instance for realistic data (optional)
        """
        self.ollama_client = ollama_client or OllamaClient()
        self.storage = storage
        self.results: List[Dict[str, Any]] = []

    def benchmark_generation(
        self,
        prompt: str,
        system: Optional[str] = None,
        num_runs: int = 3,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Benchmark a single generation task.

        Args:
            prompt: Test prompt
            system: System prompt
            num_runs: Number of runs to average
            temperature: Sampling temperature

        Returns:
            Benchmark results dict
        """
        if not self.ollama_client.is_available():
            return {
                'error': 'Ollama not available',
                'available': False
            }

        results = []

        for i in range(num_runs):
            try:
                start = time.time()
                response = self.ollama_client.generate(
                    prompt=prompt,
                    system=system,
                    temperature=temperature
                )
                duration = time.time() - start

                results.append({
                    'run': i + 1,
                    'duration_ms': int(duration * 1000),
                    'tokens_generated': response.get('tokens_generated', 0),
                    'prompt_eval_count': response.get('prompt_eval_count', 0),
                    'total_duration_ns': response.get('total_duration', 0),
                    'load_duration_ns': response.get('load_duration', 0),
                    'response_length': len(response.get('response', ''))
                })

            except Exception as e:
                logger.error(f"Benchmark run {i+1} failed: {e}")
                results.append({'run': i + 1, 'error': str(e)})

        # Calculate aggregates
        valid_results = [r for r in results if 'error' not in r]

        if not valid_results:
            return {
                'error': 'All runs failed',
                'results': results
            }

        avg_duration_ms = sum(r['duration_ms'] for r in valid_results) / len(valid_results)
        avg_tokens = sum(r['tokens_generated'] for r in valid_results) / len(valid_results)
        tokens_per_second = (avg_tokens / avg_duration_ms * 1000) if avg_duration_ms > 0 else 0

        # Time to first token (estimated from load_duration)
        avg_ttft_ms = sum(r['load_duration_ns'] for r in valid_results) / len(valid_results) / 1_000_000

        return {
            'available': True,
            'num_runs': num_runs,
            'avg_duration_ms': avg_duration_ms,
            'avg_tokens_generated': avg_tokens,
            'tokens_per_second': tokens_per_second,
            'avg_time_to_first_token_ms': avg_ttft_ms,
            'min_duration_ms': min(r['duration_ms'] for r in valid_results),
            'max_duration_ms': max(r['duration_ms'] for r in valid_results),
            'model': self.ollama_client.model,
            'runs': valid_results
        }

    def benchmark_narration(
        self,
        days: int = 30,
        num_runs: int = 3
    ) -> Dict[str, Any]:
        """
        Benchmark realistic narration task using actual data.

        Args:
            days: Number of days to analyze
            num_runs: Number of runs

        Returns:
            Benchmark results
        """
        if not self.storage:
            return {
                'error': 'Storage required for narration benchmark',
                'available': False
            }

        if not self.ollama_client.is_available():
            return {
                'error': 'Ollama not available',
                'available': False
            }

        narration_engine = NarrationEngine(
            storage=self.storage,
            ollama_client=self.ollama_client
        )

        results = []

        for i in range(num_runs):
            try:
                start = time.time()
                result = narration_engine.generate_summary(days=days, temperature=0.3)
                duration = time.time() - start

                if result.get('error'):
                    results.append({'run': i + 1, 'error': result['error']})
                else:
                    results.append({
                        'run': i + 1,
                        'duration_ms': int(duration * 1000),
                        'summary_length': len(result.get('summary', '')),
                        'model': result.get('model'),
                        'llm_duration_ms': result.get('duration_ms'),
                        'has_validation_warning': 'validation_warning' in result
                    })

            except Exception as e:
                logger.error(f"Narration benchmark run {i+1} failed: {e}")
                results.append({'run': i + 1, 'error': str(e)})

        valid_results = [r for r in results if 'error' not in r]

        if not valid_results:
            return {
                'error': 'All narration runs failed',
                'results': results
            }

        avg_duration_ms = sum(r['duration_ms'] for r in valid_results) / len(valid_results)

        return {
            'available': True,
            'task': 'narration',
            'days': days,
            'num_runs': num_runs,
            'avg_total_duration_ms': avg_duration_ms,
            'avg_llm_duration_ms': sum(r['llm_duration_ms'] for r in valid_results) / len(valid_results),
            'model': valid_results[0].get('model'),
            'runs': valid_results
        }

    def benchmark_suite(self, save_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Run comprehensive benchmark suite.

        Args:
            save_path: Path to save results JSON (optional)

        Returns:
            Complete benchmark results
        """
        suite_results = {
            'timestamp': datetime.now().isoformat(),
            'model': self.ollama_client.model,
            'ollama_available': self.ollama_client.is_available(),
            'benchmarks': {}
        }

        if not suite_results['ollama_available']:
            suite_results['error'] = 'Ollama not available'
            return suite_results

        # Test 1: Simple generation
        logger.info("Running simple generation benchmark...")
        suite_results['benchmarks']['simple_generation'] = self.benchmark_generation(
            prompt="Hello, how are you?",
            num_runs=3,
            temperature=0.7
        )

        # Test 2: Structured prompt (like narration)
        logger.info("Running structured prompt benchmark...")
        test_facts = {
            'weight_kg': 80.5,
            'weight_change_kg': -2.3,
            'avg_calories': 1800,
            'coverage_pct': 85
        }
        suite_results['benchmarks']['structured_prompt'] = self.benchmark_generation(
            prompt=f"Analyze this data and provide insights:\n{json.dumps(test_facts, indent=2)}",
            system="You are a data analyst. Provide concise insights.",
            num_runs=3,
            temperature=0.3
        )

        # Test 3: Narration (if storage available)
        if self.storage:
            logger.info("Running narration benchmark with real data...")
            suite_results['benchmarks']['narration_30d'] = self.benchmark_narration(
                days=30,
                num_runs=3
            )
        else:
            suite_results['benchmarks']['narration_30d'] = {
                'skipped': 'No storage provided'
            }

        # Calculate summary metrics
        suite_results['summary'] = self._calculate_summary(suite_results['benchmarks'])

        # Save if path provided
        if save_path:
            try:
                save_path.parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, 'w') as f:
                    json.dump(suite_results, f, indent=2)
                logger.info(f"Benchmark results saved to {save_path}")
                suite_results['saved_to'] = str(save_path)
            except Exception as e:
                logger.error(f"Failed to save benchmark results: {e}")
                suite_results['save_error'] = str(e)

        return suite_results

    def _calculate_summary(self, benchmarks: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate summary statistics across all benchmarks."""
        summary = {
            'total_benchmarks': len(benchmarks),
            'successful': sum(1 for b in benchmarks.values() if b.get('available', False))
        }

        # Aggregate tokens/s
        tps_values = [
            b.get('tokens_per_second', 0)
            for b in benchmarks.values()
            if 'tokens_per_second' in b
        ]
        if tps_values:
            summary['avg_tokens_per_second'] = sum(tps_values) / len(tps_values)
            summary['max_tokens_per_second'] = max(tps_values)

        # Aggregate latencies
        latency_values = [
            b.get('avg_duration_ms', 0)
            for b in benchmarks.values()
            if 'avg_duration_ms' in b
        ]
        if latency_values:
            summary['avg_latency_ms'] = sum(latency_values) / len(latency_values)

        return summary

    def export_results(self, path: Path) -> None:
        """
        Export all accumulated results to JSON.

        Args:
            path: Output file path
        """
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w') as f:
                json.dump(self.results, f, indent=2)
            logger.info(f"Exported benchmark results to {path}")
        except Exception as e:
            logger.error(f"Failed to export results: {e}")
            raise
