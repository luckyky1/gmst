#%% 导入必要的库
import xarray as xr  # 用于处理多维数组数据
import numpy as np   # 数值计算
import pandas as pd  # 数据处理
import matplotlib.pyplot as plt  # 绘图
import matplotlib.gridspec as gridspec  # 子图布局
import seaborn as sns  # 统计绘图
import metpy.calc   # 气象计算
from matplotlib.pylab import mpl  # matplotlib参数设置
import sys
import string  # 字符串处理
from scipy.stats import pearsonr  # 皮尔逊相关系数
from scipy.optimize import curve_fit  # 曲线拟合
from scipy import signal  # 信号处理
import datetime
import warnings
import sys
import os
# 添加当前项目根目录到Python路径
current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(current_dir)

import zhenghy  # 自定义气象数据处理模块
import eedd    # 自定义EEMD分解模块
#%% 读取EOF分析结果
file = xr.open_dataset('D:\data\data2024\energy\eof/eof_25_8_2.nc')
scores = file.scores        # EOF时间序列得分
components = file.components  # EOF空间模态
explain = file.explained_variance_ratio  # 解释方差比

#%% 设置时间范围
start_time=1979  # 开始年份
end_time = 2020+1  # 结束年份
#%% 定义数据处理函数
def rolling_smooth(data):
    """对时间序列进行滚动平均平滑处理"""
    data1 = data.rolling(time=10, min_periods=10,center=True).mean()
    return data1

def deal(data):
    """统一数据格式和预处理"""
    # 重命名坐标维度
    data = data.rename({'valid_time':'time','latitude':'lat','longitude':'lon'})
    # 设置时间坐标
    data.coords['time'] = pd.date_range('1979-1','2025-1',freq='ME')
    # 年际化处理
    data = zhenghy.annual(data)
    # 时间选择
    data = eedd.time_sel(data)
    # 去除趋势
    data = eedd.remove_depend(data)
    # 插值到统一网格
    data = data.interp(lat=np.arange(-90,91,1 ),lon=np.arange(0,361,1 ))
    # 加载数据到内存
    data = data.load()
    return data
#%% 读取和预处理气象数据
# 10米风速数据
u10 = xr.open_mfdataset('D:\data\data2024\energy\ERA5\ERA5_u10_1979_2024.nc').u10
u10 = deal(u10)

# 蒸发数据
e = xr.open_mfdataset('D:\data\data2024\energy\ERA5\ERA5_e_1979_2024.nc').e
e = deal(e)

# 总降水量数据
tp = xr.open_mfdataset('D:\data\data2024\energy\ERA5\ERA5_tp_1979_2024.nc').tp
tp = deal(tp)

# 地表温度异常数据
st = xr.open_dataset('D:\data\data2024\surface_temperature/gistemp1200_GHCNv4_ERSSTv5.nc').tempanomaly
st = zhenghy.annual(st)  # 年际化
st = eedd.time_sel(st)   # 时间选择
st = eedd.remove_depend(st)  # 去除趋势

#%% 进行回归分析
mode = 1  # 选择EOF模态（第1模态）
# 对各个气象要素与EOF时间序列进行回归分析
u10_pattern,u10_p = zhenghy.regress_3d(u10,scores[mode-1].dropna(dim='time'))  # 风速回归模式
e_pattern,e_p = zhenghy.regress_3d(e,scores[mode-1].dropna(dim='time'))        # 蒸发回归模式
tp_pattern,tp_p = zhenghy.regress_3d(tp,scores[mode-1].dropna(dim='time'))     # 降水回归模式
st_pattern,st_p = zhenghy.regress_3d(st,scores[mode-1].dropna(dim='time'))     # 温度回归模式
#%% 绘图设置和准备
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import string

# 设置绘图参数
plt.rcParams.update({"pdf.fonttype": 42,"ps.fonttype": 42,"text.usetex": False,
                     "font.size": 18,"font.family": "Arial"})

# 准备绘图数据
data_list = [u10_pattern,e_pattern*1000,tp_pattern*1000, st_pattern,]  # 数据列表（蒸发和降水单位转换为mm）
sig_list = [u10_p, e_p,tp_p,st_p]  # 显著性检验p值列表
proj = ccrs.PlateCarree(central_longitude=180)  # 设置地图投影（中央经线180度）

# 创建2x2子图
fig, axs = plt.subplots(2, 2, figsize=(14, 8), subplot_kw={'projection': proj},constrained_layout=True)
axs = axs.flatten()  # 将2D数组展平为1D
title=['u10 wind','Evaporation','precipitation','surface temperature']  # 子图标题

# 为每个子图添加基本地图要素
[(
    ax.set_title(title[i]),  # 设置标题
    ax.coastlines(),         # 添加海岸线
    ax.add_feature(cfeature.LAND, facecolor='lightgray'),   # 添加陆地
    ax.add_feature(cfeature.OCEAN, facecolor='white')       # 添加海洋
) for i, ax in enumerate(axs.ravel())]
fig.suptitle("Mode"+str(mode), fontsize=25)  # 设置总标题


#%% 绘制第1个子图：10米风速
i=0
da = data_list[i]  # 风速回归模式数据
sig = sig_list[i]  # 显著性检验p值
ax = axs[i]        # 对应的子图轴
# 绘制填色等值线图
cf = ax.contourf(da.lon,da.lat,da,transform=ccrs.PlateCarree(),
                 levels=np.arange(-0.2,0.21,0.02), cmap='RdBu_r',extend='both')
plt.colorbar(cf, ax=ax, orientation='horizontal', pad=0.05, aspect=30,label='m/s')

# 计算显著性区域（p < 0.1）
sig = sig < 0.1  
sig_bool = sig.values
lat2d, lon2d = np.meshgrid(sig.lat, sig.lon, indexing='ij')
sig_lats = lat2d[sig_bool]
sig_lons = lon2d[sig_bool]
# 可选：在显著区域添加点标记（已注释）
#ax.plot(sig_lons, sig_lats, 'k.', markersize=0.25, transform=ccrs.PlateCarree())

#%% 绘制第2个子图：蒸发
i=1
da = data_list[i]  # 蒸发回归模式数据（单位：mm/month）
sig = sig_list[i]  # 显著性检验p值
ax = axs[i]        # 对应的子图轴
# 绘制填色等值线图
cf = ax.contourf(da.lon,da.lat,da,transform=ccrs.PlateCarree(),
                 levels=np.arange(-0.1,0.1,0.01), cmap='RdBu_r',extend='both')
plt.colorbar(cf, ax=ax, orientation='horizontal', pad=0.05, aspect=30,label='mm/month')

# 计算显著性区域（p < 0.1）
sig = sig < 0.1  
sig_bool = sig.values
lat2d, lon2d = np.meshgrid(sig.lat, sig.lon, indexing='ij')
sig_lats = lat2d[sig_bool]
sig_lons = lon2d[sig_bool]
# 可选：在显著区域添加点标记（已注释）
#ax.plot(sig_lons, sig_lats, 'k.', markersize=0.25, transform=ccrs.PlateCarree())

#%% 绘制第3个子图：降水
i=2
da = data_list[i]  # 降水回归模式数据（单位：mm/month）
sig = sig_list[i]  # 显著性检验p值
ax = axs[i]        # 对应的子图轴
# 绘制填色等值线图
cf = ax.contourf(da.lon,da.lat,da,transform=ccrs.PlateCarree(),
                 levels=np.arange(-0.3,0.3,0.03), cmap='RdBu_r',extend='both')
plt.colorbar(cf, ax=ax, orientation='horizontal', pad=0.05, aspect=30,label='mm/month')

# 计算显著性区域（p < 0.1）
sig = sig < 0.1  
sig_bool = sig.values
lat2d, lon2d = np.meshgrid(sig.lat, sig.lon, indexing='ij')
sig_lats = lat2d[sig_bool]
sig_lons = lon2d[sig_bool]
# 可选：在显著区域添加点标记（已注释）
#ax.plot(sig_lons, sig_lats, 'k.', markersize=0.01, transform=ccrs.PlateCarree())


#%% 绘制第4个子图：地表温度
i=3
da = data_list[i]  # 温度回归模式数据
da = da.where(da!=0)  # 去除零值
sig = sig_list[i]     # 显著性检验p值
ax = axs[i]           # 对应的子图轴
# 绘制填色等值线图
cf = ax.contourf(da.lon,da.lat,da,transform=ccrs.PlateCarree(),
                 levels=np.arange(-0.2,0.21,0.02), cmap='RdBu_r',extend='both')
plt.colorbar(cf, ax=ax, orientation='horizontal', pad=0.05, aspect=30,label='K')

# 计算显著性区域（p < 0.1）
sig = sig < 0.1  
sig_bool = sig.values
lat2d, lon2d = np.meshgrid(sig.lat, sig.lon, indexing='ij')
sig_lats = lat2d[sig_bool]
sig_lons = lon2d[sig_bool]
# 在显著区域添加点标记
ax.plot(sig_lons, sig_lats, 'k.', markersize=0.01, transform=ccrs.PlateCarree())

#%% 添加子图标签和保存图片
# 为每个子图添加字母标签（a, b, c, d）
for index, ax in enumerate(axs.ravel()):
    ax.text(0, 1.05, string.ascii_lowercase[index],transform=ax.transAxes,
    size=22, weight='normal')

# 保存图片为高分辨率JPG格式
fig.savefig('D:/data/data2024/fig/energy_exchange/mode_'+str(mode)+'_regression_sp.jpg',dpi=800,format='jpg')