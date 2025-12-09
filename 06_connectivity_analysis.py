import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

# ==========================================
# 全局配置
# ==========================================
ROUTES_FILE = 'routes_cleaned.csv'
AIRPORTS_FILE = 'airports_cleaned.csv'

# 输出文件名
OUTPUT_STATS_IMG = '01_connectivity_stats.png'
OUTPUT_MAP_IMG = '02_global_connectivity_map.png'
OUTPUT_CSV = 'airport_rankings.csv'


def main():
    print("=== 开始连通度综合分析 (Step 1-5) ===")

    # ==========================================
    # Step 1: 数据加载与网络构建
    # ==========================================
    print("\n[Step 1] 读取数据并构建加权网络...")

    df_routes = pd.read_csv(ROUTES_FILE)
    df_airports = pd.read_csv(AIRPORTS_FILE)

    # 1.1 数据清洗
    df_routes['Source airport ID'] = pd.to_numeric(df_routes['Source airport ID'], errors='coerce')
    df_routes['Destination airport ID'] = pd.to_numeric(df_routes['Destination airport ID'], errors='coerce')
    df_routes = df_routes.dropna(subset=['Source airport ID', 'Destination airport ID'])

    df_routes['Source airport ID'] = df_routes['Source airport ID'].astype(int)
    df_routes['Destination airport ID'] = df_routes['Destination airport ID'].astype(int)

    # 1.2 计算权重 (同一航线有多少家航司运营)
    weighted_edges = df_routes.groupby(['Source airport ID', 'Destination airport ID']).size().reset_index(
        name='weight')

    print(f"  - 原始航线记录: {len(df_routes)}")
    print(f"  - 合并后加权边数: {len(weighted_edges)}")

    # 1.3 构建 NetworkX 图
    G = nx.DiGraph()
    G.add_weighted_edges_from(weighted_edges.values)

    # ==========================================
    # Step 2: 计算度指标
    # ==========================================
    print("\n[Step 2] 计算各项连通度指标...")

    # 计算不同类型的度
    out_degree = dict(G.out_degree(weight=None))
    out_degree_weighted = dict(G.out_degree(weight='weight'))
    in_degree = dict(G.in_degree(weight=None))  # 备用，虽然这次主要画出度

    # 整理结果到 DataFrame
    df_metrics = pd.DataFrame({'Airport ID': list(G.nodes())})
    df_metrics['Out_Degree'] = df_metrics['Airport ID'].map(out_degree).fillna(0)
    df_metrics['Weighted_Degree'] = df_metrics['Airport ID'].map(out_degree_weighted).fillna(0)  # 这里用加权出度作为主要指标

    # 关联机场详细信息
    df_info = df_airports[['Airport ID', 'Name', 'IATA', 'Country', 'City', 'Latitude', 'Longitude']]
    df_final = pd.merge(df_metrics, df_info, on='Airport ID', how='left')

    # 移除没有经纬度的孤立节点（方便后续画地图）
    df_final = df_final.dropna(subset=['Latitude', 'Longitude'])

    print(f"  - 参与分析的机场总数: {len(df_final)}")

    # ==========================================
    # Step 3: 统计分布可视化
    # ==========================================
    print("\n[Step 3] 生成连通度分布统计图...")

    # 使用临时样式上下文，确保统计图是白底的
    with plt.style.context('seaborn-v0_8-whitegrid'):
        plt.figure(figsize=(16, 10))

        # 子图 1: 出度分布
        plt.subplot(2, 2, 1)
        sns.histplot(df_final['Out_Degree'], bins=50, kde=False, color='skyblue')
        plt.title('Distribution: Out-Degree (Destinations)')
        plt.xlabel('Number of Connections')
        plt.yscale('log')

        # 子图 2: 加权出度分布
        plt.subplot(2, 2, 2)
        sns.histplot(df_final['Weighted_Degree'], bins=50, kde=False, color='salmon')
        plt.title('Distribution: Weighted Degree (Frequency)')
        plt.xlabel('Weighted Connections')
        plt.yscale('log')

        # 子图 3: 幂律分布验证 (Log-Log Plot)
        plt.subplot(2, 2, 3)
        degree_sequence = sorted([d for n, d in G.out_degree()], reverse=True)
        degree_sequence = [d for d in degree_sequence if d > 0]
        # 修复 Warning: 只保留 'b' 颜色参数，去掉线型参数
        plt.loglog(degree_sequence, 'b', marker='o', markersize=3, linestyle='None', alpha=0.5)
        plt.title('Power Law Verification (Log-Log Plot)')
        plt.xlabel('Rank (Log)')
        plt.ylabel('Degree (Log)')

        # 子图 4: 目的地 vs 频率
        plt.subplot(2, 2, 4)
        sns.scatterplot(x='Out_Degree', y='Weighted_Degree', data=df_final, alpha=0.5)
        plt.title('Destinations vs. Airline Frequency')
        plt.xlabel('Unique Destinations')
        plt.ylabel('Total Frequency (Weighted)')

        plt.tight_layout()
        plt.savefig(OUTPUT_STATS_IMG, dpi=300)
        print(f"  - 统计图已保存: {OUTPUT_STATS_IMG}")
        plt.close()  # 关闭画布释放内存

    # ==========================================
    # Step 4: 分级与排名
    # ==========================================
    print("\n[Step 4] 机场分级与排名导出...")

    # 计算分位数阈值
    q95 = df_final['Weighted_Degree'].quantile(0.95)
    q80 = df_final['Weighted_Degree'].quantile(0.80)

    # 定义分级函数
    def get_tier(degree):
        if degree >= q95:
            return 'Tier 1: Global Hub'
        elif degree >= q80:
            return 'Tier 2: Regional Hub'
        else:
            return 'Tier 3: Local/Spoke'

    df_final['Tier'] = df_final['Weighted_Degree'].apply(get_tier)

    # 导出 CSV
    df_export = df_final.sort_values(by='Weighted_Degree', ascending=False)
    cols_to_export = ['Name', 'IATA', 'Country', 'City', 'Weighted_Degree', 'Out_Degree', 'Tier']
    df_export[cols_to_export].to_csv(OUTPUT_CSV, index=False)

    print(f"  - 分级标准: Tier 1 (>{q95:.0f}), Tier 2 (>{q80:.0f})")
    print(f"  - 排名数据已保存: {OUTPUT_CSV}")

    # ==========================================
    # Step 5: 地理可视化
    # ==========================================
    print("\n[Step 5] 绘制全球连通性地图...")

    # 使用深色背景样式绘制地图
    with plt.style.context('dark_background'):
        plt.figure(figsize=(18, 10))

        # 5.1 绘制 Tier 3 (最底层)
        tier3 = df_final[df_final['Tier'] == 'Tier 3: Local/Spoke']
        plt.scatter(tier3['Longitude'], tier3['Latitude'],
                    s=1, c='#444444', alpha=0.3, label='Local')

        # 5.2 绘制 Tier 2 (中层)
        tier2 = df_final[df_final['Tier'] == 'Tier 2: Regional Hub']
        plt.scatter(tier2['Longitude'], tier2['Latitude'],
                    s=tier2['Weighted_Degree'] * 0.05, c='#1f77b4', alpha=0.6, label='Regional')

        # 5.3 绘制 Tier 1 (顶层)
        tier1 = df_final[df_final['Tier'] == 'Tier 1: Global Hub']
        plt.scatter(tier1['Longitude'], tier1['Latitude'],
                    s=tier1['Weighted_Degree'] * 0.1, c='#ff7f0e', alpha=0.9,
                    edgecolors='white', linewidth=0.5, label='Global Hub')

        # 5.4 标注 Top 5 机场
        top5 = df_final.nlargest(5, 'Weighted_Degree')
        for idx, row in top5.iterrows():
            plt.text(row['Longitude'] + 2, row['Latitude'], row['IATA'],
                     color='white', fontsize=10, fontweight='bold')

        plt.title('Global Airport Connectivity Map (Weighted Degree)', fontsize=16, color='white')
        plt.legend(loc='lower left', markerscale=2)
        plt.xlim(-180, 180)
        plt.ylim(-60, 90)
        plt.grid(False)  # 关闭网格

        plt.savefig(OUTPUT_MAP_IMG, dpi=300, bbox_inches='tight')
        print(f"  - 地图已保存: {OUTPUT_MAP_IMG}")
        plt.close()  # 关闭画布

    print("\n=== 所有分析步骤执行完毕！ ===")


if __name__ == "__main__":
    main()