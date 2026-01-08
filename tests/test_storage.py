"""
Tests for storage layer
"""
import pytest
from datetime import date, timedelta
from pathlib import Path
import tempfile

from core.storage import Storage
from core.schemas import DailyEntryCreate, DailyEntryUpdate


@pytest.fixture
def temp_storage():
    """Create temporary storage for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage = Storage(str(db_path))
        yield storage


def test_storage_init(temp_storage):
    """Test storage initialization."""
    assert temp_storage.db_path.exists()
    assert temp_storage.count() == 0


def test_create_entry(temp_storage):
    """Test creating a new entry."""
    entry = DailyEntryCreate(
        date=date.today(),
        weight_kg=85.5,
        bodyfat_pct=18.5,
        cal_in_kcal=2200.0,
        cal_out_sport_kcal=450.0,
        notes="Test entry",
        source="manual"
    )

    saved = temp_storage.create(entry)

    assert saved.id is not None
    assert saved.date == entry.date
    assert saved.weight_kg == entry.weight_kg
    assert saved.bodyfat_pct == entry.bodyfat_pct
    assert temp_storage.count() == 1


def test_create_duplicate_date(temp_storage):
    """Test creating entry with duplicate date raises error."""
    entry = DailyEntryCreate(
        date=date.today(),
        weight_kg=85.5,
    )

    temp_storage.create(entry)

    with pytest.raises(ValueError, match="already exists"):
        temp_storage.create(entry)


def test_get_by_id(temp_storage):
    """Test retrieving entry by ID."""
    entry = DailyEntryCreate(date=date.today(), weight_kg=85.5)
    saved = temp_storage.create(entry)

    retrieved = temp_storage.get_by_id(saved.id)

    assert retrieved is not None
    assert retrieved.id == saved.id
    assert retrieved.weight_kg == saved.weight_kg


def test_get_by_date(temp_storage):
    """Test retrieving entry by date."""
    test_date = date.today()
    entry = DailyEntryCreate(date=test_date, weight_kg=85.5)
    temp_storage.create(entry)

    retrieved = temp_storage.get_by_date(test_date)

    assert retrieved is not None
    assert retrieved.date == test_date


def test_get_all(temp_storage):
    """Test retrieving all entries."""
    # Create 5 entries
    for i in range(5):
        entry = DailyEntryCreate(
            date=date.today() - timedelta(days=i),
            weight_kg=80.0 + i
        )
        temp_storage.create(entry)

    all_entries = temp_storage.get_all()

    assert len(all_entries) == 5
    # Should be sorted by date DESC
    assert all_entries[0].date > all_entries[-1].date


def test_get_all_with_limit(temp_storage):
    """Test retrieving entries with limit."""
    for i in range(10):
        entry = DailyEntryCreate(
            date=date.today() - timedelta(days=i),
            weight_kg=80.0
        )
        temp_storage.create(entry)

    limited = temp_storage.get_all(limit=3)

    assert len(limited) == 3


def test_get_all_with_date_filter(temp_storage):
    """Test retrieving entries with date filtering."""
    start = date.today() - timedelta(days=10)

    for i in range(15):
        entry = DailyEntryCreate(
            date=date.today() - timedelta(days=i),
            weight_kg=80.0
        )
        temp_storage.create(entry)

    filtered = temp_storage.get_all(start_date=start)

    assert len(filtered) <= 11  # Today + 10 days back


def test_update_entry(temp_storage):
    """Test updating an entry."""
    entry = DailyEntryCreate(
        date=date.today(),
        weight_kg=85.5,
        bodyfat_pct=18.5
    )
    saved = temp_storage.create(entry)

    # Update weight
    updates = DailyEntryUpdate(weight_kg=84.0)
    updated = temp_storage.update(saved.id, updates)

    assert updated.weight_kg == 84.0
    assert updated.bodyfat_pct == 18.5  # Should remain unchanged


def test_update_nonexistent_entry(temp_storage):
    """Test updating non-existent entry raises error."""
    updates = DailyEntryUpdate(weight_kg=80.0)

    with pytest.raises(ValueError, match="not found"):
        temp_storage.update(999, updates)


def test_delete_entry(temp_storage):
    """Test deleting an entry."""
    entry = DailyEntryCreate(date=date.today(), weight_kg=85.5)
    saved = temp_storage.create(entry)

    result = temp_storage.delete(saved.id)

    assert result is True
    assert temp_storage.count() == 0
    assert temp_storage.get_by_id(saved.id) is None


def test_delete_nonexistent_entry(temp_storage):
    """Test deleting non-existent entry returns False."""
    result = temp_storage.delete(999)
    assert result is False


def test_validation_weight_too_low():
    """Test weight validation (too low)."""
    with pytest.raises(ValueError):
        DailyEntryCreate(date=date.today(), weight_kg=20.0)


def test_validation_weight_too_high():
    """Test weight validation (too high)."""
    with pytest.raises(ValueError):
        DailyEntryCreate(date=date.today(), weight_kg=250.0)


def test_validation_bodyfat_negative():
    """Test body fat validation (negative)."""
    with pytest.raises(ValueError):
        DailyEntryCreate(date=date.today(), weight_kg=80.0, bodyfat_pct=-5.0)


def test_validation_calories_negative():
    """Test calorie validation (negative)."""
    with pytest.raises(ValueError):
        DailyEntryCreate(
            date=date.today(),
            weight_kg=80.0,
            cal_in_kcal=-100.0
        )
