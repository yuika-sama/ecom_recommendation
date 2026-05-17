"""
Route: Danh sách sản phẩm với tìm kiếm và phân trang.
"""

import pandas as pd
from fastapi import APIRouter, HTTPException

from src.api.services.model_loader import get_models

router = APIRouter(tags=["Sản phẩm"])


@router.get("/api/products")
async def get_products(
    search: str = "",
    category: str = "",
    page: int = 1,
    limit: int = 20,
):
    """Lấy danh sách sản phẩm với tìm kiếm và phân trang."""
    models = get_models()
    if "catalog" not in models:
        raise HTTPException(503, "Product catalog chưa sẵn sàng.")

    df = models["catalog"].copy()

    # Tìm kiếm theo tên, category, description
    if search.strip():
        q = search.lower()
        cols = df.columns.tolist()
        cond = df["name"].fillna("").astype(str).str.lower().str.contains(q, na=False)
        if "category" in cols:
            cond = cond | df["category"].fillna("").astype(str).str.lower().str.contains(q, na=False)
        if "description" in cols:
            cond = cond | df["description"].fillna("").astype(str).str.lower().str.contains(q, na=False)
        df = df[cond]

    # Lọc theo category
    if category.strip():
        df = df[df["category"].str.lower() == category.lower()]

    total = len(df)
    start = (page - 1) * limit
    page_df = df.iloc[start: start + limit]

    # Lấy danh sách categories
    catalog_all = models["catalog"]
    if "category" in catalog_all.columns:
        categories = sorted(catalog_all["category"].dropna().unique().tolist())
    else:
        categories = []

    # Chỉ trả về các cột hiển thị, xử lý NaN
    display_cols = [c for c in ["product_id", "name", "category", "price", "rating"] if c in page_df.columns]
    products = (
        page_df[display_cols]
        .astype(object)
        .where(pd.notnull(page_df[display_cols]), None)
        .to_dict(orient="records")
    )

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "products": products,
        "categories": categories[:50],
    }
