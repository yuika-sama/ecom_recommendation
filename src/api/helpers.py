"""
Hàm tiện ích dùng chung cho API endpoints.
"""

import numpy as np
import pandas as pd

from src.utils.text_preprocess import load_stopwords, preprocess_text
from pathlib import Path

# ── Stopwords ──────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
STOPWORDS_PATH = ROOT_DIR / "datas" / "vietnamese-stopwords.txt"
STOPWORDS = load_stopwords(STOPWORDS_PATH)


def preprocess(text: str) -> str:
    """Tiền xử lý văn bản tiếng Việt: làm sạch, chuẩn hóa teencode, tách từ, loại stopwords."""
    return preprocess_text(text, stopwords=STOPWORDS, use_underthesea=True)


def df_to_records(df: pd.DataFrame) -> list[dict]:
    """Chuyển DataFrame thành list[dict], xử lý NaN/Inf cho JSON serialization."""
    if df is None or df.empty:
        return []
    # Thay NaN và Inf bằng None trước khi chuyển sang dict
    clean = df.replace({np.nan: None, np.inf: None, -np.inf: None})
    records = clean.to_dict(orient="records")
    # Đảm bảo không còn float NaN nào lọt qua (phòng trường hợp edge-case)
    for rec in records:
        for k, v in rec.items():
            if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
                rec[k] = None
    return records
