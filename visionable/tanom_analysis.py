#%% 导入必要的库
import xarray as xr  # 用于处理多维数组数据
import numpy as np   # 数值计算
import pandas as pd  # 数据处理
import matplotlib.pyplot as plt  # 绘图
import matplotlib.colors as mcolors  # 颜色设置
from matplotlib.widgets import Slider  # 滑杆控件
import cartopy.crs as ccrs  # 地图投影
import cartopy.feature as cfeature  # 地图特征
from datetime import datetime, timedelta
import glob
import os
# from mpl_toolkits.basemap import Basemap  # 使用cartopy替代
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 12

#%% 数据读取和处理函数
def load_tanom_files(data_dir):
    """
    读取所有tanom文件并合并为时间序列
    
    Parameters:
    -----------
    data_dir : str
        数据目录路径
        
    Returns:
    --------
    combined_ds : xarray.Dataset
        合并后的数据集
    """
    # 获取所有tanom文件
    tanom_files = sorted(glob.glob(os.path.join(data_dir, 'tanom_*.nc')))
    print(f"找到 {len(tanom_files)} 个tanom文件")
    
    if len(tanom_files) == 0:
        raise FileNotFoundError("未找到tanom文件")
    
    # 读取所有文件
    datasets = []
    time_values = []
    
    for file in tanom_files:
        try:
            # 使用decode_times=False避免时间解析错误
            ds = xr.open_dataset(file, decode_times=False)
            datasets.append(ds)
            
            # 从文件名提取时间信息（假设格式为tanom_XXXX.nc）
            filename = os.path.basename(file)
            time_code = filename.split('_')[1].split('.')[0]
            # 这里需要根据实际的时间编码规则来解析
            time_values.append(float(ds.time.values[0]))
            
        except Exception as e:
            print(f"读取文件 {file} 时出错: {e}")
            continue
    
    if len(datasets) == 0:
        raise ValueError("没有成功读取任何文件")
    
    # 合并数据集
    combined_ds = xr.concat(datasets, dim='time')
    
    # 创建新的时间坐标
    new_time = np.array(time_values)
    combined_ds = combined_ds.assign_coords(time=new_time)
    
    print(f"成功合并 {len(datasets)} 个文件")
    print(f"时间范围: {new_time.min()} 到 {new_time.max()}")
    
    return combined_ds

def create_interactive_tanom_viewer(data_dir):
    """
    创建交互式温度异常查看器
    
    Parameters:
    -----------
    data_dir : str
        数据目录路径
    """
    # 读取数据
    try:
        ds = load_tanom_files(data_dir)
    except Exception as e:
        print(f"数据读取失败: {e}")
        # 如果读取多个文件失败，尝试读取单个文件进行演示
        single_file = os.path.join(data_dir, 'tanom_5555.nc')
        if os.path.exists(single_file):
            print("使用单个文件进行演示...")
            ds = xr.open_dataset(single_file, decode_times=False)
        else:
            raise FileNotFoundError("无法找到可用的数据文件")
    
    # 获取数据变量
    temp_anom = ds['t_an']  # 温度异常数据
    lats = ds['lat'].values
    lons = ds['lon'].values
    depths = ds['depth'].values
    times = ds['time'].values
    
    # 创建图形界面
    fig = plt.figure(figsize=(16, 12))
    
    # 创建子图布局
    gs = fig.add_gridspec(2, 2, height_ratios=[3, 1], width_ratios=[1, 1])
    
    # 主地图 - 使用地图投影
    ax_map = fig.add_subplot(gs[0, :], projection=ccrs.PlateCarree())
    
    # 设置地图范围
    ax_map.set_global()
    
    # 添加地图特征
    ax_map.add_feature(cfeature.COASTLINE, linewidth=0.5)
    ax_map.add_feature(cfeature.BORDERS, linewidth=0.3)
    ax_map.add_feature(cfeature.LAND, color='lightgray', alpha=0.5)
    ax_map.add_feature(cfeature.OCEAN, color='white', alpha=0.3)
    
    # 添加网格线
    gl = ax_map.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False, alpha=0.5)
    gl.top_labels = False
    gl.right_labels = False
    
    # 初始参数
    initial_time_idx = 0
    initial_depth_idx = 0
    
    # 获取初始数据
    initial_data = temp_anom[initial_time_idx, initial_depth_idx, :, :].values
    
    # 创建颜色映射
    vmin, vmax = np.nanpercentile(temp_anom.values, [2, 98])
    
    # 自定义颜色方案
    colors = ['#000080', '#0040FF', '#0080FF', '#00BFFF', '#00FFFF', 
              '#80FF80', '#FFFF00', '#FFB000', '#FF4000', '#FF0000', '#800000']
    cmap = mcolors.LinearSegmentedColormap.from_list('temp_anom', colors, N=256)
    
    # 绘制初始数据
    lon_grid, lat_grid = np.meshgrid(lons, lats)
    im = ax_map.contourf(lon_grid, lat_grid, initial_data, 
                        levels=50, vmin=vmin, vmax=vmax, cmap=cmap, extend='both',
                        transform=ccrs.PlateCarree())
    
    # 添加颜色条
    cbar = plt.colorbar(im, ax=ax_map, orientation='horizontal', 
                       pad=0.08, shrink=0.8, aspect=30)
    cbar.set_label('温度异常 (°C)', fontsize=12)
    
    # 设置标题
    ax_map.set_title(f'海洋温度异常 - 时间: {times[initial_time_idx]:.1f}, 深度: {depths[initial_depth_idx]:.0f}m', 
                    fontsize=14, fontweight='bold', pad=20)
    
    # 创建时间滑杆
    ax_time = plt.axes([0.2, 0.05, 0.25, 0.03])
    time_slider = Slider(ax_time, '时间', 0, len(times)-1, 
                        valinit=initial_time_idx, valfmt='%d')
    
    # 创建深度滑杆
    ax_depth = plt.axes([0.55, 0.05, 0.25, 0.03])
    depth_slider = Slider(ax_depth, '深度层', 0, len(depths)-1, 
                         valinit=initial_depth_idx, valfmt='%d')
    
    # 创建深度剖面图
    ax_profile = fig.add_subplot(gs[1, 0])
    ax_profile.set_xlabel('温度异常 (°C)')
    ax_profile.set_ylabel('深度 (m)')
    ax_profile.invert_yaxis()
    ax_profile.grid(True, alpha=0.3)
    
    # 创建时间序列图
    ax_timeseries = fig.add_subplot(gs[1, 1])
    ax_timeseries.set_xlabel('时间')
    ax_timeseries.set_ylabel('平均温度异常 (°C)')
    ax_timeseries.grid(True, alpha=0.3)
    
    def update_plot(val=None):
        """更新图的函数"""
        time_idx = int(time_slider.val)
        depth_idx = int(depth_slider.val)
        
        # 更新主地图
        ax_map.clear()
        ax_map.set_global()
        
        # 重新添加地图特征
        ax_map.add_feature(cfeature.COASTLINE, linewidth=0.5)
        ax_map.add_feature(cfeature.BORDERS, linewidth=0.3)
        ax_map.add_feature(cfeature.LAND, color='lightgray', alpha=0.5)
        ax_map.add_feature(cfeature.OCEAN, color='white', alpha=0.3)
        
        # 重新添加网格线
        gl = ax_map.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False, alpha=0.5)
        gl.top_labels = False
        gl.right_labels = False
        
        # 获取当前数据
        current_data = temp_anom[time_idx, depth_idx, :, :].values
        
        # 绘制新数据
        im = ax_map.contourf(lon_grid, lat_grid, current_data, 
                           levels=50, vmin=vmin, vmax=vmax, cmap=cmap, extend='both',
                           transform=ccrs.PlateCarree())
        
        # 更新标题
        ax_map.set_title(f'海洋温度异常 - 时间: {times[time_idx]:.1f}, 深度: {depths[depth_idx]:.0f}m', 
                        fontsize=14, fontweight='bold', pad=20)
        
        # 更新颜色条
        cbar.update_normal(im)
        
        # 更新深度剖面图
        ax_profile.clear()
        # 计算全球平均的深度剖面
        depth_profile = temp_anom[time_idx, :, :, :].mean(dim=['lat', 'lon']).values
        ax_profile.plot(depth_profile, depths, 'b-', linewidth=2, marker='o', markersize=4)
        ax_profile.axvline(x=0, color='r', linestyle='--', alpha=0.7)
        ax_profile.axhline(y=depths[depth_idx], color='r', linestyle='-', linewidth=2, alpha=0.8)
        ax_profile.set_xlabel('温度异常 (°C)')
        ax_profile.set_ylabel('深度 (m)')
        ax_profile.invert_yaxis()
        ax_profile.grid(True, alpha=0.3)
        ax_profile.set_title(f'全球平均深度剖面')
        
        # 更新时间序列图
        ax_timeseries.clear()
        # 计算指定深度的全球平均时间序列
        time_series = temp_anom[:, depth_idx, :, :].mean(dim=['lat', 'lon']).values
        ax_timeseries.plot(times, time_series, 'g-', linewidth=2, marker='o', markersize=4)
        ax_timeseries.axhline(y=0, color='r', linestyle='--', alpha=0.7)
        ax_timeseries.axvline(x=times[time_idx], color='r', linestyle='-', linewidth=2, alpha=0.8)
        ax_timeseries.set_xlabel('时间')
        ax_timeseries.set_ylabel('平均温度异常 (°C)')
        ax_timeseries.grid(True, alpha=0.3)
        ax_timeseries.set_title(f'{depths[depth_idx]:.0f}m深度时间序列')
        
        plt.draw()
    
    # 连接滑杆事件
    time_slider.on_changed(update_plot)
    depth_slider.on_changed(update_plot)
    
    # 初始化辅助图
    update_plot()
    
    # 添加说明文本
    info_text = f"""
    交互式海洋温度异常分析器
    • 时间滑杆：浏览不同时间的数据
    • 深度滑杆：选择不同深度层
    • 左下：全球平均深度剖面
    • 右下：指定深度的时间序列
    • 数据深度范围：{depths[0]:.0f}-{depths[-1]:.0f}m
    """
    plt.figtext(0.02, 0.02, info_text, fontsize=10, 
               bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.8))
    
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.15)
    plt.show()
    
    return fig, time_slider, depth_slider

#%% 主函数
def main():
    """主函数"""
    # 数据目录
    data_dir = '../data'
    
    print("正在启动海洋温度异常分析器...")
    
    try:
        fig, time_slider, depth_slider = create_interactive_tanom_viewer(data_dir)
        print("分析器启动成功！")
        return fig, time_slider, depth_slider
    except Exception as e:
        print(f"启动失败: {e}")
        return None, None, None

#%% 运行主程序
if __name__ == "__main__":
    fig, time_slider, depth_slider = main()

# %%
