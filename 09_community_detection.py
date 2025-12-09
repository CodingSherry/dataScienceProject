import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# ==========================================
# 1. 数据准备 (已修复类型转换报错)
# ==========================================
ROUTES_FILE = 'routes_cleaned.csv'
AIRPORTS_FILE = 'airports_cleaned.csv'

print("Step 1: 读取数据并构建网络...")

# 读取机场信息
df_airports = pd.read_csv(AIRPORTS_FILE)
# 建立 ID -> (经度, 纬度) 和 ID -> 国家 的映射
pos = df_airports.set_index('Airport ID')[['Longitude', 'Latitude']].to_dict('index')
airport_countries = df_airports.set_index('Airport ID')['Country'].to_dict()

# 读取航线
df_routes = pd.read_csv(ROUTES_FILE)

# 【关键修复】只处理 ID 列，忽略其他列
df_routes['Source airport ID'] = pd.to_numeric(df_routes['Source airport ID'], errors='coerce')
df_routes['Destination airport ID'] = pd.to_numeric(df_routes['Destination airport ID'], errors='coerce')

# 只提取需要的两列，去除空值
df_edges = df_routes[['Source airport ID', 'Destination airport ID']].dropna()

# 安全转换为整数
df_edges = df_edges.astype(int)

# 构建无向图 (社团检测通常基于无向连接强度)
G = nx.Graph()
edges = df_edges.values
G.add_edges_from(edges)

# 仅保留主连通分量 (剔除孤岛，以免影响颜色分配)
if len(G) > 0:
    largest_cc = max(nx.connected_components(G), key=len)
    G_core = G.subgraph(largest_cc).copy()
    print(f"  - 网络构建完成。节点数: {len(G_core.nodes())}")
else:
    print("Error: 网络为空，请检查数据。")
    exit()

# ==========================================
# 2. 执行 Louvain 社团检测算法
# ==========================================
print("\nStep 2: 正在执行 Louvain 算法 (寻找抱团结构)...")

try:
    # 尝试使用 nx.community.louvain_communities (NetworkX 2.7+)
    communities = nx.community.louvain_communities(G_core, seed=42)
except AttributeError:
    # 如果 NetworkX 版本过低，提供备选提示
    print("Error: 你的 NetworkX 版本可能过低，不支持 louvain_communities。")
    print("请尝试运行: pip install --upgrade networkx")
    exit()

print(f"  - 算法自动发现了 {len(communities)} 个社团")

# ==========================================
# 3. 整理社团数据
# ==========================================
print("\nStep 3: 分析主要社团特征...")

# 将社团格式转换为: {node_id: community_id}
partition = {}
community_stats = []

for c_id, nodes in enumerate(communities):
    for node in nodes:
        partition[node] = c_id

    # 分析该社团主要由哪个国家的机场组成
    countries = [airport_countries.get(n, 'Unknown') for n in nodes]
    if countries:
        # 统计出现最多的国家
        try:
            top_country = pd.Series(countries).mode()[0]
        except IndexError:
            top_country = "Unknown"

        size = len(nodes)
        community_stats.append({
            'Community_ID': c_id,
            'Size': size,
            'Dominant_Country': top_country
        })

# 转换为 DataFrame 并按大小排序
df_stats = pd.DataFrame(community_stats).sort_values(by='Size', ascending=False)

# 只保留前 6 大社团用于绘图 (其他的归为 "Others")
top_n = 6
top_communities = df_stats.head(top_n)['Community_ID'].tolist()

print(f"  - 前 {top_n} 大社团的主导区域:")
# 打印时不显示索引，更美观
print(df_stats.head(top_n)[['Community_ID', 'Size', 'Dominant_Country']].to_string(index=False))

# ==========================================
# 4. 可视化：全球社团地图
# ==========================================
print("\nStep 4: 绘制全球社团地图...")

# 准备绘图数据
lons = []
lats = []
node_colors = []
sizes = []

# 定义颜色盘 (Tableau 10 风格)
color_map = {
    0: '#1f77b4',  # 蓝 (通常是北美或欧洲)
    1: '#ff7f0e',  # 橙 (通常是欧洲或亚洲)
    2: '#2ca02c',  # 绿 (通常是亚洲或南美)
    3: '#d62728',  # 红
    4: '#9467bd',  # 紫
    5: '#8c564b',  # 棕
    999: '#dddddd'  # 灰色 (Others)
}

# 重新映射颜色 ID (把最大的社团映射到 0,1,2,3...)
id_mapping = {old_id: new_id for new_id, old_id in enumerate(top_communities)}

for node in G_core.nodes():
    # 获取坐标 (必须在 airport_cleaned 里有记录)
    if node in pos:
        lon = pos[node]['Longitude']
        lat = pos[node]['Latitude']

        # 获取原始社团 ID
        comm_id = partition.get(node)

        # 决定颜色
        if comm_id in top_communities:
            color_id = id_mapping[comm_id]  # 映射到 0-5
            c = color_map.get(color_id, '#dddddd')
            s = 15  # 主要社团点大一点
            alpha = 0.8
        else:
            c = color_map[999]  # 其他小社团用灰色
            s = 2
            alpha = 0.2

        lons.append(lon)
        lats.append(lat)
        node_colors.append(c)
        sizes.append(s)

# 绘图
plt.figure(figsize=(18, 10))

# 使用深色背景更能凸显彩色社团
with plt.style.context('dark_background'):
    # 绘制散点
    plt.scatter(lons, lats, c=node_colors, s=sizes, alpha=alpha, edgecolors='none')

    # 手动创建图例 (因为 scatter 直接生成没法自动标 label)
    # 我们画几个“看不见”的点来生成图例
    for i in range(min(top_n, len(df_stats))):
        original_id = top_communities[i]
        info = df_stats[df_stats['Community_ID'] == original_id].iloc[0]
        label_text = f"Group {i + 1}: {info['Dominant_Country']} Region ({info['Size']} airports)"
        plt.scatter([], [], c=color_map[i], label=label_text, s=50)

    plt.legend(loc='lower left', title="Dominant Aviation Communities", fontsize=10)
    plt.title('Global Aviation Communities Detection (Louvain Method)', fontsize=18, color='white')

    # 调整地图视野
    plt.xlim(-180, 180)
    plt.ylim(-60, 90)
    plt.axis('off')  # 移除坐标轴

    output_file = 'community_detection_map.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='black')
    print(f"地图已保存为: {output_file}")
    plt.close()

print("\n=== 分析完成 ===")