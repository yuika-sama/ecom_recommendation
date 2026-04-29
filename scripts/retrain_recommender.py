"""
Script retrain và lưu lại recommender.pkl với class từ src.models.recommender.
Chạy: python scripts/retrain_recommender.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import joblib
from pathlib import Path
from src.models.recommender import ProductRecommender

ROOT_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT_DIR / "datas" / "models"

print("Dang tai product catalog...")
df_catalog = pd.read_csv(MODELS_DIR / "product_catalog.csv")
print(f"  Catalog: {df_catalog.shape}, columns: {df_catalog.columns.tolist()}")

# Rebuild combined_text nếu chưa có
if "combined_text" not in df_catalog.columns:
    name_col = next((c for c in df_catalog.columns if "name" in c.lower()), df_catalog.columns[0])
    cat_col  = next((c for c in df_catalog.columns if "categ" in c.lower()), "")
    desc_col = next((c for c in df_catalog.columns if "desc" in c.lower()), "")
    df_catalog["combined_text"] = (
        df_catalog.get(name_col, "").astype(str) + " " +
        df_catalog.get(cat_col, pd.Series([""] * len(df_catalog))).astype(str) + " " +
        df_catalog.get(desc_col, pd.Series([""] * len(df_catalog))).astype(str)
    ).str.strip()

print("Dang fit ProductRecommender...")
recommender = ProductRecommender(ngram_range=(1, 2), max_features=30_000)
recommender.fit(df_catalog, text_column="combined_text")

output_path = MODELS_DIR / "recommender.pkl"
joblib.dump(recommender, output_path)
print(f"Da luu: {output_path}")
print(f"  Matrix shape: {recommender.tfidf_matrix.shape}")
print(f"  So san pham: {len(df_catalog)}")
print("Hoan thanh! Restart uvicorn de ap dung.")
