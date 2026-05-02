"""General utility helpers for Turba Client."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import pandas as pd

from turba_client.constants import (
    CANONICAL_INPUT_COLUMNS,
    DEFAULT_MULTI_VALUE_SEPARATORS,
    DEFAULT_TARGET_YIELD_LEVEL,
    TARGET_YIELD_LEVELS,
)
from turba_client.exceptions import ValidationError


def to_float(value: object) -> float | None:
    """Convert a value to float when possible."""
    if value is None:
        return None
    text = str(value).strip().replace(",", ".")
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def missing_to_none(value: object) -> object:
    """Convert pandas/NumPy missing values to ``None``."""
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    return value


def maybe_fix_mojibake(text: str) -> str:
    """Repair common UTF-8/Latin-1 mojibake sequences when detected."""
    if not text:
        return text
    if any(marker in text for marker in ("Ã", "â", "�")):
        try:
            repaired = text.encode("latin1").decode("utf-8")
            if repaired.count("Ã") < text.count("Ã"):
                return repaired
        except Exception:
            pass
    return text


def get_response_text(response: object) -> str:
    """Safely extract decoded text from a requests-like response object."""
    content = getattr(response, "content", None)
    if isinstance(content, (bytes, bytearray)):
        encoding = (
            getattr(response, "apparent_encoding", None)
            or getattr(response, "encoding", None)
            or "utf-8"
        )
        try:
            return maybe_fix_mojibake(content.decode(encoding, errors="replace"))
        except Exception:
            return maybe_fix_mojibake(content.decode("utf-8", errors="replace"))
    return maybe_fix_mojibake(str(getattr(response, "text", "")))


def normalize_crop_name(value: str | None) -> str | None:
    """Normalize a crop name for case-insensitive matching."""
    cleaned = missing_to_none(value)
    if cleaned is None:
        return None
    text = " ".join(str(cleaned).strip().split())
    return text.casefold() if text else None


def validate_coordinates(longitude: object, latitude: object) -> tuple[float, float]:
    """Validate and coerce longitude/latitude values."""
    lon = to_float(missing_to_none(longitude))
    lat = to_float(missing_to_none(latitude))
    if lon is None or lat is None:
        raise ValidationError("longitude and latitude must be numeric values")
    if not -180.0 <= lon <= 180.0:
        raise ValidationError("longitude must be between -180 and 180")
    if not -90.0 <= lat <= 90.0:
        raise ValidationError("latitude must be between -90 and 90")
    return lon, lat


def _split_multi_value_string(value: str, separators: Sequence[str]) -> list[str]:
    pattern = "|".join(re.escape(separator) for separator in separators)
    return [item.strip() for item in re.split(pattern, value) if item.strip()]


def coerce_to_list(
    value: object,
    *,
    separators: Sequence[str] = DEFAULT_MULTI_VALUE_SEPARATORS,
) -> list[object]:
    """Coerce scalars, sequences, or delimited strings to a list."""
    cleaned = missing_to_none(value)
    if cleaned is None:
        return []
    if isinstance(cleaned, str):
        text = cleaned.strip()
        if text == "":
            return []
        if any(separator in text for separator in separators):
            return _split_multi_value_string(text, separators)
        return [text]
    if isinstance(cleaned, Sequence) and not isinstance(cleaned, (bytes, bytearray)):
        return [missing_to_none(item) for item in cleaned if missing_to_none(item) is not None]
    return [cleaned]


def validate_target_yield_levels(
    target_yield_level: object, *, default_when_empty: bool = True
) -> list[str]:
    """Validate one or multiple target-yield levels and return normalized values."""
    levels = []
    for item in coerce_to_list(target_yield_level):
        level = str(item).strip().lower()
        if level not in TARGET_YIELD_LEVELS:
            raise ValidationError(
                f"target_yield_level must contain only {sorted(TARGET_YIELD_LEVELS)}, got {target_yield_level!r}"
            )
        levels.append(level)

    if not levels and default_when_empty:
        levels = [DEFAULT_TARGET_YIELD_LEVEL]

    # Preserve order while removing duplicates.
    deduped: list[str] = []
    seen: set[str] = set()
    for level in levels:
        if level not in seen:
            seen.add(level)
            deduped.append(level)
    return deduped


def validate_target_yields(target_yield: object) -> list[float]:
    """Validate one or multiple custom target yields and return numeric values."""
    values: list[float] = []
    for item in coerce_to_list(target_yield):
        numeric = to_float(item)
        if numeric is None:
            raise ValidationError(
                f"target_yield must contain only numeric values, got {target_yield!r}"
            )
        values.append(numeric)

    deduped: list[float] = []
    seen: set[float] = set()
    for value in values:
        key = round(value, 8)
        if key not in seen:
            seen.add(key)
            deduped.append(value)
    return deduped


def normalize_crop_names(value: object) -> list[str] | None:
    """Normalize one or multiple crop names while preserving order."""
    names = [str(item).strip() for item in coerce_to_list(value) if str(item).strip()]
    if not names:
        return None
    deduped: list[str] = []
    seen: set[str] = set()
    for name in names:
        key = normalize_crop_name(name)
        if key and key not in seen:
            seen.add(key)
            deduped.append(name)
    return deduped


def generate_target_yield_levels(
    target_yield_min: float | None,
    target_yield_max: float | None,
    target_yield_step: float | None,
) -> list[tuple[str, float]]:
    """Generate low/medium/high target yield values for a crop."""
    if target_yield_min is None or target_yield_max is None:
        return []

    step = (
        target_yield_step
        if target_yield_step and target_yield_step > 0
        else (target_yield_max - target_yield_min) / 3.0
    )
    low = target_yield_min
    high = target_yield_max
    mid_raw = (target_yield_min + target_yield_max) / 2.0
    n_steps = round((mid_raw - target_yield_min) / step) if step else 0
    mid = target_yield_min + n_steps * step
    mid = max(min(mid, target_yield_max), target_yield_min)

    ordered_levels = [("low", low), ("medium", mid), ("high", high)]
    unique_levels: list[tuple[str, float]] = []
    seen: set[float] = set()
    for name, value in ordered_levels:
        rounded_value = round(value, 6)
        if rounded_value not in seen:
            seen.add(rounded_value)
            unique_levels.append((name, value))
    return unique_levels


def ensure_dataframe(data: pd.DataFrame | Iterable[dict] | str | Path) -> pd.DataFrame:
    """Coerce supported batch inputs to a DataFrame.

    Supported inputs are DataFrames, iterables of dictionaries, CSV files,
    and JSON files containing a list of records.
    """
    if isinstance(data, pd.DataFrame):
        return data.copy()
    if isinstance(data, (str, Path)):
        path = Path(data)
        suffix = path.suffix.lower()
        if suffix == ".csv":
            return pd.read_csv(path)
        if suffix == ".json":
            return pd.read_json(path)
        raise ValidationError(
            f"Unsupported file format {suffix!r}. Use CSV or JSON for batch input."
        )
    return pd.DataFrame(list(data))


def apply_column_map(
    frame: pd.DataFrame,
    column_map: Mapping[str, str] | None = None,
) -> pd.DataFrame:
    """Rename user columns to the library's canonical input schema.

    The mapping must be expressed as:

    ``{"longitude": "lon", "latitude": "lat"}``

    which means "use the user's ``lon`` column as the library's
    ``longitude`` field".
    """
    if not column_map:
        return frame.copy()

    unknown_canonical = sorted(set(column_map) - set(CANONICAL_INPUT_COLUMNS))
    if unknown_canonical:
        raise ValidationError(
            "column_map contains unknown canonical fields: "
            f"{unknown_canonical}. Supported fields are {list(CANONICAL_INPUT_COLUMNS)}"
        )

    missing_user_columns = sorted(
        user_column for user_column in column_map.values() if user_column not in frame.columns
    )
    if missing_user_columns:
        raise ValidationError(
            f"The following mapped user columns were not found in the input table: "
            f"{missing_user_columns}"
        )

    rename_map = {user_column: canonical for canonical, user_column in column_map.items()}
    normalized = frame.rename(columns=rename_map).copy()
    return normalized
