import pandas as pd
import matplotlib.pyplot as plt

plt.style.use('ggplot')

# ==========================================
# 1. 加载数据
# ==========================================
print("🚀 [Step 4] 开始商业维度分析 (修正版)...")
df_routes = pd.read_csv('routes_cleaned.csv')
df_airlines = pd.read_csv('airlines_cleaned.csv')

print(f"原始航线数: {len(df_routes)}")

# ==========================================
# 2. 数据预处理 (这里是关键修复点！)
# ==========================================
print("\n🧹 正在清洗 ID 类型...")

# A. 处理 routes 表里的 ID
# 有些 ID 可能是无效的（比如 '\\N'），我们先强制把它们变成 NaN，然后删掉
df_routes['Airline ID'] = pd.to_numeric(df_routes['Airline ID'], errors='coerce')
df_routes = df_routes.dropna(subset=['Airline ID'])
# 这一步很关键：转成整数，再转成字符串 (去掉 .0)
df_routes['Airline ID'] = df_routes['Airline ID'].astype(int).astype(str)

print(f"-> 清洗后有效航线 ID 样本: {df_routes['Airline ID'].iloc[0]} (类型: {type(df_routes['Airline ID'].iloc[0])})")


# B. 处理 airlines 表里的 ID
# 同样的操作：转数字 -> 转整数 -> 转字符串
df_airlines['Airline ID'] = pd.to_numeric(df_airlines['Airline ID'], errors='coerce')
df_airlines = df_airlines.dropna(subset=['Airline ID'])
df_airlines['Airline ID'] = df_airlines['Airline ID'].astype(int).astype(str)

# 筛选活跃航司
active_airlines = df_airlines[df_airlines['Active'] == 'Y'].copy()
print(f"-> 清洗后有效航司 ID 样本: {active_airlines['Airline ID'].iloc[0]} (类型: {type(active_airlines['Airline ID'].iloc[0])})")


# ==========================================
# 3. 关联与统计
# ==========================================
print("\n🔗 正在关联 (Merge)...")

# 统计每家航司拥有多少条航线
route_counts = df_routes['Airline ID'].value_counts().reset_index()
route_counts.columns = ['Airline ID', 'Route_Count']

# 开始连接
merged_df = pd.merge(route_counts, active_airlines, on='Airline ID')

# 检查一下是不是空的
if len(merged_df) == 0:
    print("❌ 警告：连接结果依然为空！请检查 ID 是否匹配。")
else:
    print(f"✅ 成功连接！匹配到了 {len(merged_df)} 家航空公司的航线数据。")

# 取出前 10 名
top_airlines = merged_df.head(10).sort_values(by='Route_Count', ascending=True)

# ==========================================
# 4. 可视化
# ==========================================
if not top_airlines.empty:
    print("\n🎨 正在绘图...")
    plt.figure(figsize=(10, 6))
    plt.barh(top_airlines['Name'], top_airlines['Route_Count'], color='steelblue')
    plt.title('Top 10 Airlines by Number of Routes (Global)', fontsize=14)
    plt.xlabel('Number of Routes')
    plt.grid(axis='x', linestyle='--', alpha=0.5)

    for index, value in enumerate(top_airlines['Route_Count']):
        country_name = top_airlines.iloc[index]['Country']
        plt.text(value + 20, index, f" {country_name}", va='center', fontsize=9)

    plt.tight_layout()
    plt.savefig('top_airlines.png')
    print("✅ 修复完成！请查看 'top_airlines.png'")
    plt.show()
else:
    print("❌ 无法绘图，因为数据为空。")