"""HTML parsers for upstream endpoints."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from turba_client.constants import CROP_ID
from turba_client.exceptions import UpstreamResponseError
from turba_client.models import CropRule, SiteContext
from turba_client.utils import maybe_fix_mojibake, to_float


def parse_geo_and_soil(html: str) -> SiteContext:
    """Parse one ``detail.inc.php`` HTML response."""
    soup = BeautifulSoup(maybe_fix_mojibake(html), "html.parser")

    x_input = soup.find("input", {"id": "x_coord"})
    y_input = soup.find("input", {"id": "y_coord"})
    lon = to_float(x_input.get("value")) if x_input else None
    lat = to_float(y_input.get("value")) if y_input else None

    region = province = commune = None
    id_province_input = soup.find("input", {"id": "id_province"})
    id_province = id_province_input.get("value") if id_province_input else None

    for heading in soup.find_all("h3"):
        text = maybe_fix_mojibake(heading.get_text(" ", strip=True).replace(" ", " "))
        if "Région" in text or "Region" in text:
            region = text.split(":", 1)[-1].strip()
        elif "Préfecture" in text or "Province" in text:
            province = text.split(":", 1)[-1].strip()
        elif "Commune" in text:
            commune = text.split(":", 1)[-1].strip()

    fert_table = None
    for table in soup.find_all("table"):
        th = table.find("th", string=lambda t: t and "Type de sol" in t)
        if th:
            fert_table = table
            break

    soil_type = texture_globale = None
    if fert_table:
        soil_th = fert_table.find("th", string=lambda t: t and "Type de sol" in t)
        if soil_th:
            soil_td = soil_th.find_next("td")
            soil_type = maybe_fix_mojibake(soil_td.get_text(" ", strip=True)) if soil_td else None

        texture_th = fert_table.find("th", string=lambda t: t and "Texture globale" in t)
        if texture_th:
            texture_td = texture_th.find_next("td")
            texture_globale = maybe_fix_mojibake(texture_td.get_text(" ", strip=True)) if texture_td else None

    ph_input = soup.find("input", {"id": "ph"})
    mo_input = soup.find("input", {"id": "mo"})
    p_input = soup.find("input", {"id": "p"})
    k_input = soup.find("input", {"id": "k"})

    rdt_input = soup.find("input", {"id": "rdt"})
    rdt_unit_output = soup.find("output", {"id": "ValueUnit"})

    return SiteContext(
        longitude=lon,
        latitude=lat,
        region=region,
        province=province,
        id_province=id_province,
        commune=commune,
        soil_type=soil_type,
        texture_globale=texture_globale,
        ph=to_float(ph_input.get("value") if ph_input else None),
        matiere_organique_pct=to_float(mo_input.get("value") if mo_input else None),
        p_assimilable_mgkg_p2o5=to_float(p_input.get("value") if p_input else None),
        k_mgkg_k2o=to_float(k_input.get("value") if k_input else None),
        slider_target_yield_min=to_float(rdt_input.get("min") if rdt_input else None),
        slider_target_yield_max=to_float(rdt_input.get("max") if rdt_input else None),
        slider_target_yield_step=to_float(rdt_input.get("step") if rdt_input else None),
        slider_target_yield_default=to_float(rdt_input.get("value") if rdt_input else None),
        slider_target_yield_unit=(rdt_unit_output.get_text(strip=True) if rdt_unit_output else None),
    )


def parse_crop_rules(html: str) -> dict[int, CropRule]:
    """Parse all crop slider rules available for the current site."""
    soup = BeautifulSoup(maybe_fix_mojibake(html), "html.parser")
    crop_rules: dict[int, CropRule] = {}

    for inp in soup.find_all("input", {"type": "hidden"}):
        name = (inp.get("name") or "").strip()
        value = maybe_fix_mojibake(inp.get("value", "").strip())
        match = re.match(r"(culture|min|max|step|unite)(\d+)$", name)
        if not match:
            continue

        key, cid_str = match.groups()
        cid = int(cid_str)
        meta = crop_rules.setdefault(cid, CropRule(crop_id=cid))

        if key == "culture":
            meta.crop_name_raw = value
        elif key == "min":
            meta.target_yield_min = to_float(value)
        elif key == "max":
            meta.target_yield_max = to_float(value)
        elif key == "step":
            meta.target_yield_step = to_float(value)
        elif key == "unite":
            meta.target_yield_unit = value

    for cid, meta in crop_rules.items():
        meta.crop_name = CROP_ID.get(cid, meta.crop_name_raw)

    return crop_rules


def _parse_generic_formula_application(text: str) -> dict[str, object]:
    """Parse one generic-formula application while preserving its source text."""
    raw_text = " ".join(text.split())
    application: dict[str, object] = {
        "quantity": None,
        "quantity_unit": None,
        "product_name": None,
        "application_role": None,
        "application_role_raw": None,
        "raw_text": raw_text,
    }

    quantity_match = re.match(
        r"^(?P<quantity>\d+(?:[.,]\d+)?)\s*"
        r"(?P<unit>qx?/ha)\s+"
        r"(?:(?:du|de\s+la|de\s+l['’]|d['’]|de)\s*)?"
        r"(?P<body>.+)$",
        raw_text,
        flags=re.IGNORECASE,
    )
    if quantity_match is None:
        return application

    application["quantity"] = to_float(quantity_match.group("quantity"))
    application["quantity_unit"] = "qx/ha"

    body = quantity_match.group("body").strip()
    role_match = re.search(r"\s+comme\s+(?P<role>.+?)\s*$", body, flags=re.IGNORECASE)
    if role_match is None:
        application["product_name"] = body or None
        return application

    product_name = body[: role_match.start()].strip()
    role_raw = role_match.group("role").strip()
    role_text = role_raw.casefold()

    application["product_name"] = product_name or None
    application["application_role_raw"] = role_raw or None
    if "fond" in role_text:
        application["application_role"] = "base"
    elif "couverture" in role_text:
        application["application_role"] = "top_dressing"

    return application


def _parse_generic_formula(soup: BeautifulSoup) -> dict[str, object]:
    """Extract the optional generic-formula block from a calculator response."""
    applications: list[dict[str, object]] = []
    cost_amount = None
    cost_currency = None
    cost_basis = None
    cost_raw = None

    heading = None
    for candidate in soup.find_all(["b", "strong"]):
        heading_text = " ".join(candidate.stripped_strings).casefold()
        if "recommandations" in heading_text and "formules" in heading_text:
            heading = candidate
            break

    if heading is None:
        return {
            "generic_formula_applications": applications,
            "generic_formula_cost_amount": cost_amount,
            "generic_formula_cost_currency": cost_currency,
            "generic_formula_cost_basis": cost_basis,
            "generic_formula_cost_raw": cost_raw,
        }

    container = heading.find_parent("td") or heading.parent
    application_list = heading.find_next("ul")
    if application_list is not None and application_list.find_parent("td") is container:
        applications = [
            _parse_generic_formula_application(item.get_text(" ", strip=True))
            for item in application_list.find_all("li", recursive=False)
        ]

    container_text = " ".join(container.stripped_strings)
    cost_match = re.search(
        r"(?P<raw>(?:pour\s+un\s+)?co[^\s]{0,8}t\s+de\s+"
        r"(?P<amount>\d+(?:[.,]\d+)?)\s*"
        r"(?P<currency>dh|mad)\s*/\s*(?P<basis>ha))",
        container_text,
        flags=re.IGNORECASE,
    )
    if cost_match is not None:
        cost_amount = to_float(cost_match.group("amount"))
        cost_currency = "MAD"
        cost_basis = cost_match.group("basis").lower()
        cost_raw = cost_match.group("raw")

    return {
        "generic_formula_applications": applications,
        "generic_formula_cost_amount": cost_amount,
        "generic_formula_cost_currency": cost_currency,
        "generic_formula_cost_basis": cost_basis,
        "generic_formula_cost_raw": cost_raw,
    }


def parse_calcul_response(html: str) -> dict[str, object]:
    """Parse calculator HTML and return nutrient and generic-formula recommendations."""
    soup = BeautifulSoup(maybe_fix_mojibake(html), "html.parser")

    n_kg_ha = None
    p_kg_ha = None
    k_kg_ha = None

    for row in soup.find_all("tr"):
        th = row.find("th")
        tds = row.find_all("td")

        if th is not None and tds:
            label = " ".join(th.stripped_strings).strip().lower()
            value_text = tds[-1].get_text(" ", strip=True)
        elif len(tds) >= 2:
            label = tds[0].get_text(" ", strip=True).strip().lower()
            value_text = tds[-1].get_text(" ", strip=True)
        else:
            continue

        label = maybe_fix_mojibake(label)
        value = to_float(value_text)

        if value is None:
            continue

        # Nitrogen
        if (
            "kg n/ha" in label
            or re.search(r"\bn\b", label)
            or "azote" in label
        ):
            n_kg_ha = value
            continue

        # Phosphorus / P2O5
        if (
            "kg p/ha" in label
            or "kg p2o5/ha" in label
            or "p2o5" in label
            or "phosph" in label
        ):
            p_kg_ha = value
            continue

        # Potassium / K2O
        if (
            "kg k/ha" in label
            or "kg k2o/ha" in label
            or "k2o" in label
            or "potass" in label
        ):
            k_kg_ha = value
            continue

    if n_kg_ha is None and p_kg_ha is None and k_kg_ha is None:
        raise UpstreamResponseError(
            "Could not parse NPK recommendation values from upstream calculator response."
        )

    return {
        "N_kg_ha": n_kg_ha,
        "P_kg_ha": p_kg_ha,
        "K_kg_ha": k_kg_ha,
        **_parse_generic_formula(soup),
    }
