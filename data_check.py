import pandas as pd

# ==========================================
# 1. 检查 Airports (机场数据)
# ==========================================
print("\n🔍 正在检查 Airports 数据...")
df_airports = pd.read_csv('airports_cleaned.csv')

# 查看缺失情况
print("原始缺失值统计：")
print(df_airports[['Name', 'City', 'Country', 'IATA', 'ICAO']].isnull().sum())

# 【处理策略】
# 如果 'IATA' 代码缺失，我们后续没法做关联分析（它是连接航线的钥匙）
# 所以我们要删除那些 IATA 为空，或者只有 '\N' (数据源里的空值标记) 的行
# 注意：OpenFlights 数据里有时候用 "\N" 表示空
df_airports = df_airports[df_airports['IATA'] != '\\N']
df_airports = df_airports.dropna(subset=['IATA', 'Country'])

print(f"✅ 处理后保留有效机场：{len(df_airports)} 个 (删除了无代码的机场)")
# 保存回 CSV，供下一步使用
df_airports.to_csv('airports_cleaned.csv', index=False)


# ==========================================
# 2. 检查 Routes (航线数据)
# ==========================================
print("\n🔍 正在检查 Routes 数据...")
df_routes = pd.read_csv('routes_cleaned.csv')

print("原始缺失值统计：")
print(df_routes.isnull().sum())

# 【处理策略】
# 航线数据里，最重要的是 Source airport (出发地) and Destination airport (目的地)
# 如果这两个都没有，这显就是无效数据
df_routes = df_routes.dropna(subset=['Source airport', 'Destination airport'])

print(f"✅ 处理后保留有效航线：{len(df_routes)} 条")
df_routes.to_csv('routes_cleaned.csv', index=False)


# ==========================================
# 3. 检查 Airlines (航司数据)
# ==========================================
print("\n🔍 正在检查 Airlines 数据...")
df_airlines = pd.read_csv('airlines_cleaned.csv')

# 【处理策略】
# 我们只关心 'Active' (活跃) 的航空公司
# 看看有多少是不活跃的 (N)
active_count = df_airlines[df_airlines['Active'] == 'Y'].shape[0]
print(f"ℹ️ 其中活跃的航空公司有：{active_count} 家")

# 这里我们暂时不删数据，只是心里有数就行，
# 因为后面分析时我们可以用代码筛选 df_airlines[df_airlines['Active']=='Y']

print("\n🎉 数据治理完成！关键缺失值已处理，文件已更新。")