from __future__ import annotations

from turba_client.parsers import parse_calcul_response, parse_crop_rules, parse_geo_and_soil


def test_parse_geo_and_soil() -> None:
    html = """
    <input id="x_coord" value="-7.1" />
    <input id="y_coord" value="33.1" />
    <input id="id_province" value="17" />
    <h3>Région : Test Region</h3>
    <h3>Province : Test Province</h3>
    <h3>Commune : Test Commune</h3>
    <table>
      <tr><th>Type de sol</th><td>Sandy</td></tr>
      <tr><th>Texture globale</th><td>Coarse</td></tr>
    </table>
    <input id="ph" value="7.2" />
    <input id="mo" value="1.1" />
    <input id="p" value="20" />
    <input id="k" value="150" />
    <input id="rdt" min="10" max="30" step="5" value="20" />
    <output id="ValueUnit">q/ha</output>
    """
    parsed = parse_geo_and_soil(html)
    assert parsed.longitude == -7.1
    assert parsed.latitude == 33.1
    assert parsed.region == "Test Region"
    assert parsed.soil_type == "Sandy"
    assert parsed.slider_target_yield_unit == "q/ha"


def test_parse_crop_rules() -> None:
    html = """
    <input type="hidden" name="culture1" value="Blé tendre" />
    <input type="hidden" name="min1" value="10" />
    <input type="hidden" name="max1" value="50" />
    <input type="hidden" name="step1" value="10" />
    <input type="hidden" name="unite1" value="q/ha" />
    """
    rules = parse_crop_rules(html)
    assert rules[1].crop_name == "Wheat (Rainfed)"
    assert rules[1].crop_name_raw == "Blé tendre"
    assert rules[1].target_yield_max == 50


def test_parse_calcul_response() -> None:
    html = """
    <tr><th>kg N/ha</th><td>100</td></tr>
    <tr><th>kg P/ha</th><td>40</td></tr>
    <tr><th>kg K/ha</th><td>20</td></tr>
    """
    parsed = parse_calcul_response(html)
    assert parsed["N_kg_ha"] == 100.0
    assert parsed["P_kg_ha"] == 40.0
    assert parsed["K_kg_ha"] == 20.0
    assert parsed["generic_formula_applications"] == []
    assert parsed["generic_formula_cost_amount"] is None


def test_parse_calcul_response_with_generic_formula() -> None:
    html = """
    <table><tbody><tr>
      <td><table><tbody>
        <tr><th>N (kg N/ha)</th><td>83.81</td></tr>
        <tr><th>P (kg P/ha)</th><td>34.22</td></tr>
        <tr><th>K (kg K/ha)</th><td>17.07</td></tr>
      </tbody></table></td>
      <td>
        <p><b>Recommandations basÃ©es sur les formules gÃ©nÃ©riques :</b></p>
        <ul>
          <li>0.85qx/ha du NPK(16.11.20) comme engrais de fond</li>
          <li>0,55 q/ha du TSP comme engrais de fond</li>
          <li>2.13qx/ha d'Ammonitrates comme engrais de couverture</li>
        </ul>
        <br />pour un cout de 787,45 dh/ha
      </td>
    </tr></tbody></table>
    """
    parsed = parse_calcul_response(html)

    assert parsed["generic_formula_applications"] == [
        {
            "quantity": 0.85,
            "quantity_unit": "qx/ha",
            "product_name": "NPK(16.11.20)",
            "application_role": "base",
            "application_role_raw": "engrais de fond",
            "raw_text": "0.85qx/ha du NPK(16.11.20) comme engrais de fond",
        },
        {
            "quantity": 0.55,
            "quantity_unit": "qx/ha",
            "product_name": "TSP",
            "application_role": "base",
            "application_role_raw": "engrais de fond",
            "raw_text": "0,55 q/ha du TSP comme engrais de fond",
        },
        {
            "quantity": 2.13,
            "quantity_unit": "qx/ha",
            "product_name": "Ammonitrates",
            "application_role": "top_dressing",
            "application_role_raw": "engrais de couverture",
            "raw_text": "2.13qx/ha d'Ammonitrates comme engrais de couverture",
        },
    ]
    assert parsed["generic_formula_cost_amount"] == 787.45
    assert parsed["generic_formula_cost_currency"] == "MAD"
    assert parsed["generic_formula_cost_basis"] == "ha"
    assert parsed["generic_formula_cost_raw"] == "pour un cout de 787,45 dh/ha"


def test_parse_generic_formula_preserves_partial_and_unknown_applications() -> None:
    html = """
    <tr><th>kg N/ha</th><td>100</td></tr>
    <td>
      <strong>Recommandations basées sur les formules génériques</strong>
      <ul>
        <li>1.41 qx/ha de Produit Test comme engrais foliaire</li>
        <li>instruction libre non structurée</li>
      </ul>
    </td>
    """
    parsed = parse_calcul_response(html)
    applications = parsed["generic_formula_applications"]

    assert applications[0]["quantity"] == 1.41
    assert applications[0]["product_name"] == "Produit Test"
    assert applications[0]["application_role"] is None
    assert applications[0]["application_role_raw"] == "engrais foliaire"
    assert applications[1] == {
        "quantity": None,
        "quantity_unit": None,
        "product_name": None,
        "application_role": None,
        "application_role_raw": None,
        "raw_text": "instruction libre non structurée",
    }
    assert parsed["generic_formula_cost_amount"] is None
