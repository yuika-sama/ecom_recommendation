"""
Công cụ hợp nhất danh mục sản phẩm từ nhiều nguồn, bao gồm dataset mẫu.
Cung cấp các hàm chuẩn hóa để đưa các định dạng dữ liệu khác nhau (Shopee, Tiki) về chung một cấu trúc chuẩn.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

RE_NON_NUM = re.compile(r"[^0-9.,]")
RE_MULTI_SPACE = re.compile(r"\s+")


def _normalize_category(value: str) -> str:
    """Chuẩn hóa tên danh mục: xóa khoảng trắng thừa, fallback về 'Khac'."""
    text = str(value or "").strip()
    text = RE_MULTI_SPACE.sub(" ", text)
    return text or "Khac"


def _parse_numeric(value) -> float | None:
    """Trích xuất giá trị số từ chuỗi hỗn hợp (ví dụ: '1.200.000 đ' -> 1200000.0)."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    cleaned = RE_NON_NUM.sub("", text)
    if not cleaned:
        return None
    # Xử lý trường hợp vừa có '.' vừa có ',' (vd: 1.200,50)
    if "." in cleaned and "," in cleaned:
        digits = re.sub(r"[^0-9]", "", cleaned)
        return float(digits) if digits else None

    # Phân biệt dấu phân cách hàng nghìn và thập phân
    sep = "." if "." in cleaned else "," if "," in cleaned else None
    if sep is None:
        return float(cleaned)
    parts = cleaned.split(sep)
    # Giả định nếu phần sau cùng có <= 2 chữ số thì là phần thập phân
    if len(parts[-1]) <= 2:
        return float(".".join(parts))
    return float("".join(parts))


def parse_price(value) -> float | None:
    """Trích xuất giá sản phẩm từ chuỗi thô."""
    return _parse_numeric(value)


def parse_rating(value) -> float | None:
    """Trích xuất điểm đánh giá (rating) từ chuỗi thô."""
    num = _parse_numeric(value)
    if num is None:
        return None
    return round(float(num), 3)


def parse_solds(value) -> int | None:
    """Trích xuất số lượng đã bán, xử lý các hậu tố như 'k' (nghìn), 'm' (triệu)."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).lower()
    text = text.replace("da ban", "").replace("đã bán", "").strip()
    if not text:
        return None
    multiplier = 1
    if "k" in text:
        multiplier = 1000
        text = text.replace("k", "")
    if "m" in text:
        multiplier = 1000000
        text = text.replace("m", "")
    text = text.replace(",", ".")
    num = _parse_numeric(text)
    if num is None:
        return None
    return int(num * multiplier)


def _pick_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Tìm cột đầu tiên trong DataFrame khớp với danh sách ứng viên."""
    for col in candidates:
        if col in df.columns:
            return col
    return None


def normalize_catalog_df(
    df: pd.DataFrame,
    id_prefix: str | None = None,
    source: str | None = None,
) -> pd.DataFrame:
    """
    Chuẩn hóa một DataFrame catalog thành định dạng chung.
    
    Tự động tìm kiếm các cột tương ứng (id, name, price, v.v.) dựa trên danh sách các tên cột phổ biến.
    Tạo cột `combined_text` để sử dụng cho Content-based Recommender.
    
    Args:
        df: DataFrame đầu vào.
        id_prefix: Tiền tố để thêm vào product_id (để tránh trùng lặp giữa các nguồn).
        source: Nhãn nguồn dữ liệu (sẽ được thêm vào cột `source`).
        
    Returns:
        DataFrame đã được chuẩn hóa.
    """
    id_col = _pick_column(df, ["product_id", "id", "productId", "product_uid"])
    name_col = _pick_column(df, ["name", "product_name", "title"])
    category_col = _pick_column(df, ["category", "Category"])
    desc_col = _pick_column(df, ["description", "desc", "product_description"])
    price_col = _pick_column(df, ["price", "current_price", "original_price", "Price"])
    rating_col = _pick_column(df, ["rating", "avg_rating", "rating_average"])
    image_col = _pick_column(df, ["image", "cover_link", "image_url"])
    solds_col = _pick_column(df, ["solds", "quantity_sold"])
    location_col = _pick_column(df, ["location"])

    if id_col:
        base_ids = df[id_col].astype(str)
    else:
        base_ids = pd.Series(range(1, len(df) + 1)).astype(str)

    if id_prefix:
        product_ids = id_prefix + base_ids
    else:
        product_ids = base_ids

    name = df[name_col].astype(str) if name_col else ""
    category = df[category_col].apply(_normalize_category) if category_col else "Khac"
    description = df[desc_col].astype(str) if desc_col else ""
    price = df[price_col].apply(parse_price) if price_col else None
    rating = df[rating_col].apply(parse_rating) if rating_col else None
    image = df[image_col].astype(str) if image_col else ""
    solds = df[solds_col].apply(parse_solds) if solds_col else None
    location = df[location_col].astype(str) if location_col else ""

    out = pd.DataFrame(
        {
            "product_id": product_ids,
            "name": name,
            "category": category,
            "price": price,
            "description": description,
            "rating": rating,
            "image": image,
            "solds": solds,
            "location": location,
        }
    )
    if source:
        out["source"] = source
        
    # Tạo cột văn bản tổng hợp cho Recommender
    out["combined_text"] = (
        out["name"].fillna("")
        + " "
        + out["category"].fillna("")
        + " "
        + out["description"].fillna("")
    ).str.strip()
    return out


def load_prs_products(products_dir: Path, id_prefix: str = "prs_") -> pd.DataFrame:
    """Tải và chuẩn hóa tất cả file CSV trong thư mục dataset mẫu."""
    frames: list[pd.DataFrame] = []
    for file_path in sorted(products_dir.glob("*.csv")):
        df = pd.read_csv(file_path)
        category = file_path.stem.replace("shopee_products_", "").replace("_", " ")
        df["category"] = _normalize_category(category)
        frames.append(normalize_catalog_df(df, id_prefix=id_prefix, source="prs_shopee"))
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def load_existing_catalog(path: Path) -> pd.DataFrame:
    """Tải và chuẩn hóa catalog đã có sẵn."""
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    return normalize_catalog_df(df, id_prefix=None, source="legacy")


def merge_catalogs(
    base_df: pd.DataFrame,
    extra_df: pd.DataFrame,
    dedupe_subset: list[str] | None = None,
) -> pd.DataFrame:
    """Gộp hai catalog và loại bỏ dữ liệu trùng lặp."""
    combined = pd.concat([base_df, extra_df], ignore_index=True)
    combined = combined.drop_duplicates(subset=["product_id"], keep="first")
    if dedupe_subset:
        combined = combined.drop_duplicates(subset=dedupe_subset, keep="first")
    combined = combined.reset_index(drop=True)
    return combined


def build_merged_catalog(
    existing_catalog_path: Path | None,
    prs_products_dir: Path | None,
    id_prefix: str = "prs_",
    dedupe_subset: list[str] | None = None,
) -> pd.DataFrame:
    """Pipeline đầy đủ: tải các catalog và gộp chúng lại với nhau."""
    base_df = load_existing_catalog(existing_catalog_path) if existing_catalog_path else pd.DataFrame()
    prs_df = load_prs_products(prs_products_dir, id_prefix=id_prefix) if prs_products_dir else pd.DataFrame()
    if base_df.empty and prs_df.empty:
        return pd.DataFrame()
    return merge_catalogs(base_df, prs_df, dedupe_subset=dedupe_subset)


def load_prs_orders(orders_path: Path, id_prefix: str = "prs_") -> pd.DataFrame:
    """Tải file lịch sử mua hàng, tự động thêm tiền tố id nếu cần."""
    df = pd.read_csv(orders_path)
    if "product_id" in df.columns:
        df["product_id"] = id_prefix + df["product_id"].astype(str)
    if "user_id" in df.columns:
        df["user_id"] = id_prefix + df["user_id"].astype(str)
    return df

