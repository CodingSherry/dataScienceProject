import pandas as pd
import os

print("🚀 开始批量数据清洗与转换...")

# ==========================================
# 1. 定义列名 (基于 OpenFlights 官方文档)
# ==========================================

# 机场 (airports.dat)
cols_airports = [
    'Airport ID', 'Name', 'City', 'Country', 'IATA', 'ICAO', 
    'Latitude', 'Longitude', 'Altitude', 'Timezone', 'DST', 
    'Tz database time zone', 'Type', 'Source'
]

# 航空公司 (airlines.dat)
cols_airlines = [
    'Airline ID', 'Name', 'Alias', 'IATA', 'ICAO', 
    'Callsign', 'Country', 'Active'
]

# 航线 (routes.dat)
cols_routes = [
    'Airline', 'Airline ID', 'Source airport', 'Source airport ID', 
    'Destination airport', 'Destination airport ID', 
    'Codeshare', 'Stops', 'Equipment'
]

# 机型 (planes.dat)
cols_planes = [
    'Name', 'IATA', 'ICAO'
]

# 国家 (countries.dat)
cols_countries = [
    'Name', 'iso_code', 'dafif_code'
]

# ==========================================
# 2. 定义处理任务清单
#    格式: (原文件名, 列名列表, 输出文件名)
# ==========================================
tasks = [
    ('airports.dat', cols_airports, 'airports_cleaned.csv'),
    ('airlines.dat', cols_airlines, 'airlines_cleaned.csv'),
    ('routes.dat', cols_routes, 'routes_cleaned.csv'),
    ('planes.dat', cols_planes, 'planes_cleaned.csv'),
    ('countries.dat', cols_countries, 'countries_cleaned.csv')
]

# ==========================================
# 3. 执行转换函数
# ==========================================
def process_files():
    for filename, cols, output_name in tasks:
        if os.path.exists(filename):
            try:
                # 读取数据：没有表头，处理 \N 为空值
                # on_bad_lines='skip': 遇到格式错误的行自动跳过（防止报错停止）
                df = pd.read_csv(filename, header=None, names=cols, na_values=['\\N', '-'], encoding='utf-8', on_bad_lines='skip')
                
                # 保存数据
                df.to_csv(output_name, index=False, encoding='utf-8')
                print(f"✅ 成功: {filename} -> {output_name} (行数: {len(df)})")
            except Exception as e:
                print(f"❌ 失败: {filename} 转换出错 -> {e}")
        else:
            print(f"⚠️ 跳过: 找不到文件 {filename}")

# 运行
if __name__ == "__main__":
    process_files()
    print("\n🎉 所有处理完成！请检查左侧文件列表是否出现了新的 .csv 文件。")