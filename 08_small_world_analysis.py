import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# ==========================================
# 1. 数据加载与对齐 (Fixing the Ghost Node Issue)
# ==========================================
ROUTES_FILE = 'routes_cleaned.csv'
AIRPORTS_FILE = 'airports_cleaned.csv'

print("Step 1: 读取数据并进行严格对齐...")

# 1. 读取机场数据 (作为主参考表)
df_airports = pd.read_csv(AIRPORTS_FILE)
# 获取所有“有名有姓”的有效机场 ID 列表
valid_airport_ids = set(df_airports['Airport ID'].unique())

# 创建映射字典
airport_names = df_airports.set_index('Airport ID')['Name'].to_dict()
airport_countries = df_airports.set_index('Airport ID')['Country'].to_dict()

# 2. 读取航线数据
df_routes = pd.read_csv(ROUTES_FILE)
df_routes['Source airport ID'] = pd.to_numeric(df_routes['Source airport ID'], errors='coerce')
df_routes['Destination airport ID'] = pd.to_numeric(df_routes['Destination airport ID'], errors='coerce')
df_routes = df_routes.dropna(subset=['Source airport ID', 'Destination airport ID'])
df_routes = df_routes.astype({'Source airport ID': int, 'Destination airport ID': int})

# 【关键修复】: 过滤掉那些“幽灵机场”
# 只保留 起点 和 终点 都在 valid_airport_ids 里的航线
condition = (df_routes['Source airport ID'].isin(valid_airport_ids)) & \
            (df_routes['Destination airport ID'].isin(valid_airport_ids))
df_routes_clean = df_routes[condition].copy()

print(f"  - 原始航线数: {len(df_routes)}")
print(f"  - 过滤后航线数: {len(df_routes_clean)} (剔除了未知机场的连接)")

# ==========================================
# 2. 构建网络与提取核心
# ==========================================
print("\nStep 2: 构建网络并提取核心...")

G = nx.DiGraph()
edges = df_routes_clean[['Source airport ID', 'Destination airport ID']].values
G.add_edges_from(edges)

# 提取最大强连通子图 (Core Network)
largest_cc = max(nx.strongly_connected_components(G), key=len)
G_core = G.subgraph(largest_cc).copy()

print(f"  - 核心网络节点数: {len(G_core.nodes())}")

# ==========================================
# 3. 计算“小世界”指标
# ==========================================
print("\nStep 3: 计算全网最短路径 (计算量较大，请稍候)...")

# 计算所有节点对的最短路径
# 使用 nx.shortest_path_length 而不是 all_pairs，便于直接获取长度
path_lengths = []
max_len = 0
longest_path_pair = (None, None)

# 获取所有路径长度迭代器
length_iter = nx.all_pairs_shortest_path_length(G_core)

for source, targets in length_iter:
    for target, length in targets.items():
        if source != target:
            path_lengths.append(length)
            if length > max_len:
                max_len = length
                longest_path_pair = (source, target)

avg_path = np.mean(path_lengths)
diameter = max_len

print(f"\n=== 分析结果 (已修复未知节点) ===")
print(f"1. 平均路径长度: {avg_path:.2f}")
print(f"2. 网络直径: {diameter}")

# ==========================================
# 4. 寻找“世界上最遥远的距离” (Case Study)
# ==========================================
src_id, dst_id = longest_path_pair

# 这里的 get 不会再失败，因为我们已经做过过滤了
src_name = airport_names[src_id]
dst_name = airport_names[dst_id]
src_country = airport_countries[src_id]
dst_country = airport_countries[dst_id]

print(f"\n[Case Study] 真正的最远航程:")
print(f"  起点: {src_name} ({src_country})")
print(f"  终点: {dst_name} ({dst_country})")
print(f"  跳数: {diameter} (转机 {diameter-1} 次)")

# 获取具体路径
shortest_path = nx.shortest_path(G_core, source=src_id, target=dst_id)
print("  推荐飞行路线:")
for i, node in enumerate(shortest_path):
    name = airport_names.get(node, str(node))
    print(f"    {i}. {name}")

# ==========================================
# 5. 可视化
# ==========================================
print("\nStep 4: 生成图表...")
plt.figure(figsize=(10, 6))
sns.histplot(path_lengths, bins=np.arange(1, max_len+2)-0.5, stat='probability', color='#6A5ACD')
plt.title('Degrees of Separation (Cleaned Data)', fontsize=14)
plt.xlabel('Number of Flights', fontsize=12)
plt.axvline(avg_path, color='red', linestyle='--', label=f'Avg: {avg_path:.2f}')
plt.legend()
plt.grid(axis='y', alpha=0.3)
plt.savefig('small_world_analysis_fixed.png', dpi=300)
print("图表已保存: small_world_analysis_fixed.png")
plt.show()