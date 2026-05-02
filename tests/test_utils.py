from __future__ import annotations

import pandas as pd
import pytest

from turba_client.exceptions import ValidationError
from turba_client.utils import (
    apply_column_map,
    coerce_to_list,
    generate_target_yield_levels,
    maybe_fix_mojibake,
    validate_target_yield_levels,
    validate_target_yields,
)


def test_generate_target_yield_levels() -> None:
    assert generate_target_yield_levels(10, 50, 10) == [("low", 10), ("medium", 30), ("high", 50)]


def test_validate_target_yield_levels_accepts_many() -> None:
    assert validate_target_yield_levels(["low", "medium"]) == ["low", "medium"]
    assert validate_target_yield_levels("low|high") == ["low", "high"]


def test_validate_target_yields() -> None:
    assert validate_target_yields([25, "35"]) == [25.0, 35.0]
    with pytest.raises(ValidationError):
        validate_target_yields([25, "bad"])


def test_coerce_to_list() -> None:
    assert coerce_to_list("low|high") == ["low", "high"]
    assert coerce_to_list(["low", "high"]) == ["low", "high"]


def test_apply_column_map() -> None:
    frame = pd.DataFrame([{"lon": 1, "lat": 2}])
    mapped = apply_column_map(frame, {"longitude": "lon", "latitude": "lat"})
    assert set(mapped.columns) == {"longitude", "latitude"}


def test_maybe_fix_mojibake() -> None:
    assert maybe_fix_mojibake("BlÃ© tendre") == "Blé tendre"
