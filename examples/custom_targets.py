"""Examples with multiple custom targets and soil overrides."""

from turba_client import TurbaClient

client = TurbaClient()

df = client.get_recommendations(
    longitude=-7.616,
    latitude=33.589,
    crop_name="Wheat (Rainfed)",
    target_yield=[25, 35, 45],
    ph=7.8,
    matiere_organique_pct=1.9,
    p_assimilable_mgkg_p2o5=28,
    k_mgkg_k2o=210,
)

print(df[["crop_name", "target_yield_level", "target_yield", "target_yield_mode", "N_kg_ha", "P_kg_ha", "K_kg_ha"]])

# Expected output placeholder:
#      crop_name target_yield_level  target_yield target_yield_mode  N_kg_ha  P_kg_ha  K_kg_ha
# 0  Wheat (Rainfed)            custom          25.0            custom      ...      ...      ...
