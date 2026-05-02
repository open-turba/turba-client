"""Typical interactive workflow for Turba users.

Replace coordinates with a real site before running.
"""

from turba_client import TurbaClient

client = TurbaClient()

# Step 1: inspect the site.
profile = client.get_site_profile(-7.616, 33.589)
print(profile)

# Expected output placeholder:
# SiteContext(longitude=-7.616, latitude=33.589, region='...', province='...', ...)

# Step 2: list all available crops and their target-yield ranges.
crops = client.list_crops(-7.616, 33.589)
print(crops[["crop_id", "crop_name", "target_yield_min", "target_yield_max", "target_yield_unit"]])

# Expected output placeholder:
#    crop_id     crop_name  target_yield_min  target_yield_max target_yield_unit
# 0           1   Wheat (Rainfed)     ...      ...    qx/ha

# Step 3: request recommendations for several levels at once.
recommendations = client.get_recommendations(
    longitude=-7.616,
    latitude=33.589,
    crop_name="Wheat (Rainfed)",
    target_yield_level=["low", "medium", "high"],
)
print(
    recommendations[
        ["crop_name", "target_yield_level", "target_yield", "N_kg_ha", "P_kg_ha", "K_kg_ha"]
    ]
)

# Expected output placeholder:
#      crop_name target_yield_level  target_yield  N_kg_ha  P_kg_ha  K_kg_ha
# 0  Wheat (Rainfed)        low          ...      ...      ...      ...
