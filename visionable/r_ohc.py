#%%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
k= 1.36 #标准差倍数
#%% 数据读取
GMST_EEMD = pd.read_csv("../data/OHC_byEEMD.csv",header=0,index_col=0)
GMST_EEMD.index = pd.to_datetime(GMST_EEMD.index)
GMST_ONI = pd.read_csv("../data/OHC_bynoi.csv",header=0,index_col=0)
GMST_ONI.index = pd.to_datetime(GMST_ONI.index)
GMST = pd.read_excel("../data/OHC.xlsx",header=None,index_col=0,names=['OHC','loose_OHC'])
GMST.index = pd.to_datetime(GMST.index)

gmst_6 = GMST_EEMD
gmst_12 = GMST_ONI
GMST_loose = GMST.iloc[:,1]
GMST_loose.index = pd.to_datetime(GMST_loose.index)
GMST = GMST.iloc[:,0]
GMST.index = pd.to_datetime(GMST.index)
GMST.shape
#%% 数据差分定义
def ddf(df):
    # 兼容(n,)或(n,1)的DataFrame或Series输入
    if isinstance(df, pd.Series):
        arr = df.values
    elif isinstance(df, pd.DataFrame):
        if df.shape[1] == 1:
            arr = df.iloc[:,0].values
        else:
            raise ValueError("只支持一列的DataFrame或Series")
    else:
        raise TypeError("输入必须为DataFrame或Series")
    arr = arr.reshape(-1)  # 保证为(n,)形状
    m = len(arr)
    n = np.zeros(m-1)
    for i in range(m-1):
        n[i] = -arr[i] + arr[i+1]
    daten = df.index[1:]
    s = pd.DataFrame(n, columns=['dgmst'], index=daten)
    return s

d_gmst_12 = ddf(gmst_12)
d_gmst_6 = ddf(gmst_6)
d_gmst = ddf(GMST)
d_gmst_loose = ddf(GMST_loose)
# %%
std_6 = d_gmst_6.std().item()
std_12 = d_gmst_12.std().item()
std = d_gmst.std().item()
std_loose = d_gmst_loose.std().item()
threshold_6 = k*std_6
threshold_12 =k*std_12
threshold = k*std
threshold_loose = k*std_loose  

over_6=d_gmst_6[d_gmst_6['dgmst']>=threshold_6 ]### df[df]会出现mask
over_12=d_gmst_12[d_gmst_12['dgmst']>=threshold_12]
over=d_gmst[d_gmst['dgmst']>=threshold]
over_loose=d_gmst_loose[d_gmst_loose['dgmst']>=threshold_loose]
# %%
plt.style.use('seaborn-v0_8-whitegrid')
# 设置全局字体，确保在不同系统上表现一致
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']

plt.rcParams['grid.linestyle'] = '--'
# --- 3. 创建子图 ---
# 创建一个2行1列的图，并共享X轴，这对于比较时间序列非常重要
fig, axes = plt.subplots(nrows=4, ncols=1, figsize=(24, 9), sharex=True)


# --- 4. 绘制第一个子图 (6-month average) ---
# 绘制主数据线，使用沉稳的蓝色
axes[0].plot(d_gmst_6.index, d_gmst_6, label='by EEMD_have_trend', color='cornflowerblue', linewidth=1.5)

# 绘制超过阈值的散点，使用醒目的红色，并添加黑色描边使其更清晰
axes[0].scatter(over_6.index, over_6, marker="o", s=50, color="crimson", 
                label=f'Exceeds Threshold ({threshold_6:.2f})', 
                edgecolor='black', linewidth=0.5, zorder=5) # zorder确保点在最上层

# 绘制阈值参考线，使用虚线样式
axes[0].axhline(threshold_6, lw=1.5, color="crimson", linestyle='--')

# 设置子图标题和Y轴标签
axes[0].set_title("Analysis by EEMD Temperature Anomaly", fontsize=14)
axes[0].set_ylabel(r" $10^{22}$ J", fontsize=12)
axes[0].legend(loc='upper left')


# --- 5. 绘制第二个子图 (12-month average) ---
# 绘制主数据线，使用稳重的绿色
axes[1].plot(d_gmst_12.index, d_gmst_12, label='by ONI', color='seagreen', linewidth=1.5)

# 绘制超过阈值的散点
axes[1].scatter(over_12.index, over_12, marker="o", s=50, color="crimson", 
                label=f'Exceeds Threshold ({threshold_12:.2f})', 
                edgecolor='black', linewidth=0.5, zorder=5)

# 绘制阈值参考线
axes[1].axhline(threshold_12, lw=1.5, color="crimson", linestyle='--')

# 设置子图标题和Y轴标签
axes[1].set_title("Analysis by ONI Temperature Anomaly", fontsize=14)
axes[1].set_ylabel(r" $10^{22}$ J", fontsize=12)
axes[1].legend(loc='upper left')
axes[2].plot(d_gmst_loose.index, d_gmst_loose, label='by loose_GMST', color='cornflowerblue', linewidth=1.5)
axes[2].scatter(over_loose.index, over_loose, marker="o", s=50, color="crimson", 
                label=f'Exceeds Threshold ({threshold_loose:.2f})', 
                edgecolor='black', linewidth=0.5, zorder=5)
axes[2].axhline(threshold_loose, lw=1.5, color="crimson", linestyle='--')
axes[2].set_title("Analysis by loose_GMST Temperature Anomaly", fontsize=14)
axes[2].set_ylabel(r" $10^{22}$ J", fontsize=12)
axes[2].legend(loc='upper left')
axes[3].plot(d_gmst.index, d_gmst, label='by GMST', color='cornflowerblue', linewidth=1.5)
axes[3].scatter(over.index, over, marker="o", s=50, color="crimson", 
                label=f'Exceeds Threshold ({threshold:.2f})', 
                edgecolor='black', linewidth=0.5, zorder=5)
axes[3].axhline(threshold, lw=1.5, color="crimson", linestyle='--')
axes[3].set_title("Analysis by GMST Temperature Anomaly", fontsize=14)
axes[3].set_ylabel(r" $10^{22}$ J", fontsize=12)
axes[3].legend(loc='upper left')
# --- 6. 美化整个图表 ---
# 为整个图表添加一个主标题
fig.suptitle('Time Series Analysis of OHC', fontsize=18, fontweight='bold')

# 因为共享了X轴，所以为整个图表添加一个X轴标签即可
fig.supxlabel('Year', fontsize=12)

# 自动调整布局，防止标题和标签重叠
# rect参数为suptitle留出空间
plt.tight_layout(rect=[0, 0.03, 1, 0.95])


# --- 7. 显示图像 ---
plt.show()


# %%
