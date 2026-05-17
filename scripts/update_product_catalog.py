"""
Cap nhat danh muc san pham goi y bang cach merge catalog hien tai
voi dataset tu product_recommendation_system.

Chay: python scripts/update_product_catalog.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.data.catalog_builder import (
    load_existing_catalog,
    load_prs_products,
    merge_catalogs,
)


def _resolve_path(root_dir: Path, path_value: str) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return root_dir / path


def _parse_dedupe_fields(value: str | None) -> list[str] | None:
    if not value:
        return None
    fields = [item.strip() for item in value.split(",") if item.strip()]
    return fields or None


def main():
    parser = argparse.ArgumentParser(description="Update product catalog")
    parser.add_argument(
        "--catalog-path",
        default="datas/models/product_catalog.csv",
        help="Duong dan catalog hien tai",
    )
    parser.add_argument(
        "--prs-dir",
        default="samples/product-recommendation-system/datasets/products_dataset",
        help="Thu muc dataset mau",
    )
    parser.add_argument(
        "--output-path",
        default="datas/models/product_catalog.csv",
        help="Duong dan catalog dau ra",
    )
    parser.add_argument(
        "--id-prefix",
        default="prs_",
        help="Prefix cho product_id tu dataset mau",
    )
    parser.add_argument(
        "--dedupe-fields",
        default="name,category,price",
        help="Danh sach cot dedupe (phan tach boi dau phay)",
    )

    args = parser.parse_args()
    catalog_path = _resolve_path(ROOT_DIR, args.catalog_path)
    prs_dir = _resolve_path(ROOT_DIR, args.prs_dir)
    output_path = _resolve_path(ROOT_DIR, args.output_path)
    dedupe_fields = _parse_dedupe_fields(args.dedupe_fields)

    base_df = load_existing_catalog(catalog_path)
    prs_df = load_prs_products(prs_dir, id_prefix=args.id_prefix)

    if base_df.empty and prs_df.empty:
        print("⚠️ Khong co du lieu de merge.")
        return

    merged_df = merge_catalogs(base_df, prs_df, dedupe_subset=dedupe_fields)
    merged_df.to_csv(output_path, index=False, encoding="utf-8-sig")

    base_count = len(base_df)
    prs_count = len(prs_df)
    merged_count = len(merged_df)
    print("✅ Da cap nhat catalog")
    print(f"  Base:   {base_count:,}")
    print(f"  PRS:    {prs_count:,}")
    print(f"  Merged: {merged_count:,}")
    print(f"  Output: {output_path}")

    if dedupe_fields:
        print(f"  Dedupe: {', '.join(dedupe_fields)}")


if __name__ == "__main__":
    main()
