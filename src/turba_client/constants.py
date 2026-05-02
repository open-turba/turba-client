"""Project constants for Turba Client Library."""

from __future__ import annotations

DETAIL_URL = "http://www.fertimap.ma/php/detail.inc.php"
CALCUL_URL = "http://www.fertimap.ma/php/calcul.php"

DEFAULT_TIMEOUT = 15
DEFAULT_SLEEP_SECONDS = 0.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_TARGET_YIELD_LEVEL = "medium"
DEFAULT_USER_AGENT = "turba-client/0.1.0"

TARGET_YIELD_LEVELS = {"low", "medium", "high"}
DEFAULT_MULTI_VALUE_SEPARATORS = ("|", ";")

CANONICAL_INPUT_COLUMNS = (
    "longitude",
    "latitude",
    "crop_name",
    "target_yield_level",
    "target_yield",
    "ph",
    "matiere_organique_pct",
    "p_assimilable_mgkg_p2o5",
    "k_mgkg_k2o",
)

# Mapping upstream crop identifiers.
CROP_ID: dict[int, str] = {
    1: "Wheat (Rainfed)",
    2: "Wheat (Irrigated)",
    3: "Barley (Rainfed)",
    4: "Sunflower",
    5: "Rapeseed",
    6: "Maize (Grain)",
    7: "Maize (Silage)",
    8: "Potato",
    9: "Strawberry",
    10: "Sweet Potato",
    11: "Onion",
    12: "Artichoke",
    13: "Olive (Rainfed)",
    14: "Olive (Irrigated)",
    15: "Apple Tree",
    16: "Apple Tree",
    17: "Peach",
    18: "Nectarine",
    19: "Plum",
    20: "Citrus (Oranges)",
    21: "Citrus (Small Fruits)",
    22: "Sugar Beet",
    23: "Sugarcane",
    24: "Peanut",
    25: "Faba Bean (Dry)",
    26: "Broad Bean",
    27: "Lentil",
    28: "Pea (Dry)",
    29: "Chickpea",
    30: "Beans (Dry)",
    31: "Alfalfa (Fresh Per Year)",
    32: "Table Grapevine",
    33: "Melon",
    34: "Almond",
    35: "Tomato (Open Field)",
    36: "Eggplant",
}
