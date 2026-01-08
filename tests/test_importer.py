"""
Tests for data importer
"""
import pytest
from datetime import date
from pathlib import Path
import tempfile
import pandas as pd

from core.storage import Storage
from core.importer import Importer
from core.schemas import DailyEntryCreate


@pytest.fixture
def temp_storage():
    """Create temporary storage for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage = Storage(str(db_path))
        yield storage


@pytest.fixture
def sample_excel_file():
    """Create a sample Excel file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        # Create sample data
        data = {
            'Date': pd.date_range('2026-01-01', periods=5),
            'Actual': [85.5, 85.3, 85.1, 84.9, 84.7],
            '% FAT': [18.5, 18.4, 18.3, 18.2, 18.1],
            'Daily Food (IN)': [2200, 2100, 2300, 2000, 2150],
            'Excercise (OUT)': [450, 400, 500, 350, 420]
        }

        df = pd.DataFrame(data)
        df.to_excel(f.name, index=False)

        yield f.name

        # Cleanup
        Path(f.name).unlink()


def test_importer_init(temp_storage):
    """Test importer initialization."""
    importer = Importer(temp_storage)
    assert importer.storage == temp_storage


def test_import_excel_basic(temp_storage, sample_excel_file):
    """Test basic Excel import."""
    importer = Importer(temp_storage)

    column_mapping = {
        'Date': 'date',
        'Actual': 'weight_kg',
        '% FAT': 'bodyfat_pct',
        'Daily Food (IN)': 'cal_in_kcal',
        'Excercise (OUT)': 'cal_out_sport_kcal'
    }

    stats = importer.import_excel(sample_excel_file, column_mapping)

    assert stats['total'] == 5
    assert stats['imported'] == 5
    assert stats['skipped'] == 0
    assert stats['errors'] == 0
    assert temp_storage.count() == 5


def test_import_excel_skip_duplicates(temp_storage, sample_excel_file):
    """Test Excel import with duplicate skipping."""
    importer = Importer(temp_storage)

    column_mapping = {
        'Date': 'date',
        'Actual': 'weight_kg',
    }

    # First import
    stats1 = importer.import_excel(sample_excel_file, column_mapping)
    assert stats1['imported'] == 5

    # Second import (should skip all)
    stats2 = importer.import_excel(
        sample_excel_file,
        column_mapping,
        skip_duplicates=True
    )
    assert stats2['imported'] == 0
    assert stats2['skipped'] == 5


def test_import_excel_missing_columns(temp_storage):
    """Test import with missing required columns."""
    importer = Importer(temp_storage)

    # Create file with only date (no weight)
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        data = {'Date': pd.date_range('2026-01-01', periods=3)}
        df = pd.DataFrame(data)
        df.to_excel(f.name, index=False)

        column_mapping = {
            'Date': 'date',
            'Weight': 'weight_kg'  # Column doesn't exist
        }

        stats = importer.import_excel(f.name, column_mapping)

        # Should skip all (no weight data)
        assert stats['skipped'] == 3
        assert stats['imported'] == 0

        Path(f.name).unlink()


def test_import_excel_with_nulls(temp_storage):
    """Test import with null values."""
    importer = Importer(temp_storage)

    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        data = {
            'Date': pd.date_range('2026-01-01', periods=3),
            'Actual': [85.5, None, 84.7],  # Middle row has null weight
            '% FAT': [18.5, 18.4, None]  # Last row has null bodyfat
        }
        df = pd.DataFrame(data)
        df.to_excel(f.name, index=False)

        column_mapping = {
            'Date': 'date',
            'Actual': 'weight_kg',
            '% FAT': 'bodyfat_pct'
        }

        stats = importer.import_excel(f.name, column_mapping)

        # Should import 2 (skip middle row with no weight)
        assert stats['imported'] == 2
        assert stats['skipped'] == 1

        Path(f.name).unlink()


def test_import_weight_xlsx_integration(temp_storage):
    """Test import_weight_xlsx with mock file."""
    # This test requires Weight.xlsx to exist
    # We'll create a mock version
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        data = {
            'Date': pd.date_range('2020-01-01', periods=10),
            'Actual': [100.0 + i * 0.1 for i in range(10)],
            '% FAT': [20.0] * 10,
            'Daily Food (IN)': [2000] * 10,
            'Excercise (OUT)': [400] * 10
        }
        df = pd.DataFrame(data)
        df.to_excel(f.name, index=False)

        importer = Importer(temp_storage)
        stats = importer.import_weight_xlsx(f.name)

        assert stats['total'] == 10
        assert stats['imported'] == 10

        Path(f.name).unlink()
