"""
Polish Holiday Calendar for DIET_APP
Provides Polish national holidays and observances for pattern analysis.
"""
from datetime import date, timedelta
from typing import Dict, List, Optional
from functools import lru_cache


class PolishHolidayCalendar:
    """
    Calendar of Polish national holidays and observances.
    Supports years 2020-2030 for diet tracking analysis.
    """

    # Fixed holidays (same date every year)
    FIXED_HOLIDAYS = {
        (1, 1): "Nowy Rok (New Year's Day)",
        (1, 6): "Trzech Króli (Epiphany)",
        (5, 1): "Święto Pracy (Labour Day)",
        (5, 3): "Święto Konstytucji 3 Maja (Constitution Day)",
        (8, 15): "Wniebowzięcie NMP (Assumption of Mary)",
        (11, 1): "Wszystkich Świętych (All Saints' Day)",
        (11, 11): "Święto Niepodległości (Independence Day)",
        (12, 25): "Boże Narodzenie (Christmas Day)",
        (12, 26): "Drugi Dzień Bożego Narodzenia (Boxing Day)",
    }

    def __init__(self):
        """Initialize Polish holiday calendar."""
        self._cache: Dict[int, Dict[date, str]] = {}

    @staticmethod
    def _calculate_easter(year: int) -> date:
        """
        Calculate Easter date using Meeus/Jones/Butcher algorithm.

        Args:
            year: Year to calculate Easter for

        Returns:
            Date of Easter Sunday
        """
        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        month = (h + l - 7 * m + 114) // 31
        day = ((h + l - 7 * m + 114) % 31) + 1

        return date(year, month, day)

    def _get_movable_holidays(self, year: int) -> Dict[date, str]:
        """
        Get movable holidays for a specific year (based on Easter).

        Args:
            year: Year to get holidays for

        Returns:
            Dict mapping date to holiday name
        """
        easter = self._calculate_easter(year)

        return {
            easter: "Wielkanoc (Easter Sunday)",
            easter + timedelta(days=1): "Poniedziałek Wielkanocny (Easter Monday)",
            easter + timedelta(days=49): "Zielone Świątki (Pentecost)",
            easter + timedelta(days=60): "Boże Ciało (Corpus Christi)",
        }

    @lru_cache(maxsize=20)
    def get_holidays(self, year: int) -> Dict[date, str]:
        """
        Get all Polish holidays for a specific year.

        Args:
            year: Year to get holidays for

        Returns:
            Dict mapping date to holiday name
        """
        holidays = {}

        # Add fixed holidays
        for (month, day), name in self.FIXED_HOLIDAYS.items():
            holidays[date(year, month, day)] = name

        # Add movable holidays (Easter-based)
        holidays.update(self._get_movable_holidays(year))

        return holidays

    def is_holiday(self, check_date: date) -> bool:
        """
        Check if a date is a Polish national holiday.

        Args:
            check_date: Date to check

        Returns:
            True if date is a holiday
        """
        holidays = self.get_holidays(check_date.year)
        return check_date in holidays

    def get_holiday_name(self, check_date: date) -> Optional[str]:
        """
        Get the name of holiday for a specific date.

        Args:
            check_date: Date to check

        Returns:
            Holiday name if date is a holiday, None otherwise
        """
        holidays = self.get_holidays(check_date.year)
        return holidays.get(check_date)

    def get_holidays_in_range(self, start_date: date, end_date: date) -> List[Dict]:
        """
        Get all holidays in a date range.

        Args:
            start_date: Start of range
            end_date: End of range

        Returns:
            List of dicts with 'date' and 'name' keys
        """
        result = []

        # Get all years in range
        years = range(start_date.year, end_date.year + 1)

        for year in years:
            holidays = self.get_holidays(year)
            for holiday_date, name in holidays.items():
                if start_date <= holiday_date <= end_date:
                    result.append({
                        'date': holiday_date,
                        'name': name
                    })

        # Sort by date
        result.sort(key=lambda x: x['date'])

        return result

    def days_to_next_holiday(self, from_date: date) -> int:
        """
        Calculate days until next holiday.

        Args:
            from_date: Starting date

        Returns:
            Number of days to next holiday
        """
        # Check this year and next year
        for year in [from_date.year, from_date.year + 1]:
            holidays = self.get_holidays(year)
            future_holidays = [d for d in holidays.keys() if d > from_date]

            if future_holidays:
                next_holiday = min(future_holidays)
                return (next_holiday - from_date).days

        return 365  # Default if no holiday found

    def days_since_last_holiday(self, from_date: date) -> int:
        """
        Calculate days since last holiday.

        Args:
            from_date: Starting date

        Returns:
            Number of days since last holiday
        """
        # Check this year and last year
        for year in [from_date.year, from_date.year - 1]:
            holidays = self.get_holidays(year)
            past_holidays = [d for d in holidays.keys() if d < from_date]

            if past_holidays:
                last_holiday = max(past_holidays)
                return (from_date - last_holiday).days

        return 365  # Default if no holiday found

    def is_long_weekend(self, check_date: date) -> bool:
        """
        Check if date is part of a long weekend (holiday near weekend).

        Args:
            check_date: Date to check

        Returns:
            True if part of long weekend
        """
        # Check if this date or adjacent days are holidays
        for offset in range(-2, 3):
            test_date = check_date + timedelta(days=offset)
            if self.is_holiday(test_date):
                # Check if holiday is Fri/Mon (making long weekend)
                if test_date.weekday() in [0, 4]:  # Monday or Friday
                    return True
                # Or if holiday is Thu/Tue and bridges to weekend
                if test_date.weekday() in [1, 3]:  # Tuesday or Thursday
                    return abs((check_date - test_date).days) <= 1

        return False
