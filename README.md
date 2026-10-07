<h1 align="center">turba-client</h1>

<p align="center">
  <strong>A Python client for querying publicly accessible soil profile and fertilizer recommendation workflows across Morocco.</a></strong>
</p>

<p align="center">
  Query site-level fertilizer recommendations from geographic coordinates, inspect available crops and yield-target ranges, and scale from one field to many with a clean Python API and CLI.
</p>

<p align="center">
  <!-- PyPI version -->
  <a href="https://pypi.org/project/turba-client/">
    <img src="https://img.shields.io/pypi/v/turba-client.svg?label=PyPI" alt="PyPI" />
  </a>

  <!-- Security -->
  <a href="https://badge.socket.dev/pypi/package/turba-client/0.1.0?artifact_id=tar-gz">
    <img src="https://badge.socket.dev/pypi/package/turba-client/0.1.0?artifact_id=tar-gz" alt="Socket Security" />
  </a>

  <!-- Downloads -->
  <a href="https://pepy.tech/project/turba-client">
    <img src="https://static.pepy.tech/badge/turba-client" alt="Downloads" />
  </a>

  <!-- arXiv -->
  <a href="https://arxiv.org/abs/2610.05949">
    <img src="https://img.shields.io/badge/arXiv-2610.05949-b31b1b.svg" alt="arXiv" />
  </a>

  <!-- License -->
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT" />
  </a>
</p>

---

## Why `turba_client`?

`turba_client` is a production-friendly Python library that makes it easy to query **site-specific NPK fertilizer recommendations** from [**fertimap.ma**](http://www.fertimap.ma/) using only a field location, with optional agronomic overrides.

It is designed for researchers, agronomists, and developers who want a reproducible way to move from:

- **coordinates**
- to **site context**
- to **available crops and yield targets**
- to **fertilizer recommendations**
- and finally to **batch processing and downstream analysis**

The library supports both **single-field workflows** and **multi-field pipelines**, with a clean Python interface and command-line support.

---

## What you can do with it

With `turba_client`, you can:

- query a site from its **longitude** and **latitude**
- inspect soil and administrative context returned for that site
- list the crops available at that location
- request recommendations for:
  - one crop or many crops
  - one target-yield level or many target-yield levels
  - explicit numeric target yields
- override selected field values when needed:
  - `crop_name`
  - `target_yield_level`
  - `ph`
  - `matiere_organique_pct`
  - `p_assimilable_mgkg_p2o5`
  - `k_mgkg_k2o`
- process many fields at once from a DataFrame or CSV
- map user column names to the library schema before batch processing

---

## Installation

### From PyPI

```bash
pip install turba-client
````

### Development install

```bash
pip install -e .[dev]
```

---

## Quick start

```python
from turba_client import TurbaClient

client = TurbaClient()

df = client.get_recommendations(
    longitude=-7.616,
    latitude=33.589,
    crop_name="Wheat (Rainfed)",
    target_yield_level="medium",
)

print(df[["crop_name", "target_yield_level", "N_kg_ha", "P_kg_ha", "K_kg_ha"]])
```

**Expected output**

```text
        crop_name target_yield_level  N_kg_ha  P_kg_ha  K_kg_ha
0      Wheat (Rainfed)    medium    ...      ...      ...
```

---

# User Workflow

The typical `turba_client` workflow is intentionally simple:

## 1) Start with a site

You provide coordinates.

```python
from turba_client import TurbaClient

client = TurbaClient()

site = client.get_site_profile(
    longitude=-7.616,
    latitude=33.589,
)

print(site)
```

**Expected output**

```text
SiteProfile(
    longitude=-7.616,
    latitude=33.589,
    region='...',
    province='...',
    commune='...',
    soil_type='...',
    texture_globale='...',
    ph=...,
    matiere_organique_pct=...,
    p_assimilable_mgkg_p2o5=...,
    k_mgkg_k2o=...
)
```

This step answers:
**What does turba-client know about this field?**

---

## 2) Discover the crops available for that site

```python
crops = client.list_crops(
    longitude=-7.616,
    latitude=33.589,
)

print(crops[["crop_id", "crop_name", "target_yield_min", "target_yield_max", "target_yield_step", "target_yield_unit"]])
```

**Expected output**

```text
   crop_id      crop_name        target_yield_min  target_yield_max  target_yield_step  target_yield_unit
0          1      Wheat (Rainfed)          ...      ...      ...      ...
1          2      Wheat (Irrigated)        ...      ...      ...      ...
2          3      Barley (Rainfed)         ...      ...      ...      ...
...
```

This step answers:
**Which crops are valid here, and what are the allowed target-yield ranges?**

---

## 3) Choose a target strategy

You can request recommendations using:

* a standard target level: `"low"`, `"medium"`, `"high"`
* several target levels at once
* one or more explicit numeric target yields

### A. One target level

```python
df = client.get_recommendations(
    longitude=-7.616,
    latitude=33.589,
    crop_name="Wheat (Rainfed)",
    target_yield_level="medium",
)
```

### B. Multiple target levels

```python
df = client.get_recommendations(
    longitude=-7.616,
    latitude=33.589,
    crop_name="Wheat (Rainfed)",
    target_yield_level=["low", "medium", "high"],
)
```

### C. A custom numeric target yield

```python
df = client.get_recommendations(
    longitude=-7.616,
    latitude=33.589,
    crop_name="Wheat (Rainfed)",
    target_yield=45,
)
```

### D. Multiple custom numeric target yields

```python
df = client.get_recommendations(
    longitude=-7.616,
    latitude=33.589,
    crop_name="Wheat (Rainfed)",
    target_yield=[35, 45, 55],
)
```

> If a numeric `target_yield` falls outside the valid crop range returned by turba-client for that site, `turba_client` raises a validation error.

This step answers:
**What production target am I optimizing for?**

---

## 4) Request recommendations

### Single crop

```python
df = client.get_recommendations(
    longitude=-7.616,
    latitude=33.589,
    crop_name="Wheat (Rainfed)",
    target_yield_level="high",
)

print(df[[
    "crop_name",
    "target_yield_level",
    "target_yield_value",
    "N_kg_ha",
    "P_kg_ha",
    "K_kg_ha",
]])
```

**Expected output**

```text
      crop_name target_yield_level  target_yield_value  N_kg_ha  P_kg_ha  K_kg_ha
0    Wheat (Rainfed)      high      ...      ...      ...      ...
```

### Multiple crops at once

```python
df = client.get_recommendations(
    longitude=-7.616,
    latitude=33.589,
    crop_name=["Wheat (Rainfed)", "Barley (Rainfed)"],
    target_yield_level="medium",
)
```

### All available crops for a site

If `crop_name` is omitted, the client can return recommendations across the valid crop space for the requested target strategy.

```python
df = client.get_recommendations(
    longitude=-7.616,
    latitude=33.589,
    target_yield_level="medium",
)
```

This step answers:
**What N, P, and K recommendations should I use under the chosen crop and target settings?**

---

## 5) Override selected field values when needed

For scenario testing, controlled comparisons, or curated field data, you can override the values used in the recommendation request.

```python
df = client.get_recommendations(
    longitude=-7.616,
    latitude=33.589,
    crop_name="Wheat (Rainfed)",
    target_yield_level="medium",
    ph=7.8,
    matiere_organique_pct=1.9,
    p_assimilable_mgkg_p2o5=28,
    k_mgkg_k2o=210,
)
```

This is useful when:

* you want to compare default vs curated values
* you have field-lab measurements that should replace parsed defaults
* you want reproducible sensitivity analyses

---

## 6) Scale to many sites

`turba_client` supports batch processing from pandas DataFrames and CSV files.

### Batch from a DataFrame

```python
import pandas as pd
from turba_client import TurbaClient

client = TurbaClient()

sites = pd.DataFrame([
    {
        "longitude": -7.616,
        "latitude": 33.589,
        "crop_name": "Wheat (Rainfed)",
        "target_yield_level": "medium",
    },
    {
        "longitude": -6.832,
        "latitude": 33.972,
        "crop_name": "Barley (Rainfed)",
        "target_yield_level": ["low", "high"],
        "matiere_organique_pct": 1.5,
        "p_assimilable_mgkg_p2o5": 20,
        "k_mgkg_k2o": 160,
    },
])

results = client.get_recommendations_batch(sites)
print(results.head())
```

### Batch with custom column names

If your input data uses different column names, map them first.

```python
prepared = client.prepare_input_table(
    sites,
    column_map={
        "longitude": "lon",
        "latitude": "lat",
        "crop_name": "crop",
        "target_yield_level": "target_level",
    },
)

results = client.get_recommendations_batch(prepared)
```

This step answers:
**How do I move from one field to a full operational dataset?**

---

# Python API

## Main public interface

```python
from turba_client import TurbaClient
```

### `TurbaClient(...)`

Create a client.

```python
client = TurbaClient(
    timeout=20,
    sleep_seconds=0.2,
    max_retries=3,
    user_agent="turba-client/0.1.0",
)
```

### `get_site_profile(...)`

Inspect the site-level administrative and soil context.

```python
client.get_site_profile(longitude=-7.616, latitude=33.589)
```

### `list_crops(...)`

List available crops and target-yield ranges for a site.

```python
client.list_crops(longitude=-7.616, latitude=33.589)
```

### `get_recommendations(...)`

Get recommendations for one site.

```python
client.get_recommendations(
    longitude=-7.616,
    latitude=33.589,
    crop_name="Wheat (Rainfed)",
    target_yield_level="medium",
)
```

Supports:

* one or more crops
* one or more `target_yield_level` values
* one or more `target_yield` values
* optional overrides

### `prepare_input_table(...)`

Normalize input tables before batch runs.

```python
client.prepare_input_table(df, column_map={...})
```

### `get_recommendations_batch(...)`

Process multiple rows in a batch.

```python
client.get_recommendations_batch(df)
```

---

# CLI usage

The package installs a command-line tool named `turba-client`.

## Single-site request

```bash
turba-client recommend-site \
  --longitude -7.616 \
  --latitude 33.589 \
  --crop-name "Wheat (Rainfed)" \
  --target-yield-level medium
```

## Multiple target levels

```bash
turba-client recommend-site \
  --longitude -7.616 \
  --latitude 33.589 \
  --crop-name "Wheat (Rainfed)" \
  --target-yield-level low \
  --target-yield-level medium \
  --target-yield-level high
```

## Custom numeric target yield

```bash
turba-client recommend-site \
  --longitude -7.616 \
  --latitude 33.589 \
  --crop-name "Wheat (Rainfed)" \
  --target-yield 45
```

## Batch from CSV

```bash
turba-client recommend-many \
  --input-file sites.csv \
  --output results.csv
```

---

# Validation and errors

The library validates:

* coordinate ranges
* accepted target level names
* target-yield bounds against crop-specific allowed ranges
* required columns for batch processing

Typical exceptions include:

* `ValidationError`
* `CropNotFoundError`
* `SiteDataNotFoundError`
* `UpstreamResponseError`

Example:

```python
from turba_client import (
    TurbaClient,
    ValidationError,
    CropNotFoundError,
    SiteDataNotFoundError,
    UpstreamResponseError,
)

client = TurbaClient()

try:
    df = client.get_recommendations(
        longitude=-7.616,
        latitude=33.589,
        crop_name="Non Existing Crop",
    )
except ValidationError as e:
    print("Invalid input:", e)
except CropNotFoundError as e:
    print("Crop not found:", e)
except SiteDataNotFoundError as e:
    print("No site data found:", e)
except UpstreamResponseError as e:
    print("Unexpected upstream response:", e)
```

---

# Example files

The `examples/` directory contains end-to-end scripts:

* `basic_usage.py`
* `custom_targets.py`
* `batch_with_column_mapping.py`
* `user_workflow.py`

These examples are intended to mirror real user journeys:

* inspect a site
* list crops
* request recommendations
* run batch processing
* export results

---

# Development

## Run tests

```bash
pytest
```

## Build distributions

```bash
python -m build
```

This creates wheel and source-distribution artifacts in `dist/`.

---

# Acknowledgment

This library builds on the valuable work of the [**fertimap.ma**](http://www.fertimap.ma/), which developed and maintains the underlying platform and recommendation service. `turba_client` is an independent Python client created to make [fertimap.ma](http://www.fertimap.ma/) workflows more accessible for developers, researchers, and applied agronomy use cases. It does not claim ownership of the platform, its data, or its recommendation engine.
