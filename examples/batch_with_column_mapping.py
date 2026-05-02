"""Batch example where the user CSV headers differ from the library schema."""

import pandas as pd

from turba_client import TurbaClient

client = TurbaClient()

raw = pd.DataFrame(
    [
        {"lon": -7.616, "lat": 33.589, "crop": "Wheat (Rainfed)", "targets": "low|high"},
        {"lon": -6.832, "lat": 33.972, "crop": "Barley (Rainfed)", "yield_values": "20|30"},
    ]
)

results = client.get_recommendations_batch(
    raw,
    column_map={
        "longitude": "lon",
        "latitude": "lat",
        "crop_name": "crop",
        "target_yield_level": "targets",
        # Or use target_yield instead when your CSV contains numeric custom targets.
        # "target_yield": "yield_values",
    },
)

print(results.head())

# Expected output placeholder:
#    input_row_index  longitude  latitude     crop_name target_yield_level  ...
# 0                0     -7.616    33.589  Wheat (Rainfed)             low  ...
