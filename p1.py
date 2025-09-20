import pandas as pd

# 读取Excel文件，第一行作为列名，第一列作为行索引
df = pd.read_excel("../gmst/GMSL.xlsx", index_col=0)

# 确保索引是日期时间格式
df.index = pd.to_datetime(df.index)

# 获取第二列数据（假设列名为'GMSL'）
gmsl_column = df.columns[0]  # 第一个数据列名
gmsl_data = df[gmsl_column]

# 执行loose平滑（示例：使用12期滚动中位数）
loose_smooth = gmsl_data.rolling(
    window=12,      # 滑动窗口大小（根据需求调整）
    min_periods=1,  # 最小计算数据点
    center=True      # 中心对齐（两侧平滑）
).median()          # 使用中位数替代异常值

# 添加新列到DataFrame
df.insert(
    loc=1,  # 位置在第二列后（第三列）
    column='loose_GMSL', 
    value=loose_smooth.values
)

# 保存结果（可选）
df.to_excel("../gmst/GMSL_smoothed.xlsx", index=True)
