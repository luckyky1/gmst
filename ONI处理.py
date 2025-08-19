#%%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
#%%
data1 = pd.read_csv('nino34.csv',index_col=0)
data1.index = pd.to_datetime(data1.index)
len(data1)/12
#%%
data2 = np.zeros([int(len(data1)/12),1])
for i in range(int(len(data1)/12)):
    for j in range(12):
        if j == 10 and i == 11:
            data2[i]+=data1.iloc[i*12+j]

data2_1 = np.zeros([int(len(data1)/12)-1,1])
for i in range(1,int(len(data1)/12)):
    for j in range(12):
        if j ==0:
            data2_1[i-1]+=data1.iloc[i*12+j]
data2_1 = data2_1
#%%
data_real = data2[:-1]+data2_1
#%%
data_real[0] == data1.iloc[10]+data1.iloc[12]+data1.iloc[11]
#%%
data_real = data_real/3
#%%
data2.shape
# 生成每年一个时间戳，作为新的索引列
years = [data1.index[i*12] for i in range(int(len(data1)/12)-1)]
data2 = pd.DataFrame(data_real,index=years,columns=['ONI'])
#%%
data2.to_csv('nino34_mean_real.csv',header=0)
#%%