import pandas as pd
import re
import warnings
warnings.filterwarnings('ignore')

# 1. Read JSON
print("Reading JSON...")
df_json = pd.read_json('datas/recommend_dataset/shopee_product_desc.json')
print(f"JSON rows: {len(df_json)}")

# Extract item_id and shop_id
def extract_ids(url):
    match = re.search(r'-i\.(\d+)\.(\d+)', str(url))
    if match:
        return match.group(1), match.group(2) # shop_id, item_id
    return None, None

df_json[['shop_id', 'item_id']] = df_json['url'].apply(lambda x: pd.Series(extract_ids(x)))

# 2. Read Excel
print("Reading Excel...")
df_excel = pd.read_excel('datas/recommend_dataset/data.xlsx')
print(f"Excel rows: {len(df_excel)}")

# Convert to string to ensure matching
df_json['item_id'] = df_json['item_id'].astype(str)
df_excel['item_id'] = df_excel['item_id'].astype(str)

# 3. Merge
df_merged = pd.merge(df_excel, df_json, on='item_id', how='inner', suffixes=('_excel', '_json'))
print(f"Merged rows: {len(df_merged)}")
print("Columns:", df_merged.columns.tolist())
print(df_merged[['item_id', 'name', 'url']].head(2))
