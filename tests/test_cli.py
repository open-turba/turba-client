from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from turba_client import cli


class DummyClient:
    def get_recommendations(self, **kwargs):
        return pd.DataFrame(
            [
                {
                    **kwargs,
                    "N_kg_ha": 120,
                    "P_kg_ha": 45,
                    "K_kg_ha": 30,
                    "generic_formula_applications": [
                        {
                            "quantity": 1.41,
                            "quantity_unit": "qx/ha",
                            "product_name": "TSP",
                            "application_role": "base",
                        }
                    ],
                    "generic_formula_cost_amount": 858.9,
                }
            ]
        )

    def get_recommendations_batch(self, frame, column_map=None):
        if isinstance(frame, (str, Path)):
            data = pd.read_csv(frame)
        else:
            data = frame.copy()
        result = data.assign(N_kg_ha=120, P_kg_ha=45, K_kg_ha=30)
        result["generic_formula_applications"] = [
            [{"quantity": 1.41, "quantity_unit": "qx/ha", "product_name": "TSP"}]
            for _ in range(len(result))
        ]
        return result


@pytest.fixture()
def patch_client(monkeypatch):
    monkeypatch.setattr(cli, "TurbaClient", lambda: DummyClient())


def test_cli_get_recommendations_json_stdout(monkeypatch, capsys, patch_client) -> None:
    monkeypatch.setattr(
        "sys.argv",
        [
            "turba-client",
            "get-recommendations",
            "--longitude",
            "-7.616",
            "--latitude",
            "33.589",
            "--target-yield-level",
            "low",
            "high",
        ],
    )
    cli.main()
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload[0]["N_kg_ha"] == 120
    assert payload[0]["generic_formula_applications"][0]["product_name"] == "TSP"


def test_cli_get_recommendations_batch_writes_file(monkeypatch, patch_client, tmp_path: Path) -> None:
    input_file = tmp_path / "sites.csv"
    output_file = tmp_path / "results.csv"
    pd.DataFrame([{"lon": -7.616, "lat": 33.589}]).to_csv(input_file, index=False)

    monkeypatch.setattr(
        "sys.argv",
        [
            "turba-client",
            "get-recommendations-batch",
            "--input-file",
            str(input_file),
            "--column-map",
            "longitude=lon",
            "--column-map",
            "latitude=lat",
            "--output",
            str(output_file),
        ],
    )
    cli.main()
    assert output_file.exists()
    result = pd.read_csv(output_file)
    assert result.loc[0, "K_kg_ha"] == 30
    applications = json.loads(result.loc[0, "generic_formula_applications"])
    assert applications[0]["product_name"] == "TSP"


def test_csv_output_does_not_mutate_nested_cells(tmp_path: Path) -> None:
    applications = [{"product_name": "Ammonitrates", "application_role": "top_dressing"}]
    dataframe = pd.DataFrame([{"generic_formula_applications": applications}])
    output_file = tmp_path / "results.csv"

    cli._write_output(dataframe, str(output_file), stdout_format="csv")

    assert dataframe.loc[0, "generic_formula_applications"] is applications
    result = pd.read_csv(output_file)
    assert json.loads(result.loc[0, "generic_formula_applications"]) == applications
