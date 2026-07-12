from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

import pandas as pd
import pytest

from turba_client.client import TurbaClient
from turba_client.constants import CALCUL_URL, DETAIL_URL

DETAIL_HTML = """
<html>
  <body>
    <input id="x_coord" value="-7.616" />
    <input id="y_coord" value="33.589" />
    <input id="id_province" value="42" />

    <h3>Région : Casablanca-Settat</h3>
    <h3>Province : Nouaceur</h3>
    <h3>Commune : Bouskoura</h3>

    <table>
      <tr><th>Type de sol</th><td>Clay Loam</td></tr>
      <tr><th>Texture globale</th><td>Fine</td></tr>
    </table>

    <input id="ph" value="7.4" />
    <input id="mo" value="1.8" />
    <input id="p" value="22" />
    <input id="k" value="180" />

    <input id="rdt" min="10" max="50" step="10" value="30" />
    <output id="ValueUnit">q/ha</output>

    <input type="hidden" name="culture1" value="Blé tendre" />
    <input type="hidden" name="min1" value="10" />
    <input type="hidden" name="max1" value="50" />
    <input type="hidden" name="step1" value="10" />
    <input type="hidden" name="unite1" value="q/ha" />

    <input type="hidden" name="culture3" value="Orge" />
    <input type="hidden" name="min3" value="8" />
    <input type="hidden" name="max3" value="32" />
    <input type="hidden" name="step3" value="8" />
    <input type="hidden" name="unite3" value="q/ha" />
  </body>
</html>
"""

CALCUL_HTML = """
<html>
  <body>
    <table>
      <tr>
        <td>
          <table>
            <tr><th>kg N/ha</th><td>120</td></tr>
            <tr><th>kg P/ha</th><td>45</td></tr>
            <tr><th>kg K/ha</th><td>30</td></tr>
          </table>
        </td>
        <td>
          <p><b>Recommandations basÃ©es sur les formules gÃ©nÃ©riques :</b></p>
          <ul>
            <li>0.85qx/ha du NPK(16.11.20) comme engrais de fond</li>
            <li>0.55qx/ha du TSP comme engrais de fond</li>
            <li>2.13qx/ha d'Ammonitrates comme engrais de couverture</li>
          </ul>
          <br />pour un cout de 787.45 dh/ha
        </td>
      </tr>
    </table>
  </body>
</html>
"""


class MockResponse:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code
        self.content = text.encode("utf-8")
        self.encoding = "utf-8"
        self.apparent_encoding = "utf-8"

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP error: {self.status_code}")


class MockSession:
    def __init__(self):
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        if url == DETAIL_URL:
            return MockResponse(DETAIL_HTML)
        if url == CALCUL_URL:
            return MockResponse(CALCUL_HTML)
        raise RuntimeError(f"Unexpected URL {url}")


@pytest.fixture()
def mock_session() -> MockSession:
    return MockSession()


@pytest.fixture()
def client(mock_session: MockSession) -> TurbaClient:
    return TurbaClient(session=mock_session, sleep_seconds=0)


@pytest.fixture()
def batch_input() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"longitude": -7.616, "latitude": 33.589, "crop_name": "Wheat (Rainfed)"},
            {
                "longitude": -7.616,
                "latitude": 33.589,
                "crop_name": "Barley (Rainfed)",
                "target_yield_level": "high",
            },
        ]
    )
