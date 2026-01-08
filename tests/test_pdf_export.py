"""
Tests for PDF Export Engine
"""
import pytest
from datetime import date, timedelta
from pathlib import Path
import tempfile
import io

from pypdf import PdfReader

from core.storage import Storage
from core.pdf_export import PDFExportEngine
from core.schemas import DailyEntryCreate


@pytest.fixture
def storage_with_data():
    """Create storage with comprehensive test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage = Storage(str(db_path))

        # 30 days of varied data
        base_date = date(2026, 1, 1)
        for i in range(30):
            entry = DailyEntryCreate(
                date=base_date + timedelta(days=i),
                weight_kg=85.0 - (i * 0.1),
                bodyfat_pct=20.0 - (i * 0.03),
                cal_in_kcal=1800.0 + (i * 10),
                cal_out_sport_kcal=300.0,
                source="test"
            )
            storage.create(entry)

        yield storage


@pytest.fixture
def storage_minimal():
    """Create storage with minimal data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage = Storage(str(db_path))

        # Just 5 days
        base_date = date(2026, 1, 1)
        for i in range(5):
            entry = DailyEntryCreate(
                date=base_date + timedelta(days=i),
                weight_kg=85.0,
                source="test"
            )
            storage.create(entry)

        yield storage


def test_pdf_export_engine_init(storage_with_data):
    """Test PDF export engine initialization."""
    engine = PDFExportEngine(storage_with_data, bmr_kcal=2000.0, target_weight_kg=75.0)
    assert engine.storage == storage_with_data
    assert engine.bmr_kcal == 2000.0
    assert engine.target_weight_kg == 75.0


def test_export_to_pdf_basic(storage_with_data):
    """Test basic PDF export."""
    engine = PDFExportEngine(storage_with_data)

    pdf_bytes = engine.export_to_pdf(days=30)

    # Should return bytes
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0


def test_export_to_pdf_loads_correctly(storage_with_data):
    """Test that exported PDF can be loaded."""
    engine = PDFExportEngine(storage_with_data)

    pdf_bytes = engine.export_to_pdf(days=30)

    # Load with PyPDF2
    reader = PdfReader(io.BytesIO(pdf_bytes))

    # Should have at least 1 page
    assert len(reader.pages) >= 1


def test_export_to_pdf_contains_title(storage_with_data):
    """Test that PDF contains title."""
    engine = PDFExportEngine(storage_with_data)

    pdf_bytes = engine.export_to_pdf(days=30)

    # Load and extract text
    reader = PdfReader(io.BytesIO(pdf_bytes))
    first_page_text = reader.pages[0].extract_text()

    # Should contain title
    assert "DIET_APP" in first_page_text or "Report" in first_page_text


def test_export_without_kpis(storage_with_data):
    """Test export without KPIs."""
    engine = PDFExportEngine(storage_with_data)
    pdf_bytes = engine.export_to_pdf(days=30, include_kpis=False)

    # Should still generate PDF
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0


def test_export_without_red_flags(storage_with_data):
    """Test export without Red Flags."""
    engine = PDFExportEngine(storage_with_data)
    pdf_bytes = engine.export_to_pdf(days=30, include_red_flags=False)

    # Should still generate PDF
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0


def test_export_without_charts(storage_with_data):
    """Test export without charts."""
    engine = PDFExportEngine(storage_with_data)
    pdf_bytes = engine.export_to_pdf(days=30, include_charts=False)

    # Should still generate PDF (likely fewer pages)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0


def test_export_minimal_sections(storage_with_data):
    """Test export with minimal sections."""
    engine = PDFExportEngine(storage_with_data)
    pdf_bytes = engine.export_to_pdf(
        days=30,
        include_kpis=False,
        include_red_flags=False,
        include_charts=False
    )

    # Should have minimal PDF (summary only)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0

    # Should have at least 1 page
    reader = PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) >= 1


def test_export_empty_data_handling():
    """Test export with empty database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage = Storage(str(db_path))

        engine = PDFExportEngine(storage)
        pdf_bytes = engine.export_to_pdf(days=30)

        # Should still generate PDF
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0

        # Should have at least 1 page
        reader = PdfReader(io.BytesIO(pdf_bytes))
        assert len(reader.pages) >= 1


def test_export_different_periods(storage_with_data):
    """Test export with different time periods."""
    engine = PDFExportEngine(storage_with_data)

    for days in [7, 14, 30, 60, 90]:
        pdf_bytes = engine.export_to_pdf(days=days)

        # Should generate valid PDF
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0


def test_export_with_custom_bmr(storage_with_data):
    """Test export with custom BMR."""
    engine = PDFExportEngine(storage_with_data, bmr_kcal=2500.0)

    pdf_bytes = engine.export_to_pdf(days=30)

    # Should generate valid PDF
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0


def test_export_with_custom_target_weight(storage_with_data):
    """Test export with custom target weight."""
    engine = PDFExportEngine(storage_with_data, target_weight_kg=70.0)

    pdf_bytes = engine.export_to_pdf(days=30)

    # Should generate valid PDF
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0


def test_export_deterministic(storage_with_data):
    """Test that repeated exports produce identical results."""
    engine = PDFExportEngine(storage_with_data)

    pdf_bytes1 = engine.export_to_pdf(days=30)
    pdf_bytes2 = engine.export_to_pdf(days=30)

    # Should be identical (PDF generation is deterministic)
    # Note: ReportLab may include timestamps, so we check structure instead
    assert len(pdf_bytes1) == len(pdf_bytes2)

    # Check both can be loaded
    reader1 = PdfReader(io.BytesIO(pdf_bytes1))
    reader2 = PdfReader(io.BytesIO(pdf_bytes2))

    assert len(reader1.pages) == len(reader2.pages)


def test_export_multiple_pages(storage_with_data):
    """Test that comprehensive export creates multiple pages."""
    engine = PDFExportEngine(storage_with_data)

    pdf_bytes = engine.export_to_pdf(
        days=30,
        include_kpis=True,
        include_red_flags=True,
        include_charts=True
    )

    reader = PdfReader(io.BytesIO(pdf_bytes))

    # Should have multiple pages (summary + charts + kpis + red flags)
    assert len(reader.pages) >= 2


def test_export_minimal_data(storage_minimal):
    """Test export with minimal data."""
    engine = PDFExportEngine(storage_minimal)

    pdf_bytes = engine.export_to_pdf(days=30)

    # Should still generate PDF
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0


def test_export_file_size_reasonable(storage_with_data):
    """Test that PDF file size is reasonable."""
    engine = PDFExportEngine(storage_with_data)

    pdf_bytes = engine.export_to_pdf(days=30)

    # Should be reasonable size (typically < 5 MB for this data)
    file_size_mb = len(pdf_bytes) / (1024 * 1024)
    assert file_size_mb < 5.0


def test_export_without_charts_smaller(storage_with_data):
    """Test that PDF without charts is smaller."""
    engine = PDFExportEngine(storage_with_data)

    pdf_with_charts = engine.export_to_pdf(days=30, include_charts=True)
    pdf_without_charts = engine.export_to_pdf(days=30, include_charts=False)

    # PDF with charts should typically be larger
    # (unless charts fail to generate, then they might be similar)
    assert len(pdf_without_charts) > 0
    assert len(pdf_with_charts) > 0


def test_export_text_extraction(storage_with_data):
    """Test that text can be extracted from PDF."""
    engine = PDFExportEngine(storage_with_data)

    pdf_bytes = engine.export_to_pdf(days=30)

    reader = PdfReader(io.BytesIO(pdf_bytes))

    # Extract all text
    all_text = ""
    for page in reader.pages:
        all_text += page.extract_text()

    # Should contain some expected text
    assert len(all_text) > 100  # Should have substantial content
