"""
SQLite storage layer for DIET_APP
Handles database operations and CRUD for DailyEntry.
"""
import sqlite3
from datetime import date
from pathlib import Path
from typing import List, Optional
from contextlib import contextmanager

from core.schemas import DailyEntry, DailyEntryCreate, DailyEntryUpdate


class Storage:
    """SQLite storage manager for daily entries."""

    def __init__(self, db_path: str = "data/diet_app.db"):
        """
        Initialize storage.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_connection(self):
        """Get database connection context manager."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL UNIQUE,
                    weight_kg REAL NOT NULL,
                    bodyfat_pct REAL,
                    cal_in_kcal REAL,
                    cal_out_sport_kcal REAL,
                    notes TEXT,
                    source TEXT DEFAULT 'manual',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create index on date for fast lookups
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_date
                ON daily_entries(date DESC)
            """)

    def create(self, entry: DailyEntryCreate) -> DailyEntry:
        """
        Create a new daily entry.

        Args:
            entry: DailyEntryCreate schema

        Returns:
            Created DailyEntry with ID

        Raises:
            ValueError: If entry for this date already exists
        """
        entry_id = None
        with self._get_connection() as conn:
            try:
                cursor = conn.execute("""
                    INSERT INTO daily_entries
                    (date, weight_kg, bodyfat_pct, cal_in_kcal,
                     cal_out_sport_kcal, notes, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry.date.isoformat(),
                    entry.weight_kg,
                    entry.bodyfat_pct,
                    entry.cal_in_kcal,
                    entry.cal_out_sport_kcal,
                    entry.notes,
                    entry.source
                ))

                entry_id = cursor.lastrowid

            except sqlite3.IntegrityError:
                raise ValueError(f"Entry for date {entry.date} already exists")

        return self.get_by_id(entry_id)

    def get_by_id(self, entry_id: int) -> Optional[DailyEntry]:
        """Get entry by ID."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM daily_entries WHERE id = ?",
                (entry_id,)
            ).fetchone()

            if row:
                return self._row_to_entry(row)
            return None

    def get_by_date(self, entry_date: date) -> Optional[DailyEntry]:
        """Get entry by date."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM daily_entries WHERE date = ?",
                (entry_date.isoformat(),)
            ).fetchone()

            if row:
                return self._row_to_entry(row)
            return None

    def get_all(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[DailyEntry]:
        """
        Get all entries with optional filtering.

        Args:
            limit: Max number of entries to return
            offset: Number of entries to skip
            start_date: Filter entries >= this date
            end_date: Filter entries <= this date

        Returns:
            List of DailyEntry objects
        """
        query = "SELECT * FROM daily_entries WHERE 1=1"
        params = []

        if start_date:
            query += " AND date >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND date <= ?"
            params.append(end_date.isoformat())

        query += " ORDER BY date DESC"

        if limit:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_entry(row) for row in rows]

    def update(self, entry_id: int, updates: DailyEntryUpdate) -> DailyEntry:
        """
        Update an existing entry.

        Args:
            entry_id: ID of entry to update
            updates: DailyEntryUpdate schema with fields to update

        Returns:
            Updated DailyEntry

        Raises:
            ValueError: If entry not found
        """
        # Get existing entry
        existing = self.get_by_id(entry_id)
        if not existing:
            raise ValueError(f"Entry with id {entry_id} not found")

        # Build update query dynamically
        update_fields = []
        params = []

        for field, value in updates.model_dump(exclude_unset=True).items():
            update_fields.append(f"{field} = ?")
            params.append(value)

        if not update_fields:
            return existing

        # Add updated_at timestamp
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(entry_id)

        query = f"""
            UPDATE daily_entries
            SET {', '.join(update_fields)}
            WHERE id = ?
        """

        with self._get_connection() as conn:
            conn.execute(query, params)

        return self.get_by_id(entry_id)

    def delete(self, entry_id: int) -> bool:
        """
        Delete an entry by ID.

        Args:
            entry_id: ID of entry to delete

        Returns:
            True if deleted, False if not found
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM daily_entries WHERE id = ?",
                (entry_id,)
            )
            return cursor.rowcount > 0

    def count(self) -> int:
        """Get total count of entries."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) as cnt FROM daily_entries").fetchone()
            return row["cnt"]

    def _row_to_entry(self, row: sqlite3.Row) -> DailyEntry:
        """Convert SQLite row to DailyEntry."""
        return DailyEntry(
            id=row["id"],
            date=date.fromisoformat(row["date"]),
            weight_kg=row["weight_kg"],
            bodyfat_pct=row["bodyfat_pct"],
            cal_in_kcal=row["cal_in_kcal"],
            cal_out_sport_kcal=row["cal_out_sport_kcal"],
            notes=row["notes"],
            source=row["source"]
        )
