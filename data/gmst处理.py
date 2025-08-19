#%%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
#%%
# delim_whitespace=True 的意思是用任意空白字符（如空格、制表符）作为分隔符来读取数据
# 读取txt文件，跳过前4行表头，读取后面的数据
# date_parser参数用于指定如何将读取到的日期字符串转换为datetime对象。
# 在这里，date_parser=lambda x: pd.to_datetime(x,format='%Y') 表示将'Year'这一列的年份字符串按照'%Y'的格式（即四位数年份）转换为pandas的datetime类型。
# 这样做的好处是后续可以方便地进行基于时间的索引、切片和时间序列分析等操作。
# 想要指定哪一列作为日期列，需要用参数parse_dates。例如：parse_dates=['Year']，这样pandas会自动将'Year'列解析为日期类型。


data = pd.read_csv('gmst.txt', 
                   delim_whitespace=True,  # 用空白字符分隔数据
                   skiprows=5, 
                   names=['Year', 'No_Smoothing', 'Lowess(5)'],index_col=0,date_parser=lambda x: pd.to_datetime(x,format='%Y'))

data.head()
#%%
data.to_csv('gmst.csv',header=None)
#%%