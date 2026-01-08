"""
Data importer for DIET_APP
Imports historical data from Excel/CSV into SQLite.
"""
from datetime import date
from pathlib import Path
from typing import Dict, List
import pandas as pd

from core.schemas import DailyEntryCreate
from core.storage import Storage


class Importer:
    """Data importer for historical data."""

    def __init__(self, storage: Storage):
        """
        Initialize importer.

        Args:
            storage: Storage instance
        """
        self.storage = storage

    def import_excel(
        self,
        file_path: str,
        column_mapping: Dict[str, str],
        skip_duplicates: bool = True
    ) -> Dict[str, int]:
        """
        Import data from Excel file.

        Args:
            file_path: Path to Excel file
            column_mapping: Mapping of Excel columns to DailyEntry fields
                Example: {
                    'Date': 'date',
                    'Actual': 'weight_kg',
                    '% FAT': 'bodyfat_pct',
                    'Daily Food (IN)': 'cal_in_kcal',
                    'Excercise (OUT)': 'cal_out_sport_kcal'
                }
            skip_duplicates: If True, skip entries that already exist

        Returns:
            Dictionary with import statistics:
            {
                'total': total rows in file,
                'imported': successfully imported,
                'skipped': skipped (duplicates or invalid),
                'errors': errors encountered
            }
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Read Excel
        df = pd.read_excel(file_path)

        stats = {
            'total': len(df),
            'imported': 0,
            'skipped': 0,
            'errors': 0
        }

        for idx, row in df.iterrows():
            try:
                # Map columns to DailyEntry fields
                entry_data = {}

                for excel_col, entry_field in column_mapping.items():
                    if excel_col not in df.columns:
                        continue

                    value = row[excel_col]

                    # Handle pandas NaN/NaT
                    if pd.isna(value):
                        continue

                    # Convert date
                    if entry_field == 'date':
                        if isinstance(value, pd.Timestamp):
                            entry_data[entry_field] = value.date()
                        else:
                            entry_data[entry_field] = pd.to_datetime(value).date()
                    # Convert body fat % from decimal (0.0-1.0) to percentage (0-100)
                    elif entry_field == 'bodyfat_pct':
                        float_val = float(value)
                        # If value is < 1.5, assume it's in decimal format (e.g., 0.19 = 19%)
                        if float_val < 1.5:
                            entry_data[entry_field] = float_val * 100.0
                        else:
                            entry_data[entry_field] = float_val
                    # Exercise calories might be negative in Excel (treat as positive)
                    elif entry_field == 'cal_out_sport_kcal':
                        entry_data[entry_field] = abs(float(value))
                    else:
                        entry_data[entry_field] = float(value)

                # Skip if no date or weight
                if 'date' not in entry_data or 'weight_kg' not in entry_data:
                    stats['skipped'] += 1
                    continue

                # Check if entry already exists
                if skip_duplicates:
                    existing = self.storage.get_by_date(entry_data['date'])
                    if existing:
                        stats['skipped'] += 1
                        continue

                # Create entry
                entry = DailyEntryCreate(
                    source='import',
                    **entry_data
                )

                self.storage.create(entry)
                stats['imported'] += 1

            except Exception as e:
                stats['errors'] += 1
                print(f"Error importing row {idx}: {e}")

        return stats

    def import_weight_xlsx(
        self,
        file_path: str = "Weight.xlsx",
        skip_duplicates: bool = True
    ) -> Dict[str, int]:
        """
        Import Weight.xlsx with predefined column mapping.

        Args:
            file_path: Path to Weight.xlsx
            skip_duplicates: If True, skip existing entries

        Returns:
            Import statistics
        """
        column_mapping = {
            'Date': 'date',
            'Actual': 'weight_kg',
            '% FAT.1': 'bodyfat_pct',
            'Daily Food (IN)': 'cal_in_kcal',
            'Excercise (OUT)': 'cal_out_sport_kcal'
        }

        return self.import_excel(
            file_path=file_path,
            column_mapping=column_mapping,
            skip_duplicates=skip_duplicates
        )
