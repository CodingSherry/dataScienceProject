import pandas as pd
import matplotlib.pyplot as plt

# 【修复点】改用兼容性最好的 'ggplot' 样式，确保在任何版本都能运行
plt.style.use('ggplot')

# ==========================================
# 1. 准备两份数据
# ==========================================
print("🚀 [Step 3] 开始网络维度分析 (Network Analysis)...")

# 读取机场列表 (为了获取机场的名字和国家)
df_airports = pd.read_csv('airports_cleaned.csv')
print(f"-> 机场表加载完毕: {len(df_airports)} 行")

# 读取航线列表 (为了统计繁忙度)
df_routes = pd.read_csv('routes_cleaned.csv')
print(f"-> 航线表加载完毕: {len(df_routes)} 行")


# ==========================================
# 2. 统计逻辑：计算每个机场出发了多少条航线
# ==========================================
print("\n🔄 正在统计每个机场的出发航线数...")

# 我们关注 'Source airport' (出发地代码，比如 'PEK', 'JFK')
# value_counts() 统计每个代码出现了多少次
# reset_index() 把统计结果变成一个标准的 DataFrame 表格
route_counts = df_routes['Source airport'].value_counts().reset_index()

# 重命名列名，让含义更清楚：index -> IATA代码, Source airport -> 航线数量
route_counts.columns = ['IATA', 'Routes_Count']

print(f"   统计示例: {route_counts.iloc[0]['IATA']} 有 {route_counts.iloc[0]['Routes_Count']} 条出发航线")


# ==========================================
# 3. 核心技术：Merge (关联查询)
# ==========================================
print("\n🔗 正在关联机场详细信息 (Merge)...")

# 问题：route_counts 里只有 'IATA' 代码 (如 'LHR')，没有名字。
# 解决：拿 'IATA' 当钥匙，去 df_airports 表里查名字。
# how='left' 意思是：以统计表为主，哪怕机场表里查不到名字，也要保留统计数据
df_merged = pd.merge(route_counts, df_airports, on='IATA', how='left')

# 清洗：关联后，有些冷门代码可能查不到名字 (Name 为 NaN)，去掉它们
df_hubs = df_merged.dropna(subset=['Name', 'Country'])

# 取出全球 Top 15 最繁忙的枢纽
# ascending=True 是为了让 barh 图里数量最多的排在最上面（视觉习惯）
top_15_hubs = df_hubs.head(15).sort_values(by='Routes_Count', ascending=True)


# ==========================================
# 4. 可视化：全球枢纽排行榜
# ==========================================
print("\n🎨 正在绘制全球枢纽排行榜...")

plt.figure(figsize=(12, 8))

# 绘制水平柱状图
# color='teal' 是青色，配 ggplot 风格很清楚
plt.barh(top_15_hubs['Name'], top_15_hubs['Routes_Count'], color='teal')

# 添加细节
plt.xlabel('Number of Departure Routes', fontsize=12)
plt.title('Top 15 Global Airport Hubs (Connectivity)', fontsize=16)
plt.grid(axis='x', linestyle='--', alpha=0.7) # 只显示竖向网格

# 在每个柱子末尾标出国家名，增加信息量
for index, value in enumerate(top_15_hubs['Routes_Count']):
    country_name = top_15_hubs.iloc[index]['Country']
    # 在柱子右边一点点的位置写上国家名
    plt.text(value + 10, index, f"({country_name})", va='center', fontsize=10, color='black')

plt.tight_layout()
plt.savefig('network_hubs_ranking.png')
print("✅ 结果已保存为 'network_hubs_ranking.png'")

plt.show()