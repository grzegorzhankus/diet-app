"""
Comprehensive tests for LLM integration (Client, Narration, Q&A, Benchmark)
Uses mocking to avoid requiring actual Ollama instance.
"""
import pytest
from unittest.mock import Mock, patch
from datetime import date, timedelta
from pathlib import Path
import tempfile
import json
import requests

from core.storage import Storage
from core.schemas import DailyEntryCreate
from core.llm.client import OllamaClient
from core.llm.narration import NarrationEngine
from core.llm.qa_engine import QAEngine
from core.llm.benchmark import LLMBenchmark


# ======== Fixtures ========

@pytest.fixture
def storage_with_data():
    """Create storage with test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage = Storage(str(db_path))

        base_date = date(2026, 1, 1)
        for i in range(30):
            entry = DailyEntryCreate(
                date=base_date + timedelta(days=i),
                weight_kg=82.0 - (i * 0.1),
                bodyfat_pct=22.0 - (i * 0.05) if i % 2 == 0 else None,
                cal_in_kcal=1900 + (i % 5) * 50,
                cal_out_sport_kcal=300 + (i % 3) * 50,
                notes=f"Day {i+1}",
                source="test"
            )
            storage.create(entry)

        yield storage


@pytest.fixture
def mock_ollama_client():
    """Create mock Ollama client."""
    client = Mock(spec=OllamaClient)
    client.is_available.return_value = True
    client.model = "llama3.2:latest"
    return client


@pytest.fixture
def mock_requests():
    """Mock requests module."""
    with patch('core.llm.client.requests') as mock:
        yield mock


# ======== OllamaClient Tests (11 tests) ========

def test_ollama_client_init():
    """Test OllamaClient initialization."""
    client = OllamaClient()
    assert client.base_url == "http://localhost:11434"
    assert client.model == "llama3.2:latest"


def test_is_available_success(mock_requests):
    """Test is_available when Ollama is running."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_requests.get.return_value = mock_response

    client = OllamaClient()
    assert client.is_available() is True


def test_is_available_failure(mock_requests):
    """Test is_available when Ollama is not running."""
    mock_requests.get.side_effect = requests.exceptions.ConnectionError()

    client = OllamaClient()
    assert client.is_available() is False


def test_generate_success(mock_requests):
    """Test successful generation."""
    mock_get = Mock()
    mock_get.status_code = 200
    mock_requests.get.return_value = mock_get

    mock_post = Mock()
    mock_post.json.return_value = {
        'response': 'Generated text',
        'model': 'llama3.2:latest',
        'total_duration': 1000000000,
        'eval_count': 20
    }
    mock_requests.post.return_value = mock_post

    client = OllamaClient()
    result = client.generate(prompt="Test", temperature=0.5)

    assert result['response'] == 'Generated text'
    assert result['tokens_generated'] == 20


def test_generate_unavailable():
    """Test generation when Ollama unavailable."""
    client = OllamaClient()
    client._available = False

    with pytest.raises(RuntimeError, match="Ollama is not available"):
        client.generate(prompt="Test")


# ======== NarrationEngine Tests (5 tests) ========

def test_narration_engine_init(storage_with_data):
    """Test NarrationEngine initialization."""
    engine = NarrationEngine(storage=storage_with_data)
    assert engine.storage == storage_with_data
    assert engine.bmr_kcal == 2000.0


def test_extract_facts(storage_with_data):
    """Test fact extraction from data."""
    engine = NarrationEngine(storage=storage_with_data)
    facts = engine._extract_facts(days=30)

    assert 'period' in facts
    assert 'summary' in facts
    assert 'kpis' in facts
    assert 'red_flags' in facts
    assert facts['period']['days'] == 30
    assert len(facts['kpis']) > 0


def test_generate_summary_ollama_unavailable(storage_with_data):
    """Test summary generation when Ollama unavailable."""
    mock_client = Mock(spec=OllamaClient)
    mock_client.is_available.return_value = False

    engine = NarrationEngine(storage=storage_with_data, ollama_client=mock_client)
    result = engine.generate_summary(days=30)

    assert result['summary'] is None
    assert result['facts'] is not None
    assert result['available'] is False


def test_generate_summary_success(storage_with_data, mock_ollama_client):
    """Test successful summary generation."""
    mock_ollama_client.generate.return_value = {
        'response': 'You have made good progress.',
        'model': 'llama3.2:latest',
        'duration_ms': 1500
    }

    engine = NarrationEngine(storage=storage_with_data, ollama_client=mock_ollama_client)
    result = engine.generate_summary(days=30)

    assert result['summary'] is not None
    assert result['available'] is True
    assert result['model'] == 'llama3.2:latest'


def test_generate_recommendation_success(storage_with_data, mock_ollama_client):
    """Test recommendation generation."""
    mock_ollama_client.generate.return_value = {
        'response': 'Maintain your current routine.',
        'model': 'llama3.2:latest',
        'duration_ms': 1200
    }

    engine = NarrationEngine(storage=storage_with_data, ollama_client=mock_ollama_client)
    result = engine.generate_recommendation(focus='general')

    assert result['recommendation'] is not None
    assert result['available'] is True


# ======== QAEngine Tests (4 tests) ========

def test_qa_engine_init(storage_with_data):
    """Test QAEngine initialization."""
    engine = QAEngine(storage=storage_with_data)
    assert engine.storage == storage_with_data


def test_retrieve_context(storage_with_data):
    """Test context retrieval."""
    engine = QAEngine(storage=storage_with_data)
    context = engine._retrieve_context("What is my weight?", days=30)

    assert 'summary' in context
    assert context['period_days'] == 30


def test_ask_ollama_unavailable(storage_with_data):
    """Test asking question when Ollama unavailable."""
    mock_client = Mock(spec=OllamaClient)
    mock_client.is_available.return_value = False

    engine = QAEngine(storage=storage_with_data, ollama_client=mock_client)
    result = engine.ask("What is my weight?", days=30)

    assert result['answer'] is not None  # Fallback provided
    assert result['available'] is False


def test_ask_success(storage_with_data, mock_ollama_client):
    """Test successful question answering."""
    mock_ollama_client.generate.return_value = {
        'response': 'Your weight is improving.',
        'model': 'llama3.2:latest',
        'duration_ms': 1300
    }

    engine = QAEngine(storage=storage_with_data, ollama_client=mock_ollama_client)
    result = engine.ask("How is my weight?", days=30)

    assert result['answer'] is not None
    assert result['available'] is True


# ======== LLMBenchmark Tests (5 tests) ========

def test_benchmark_init():
    """Test LLMBenchmark initialization."""
    benchmark = LLMBenchmark()
    assert benchmark.ollama_client is not None
    assert benchmark.results == []


def test_benchmark_generation_unavailable():
    """Test benchmark when Ollama unavailable."""
    mock_client = Mock(spec=OllamaClient)
    mock_client.is_available.return_value = False

    benchmark = LLMBenchmark(ollama_client=mock_client)
    result = benchmark.benchmark_generation(prompt="Test", num_runs=3)

    assert result['available'] is False


def test_benchmark_generation_success(mock_ollama_client):
    """Test successful generation benchmark."""
    mock_ollama_client.generate.return_value = {
        'response': 'Test',
        'tokens_generated': 10,
        'total_duration': 1000000000,
        'load_duration': 100000000,
        'prompt_eval_count': 5
    }

    benchmark = LLMBenchmark(ollama_client=mock_ollama_client)
    result = benchmark.benchmark_generation(prompt="Test", num_runs=3)

    assert result['available'] is True
    assert result['num_runs'] == 3
    assert 'tokens_per_second' in result


def test_benchmark_suite_success(mock_ollama_client):
    """Test successful benchmark suite."""
    mock_ollama_client.generate.return_value = {
        'response': 'Test',
        'tokens_generated': 15,
        'total_duration': 1000000000,
        'load_duration': 100000000,
        'prompt_eval_count': 5,
        'duration_ms': 1000
    }

    benchmark = LLMBenchmark(ollama_client=mock_ollama_client)
    result = benchmark.benchmark_suite()

    assert result['ollama_available'] is True
    assert 'benchmarks' in result
    assert 'summary' in result


def test_benchmark_suite_save(mock_ollama_client, tmp_path):
    """Test saving benchmark results."""
    mock_ollama_client.generate.return_value = {
        'response': 'Test',
        'tokens_generated': 10,
        'total_duration': 1000000000,
        'load_duration': 100000000,
        'prompt_eval_count': 5,
        'duration_ms': 1000
    }

    benchmark = LLMBenchmark(ollama_client=mock_ollama_client)
    save_path = tmp_path / "results.json"

    result = benchmark.benchmark_suite(save_path=save_path)

    assert save_path.exists()
    assert result['saved_to'] == str(save_path)
