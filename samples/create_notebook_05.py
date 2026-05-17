import nbformat as nbf

nb = nbf.v4.new_notebook()

nb['cells'] = [
    nbf.v4.new_markdown_cell("""# 🛒 Notebook 05 — Cập nhật Shopee Recommender Model

**Mục tiêu:**
- Gộp dữ liệu từ Shopee (`data.xlsx` & `shopee_product_desc.json`) để xây dựng một tập catalog mới với hơn 15.000 sản phẩm.
- Huấn luyện lại mô hình Recommender (Content-based Filtering) sử dụng cấu trúc TF-IDF và Cosine Similarity.
- Xuất mô hình mới để tích hợp vào API backend, giúp chatbot AI tư vấn sâu hơn dựa trên `description`.

**Đầu vào:** `datas/recommend_dataset/data.xlsx`, `datas/recommend_dataset/shopee_product_desc.json`  
**Đầu ra:** `datas/models/shopee_catalog_new.csv`, `datas/models/shopee_recommender.pkl`
"""),
    nbf.v4.new_code_cell("""import pandas as pd
import re
import urllib.parse
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Khai báo đường dẫn
excel_path = "../datas/recommend_dataset/data.xlsx"
json_path = "../datas/recommend_dataset/shopee_product_desc.json"
out_csv = "../datas/models/shopee_catalog_new.csv"
out_model = "../datas/models/shopee_recommender.pkl"
"""),
    nbf.v4.new_markdown_cell("""## 1. Trích xuất & Gộp dữ liệu (Merge Data)"""),
    nbf.v4.new_code_cell("""def extract_from_shopee_url(url):
    try:
        url_str = str(url)
        decoded_url = urllib.parse.unquote(url_str)
        # Lấy tên, shop_id, item_id
        match = re.search(r'shopee\.vn/([^/]+)-i\.(\d+)\.(\d+)', decoded_url)
        if match:
            return match.group(1).replace('-', ' '), match.group(2), match.group(3)
    except:
        pass
    return None, None, None

# Đọc JSON
df_json = pd.read_json(json_path)
extracted = df_json['url'].apply(extract_from_shopee_url)
df_json['name'] = [x[0] for x in extracted]
df_json['item_id'] = [x[1] for x in extracted]
df_json['shop_id'] = [x[2] for x in extracted]
df_json = df_json.rename(columns={'desc': 'description'}).dropna(subset=['item_id'])
df_json['product_id'] = 'shp_' + df_json['shop_id'].astype(str) + '_' + df_json['item_id'].astype(str)
df_json['location'] = ""

# Đọc Excel
df_excel = pd.read_excel(excel_path)
df_excel['product_id'] = 'shp_' + df_excel['shop_id'].astype(str) + '_' + df_excel['item_id'].astype(str)
df_excel = df_excel.rename(columns={'shop_location': 'location'})
df_excel['description'] = ""
df_excel['url'] = ""

# Gộp (Concat)
df_combined = pd.concat([
    df_json[['product_id', 'name', 'description', 'url', 'location']], 
    df_excel[['product_id', 'name', 'description', 'url', 'location']]
], ignore_index=True)

# Xử lý missing & duplicate
df_combined['has_desc'] = df_combined['description'].apply(lambda x: 1 if pd.notna(x) and x != "" else 0)
df_combined = df_combined.sort_values(by='has_desc', ascending=False).drop_duplicates(subset=['product_id'], keep='first')
df_combined['name'] = df_combined['name'].fillna("Sản phẩm Shopee")
df_combined['description'] = df_combined['description'].fillna("")
df_combined['location'] = df_combined['location'].fillna("Toàn quốc")
df_combined['category'] = "Shopee"

df_combined['combined_text'] = (df_combined['name'] + " " + df_combined['description']).str.strip()

print(f"Tổng số sản phẩm sau khi gộp: {len(df_combined)}")
df_combined.to_csv(out_csv, index=False, encoding='utf-8-sig')
df_combined.head(3)
"""),
    nbf.v4.new_markdown_cell("""## 2. Huấn luyện mô hình Recommender (TF-IDF)"""),
    nbf.v4.new_code_cell("""import joblib
import sys
sys.path.append('..')
from src.models.recommender import ProductRecommender

print("Khởi tạo mô hình ProductRecommender...")
recommender = ProductRecommender(ngram_range=(1, 2), max_features=40000)

print("Đang huấn luyện (fit) mô hình trên text kết hợp (Tên + Mô tả)...")
recommender.fit(df_combined, text_column='combined_text')

# Lưu mô hình
joblib.dump(recommender, out_model)
print(f"Mô hình đã được lưu tại: {out_model}")
"""),
    nbf.v4.new_markdown_cell("""## 3. Chạy thử Gợi ý (Test Recommendation)"""),
    nbf.v4.new_code_cell("""query = "bánh tráng trộn siêu cay"
print(f"Kết quả gợi ý cho query: '{query}'\\n" + "-"*50)

results = recommender.recommend_by_query(query, top_k=5)
results[['product_id', 'name', 'location', 'similarity_score']]
""")
]

with open('notebooks/05_shopee_recommender.ipynb', 'w', encoding='utf-8') as f:
    nbf.write(nb, f)
print("Tạo notebook thành công!")
