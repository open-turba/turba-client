from __future__ import annotations

import pandas as pd
import pytest

from turba_client.exceptions import CropNotFoundError, ValidationError


def test_get_site_profile(client) -> None:
    context = client.get_site_profile(-7.616, 33.589)
    assert context.id_province == "42"
    assert context.matiere_organique_pct == 1.8


def test_list_crops(client) -> None:
    df = client.list_crops(-7.616, 33.589)
    assert list(df["crop_id"]) == [1, 3]
    assert df.loc[df["crop_id"] == 1, "crop_name_raw"].iloc[0] == "Blé tendre"


def test_get_recommendations_for_all_crops(client) -> None:
    df = client.get_recommendations(-7.616, 33.589)
    assert len(df) == 2
    assert set(df["crop_name"]) == {"Wheat (Rainfed)", "Barley (Rainfed)"}
    assert set(df["target_yield_level"]) == {"medium"}
    assert set(df["N_kg_ha"]) == {120.0}
    assert all(len(items) == 3 for items in df["generic_formula_applications"])
    assert set(df["generic_formula_cost_amount"]) == {787.45}


def test_get_recommendations_accepts_multiple_levels(client) -> None:
    df = client.get_recommendations(
        -7.616,
        33.589,
        crop_name="Wheat (Rainfed)",
        target_yield_level=["high", "low", "medium"],
    )
    assert list(df["target_yield_level"]) == ["high", "low", "medium"]
    assert list(df["target_yield"]) == [50, 10, 30]


def test_get_recommendations_accepts_custom_targets(client) -> None:
    df = client.get_recommendations(
        -7.616,
        33.589,
        crop_name="Wheat (Rainfed)",
        target_yield=[25, 35],
    )
    assert list(df["target_yield_level"]) == ["custom", "custom"]
    assert list(df["target_yield_mode"]) == ["custom", "custom"]
    assert list(df["target_yield"]) == [25, 35]


def test_get_recommendations_rejects_out_of_range_custom_target(client) -> None:
    with pytest.raises(ValidationError):
        client.get_recommendations(
            -7.616,
            33.589,
            crop_name="Wheat (Rainfed)",
            target_yield=55,
        )


def test_get_recommendations_for_single_crop_with_override(client) -> None:
    df = client.get_recommendations(
        -7.616,
        33.589,
        crop_name="Wheat (Rainfed)",
        target_yield_level="high",
        p_assimilable_mgkg_p2o5=55,
    )
    assert len(df) == 1
    row = df.iloc[0]
    assert row["crop_name"] == "Wheat (Rainfed)"
    assert row["target_yield_level"] == "high"
    assert row["target_yield_value"] == 50
    assert row["p_assimilable_mgkg_p2o5"] == 55
    assert row["generic_formula_applications"][2]["product_name"] == "Ammonitrates"
    assert row["generic_formula_cost_currency"] == "MAD"


def test_get_recommendations_rejects_unknown_crop(client) -> None:
    with pytest.raises(CropNotFoundError):
        client.get_recommendations(-7.616, 33.589, crop_name="Banana")


def test_get_recommendations_batch(client, batch_input) -> None:
    df = client.get_recommendations_batch(batch_input)
    assert len(df) == 2
    assert list(df["target_yield_level"]) == ["medium", "high"]
    assert list(df["input_row_index"]) == [0, 1]


def test_get_recommendations_batch_with_column_map(client) -> None:
    raw = pd.DataFrame(
        [
            {
                "lon": -7.616,
                "lat": 33.589,
                "crop": "Wheat (Rainfed)",
                "targets": "low|high",
            }
        ]
    )
    df = client.get_recommendations_batch(
        raw,
        column_map={
            "longitude": "lon",
            "latitude": "lat",
            "crop_name": "crop",
            "target_yield_level": "targets",
        },
    )
    assert len(df) == 2
    assert list(df["target_yield_level"]) == ["low", "high"]


def test_recommend_many_requires_coordinates(client) -> None:
    with pytest.raises(ValidationError):
        client.get_recommendations_batch([{"longitude": -7.616}])


def test_backward_compatibility_aliases(client) -> None:
    df = client.recommend_site(-7.616, 33.589, crop_name="Wheat (Rainfed)")
    assert len(df) == 1
    assert hasattr(client, "recommend_many")
