import pandas as pd

# 读取清洗后的数据
df = pd.read_csv('airports_cleaned.csv')

print("=== 1. 检查数据类型 (Dtype) ===")
# info() 是最强大的体检函数，它会告诉您每一列是什么类型
# float64 = 小数, int64 = 整数, object = 文字
print(df.info())

print("\n=== 2. 检查每一列有多少个空值 ===")
# isnull().sum() 会直接数出每一列有几个 NaN
print(df.isnull().sum())