"""Public client API for Turba Client."""

from __future__ import annotations

import time
from dataclasses import asdict
from typing import Iterable, Mapping

import pandas as pd

from turba_client.constants import (
    CALCUL_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_SLEEP_SECONDS,
    DEFAULT_TIMEOUT,
    DETAIL_URL,
)
from turba_client.exceptions import (
    CropNotFoundError,
    SiteDataNotFoundError,
    UpstreamResponseError,
    ValidationError,
)
from turba_client.models import CropRule, SiteContext, TargetRequest
from turba_client.parsers import (
    parse_calcul_response,
    parse_crop_rules,
    parse_geo_and_soil,
)
from turba_client.session import build_session
from turba_client.utils import (
    apply_column_map,
    ensure_dataframe,
    generate_target_yield_levels,
    get_response_text,
    missing_to_none,
    normalize_crop_name,
    normalize_crop_names,
    validate_coordinates,
    validate_target_yield_levels,
    validate_target_yields,
)


class TurbaClient:
    """Client for querying soil profile and fertilizer recommendation workflows."""

    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT,
        sleep_seconds: float = DEFAULT_SLEEP_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        user_agent: str | None = None,
        session=None,
    ) -> None:
        self.timeout = timeout
        self.sleep_seconds = sleep_seconds
        self.max_retries = max_retries
        self.session = session or build_session(
            max_retries=max_retries,
            user_agent=user_agent,
        )

    def get_site_profile(self, longitude: object, latitude: object) -> SiteContext:
        """Fetch and parse site metadata for a coordinate pair."""
        _, _, context, _ = self._fetch_site_payload(longitude, latitude)
        return context

    def list_crops(self, longitude: object, latitude: object) -> pd.DataFrame:
        """Return all crop rules available at a site as a DataFrame."""
        _, _, _, rules = self._fetch_site_payload(longitude, latitude)
        if not rules:
            raise UpstreamResponseError("No crop rules found in upstream detail response")
        return pd.DataFrame([asdict(rule) for rule in rules.values()]).sort_values(
            by="crop_id"
        )

    def get_recommendations(
        self,
        longitude: object,
        latitude: object,
        crop_name: object | None = None,
        target_yield_level: object | None = None,
        target_yield: object | None = None,
        ph: float | None = None,
        matiere_organique_pct: float | None = None,
        p_assimilable_mgkg_p2o5: float | None = None,
        k_mgkg_k2o: float | None = None,
    ) -> pd.DataFrame:
        """Return recommendations for one site.

        Parameters
        ----------
        crop_name:
            One crop name, a list/tuple of crop names, or ``None`` for all crops.
        target_yield_level:
            One level, many levels, or a delimited string such as ``"low|high"``.
        target_yield:
            One custom numeric target yield or many values. Each value must be
            within the selected crop's ``target_yield_min`` and ``target_yield_max`` range.
        """
        lon, lat, site_context, crop_rules = self._fetch_site_payload(longitude, latitude)
        selected_rules = self._select_crop_rules(crop_rules, crop_name)
        effective_ph = ph if ph is not None else site_context.ph
        effective_mo = (
            matiere_organique_pct
            if matiere_organique_pct is not None
            else site_context.matiere_organique_pct
        )
        effective_p = (
            p_assimilable_mgkg_p2o5
            if p_assimilable_mgkg_p2o5 is not None
            else site_context.p_assimilable_mgkg_p2o5
        )
        effective_k = k_mgkg_k2o if k_mgkg_k2o is not None else site_context.k_mgkg_k2o

        recommendation_rows: list[dict] = []
        for rule in selected_rules:
            target_requests = self._resolve_target_requests(
                crop_rule=rule,
                target_yield_level=target_yield_level,
                target_yield=target_yield,
            )
            for target_request in target_requests:
                rec = self._fetch_calculation(
                    longitude=lon,
                    latitude=lat,
                    site_context=site_context,
                    crop_rule=rule,
                    target_request=target_request,
                    ph=effective_ph,
                    matiere_organique_pct=effective_mo,
                    p_assimilable_mgkg_p2o5=effective_p,
                    k_mgkg_k2o=effective_k,
                )
                recommendation_rows.append(rec)
                time.sleep(self.sleep_seconds)

        return pd.DataFrame(recommendation_rows)

    def prepare_input_table(
        self,
        data: pd.DataFrame | Iterable[dict] | str,
        column_map: Mapping[str, str] | None = None,
    ) -> pd.DataFrame:
        """Load and align a batch input table to the library schema."""
        frame = ensure_dataframe(data)
        return apply_column_map(frame, column_map=column_map)

    def get_recommendations_batch(
        self,
        data: pd.DataFrame | Iterable[dict] | str,
        column_map: Mapping[str, str] | None = None,
    ) -> pd.DataFrame:
        """Return recommendations for multiple sites.

        ``column_map`` must follow the form ``{"longitude": "lon"}``, meaning
        the user's ``lon`` column should be used as the library's ``longitude`` field.
        """
        frame = self.prepare_input_table(data, column_map=column_map)
        required_columns = {"longitude", "latitude"}
        missing = required_columns - set(frame.columns)
        if missing:
            raise ValidationError(
                f"Batch input is missing required columns: {sorted(missing)}"
            )

        outputs: list[pd.DataFrame] = []
        for input_row_index, (_, row) in enumerate(frame.iterrows()):
            result = self.get_recommendations(
                longitude=missing_to_none(row["longitude"]),
                latitude=missing_to_none(row["latitude"]),
                crop_name=missing_to_none(row.get("crop_name")),
                target_yield_level=missing_to_none(row.get("target_yield_level")),
                target_yield=missing_to_none(row.get("target_yield")),
                ph=missing_to_none(row.get("ph")),
                matiere_organique_pct=missing_to_none(row.get("matiere_organique_pct")),
                p_assimilable_mgkg_p2o5=missing_to_none(row.get("p_assimilable_mgkg_p2o5")),
                k_mgkg_k2o=missing_to_none(row.get("k_mgkg_k2o")),
            )
            result.insert(0, "input_row_index", input_row_index)
            outputs.append(result)

        if not outputs:
            return pd.DataFrame()
        return pd.concat(outputs, ignore_index=True)

    # ------------------------------------------------------------------
    # Backward-compatible method aliases from v0.1.x
    # ------------------------------------------------------------------
    def get_site_context(self, longitude: object, latitude: object) -> SiteContext:
        return self.get_site_profile(longitude, latitude)

    def list_available_crops(self, longitude: object, latitude: object) -> pd.DataFrame:
        return self.list_crops(longitude, latitude)

    def recommend_site(self, *args, **kwargs) -> pd.DataFrame:
        return self.get_recommendations(*args, **kwargs)

    def recommend_many(self, data, column_map: Mapping[str, str] | None = None) -> pd.DataFrame:
        return self.get_recommendations_batch(data, column_map=column_map)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _fetch_site_payload(
        self,
        longitude: object,
        latitude: object,
    ) -> tuple[float, float, SiteContext, dict[int, CropRule]]:
        """Fetch detail HTML once and parse both site and crop metadata."""
        lon, lat = validate_coordinates(longitude, latitude)
        response = self.session.get(
            DETAIL_URL,
            params={"x": lon, "y": lat},
            timeout=self.timeout,
        )
        response.raise_for_status()
        html = get_response_text(response)

        site_context = parse_geo_and_soil(html)
        crop_rules = parse_crop_rules(html)
        if site_context.id_province is None and site_context.soil_type is None and site_context.ph is None:
            raise SiteDataNotFoundError(
                f"No usable site data found for longitude={lon}, latitude={lat}"
            )
        if not crop_rules:
            raise SiteDataNotFoundError(
                f"No crop rules found for longitude={lon}, latitude={lat}"
            )
        return lon, lat, site_context, crop_rules

    def _select_crop_rules(
        self,
        crop_rules: dict[int, CropRule],
        crop_name: object | None,
    ) -> list[CropRule]:
        """Return either all crop rules or the ones matching the requested names."""
        requested_names = normalize_crop_names(crop_name)
        if requested_names is None:
            return list(crop_rules.values())

        available_by_name: dict[str, list[CropRule]] = {}
        for rule in crop_rules.values():
            normalized = normalize_crop_name(rule.crop_name)
            if normalized is not None:
                available_by_name.setdefault(normalized, []).append(rule)

        selected: list[CropRule] = []
        missing_names: list[str] = []
        for requested_name in requested_names:
            key = normalize_crop_name(requested_name)
            matches = available_by_name.get(key or "", [])
            if not matches:
                missing_names.append(requested_name)
            else:
                selected.extend(matches)

        if missing_names:
            available = sorted(
                rule.crop_name for rule in crop_rules.values() if rule.crop_name
            )
            raise CropNotFoundError(
                f"Crop(s) {missing_names!r} not found. Available crops: {available}"
            )
        return selected

    def _resolve_target_requests(
        self,
        crop_rule: CropRule,
        target_yield_level: object | None,
        target_yield: object | None,
    ) -> list[TargetRequest]:
        """Resolve requested target-yield levels and/or custom targets for one crop."""
        use_default_level = target_yield is None
        requested_levels = validate_target_yield_levels(
            target_yield_level,
            default_when_empty=use_default_level,
        )
        requested_custom_targets = validate_target_yields(target_yield)
        level_to_value = dict(
            generate_target_yield_levels(
                crop_rule.target_yield_min,
                crop_rule.target_yield_max,
                crop_rule.target_yield_step,
            )
        )

        target_requests: list[TargetRequest] = []
        for level in requested_levels:
            if level not in level_to_value:
                raise UpstreamResponseError(
                    f"target_yield_level {level!r} is not available for crop {crop_rule.crop_name!r}"
                )
            target_requests.append(
                TargetRequest(
                    request_label=level,
                    request_mode="level",
                    target_yield=level_to_value[level],
                )
            )

        for custom_value in requested_custom_targets:
            self._validate_custom_target_within_rule(custom_value, crop_rule)
            target_requests.append(
                TargetRequest(
                    request_label="custom",
                    request_mode="custom",
                    target_yield=custom_value,
                )
            )

        deduped: list[TargetRequest] = []
        seen: set[tuple[str, float]] = set()
        for request in target_requests:
            key = (request.request_mode, round(request.target_yield, 8))
            if key not in seen:
                seen.add(key)
                deduped.append(request)
        return deduped

    def _validate_custom_target_within_rule(
        self,
        target_yield: float,
        crop_rule: CropRule,
    ) -> None:
        """Ensure a custom target yield is within the upstream allowed range."""
        if (
            crop_rule.target_yield_min is None
            or crop_rule.target_yield_max is None
        ):
            raise UpstreamResponseError(
                f"The crop {crop_rule.crop_name!r} does not expose target-yield bounds."
            )
        if (
            target_yield < crop_rule.target_yield_min
            or target_yield > crop_rule.target_yield_max
        ):
            raise ValidationError(
                f"target_yield={target_yield} is outside the allowed range for "
                f"{crop_rule.crop_name!r}: [{crop_rule.target_yield_min}, {crop_rule.target_yield_max}]"
            )

    def _fetch_calculation(
        self,
        longitude: float,
        latitude: float,
        site_context: SiteContext,
        crop_rule: CropRule,
        target_request: TargetRequest,
        ph: float | None,
        matiere_organique_pct: float | None,
        p_assimilable_mgkg_p2o5: float | None,
        k_mgkg_k2o: float | None,
    ) -> dict:
        """Call upstream calculator endpoint and compose one output row."""
        params = {
            "id_province": site_context.id_province,
            "culture": crop_rule.crop_id,
            "mo": matiere_organique_pct,
            "p": p_assimilable_mgkg_p2o5,
            "k": k_mgkg_k2o,
            "rdt": target_request.target_yield,
            "x_coord": longitude,
            "y_coord": latitude,
        }
        response = self.session.get(CALCUL_URL, params=params, timeout=self.timeout)
        response.raise_for_status()
        rec = parse_calcul_response(get_response_text(response))

        if rec["N_kg_ha"] is None and rec["P_kg_ha"] is None and rec["K_kg_ha"] is None:
            raise UpstreamResponseError(
                f"Could not parse NPK recommendation from upstream calculator response "
                f"for crop_id={crop_rule.crop_id}, target_yield={target_request.target_yield}, "
                f"longitude={longitude}, latitude={latitude}."
            )

        return {
            "longitude": longitude,
            "latitude": latitude,
            "region": site_context.region,
            "province": site_context.province,
            "id_province": site_context.id_province,
            "commune": site_context.commune,
            "soil_type": site_context.soil_type,
            "texture_globale": site_context.texture_globale,
            "ph": ph,
            "matiere_organique_pct": matiere_organique_pct,
            "p_assimilable_mgkg_p2o5": p_assimilable_mgkg_p2o5,
            "k_mgkg_k2o": k_mgkg_k2o,
            "slider_target_yield_min": site_context.slider_target_yield_min,
            "slider_target_yield_max": site_context.slider_target_yield_max,
            "slider_target_yield_step": site_context.slider_target_yield_step,
            "slider_target_yield_unit": site_context.slider_target_yield_unit,
            "crop_id": crop_rule.crop_id,
            "crop_name_raw": crop_rule.crop_name_raw,
            "crop_name": crop_rule.crop_name,
            "target_yield_level": target_request.request_label,
            "target_yield_mode": target_request.request_mode,
            "target_yield": target_request.target_yield,
            "target_yield_min": crop_rule.target_yield_min,
            "target_yield_max": crop_rule.target_yield_max,
            "target_yield_step": crop_rule.target_yield_step,
            "target_yield_unit": crop_rule.target_yield_unit,
            "target_yield_value": target_request.target_yield,
            "N_kg_ha": rec["N_kg_ha"],
            "P_kg_ha": rec["P_kg_ha"],
            "K_kg_ha": rec["K_kg_ha"],
            "generic_formula_applications": rec["generic_formula_applications"],
            "generic_formula_cost_amount": rec["generic_formula_cost_amount"],
            "generic_formula_cost_currency": rec["generic_formula_cost_currency"],
            "generic_formula_cost_basis": rec["generic_formula_cost_basis"],
            "generic_formula_cost_raw": rec["generic_formula_cost_raw"],
        }
