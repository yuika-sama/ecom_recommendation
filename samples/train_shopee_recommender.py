import pandas as pd
import joblib
import logging
from pathlib import Path
from src.models.recommender import ProductRecommender

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def build_new_recommender():
    data_path = Path("datas/models/shopee_catalog_new.csv")
    model_path = Path("datas/models/shopee_recommender.pkl")
    
    logger.info(f"Loading new catalog from {data_path}...")
    df = pd.read_csv(data_path)
    
    logger.info("Initializing ProductRecommender...")
    # Increase max_features since dataset is large
    recommender = ProductRecommender(ngram_range=(1, 2), max_features=40000)
    
    logger.info("Fitting recommender model on 'combined_text'...")
    recommender.fit(df, text_column='combined_text')
    
    logger.info(f"Saving model to {model_path}...")
    joblib.dump(recommender, model_path)
    logger.info("Model saved successfully.")

if __name__ == "__main__":
    build_new_recommender()
