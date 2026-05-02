"""Command-line interface for Turba Client."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from turba_client.client import TurbaClient
from turba_client.exceptions import ValidationError


def _parse_column_map(values: list[str] | None) -> dict[str, str] | None:
    if not values:
        return None
    mapping: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise ValidationError(
                f"Invalid --column-map value {value!r}. Use canonical=user_column syntax."
            )
        canonical, user_column = value.split("=", 1)
        mapping[canonical.strip()] = user_column.strip()
    return mapping


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="turba-client")
    subparsers = parser.add_subparsers(dest="command", required=True)

    site_parser = subparsers.add_parser(
        "get-recommendations",
        aliases=["recommend-site"],
        help="Fetch fertilizer recommendations for one site",
    )
    site_parser.add_argument("--longitude", required=True, type=float)
    site_parser.add_argument("--latitude", required=True, type=float)
    site_parser.add_argument(
        "--crop-name",
        action="append",
        help="Crop name. Repeat the flag to request more than one crop.",
    )
    site_parser.add_argument(
        "--target-yield-level",
        nargs="+",
        default=None,
        help="One or many target-yield levels: low medium high",
    )
    site_parser.add_argument(
        "--target-yield",
        nargs="+",
        type=float,
        default=None,
        help="One or many custom target-yield values.",
    )
    site_parser.add_argument("--ph", type=float)
    site_parser.add_argument("--matiere-organique-pct", type=float)
    site_parser.add_argument("--p-assimilable-mgkg-p2o5", type=float)
    site_parser.add_argument("--k-mgkg-k2o", type=float)
    site_parser.add_argument("--output")
    site_parser.add_argument(
        "--format", choices=["json", "csv"], default="json", help="stdout format"
    )

    batch_parser = subparsers.add_parser(
        "get-recommendations-batch",
        aliases=["recommend-many"],
        help="Fetch recommendations for a CSV or JSON batch file",
    )
    batch_parser.add_argument("--input-file", required=True)
    batch_parser.add_argument(
        "--column-map",
        action="append",
        help="Map library field names to user columns, e.g. longitude=lon",
    )
    batch_parser.add_argument("--output")
    batch_parser.add_argument(
        "--format", choices=["json", "csv"], default="csv", help="stdout format"
    )

    return parser


def _write_output(dataframe: pd.DataFrame, output_path: str | None, stdout_format: str) -> None:
    if output_path:
        output = Path(output_path)
        if output.suffix.lower() == ".json":
            output.write_text(dataframe.to_json(orient="records", indent=2), encoding="utf-8")
        else:
            dataframe.to_csv(output, index=False)
        return

    if stdout_format == "csv":
        print(dataframe.to_csv(index=False), end="")
    else:
        print(json.dumps(dataframe.to_dict(orient="records"), indent=2, default=str))


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    client = TurbaClient()

    if args.command in {"get-recommendations", "recommend-site"}:
        df = client.get_recommendations(
            longitude=args.longitude,
            latitude=args.latitude,
            crop_name=args.crop_name,
            target_yield_level=args.target_yield_level,
            target_yield=args.target_yield,
            ph=args.ph,
            matiere_organique_pct=args.matiere_organique_pct,
            p_assimilable_mgkg_p2o5=args.p_assimilable_mgkg_p2o5,
            k_mgkg_k2o=args.k_mgkg_k2o,
        )
        _write_output(df, args.output, args.format)
        return

    if args.command in {"get-recommendations-batch", "recommend-many"}:
        column_map = _parse_column_map(args.column_map)
        df = client.get_recommendations_batch(args.input_file, column_map=column_map)
        _write_output(df, args.output, stdout_format=args.format)
        return

    parser.error("Unknown command")


if __name__ == "__main__":
    main()
