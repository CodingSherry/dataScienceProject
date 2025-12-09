import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import random
import numpy as np

# ==========================================
# 1. 数据准备 (已修复报错)
# ==========================================
ROUTES_FILE = 'routes_cleaned.csv'
print("正在构建网络模型...")

df_routes = pd.read_csv(ROUTES_FILE)

# 【关键修改】只处理 ID 列，忽略其他可能包含字符（如 '2P'）的列
df_routes['Source airport ID'] = pd.to_numeric(df_routes['Source airport ID'], errors='coerce')
df_routes['Destination airport ID'] = pd.to_numeric(df_routes['Destination airport ID'], errors='coerce')

# 只提取我们需要的两列，并去除空值
df_edges = df_routes[['Source airport ID', 'Destination airport ID']].dropna()

# 转换为整数
df_edges = df_edges.astype(int)

# 构建无向图用于鲁棒性分析
# (注：分析连通性时，通常视为无向图)
G = nx.Graph()
edges = df_edges.values
G.add_edges_from(edges)

print(f"网络构建完成。节点数: {len(G.nodes())}, 边数: {len(G.edges())}")


# ==========================================
# 2. 定义攻击模拟函数
# ==========================================
def simulate_attack(graph, attack_order, step=20):
    """
    模拟攻击过程
    :param graph: 初始网络
    :param attack_order: 节点删除顺序 (list)
    :param step: 每删除多少个节点记录一次数据 (为了加速)
    :return: (x轴:删除比例, y轴:剩余最大连通子图比例)
    """
    G_temp = graph.copy()
    initial_size = len(G_temp)
    if initial_size == 0:
        return [0], [0]

    # 初始最大连通子图大小
    initial_largest_cc = len(max(nx.connected_components(G_temp), key=len))

    x_data = [0]  # 删除节点的比例
    y_data = [1.0]  # 剩余连通性的比例 (归一化)

    removed_count = 0

    print(f"开始模拟... (总节点数: {initial_size})")

    # 批量处理以提高速度
    for i in range(0, len(attack_order), step):
        # 这一批要删除的节点
        nodes_to_remove = attack_order[i: i + step]

        # 安全删除（防止节点不在图中报错）
        G_temp.remove_nodes_from([n for n in nodes_to_remove if n in G_temp])

        removed_count += len(nodes_to_remove)

        # 记录当前状态
        if len(G_temp) > 0:
            # 计算当前最大连通子图的大小
            # 优化：如果图已经空了，直接设为0
            if G_temp.number_of_edges() == 0 and G_temp.number_of_nodes() > 0:
                # 这种情况下最大连通子图就是1（孤立点）
                current_largest_cc = 1
            else:
                current_largest_cc = len(max(nx.connected_components(G_temp), key=len))

            x_data.append(removed_count / initial_size)
            y_data.append(current_largest_cc / initial_largest_cc)
        else:
            x_data.append(removed_count / initial_size)
            y_data.append(0)
            break

    return x_data, y_data


# ==========================================
# 3. 执行两种策略
# ==========================================

# --- 策略 A: 随机攻击 (Random) ---
print("\n[Scenario 1] 正在执行随机攻击模拟...")
nodes_random = list(G.nodes())
random.shuffle(nodes_random)  # 打乱顺序
# step=50 加快速度
x_random, y_random = simulate_attack(G, nodes_random, step=50)

# --- 策略 B: 蓄意攻击 (Targeted) ---
print("\n[Scenario 2] 正在执行蓄意攻击模拟 (按度数攻击)...")
# 按度数从大到小排序
nodes_sorted = sorted(G.degree, key=lambda x: x[1], reverse=True)
nodes_targeted = [n[0] for n in nodes_sorted]
x_targeted, y_targeted = simulate_attack(G, nodes_targeted, step=50)

# ==========================================
# 4. 可视化对比结果
# ==========================================
print("\n正在绘图...")
plt.figure(figsize=(10, 6))

# 绘制随机攻击曲线
plt.plot(x_random, y_random, label='Random Failure (Error)', color='green', linewidth=2, linestyle='--')

# 绘制蓄意攻击曲线
plt.plot(x_targeted, y_targeted, label='Targeted Attack (Hub Removal)', color='red', linewidth=2)

plt.title('Network Robustness Analysis: Random vs. Targeted Attack', fontsize=14)
plt.xlabel('Fraction of Nodes Removed (f)', fontsize=12)
plt.ylabel('Relative Size of Giant Component (S)', fontsize=12)
plt.legend(fontsize=11)
plt.grid(True, alpha=0.3)

# 标注关键点
plt.annotate('Robust against errors', xy=(0.5, 0.8), xytext=(0.6, 0.9),
             arrowprops=dict(facecolor='green', shrink=0.05))

plt.annotate('Fragile to attacks', xy=(0.1, 0.4), xytext=(0.2, 0.6),
             arrowprops=dict(facecolor='red', shrink=0.05))

output_file = 'robustness_analysis.png'
plt.savefig(output_file, dpi=300)
print(f"鲁棒性分析图已保存为: {output_file}")
plt.show()