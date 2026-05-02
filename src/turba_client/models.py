"""Typed dataclasses used internally and exposed where helpful."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SiteContext:
    """Parsed site metadata returned by upstream detail endpoint."""

    longitude: float | None = None
    latitude: float | None = None
    region: str | None = None
    province: str | None = None
    id_province: str | None = None
    commune: str | None = None
    soil_type: str | None = None
    texture_globale: str | None = None
    ph: float | None = None
    matiere_organique_pct: float | None = None
    p_assimilable_mgkg_p2o5: float | None = None
    k_mgkg_k2o: float | None = None
    slider_target_yield_min: float | None = None
    slider_target_yield_max: float | None = None
    slider_target_yield_step: float | None = None
    slider_target_yield_default: float | None = None
    slider_target_yield_unit: str | None = None


@dataclass(slots=True)
class CropRule:
    """RDT slider metadata for one upstream crop."""

    crop_id: int
    crop_name_raw: str | None = None
    crop_name: str | None = None
    target_yield_min: float | None = None
    target_yield_max: float | None = None
    target_yield_step: float | None = None
    target_yield_unit: str | None = None


@dataclass(slots=True)
class TargetRequest:
    """One resolved target-yield request for a given crop."""

    request_label: str
    request_mode: str
    target_yield: float
