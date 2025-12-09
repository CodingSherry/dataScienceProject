import pandas as pd
import matplotlib.pyplot as plt

# 设置一种好看的绘图风格
plt.style.use('ggplot')

# ==========================================
# 1. 加载数据
# ==========================================
print("🚀 [Step 2] 开始地理维度分析...")
df = pd.read_csv('airports_cleaned.csv')
print(f"数据加载完毕，当前分析样本：{len(df)} 个机场")

# ==========================================
# 2. 统计分析 (Data Aggregation)
# ==========================================

# A. 国家排名：谁的机场最多？
# value_counts() 是统计分类数据的神器
country_counts = df['Country'].value_counts().head(10)

# B. 海拔统计：找出极值
max_alt = df.loc[df['Altitude'].idxmax()]
min_alt = df.loc[df['Altitude'].idxmin()]

print("\n--- 📊 统计简报 ---")
print(f"机场最多的国家: {country_counts.index[0]} ({country_counts.values[0]} 个)")
print(f"世界最高机场: {max_alt['Name']} ({max_alt['Country']}) - 海拔 {max_alt['Altitude']} ft")
print(f"世界最低机场: {min_alt['Name']} ({min_alt['Country']}) - 海拔 {min_alt['Altitude']} ft")


# ==========================================
# 3. 综合可视化 (Visualization)
# ==========================================
print("\n🎨 正在绘制综合分析面板 (Geo Dashboard)...")

# 创建一个画布，包含 2 行 1 列的子图 (上下排列)
# figsize=(10, 12) 控制图片长宽
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))

# --- 子图 1: Top 10 国家机场数量 (条形图) ---
# barh 是 horizontal bar (水平条形图)，适合显示长长的国家名
country_counts.sort_values().plot(kind='barh', ax=ax1, color='#3498db')
ax1.set_title('Top 10 Countries by Number of Airports')
ax1.set_xlabel('Count')
# 在柱状图末尾标上具体数字
for index, value in enumerate(country_counts.sort_values()):
    ax1.text(value, index, str(value))

# --- 子图 2: 用经纬度画“世界地图” (散点图) ---
# 这是一个很有趣的数据科学技巧：
# 只要有经纬度，散点图就能自动拼成地图的形状
# s=1 表示点的大小，alpha=0.5 表示透明度（防止点太密集糊在一起）
ax2.scatter(df['Longitude'], df['Latitude'], s=2, alpha=0.4, color='#e74c3c')
ax2.set_title('Global Airports Location Map')
ax2.set_xlabel('Longitude')
ax2.set_ylabel('Latitude')
ax2.grid(True)

# 自动调整布局，防止标题和坐标轴重叠
plt.tight_layout()

# 保存结果
plt.savefig('geo_analysis_dashboard.png')
print("✅ 结果已保存为 'geo_analysis_dashboard.png'")

# 展示
plt.show()