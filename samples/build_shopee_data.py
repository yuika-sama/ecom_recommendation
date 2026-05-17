import pandas as pd
import re
import urllib.parse
from pathlib import Path

def extract_from_shopee_url(url):
    """Trích xuất name, item_id, shop_id từ URL Shopee."""
    try:
        url_str = str(url)
        decoded_url = urllib.parse.unquote(url_str)
        # Regex tìm chuỗi dạng: shopee.vn/<name>-i.<shop_id>.<item_id>
        match = re.search(r'shopee\.vn/([^/]+)-i\.(\d+)\.(\d+)', decoded_url)
        if match:
            name_raw = match.group(1)
            name = name_raw.replace('-', ' ')
            shop_id = match.group(2)
            item_id = match.group(3)
            return name, item_id, shop_id
    except Exception:
        pass
    return None, None, None

def build_shopee_catalog(excel_path: str, json_path: str, output_path: str):
    print("1. Đọc file JSON...")
    df_json = pd.read_json(json_path)
    
    # Trích xuất dữ liệu từ URL
    extracted = df_json['url'].apply(extract_from_shopee_url)
    df_json['name'] = [x[0] for x in extracted]
    df_json['item_id'] = [x[1] for x in extracted]
    df_json['shop_id'] = [x[2] for x in extracted]
    
    # Đổi tên cột desc -> description
    df_json = df_json.rename(columns={'desc': 'description'})
    # Lọc bỏ các dòng không parse được URL
    df_json = df_json.dropna(subset=['item_id'])
    df_json['product_id'] = 'shp_' + df_json['shop_id'].astype(str) + '_' + df_json['item_id'].astype(str)
    
    # Chọn các cột cần thiết
    df_json_clean = df_json[['product_id', 'name', 'description', 'url']]
    df_json_clean['location'] = ""
    print(f"   -> Đã xử lý {len(df_json_clean)} sản phẩm từ JSON.")

    print("2. Đọc file Excel...")
    df_excel = pd.read_excel(excel_path)
    
    df_excel['product_id'] = 'shp_' + df_excel['shop_id'].astype(str) + '_' + df_excel['item_id'].astype(str)
    # Excel có name, shop_location
    df_excel = df_excel.rename(columns={'shop_location': 'location'})
    df_excel['description'] = ""
    df_excel['url'] = ""
    
    df_excel_clean = df_excel[['product_id', 'name', 'description', 'url', 'location']]
    print(f"   -> Đã xử lý {len(df_excel_clean)} sản phẩm từ Excel.")

    print("3. Gộp dữ liệu...")
    df_combined = pd.concat([df_json_clean, df_excel_clean], ignore_index=True)
    
    # Xử lý trùng lặp dựa trên product_id. Ưu tiên giữ dữ liệu có description hoặc location
    df_combined['has_desc'] = df_combined['description'].apply(lambda x: 1 if pd.notna(x) and x != "" else 0)
    df_combined = df_combined.sort_values(by='has_desc', ascending=False)
    df_combined = df_combined.drop_duplicates(subset=['product_id'], keep='first')
    df_combined = df_combined.drop(columns=['has_desc'])
    
    # Xử lý missing
    df_combined['name'] = df_combined['name'].fillna("Sản phẩm Shopee")
    df_combined['description'] = df_combined['description'].fillna("")
    df_combined['location'] = df_combined['location'].fillna("Toàn quốc")
    df_combined['category'] = "Shopee"
    df_combined['price'] = None
    df_combined['rating'] = None
    df_combined['solds'] = None
    df_combined['image'] = ""
    
    # Tạo combined_text cho NLP
    df_combined['combined_text'] = (
        df_combined['name'] + " " + df_combined['description']
    ).str.strip()
    
    print(f"   -> Tổng cộng sau khi gộp và bỏ trùng: {len(df_combined)} sản phẩm.")
    
    print(f"4. Lưu ra file CSV: {output_path}")
    df_combined.to_csv(output_path, index=False, encoding='utf-8-sig')
    print("Hoàn tất!")

if __name__ == "__main__":
    excel_file = "datas/recommend_dataset/data.xlsx"
    json_file = "datas/recommend_dataset/shopee_product_desc.json"
    output_file = "datas/models/shopee_catalog_new.csv"
    build_shopee_catalog(excel_file, json_file, output_file)
