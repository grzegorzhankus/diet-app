"""
Pydantic schemas for DIET_APP
Defines data models with validation.
"""
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class DailyEntry(BaseModel):
    """
    Daily entry for diet and training tracking.

    Fields:
    - date: Date of measurement (YYYY-MM-DD)
    - weight_kg: Body weight in kg (30-200)
    - bodyfat_pct: Body fat percentage 0-100 (optional)
    - cal_in_kcal: Calories intake in kcal (>=0, optional)
    - cal_out_sport_kcal: Calories burned through exercise (>=0, optional)
    - notes: Optional text notes
    - source: Data source (manual, import, api)
    """

    id: Optional[int] = None
    date: date
    weight_kg: float = Field(..., ge=30.0, le=200.0)
    bodyfat_pct: Optional[float] = Field(None, ge=0.0, le=100.0)
    cal_in_kcal: Optional[float] = Field(None, ge=0.0)
    cal_out_sport_kcal: Optional[float] = Field(None, ge=0.0)
    notes: Optional[str] = None
    source: str = Field(default="manual")

    @field_validator("bodyfat_pct")
    @classmethod
    def validate_bodyfat(cls, v):
        """Validate body fat percentage is reasonable."""
        if v is not None and (v < 3.0 or v > 60.0):
            raise ValueError("Body fat % should be between 3-60% for reasonable values")
        return v

    @field_validator("weight_kg")
    @classmethod
    def validate_weight(cls, v):
        """Validate weight is in reasonable range and round to 1 decimal."""
        if v < 30.0 or v > 200.0:
            raise ValueError("Weight must be between 30-200 kg")
        return round(v, 1)

    class Config:
        """Pydantic config."""
        from_attributes = True
        json_schema_extra = {
            "example": {
                "date": "2026-01-07",
                "weight_kg": 85.5,
                "bodyfat_pct": 18.5,
                "cal_in_kcal": 2200.0,
                "cal_out_sport_kcal": 450.0,
                "notes": "Morning measurement, fasted",
                "source": "manual"
            }
        }


class DailyEntryCreate(BaseModel):
    """Schema for creating a new daily entry (without ID)."""
    date: date
    weight_kg: float = Field(..., ge=30.0, le=200.0)
    bodyfat_pct: Optional[float] = Field(None, ge=0.0, le=100.0)
    cal_in_kcal: Optional[float] = Field(None, ge=0.0)
    cal_out_sport_kcal: Optional[float] = Field(None, ge=0.0)
    notes: Optional[str] = None
    source: str = Field(default="manual")

    @field_validator("weight_kg")
    @classmethod
    def round_weight(cls, v):
        """Round weight to 1 decimal place."""
        return round(v, 1)

    @field_validator("bodyfat_pct")
    @classmethod
    def round_bodyfat(cls, v):
        """Round body fat to 1 decimal place."""
        return round(v, 1) if v is not None else None


class DailyEntryUpdate(BaseModel):
    """Schema for updating an existing daily entry (all fields optional)."""
    weight_kg: Optional[float] = Field(None, ge=30.0, le=200.0)
    bodyfat_pct: Optional[float] = Field(None, ge=0.0, le=100.0)
    cal_in_kcal: Optional[float] = Field(None, ge=0.0)
    cal_out_sport_kcal: Optional[float] = Field(None, ge=0.0)
    notes: Optional[str] = None

    @field_validator("weight_kg")
    @classmethod
    def round_weight(cls, v):
        """Round weight to 1 decimal place."""
        return round(v, 1) if v is not None else None

    @field_validator("bodyfat_pct")
    @classmethod
    def round_bodyfat(cls, v):
        """Round body fat to 1 decimal place."""
        return round(v, 1) if v is not None else None
