"""
Service quản lý tải và cache các mô hình Machine Learning.
"""

import json
import logging
from pathlib import Path

import joblib
import pandas as pd

# Import class để joblib.load() hoạt động đúng
from src.models.recommender import ProductRecommender          # noqa: F401
from src.models.collab_filter import CollaborativeFilteringRecommender  # noqa: F401

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
PROCESSED_DIR = ROOT_DIR / "datas" / "processed"
MODELS_DIR = ROOT_DIR / "datas" / "models"

_models: dict = {}
_load_attempted = False


def get_models() -> dict:
    """Tải và cache tất cả models. Load từng model độc lập để tránh lỗi cascade."""
    global _load_attempted
    if _load_attempted:
        return _models
    _load_attempted = True

    # Tải các model pickle
    _load_one("tfidf",          PROCESSED_DIR / "tfidf_vectorizer.pkl")
    _load_one("nb",             MODELS_DIR / "naive_bayes.pkl")
    _load_one("gmm",            MODELS_DIR / "gmm_model.pkl")
    _load_one("svd",            MODELS_DIR / "svd_transformer.pkl")
    # Thay đổi sang shopee recommender
    _load_one("recommender",    MODELS_DIR / "shopee_recommender.pkl")
    _load_one("cf_recommender", MODELS_DIR / "cf_recommender.pkl")

    # Tải association rules (CSV)
    try:
        _models["rules"] = pd.read_csv(MODELS_DIR / "association_rules.csv")
        logger.info("  [OK] rules (%d rows)", len(_models["rules"]))
    except Exception as e:
        logger.warning("  [SKIP] rules: %s", e)

    # Tải topic labels (JSON)
    try:
        with open(MODELS_DIR / "topic_labels.json", "r", encoding="utf-8") as f:
            _models["topic_labels"] = json.load(f)
        logger.info("  [OK] topic_labels")
    except Exception as e:
        logger.warning("  [SKIP] topic_labels: %s", e)

    # Tải product catalog (CSV) - Dùng bộ Shopee mới
    try:
        _models["catalog"] = pd.read_csv(MODELS_DIR / "shopee_catalog_new.csv")
        logger.info("  [OK] catalog (%d products)", len(_models["catalog"]))
    except Exception as e:
        logger.warning("  [SKIP] catalog: %s", e)

    loaded = [
        k for k in ("tfidf", "nb", "gmm", "svd", "recommender", "cf_recommender", "rules")
        if k in _models
    ]
    logger.info("Models đã tải: %s", loaded)
    return _models


def _load_one(key: str, path: Path):
    """Tải một model từ file pickle. Log lỗi nếu thất bại."""
    try:
        _models[key] = joblib.load(path)
        logger.info("  [OK] %s", key)
    except Exception as e:
        logger.warning("  [FAIL] %s: %s", key, e)
