#%% 导入必要的库
import xarray as xr  # 用于处理多维数组数据
import numpy as np   # 数值计算
import pandas as pd  # 数据处理
import matplotlib.pyplot as plt  # 绘图
import matplotlib.colors as mcolors  # 颜色设置
from matplotlib.widgets import Slider  # 滑杆控件
# import cartopy.crs as ccrs  # 地图投影
# import cartopy.feature as cfeature  # 地图特征
from datetime import datetime, timedelta
import glob
import os
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 12

#%% 数据读取和处理函数
def load_sea_level_files(data_dir, strategy='sample'):
    """
    读取海平面网格文件并合并为时间序列
    
    Parameters:
    -----------
    data_dir : str
        数据目录路径
    strategy : str
        读取策略：'all'(全部), 'sample'(采样), 'recent'(最近), 'decade'(按十年)
        
    Returns:
    --------
    combined_ds : xarray.Dataset
        合并后的数据集
    """
    # 获取所有海平面文件
    sea_level_files = sorted(glob.glob(os.path.join(data_dir, 'dt_global_twosat_phy_l4_*.nc')))
    print(f"找到 {len(sea_level_files)} 个海平面文件")
    
    if len(sea_level_files) == 0:
        raise FileNotFoundError("未找到海平面文件")
    
    # 根据策略选择文件
    selected_files = []
    
    if strategy == 'all':
        selected_files = sea_level_files
        print("策略：读取所有文件")
    elif strategy == 'sample':
        # 采样策略：每年选择1-2个文件，覆盖整个时间范围
        years = {}
        for file in sea_level_files:
            # 从文件名提取年份：dt_global_twosat_phy_l4_YYYYMM_vDT2021-M01.nc
            basename = os.path.basename(file)
            year_month = basename.split('_')[4][:6]  # YYYYMM
            year = year_month[:4]
            month = year_month[4:]
            
            if year not in years:
                years[year] = []
            years[year].append((file, month))
        
        # 每年选择1月和7月的数据（如果有的话）
        for year, files in sorted(years.items()):  # 按年份排序
            files.sort(key=lambda x: x[1])  # 按月份排序
            # 优先选择1月和7月
            selected_months = ['01', '07']
            year_files = []
            for month in selected_months:
                for file, file_month in files:
                    if file_month == month:
                        year_files.append(file)
                        break
            if not year_files:  # 如果没有1月和7月，选择第一个可用的
                if files:  # 确保files不为空
                    year_files.append(files[0][0])
            selected_files.extend(year_files)
            
            # 调试信息
            if len(year_files) > 0:
                print(f"年份 {year}: 选择了 {len(year_files)} 个文件")
        
        print(f"策略：采样读取，每年选择代表性月份，共 {len(selected_files)} 个文件")
        
    elif strategy == 'recent':
        # 最近10年的数据
        selected_files = sea_level_files[-120:]  # 大约10年*12月
        print(f"策略：最近数据，共 {len(selected_files)} 个文件")
        
    elif strategy == 'decade':
        # 每十年选择几个代表性文件
        decades = {}
        for file in sea_level_files:
            basename = os.path.basename(file)
            year = basename.split('_')[4][:4]
            decade = year[:3] + '0'  # 1990, 2000, 2010等
            if decade not in decades:
                decades[decade] = []
            decades[decade].append(file)
        
        for decade, files in decades.items():
            selected_files.extend(files[:6])  # 每十年选6个文件
        
        print(f"策略：十年采样，共 {len(selected_files)} 个文件")
    
    # 限制最大文件数量以避免内存问题
    max_files = min(len(selected_files), 50)
    selected_files = selected_files[:max_files]
    
    print(f"实际读取 {max_files} 个文件...")
    
    # 读取文件
    datasets = []
    for i, file in enumerate(selected_files):
        try:
            ds = xr.open_dataset(file)
            datasets.append(ds)
            if (i + 1) % 10 == 0:
                print(f"已读取 {i + 1}/{max_files} 个文件")
        except Exception as e:
            print(f"读取文件 {file} 时出错: {e}")
            continue
    
    if len(datasets) == 0:
        raise ValueError("没有成功读取任何文件")
    
    # 合并数据集
    print("正在合并数据集...")
    combined_ds = xr.concat(datasets, dim='time')
    
    # 按时间排序
    combined_ds = combined_ds.sortby('time')
    
    print(f"成功合并 {len(datasets)} 个文件")
    print(f"时间范围: {combined_ds.time.values[0]} 到 {combined_ds.time.values[-1]}")
    print(f"时间点数量: {len(combined_ds.time)}")
    
    return combined_ds

def create_interactive_sea_level_viewer(data_dir):
    """
    创建交互式海平面异常查看器
    
    Parameters:
    -----------
    data_dir : str
        数据目录路径
    """
    # 读取数据 - 使用采样策略
    try:
        ds = load_sea_level_files(data_dir, strategy='sample')
    except Exception as e:
        print(f"数据读取失败: {e}")
        # 如果读取多个文件失败，尝试读取单个文件进行演示
        single_file = os.path.join(data_dir, 'dt_global_twosat_phy_l4_202010_vDT2021-M01.nc')
        if not os.path.exists(single_file):
            # 尝试另一个路径
            single_file = 'qixiangzhishu/gmst/data/sea_level_grid/dt_global_twosat_phy_l4_202010_vDT2021-M01.nc'
        
        if os.path.exists(single_file):
            print("使用单个文件进行演示...")
            ds = xr.open_dataset(single_file)
        else:
            raise FileNotFoundError("无法找到可用的数据文件")
    
    # 获取数据变量
    sla = ds['sla']  # 海平面异常数据
    eke = ds['eke']  # 涡动能数据
    lats = ds['latitude'].values
    lons = ds['longitude'].values
    times = ds['time'].values
    
    print(f"数据维度: 时间={len(times)}, 纬度={len(lats)}, 经度={len(lons)}")
    print(f"海平面异常范围: {float(sla.min().values):.3f} 到 {float(sla.max().values):.3f} m")
    
    # 创建图形界面
    fig = plt.figure(figsize=(18, 12))
    
    # 创建子图布局
    gs = fig.add_gridspec(2, 2, height_ratios=[2, 1], hspace=0.3, wspace=0.2)
    
    # 主地图 - 海平面异常
    ax_sla = fig.add_subplot(gs[0, 0])
    ax_sla.set_xlim(-180, 180)
    ax_sla.set_ylim(-90, 90)
    ax_sla.set_xlabel('经度 (°E)')
    ax_sla.set_ylabel('纬度 (°N)')
    ax_sla.grid(True, alpha=0.3)
    
    # 涡动能地图
    ax_eke = fig.add_subplot(gs[0, 1])
    ax_eke.set_xlim(-180, 180)
    ax_eke.set_ylim(-90, 90)
    ax_eke.set_xlabel('经度 (°E)')
    ax_eke.set_ylabel('纬度 (°N)')
    ax_eke.grid(True, alpha=0.3)
    
    # 初始参数
    initial_time_idx = 0
    
    # 获取初始数据
    initial_sla = sla[initial_time_idx, :, :].values
    initial_eke = eke[initial_time_idx, :, :].values
    
    # 创建颜色映射
    sla_vmin, sla_vmax = np.nanpercentile(sla.values, [2, 98])
    eke_vmin, eke_vmax = np.nanpercentile(eke.values, [2, 98])
    
    # 海平面异常颜色方案（蓝-白-红）
    sla_colors = ['#000080', '#0040FF', '#0080FF', '#00BFFF', '#87CEEB', 
                  '#FFFFFF', '#FFB6C1', '#FF69B4', '#FF4500', '#FF0000', '#800000']
    sla_cmap = mcolors.LinearSegmentedColormap.from_list('sla', sla_colors, N=256)
    
    # 涡动能颜色方案（黄-橙-红）
    eke_colors = ['#FFFF00', '#FFD700', '#FFA500', '#FF8C00', '#FF4500', '#FF0000', '#8B0000']
    eke_cmap = mcolors.LinearSegmentedColormap.from_list('eke', eke_colors, N=256)
    
    # 绘制初始数据
    lon_grid, lat_grid = np.meshgrid(lons, lats)
    
    # 海平面异常
    im_sla = ax_sla.contourf(lon_grid, lat_grid, initial_sla, 
                            levels=50, vmin=sla_vmin, vmax=sla_vmax, 
                            cmap=sla_cmap, extend='both')
    
    # 涡动能
    im_eke = ax_eke.contourf(lon_grid, lat_grid, initial_eke, 
                            levels=50, vmin=eke_vmin, vmax=eke_vmax, 
                            cmap=eke_cmap, extend='both')
    
    # 添加颜色条
    cbar_sla = plt.colorbar(im_sla, ax=ax_sla, orientation='horizontal', 
                           pad=0.05, shrink=0.8, aspect=30)
    cbar_sla.set_label('海平面异常 (m)', fontsize=10)
    
    cbar_eke = plt.colorbar(im_eke, ax=ax_eke, orientation='horizontal', 
                           pad=0.05, shrink=0.8, aspect=30)
    cbar_eke.set_label('涡动能 (m²/s²)', fontsize=10)
    
    # 设置标题
    time_str = pd.to_datetime(times[initial_time_idx]).strftime('%Y年%m月')
    ax_sla.set_title(f'海平面异常 - {time_str}', fontsize=12, fontweight='bold')
    ax_eke.set_title(f'涡动能 - {time_str}', fontsize=12, fontweight='bold')
    
    # 创建时间滑杆
    ax_time = plt.axes([0.2, 0.02, 0.6, 0.03])
    time_slider = Slider(ax_time, '时间', 0, len(times)-1, 
                        valinit=initial_time_idx, valfmt='%d')
    
    # 创建统计图
    ax_stats = fig.add_subplot(gs[1, :])
    
    def update_plot(val=None):
        """更新图的函数"""
        time_idx = int(time_slider.val)
        
        # 更新海平面异常地图
        ax_sla.clear()
        ax_sla.set_xlim(-180, 180)
        ax_sla.set_ylim(-90, 90)
        ax_sla.set_xlabel('经度 (°E)')
        ax_sla.set_ylabel('纬度 (°N)')
        ax_sla.grid(True, alpha=0.3)
        
        # 更新涡动能地图
        ax_eke.clear()
        ax_eke.set_xlim(-180, 180)
        ax_eke.set_ylim(-90, 90)
        ax_eke.set_xlabel('经度 (°E)')
        ax_eke.set_ylabel('纬度 (°N)')
        ax_eke.grid(True, alpha=0.3)
        
        # 获取当前数据
        current_sla = sla[time_idx, :, :].values
        current_eke = eke[time_idx, :, :].values
        
        # 绘制新数据
        im_sla = ax_sla.contourf(lon_grid, lat_grid, current_sla, 
                               levels=50, vmin=sla_vmin, vmax=sla_vmax, 
                               cmap=sla_cmap, extend='both')
        
        im_eke = ax_eke.contourf(lon_grid, lat_grid, current_eke, 
                               levels=50, vmin=eke_vmin, vmax=eke_vmax, 
                               cmap=eke_cmap, extend='both')
        
        # 更新标题
        current_time_str = pd.to_datetime(times[time_idx]).strftime('%Y年%m月')
        ax_sla.set_title(f'海平面异常 - {current_time_str}', fontsize=12, fontweight='bold')
        ax_eke.set_title(f'涡动能 - {current_time_str}', fontsize=12, fontweight='bold')
        
        # 更新颜色条
        cbar_sla.update_normal(im_sla)
        cbar_eke.update_normal(im_eke)
        
        # 更新统计图
        ax_stats.clear()
        
        # 计算全球平均时间序列
        sla_global_mean = sla.mean(dim=['latitude', 'longitude']).values
        eke_global_mean = eke.mean(dim=['latitude', 'longitude']).values
        
        # 绘制时间序列
        time_dates = pd.to_datetime(times)
        ax_stats.plot(time_dates, sla_global_mean * 1000, 'b-', linewidth=2, 
                     label='海平面异常 (mm)', marker='o', markersize=4)
        ax_stats.axvline(x=time_dates[time_idx], color='r', linestyle='-', 
                        linewidth=2, alpha=0.8, label='当前时间')
        
        # 创建第二个y轴用于涡动能
        ax_stats2 = ax_stats.twinx()
        ax_stats2.plot(time_dates, eke_global_mean, 'g-', linewidth=2, 
                      label='涡动能 (m²/s²)', marker='s', markersize=4)
        
        ax_stats.set_xlabel('时间')
        ax_stats.set_ylabel('海平面异常 (mm)', color='b')
        ax_stats2.set_ylabel('涡动能 (m²/s²)', color='g')
        ax_stats.grid(True, alpha=0.3)
        ax_stats.legend(loc='upper left')
        ax_stats2.legend(loc='upper right')
        ax_stats.set_title('全球平均时间序列')
        
        plt.draw()
    
    # 连接滑杆事件
    time_slider.on_changed(update_plot)
    
    # 初始化统计图
    update_plot()
    
    # 添加说明文本
    info_text = f"""
    交互式海平面异常分析器
    • 左上：海平面异常分布 (m)
    • 右上：涡动能分布 (m²/s²)
    • 下方：全球平均时间序列
    • 数据分辨率：{len(lats)}×{len(lons)}网格
    • 时间范围：{len(times)}个时间点
    """
    plt.figtext(0.02, 0.12, info_text, fontsize=9, 
               bbox=dict(boxstyle="round,pad=0.3", facecolor="lightcyan", alpha=0.8))
    
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.15)
    plt.show()
    
    return fig, time_slider

#%% 主函数
def main():
    """主函数"""
    # 数据目录
    data_dir = '../data/sea_level_grid'
    # 如果相对路径不存在，尝试绝对路径
    if not os.path.exists(data_dir):
        data_dir = 'qixiangzhishu/gmst/data/sea_level_grid'
    
    print("正在启动海平面异常分析器...")
    
    try:
        fig, time_slider = create_interactive_sea_level_viewer(data_dir)
        print("分析器启动成功！")
        return fig, time_slider
    except Exception as e:
        print(f"启动失败: {e}")
        return None, None

#%% 运行主程序
if __name__ == "__main__":
    fig, time_slider = main()

# %%
