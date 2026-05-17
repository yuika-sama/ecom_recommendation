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
from src.data.catalog_builder import normalize_catalog_df
from src.models.recommender import ProductRecommender

ROOT_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT_DIR / "datas" / "models"

print("Dang tai product catalog...")
raw_catalog = pd.read_csv(MODELS_DIR / "product_catalog.csv")
print(f"  Catalog: {raw_catalog.shape}, columns: {raw_catalog.columns.tolist()}")

df_catalog = normalize_catalog_df(raw_catalog, id_prefix=None, source=None)

print("Dang fit ProductRecommender...")
recommender = ProductRecommender(ngram_range=(1, 2), max_features=30_000)
recommender.fit(df_catalog, text_column="combined_text")

output_path = MODELS_DIR / "recommender.pkl"
joblib.dump(recommender, output_path)
print(f"Da luu: {output_path}")
print(f"  Matrix shape: {recommender.tfidf_matrix.shape}")
print(f"  So san pham: {len(df_catalog)}")
print("Hoan thanh! Restart uvicorn de ap dung.")
