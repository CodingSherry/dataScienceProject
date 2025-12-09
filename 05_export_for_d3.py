import pandas as pd
import json

print("🚀 正在为 D3.js 准备数据...")

# 1. 读取清洗好的数据
df_airports = pd.read_csv('airports_cleaned.csv')
df_routes = pd.read_csv('routes_cleaned.csv')

# 2. 筛选最繁忙的航线 (为了防止浏览器卡死，我们只画 Top 2000 条航线)
# 逻辑：只保留源机场和目标机场都在 airports 表里的航线
valid_routes = df_routes[
    df_routes['Source airport'].isin(df_airports['IATA']) & 
    df_routes['Destination airport'].isin(df_airports['IATA'])
]
print(f"有效航线总数: {len(valid_routes)}")

# 随机抽样 2000 条 (或者按某种权重选，这里简单起见用抽样)
sample_routes = valid_routes.sample(n=2000, random_state=42)

# 3. 构建 JSON 结构
# 我们需要生成一个包含 points (机场) 和 links (航线) 的字典
export_data = {
    "airports": [],
    "routes": []
}

# -> 建立一个 IATA 到 经纬度 的查找字典，加快速度
airport_lookup = df_airports.set_index('IATA')[['Latitude', 'Longitude', 'Name', 'City', 'Country']].to_dict('index')

# -> 填充机场数据 (只填充在航线中出现的机场，节省空间)
used_iatas = set(sample_routes['Source airport']).union(set(sample_routes['Destination airport']))

for iata in used_iatas:
    if iata in airport_lookup:
        info = airport_lookup[iata]
        export_data["airports"].append({
            "code": iata,
            "name": info['Name'],
            "country": info['Country'],
            "loc": [info['Longitude'], info['Latitude']] # D3 习惯 [经度, 纬度]
        })

# -> 填充航线数据
for _, row in sample_routes.iterrows():
    src = row['Source airport']
    dst = row['Destination airport']
    # 确保源和目的都有坐标
    if src in airport_lookup and dst in airport_lookup:
        export_data["routes"].append({
            "source": src,
            "target": dst
        })

# 4. 保存为 data.json
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(export_data, f, ensure_ascii=False)

print(f"✅ 数据已导出为 'data.json'！包含 {len(export_data['airports'])} 个机场和 {len(export_data['routes'])} 条航线。")