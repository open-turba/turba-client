"""Minimal example for the public API."""

from turba_client import TurbaClient

client = TurbaClient()
recommendations = client.recommend_site(
    longitude=-7.616,
    latitude=33.589,
    crop_name="Wheat (Rainfed)",
)
print(recommendations)

first = recommendations.iloc[0]
print("Generic-formula applications:", first["generic_formula_applications"])
print(
    "Upstream estimated cost:",
    first["generic_formula_cost_amount"],
    first["generic_formula_cost_currency"],
    "per",
    first["generic_formula_cost_basis"],
)
