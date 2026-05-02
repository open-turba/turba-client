"""Minimal example for the public API."""

from turba_client import TurbaClient

client = TurbaClient()
recommendations = client.recommend_site(
    longitude=-7.616,
    latitude=33.589,
    crop_name="Wheat (Rainfed)",
)
print(recommendations)
