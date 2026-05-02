from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from turba_client import cli


class DummyClient:
    def get_recommendations(self, **kwargs):
        return pd.DataFrame([{**kwargs, "N_kg_ha": 120, "P_kg_ha": 45, "K_kg_ha": 30}])

    def get_recommendations_batch(self, frame, column_map=None):
        if isinstance(frame, (str, Path)):
            data = pd.read_csv(frame)
        else:
            data = frame.copy()
        return data.assign(N_kg_ha=120, P_kg_ha=45, K_kg_ha=30)


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
