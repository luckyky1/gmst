
#%%
import xarray as xr

# 注意：使用一个不包含任何中文字符的简单路径
# 在 Windows 中，推荐在路径字符串前加上 r，表示这是一个“原始字符串”，可以避免反斜杠问题
import os
file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'mean_halosteric_sea_level_anomaly_0-2000_pentad.nc')

try:
    with xr.open_dataset(file_path, decode_times=False) as ds:
        print("--- xarray Dataset 概览 ---")
        print(ds)
except FileNotFoundError:
    print(f"错误：找不到文件，请检查路径 '{file_path}' 是否正确。")
except Exception as e:
    print(f"发生错误：{e}")

# %%
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Slider
import matplotlib.patches as mpatches
from mpl_toolkits.basemap import Basemap
from datetime import datetime, timedelta
import matplotlib.colors as mcolors

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

def create_interactive_map():
    """创建带滑杆的交互式投影图"""
    # 重新加载数据
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'mean_halosteric_sea_level_anomaly_0-2000_pentad.nc')
    
    with xr.open_dataset(file_path, decode_times=False) as ds:
        # 获取数据
        data = ds['b_mm_hs']  # 海平面异常数据
        lats = ds['lat'].values
        lons = ds['lon'].values
        times = ds['time'].values
        
        # 转换时间为具体日期
        # 根据数据属性，时间单位是 "months since 1955-01-01 00:00:00"
        base_date = datetime(1955, 1, 1)
        dates = [base_date + timedelta(days=float(time) * 30.44) for time in times]  # 30.44天/月
        
        # 创建图形和子图
        fig = plt.figure(figsize=(15, 10))
        
        # 创建地图投影
        ax = plt.axes([0.1, 0.15, 0.8, 0.75])
        m = Basemap(projection='cyl', llcrnrlat=-90, urcrnrlat=90,
                    llcrnrlon=-180, urcrnrlon=180, resolution='c', ax=ax)
        
        # 绘制地图特征
        m.drawcoastlines(linewidth=0.5)
        m.drawcountries(linewidth=0.3)
        m.drawmapboundary(fill_color='lightblue')
        m.fillcontinents(color='lightgray', lake_color='lightblue')
        
        # 添加网格线
        m.drawmeridians(np.arange(-180, 181, 30), labels=[0,0,0,1], fontsize=8)
        m.drawparallels(np.arange(-90, 91, 30), labels=[1,0,0,0], fontsize=8)
        
        # 创建经纬度网格
        lon_grid, lat_grid = np.meshgrid(lons, lats)
        x, y = m(lon_grid, lat_grid)
        
        # 创建初始数据（第一个时间步）
        initial_data = data[0, 0, :, :].values  # [time, depth, lat, lon]
        
        # 创建颜色映射 - 使用更美观的颜色方案
        vmin, vmax = np.nanpercentile(data.values, [2, 98])  # 使用2%和98%分位数获得更好的对比度
        
        # 创建自定义颜色映射
        colors = ['#000080', '#0000FF', '#0080FF', '#00FFFF', '#80FF80', 
                 '#FFFF00', '#FF8000', '#FF0000', '#800000']
        n_bins = 256
        cmap = mcolors.LinearSegmentedColormap.from_list('custom', colors, N=n_bins)
        
        # 绘制初始数据
        im = m.contourf(x, y, initial_data, 
                       levels=32, 
                       vmin=vmin, vmax=vmax,
                       cmap=cmap, 
                       extend='both')
        
        # 添加颜色条
        cbar = plt.colorbar(im, ax=ax, orientation='horizontal', 
                           pad=0.05, shrink=0.8, aspect=30)
        cbar.set_label('海平面异常 (mm)', fontsize=12)
        
        # 设置标题
        ax.set_title(f'全球海平面异常 - {dates[0].strftime("%Y年%m月%d日")}', 
                    fontsize=16, pad=20, fontweight='bold')
        
        # 创建滑杆
        ax_slider = plt.axes([0.2, 0.02, 0.6, 0.03])
        time_slider = Slider(ax_slider, '时间', 0, len(times)-1, 
                           valinit=0, valfmt='%d')
        
        def update_plot(val):
            """更新图的函数"""
            time_idx = int(time_slider.val)
            
            # 清除之前的等高线
            for coll in ax.collections:
                coll.remove()
            
            # 绘制新数据
            current_data = data[time_idx, 0, :, :].values
            im = m.contourf(x, y, current_data, 
                           levels=32, 
                           vmin=vmin, vmax=vmax,
                           cmap=cmap, 
                           extend='both')
            
            # 更新标题
            ax.set_title(f'全球海平面异常 - {dates[time_idx].strftime("%Y年%m月%d日")}', 
                        fontsize=16, pad=20, fontweight='bold')
            
            # 更新颜色条
            cbar.update_normal(im)
            
            plt.draw()
        
        # 连接滑杆事件
        time_slider.on_changed(update_plot)
        
        # 添加说明文本
        info_text = f"""
        交互式海平面异常图
        • 使用滑杆浏览不同时间的数据
        • 深蓝色→蓝色→青色→绿色→黄色→橙色→红色→深红色
        • 时间范围：{dates[0].strftime('%Y年%m月')} 至 {dates[-1].strftime('%Y年%m月')}
        • 数据来源：NOAA NODC
        """
        plt.figtext(0.02, 0.02, info_text, fontsize=10, 
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.8))
        
        plt.tight_layout()
        plt.show()
        
        return fig, ax, time_slider

# 运行交互式地图
if __name__ == "__main__":
    fig, ax, slider = create_interactive_map()

# %%
