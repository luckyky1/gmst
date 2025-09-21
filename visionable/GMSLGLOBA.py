#%%
import os
import glob
import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter

def plot_ssl_2000m_composite_map(folder_path: str, target_years: list[int]):
    """
    对指定年份列表的2000米深度海平面(SSL_2000m)进行合成分析并可视化。
    （该版本已根据最终的时间坐标格式进行修复）

    参数:
    ----------
    folder_path : str
        包含月度2000米深度海平面NetCDF文件的文件夹路径。
    target_years : list[int]
        一个包含整数年份的列表。
    """
    # --- 1. 设置与字体 ---
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial']
    plt.rcParams['axes.unicode_minus'] = False
    
    # --- 2. 智能数据加载 ---
    print("--- 开始智能加载所有NetCDF文件... ---")
    try:
        all_files = glob.glob(os.path.join(folder_path, 'Steric_IAP_2000m_year_*.nc'))
        if not all_files:
            raise FileNotFoundError("在指定路径下找不到任何匹配 'Steric_IAP_2000m_year_*.nc' 格式的文件。")
        
        # 先让它作为数字读入
        ds = xr.open_mfdataset(all_files, combine='nested', concat_dim='time', engine='netcdf4', decode_times=False)
        
        # --- 【最终关键修复】根据 YYYYMM.0 格式手动转换时间坐标 ---
        # 1. 获取浮点数时间值 (例如 194801.0)
        time_values_float = ds['time'].values
        # 2. 转换为整数，再转换为字符串 (例如 '194801')
        time_values_str = [str(int(t)) for t in time_values_float]
        # 3. 使用 pandas.to_datetime 并指定格式 '%Y%m' 进行精确转换
        time_as_datetime = pd.to_datetime(time_values_str, format='%Y%m')
        # 4. 将转换后的datetime对象重新赋值给time坐标
        ds = ds.assign_coords(time=time_as_datetime)
        # --- 修复结束 ---

        ds = ds.sortby('time')
        
        ssl_data = ds['SSL_2000m']
        lat = ds['lat'].values
        lon = ds['lon'].values
            
    except Exception as e:
        print(f"数据加载失败: {e}")
        return
        
    print(f"数据加载完成，共加载了 {len(ds.time)} 个时间点。")

    # --- 3. 核心计算：合成分析 (此部分逻辑无需改变) ---
    print(f"\n--- 开始对 {len(target_years)} 个指定年份进行合成分析 ---")
    
    composite_stack = []
    processed_years_list = []

    for year in target_years:
        print(f"\n--- 正在处理年份: {year} ---")
        monthly_diffs_stack = []
        
        for month in range(1, 13):
            try:
                # 现在 .dt.year 可以正常工作了
                data_prev = ssl_data.sel(time=(ssl_data.time.dt.year == year - 1) & (ssl_data.time.dt.month == month)).squeeze()
                data_next = ssl_data.sel(time=(ssl_data.time.dt.year == year + 1) & (ssl_data.time.dt.month == month)).squeeze()

                if data_prev.size == 0 or data_next.size == 0:
                    raise IndexError
                
                monthly_diff = (data_prev - data_next) / 2.0
                monthly_diffs_stack.append(monthly_diff)

            except (KeyError, IndexError):
                print(f"  -> 跳过 {year}年{month:02d}月：缺少前一年或后一年的数据。")
                continue
        
        if monthly_diffs_stack:
            annual_mean_rate = xr.concat(monthly_diffs_stack, dim='month').mean(dim='month', skipna=True)
            composite_stack.append(annual_mean_rate)
            processed_years_list.append(year)
            print(f"--- 年份 {year} 处理完成，共计算了 {len(monthly_diffs_stack)} 个月。---")

    if not composite_stack:
        print("\n错误: 未能成功处理任何指定年份，分析终止。")
        return
        
    final_composite_map = xr.concat(composite_stack, dim='year').mean(dim='year', skipna=True)
    print(f"\n--- 所有年份合成完毕！最终合成了 {len(processed_years_list)} 个年份 ---")

    # --- 4. 结果可视化 (无变化) ---
    fig = plt.figure(figsize=(15, 8))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.Robinson(central_longitude=180))
    ax.set_global()
    
    max_abs_val = 20
    levels = np.linspace(-max_abs_val, max_abs_val, 51)
    im = ax.contourf(lon, lat, final_composite_map * 1000,
                     levels=levels, transform=ccrs.PlateCarree(),
                     cmap='RdBu_r', extend='both')
    
    ax.add_feature(cfeature.LAND, edgecolor='black', facecolor='#d9d9d9', zorder=1)
    ax.coastlines(linewidth=0.8)
    ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, linestyle='--',
                 xlocs=range(0, 361, 60), ylocs=range(-90, 91, 30))

    cbar = fig.colorbar(im, ax=ax, orientation='horizontal', shrink=0.8, pad=0.08, aspect=40)
    cbar.set_label('合成年平均SSL (2000m) 变化率 (毫米/年)', fontsize=14)
    cbar.ax.tick_params(labelsize=12)

    title_str = f'特定年份合成2000米深度海平面变化率 ({len(processed_years_list)}个年份平均)'
    ax.set_title(title_str, fontsize=20, fontweight='bold', pad=20)
    
    plt.show()

# --- 如何使用这个函数的示例 ---
if __name__ == '__main__':
    data_folder_path = 'D:\\SCIENCE\\atmospheric_physic\\daqi\\qixiangzhishu\\gmst\\data\\sea_level_grid'
    years_to_analyze = [1949, 2006, 2012]
    
    try:
        plot_ssl_2000m_composite_map(folder_path=data_folder_path, target_years=years_to_analyze)
    except Exception as e:
        print(f"\n程序运行中发生未知错误: {e}")
# %% OHC
import os
import glob
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter

def plot_ohc_composite_map(base_path: str, data_type: str, file_prefix: str, data_var_name: str, target_years: list[int]):
    """
    对指定年份列表的海洋热含量(OHC)进行合成分析并进行可视化。
    (该版本已根据您的Matlab脚本适配了OHC的数据结构)

    参数:
    ----------
    base_path : str
        数据文件夹的根路径 (e.g., '.../data/ohc/dataall')。
    data_type : str
        数据类型文件夹的前缀 (e.g., 'OHC')。
    file_prefix : str
        NetCDF文件名的前缀 (e.g., 'OHC_IAP_0_6000m')。
    data_var_name : str
        NetCDF文件内部的数据变量名 (e.g., 'OHC2000')。
    target_years : list[int]
        一个包含整数年份的列表，用于指定哪些年份需要进行合成分析。
    """
    # --- 1. 设置与字体 ---
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial']
    plt.rcParams['axes.unicode_minus'] = False
    
    # --- 2. 核心计算：合成分析 ---
    print(f"--- 开始为 [{data_type}] 数据类型进行多年合成分析 ---")
    
    composite_stack = []
    processed_years_list = []

    # --- 预加载经纬度信息 (与Matlab逻辑一致) ---
    try:
        first_year_folder = os.path.join(base_path, f"{data_type}{target_years[0]}")
        any_file = glob.glob(os.path.join(first_year_folder, '*.nc'))[0]
        with xr.open_dataset(any_file) as ds_template:
            lat = ds_template['lat'].values
            lon = ds_template['lon'].values
    except (IndexError, FileNotFoundError):
        print(f"错误: 无法在文件夹 '{first_year_folder}' 中找到任何 .nc 文件来预加载坐标。")
        return

    # 外层循环：遍历每一个目标年份
    for year in target_years:
        print(f"\n--- 正在处理年份: {year} ---")
        monthly_diffs_stack = []
        
        # 内层循环：遍历12个月
        for month in range(1, 13):
            try:
                # 构建前后年份的文件路径，与Matlab的sprintf和fullfile逻辑一致
                prev_file_name = f'{file_prefix}_year_{year-1}_month_{month:02d}.nc'
                next_file_name = f'{file_prefix}_year_{year+1}_month_{month:02d}.nc'
                
                prev_file_path = os.path.join(base_path, f"{data_type}{year-1}", prev_file_name)
                next_file_path = os.path.join(base_path, f"{data_type}{year+1}", next_file_name)

                with xr.open_dataset(prev_file_path) as ds_prev, xr.open_dataset(next_file_path) as ds_next:
                    # 读取数据并替换填充值 (1e20) 为 NaN
                    data_prev = ds_prev[data_var_name].where(ds_prev[data_var_name] < 1e20).squeeze()
                    data_next = ds_next[data_var_name].where(ds_next[data_var_name] < 1e20).squeeze()
                    
                    # 计算中心差分
                    monthly_diff = (data_prev - data_next) / 2.0
                    monthly_diffs_stack.append(monthly_diff)

            except FileNotFoundError:
                print(f"  -> 跳过 {year}年{month:02d}月：缺少前一年或后一年的数据文件。")
                continue
            except KeyError:
                print(f"  -> 跳过 {year}年{month:02d}月：文件中找不到变量 '{data_var_name}'。")
                continue

        if monthly_diffs_stack:
            annual_mean_rate = xr.concat(monthly_diffs_stack, dim='month').mean(dim='month', skipna=True)
            composite_stack.append(annual_mean_rate)
            processed_years_list.append(year)
            print(f"--- 年份 {year} 处理完成，共计算了 {len(monthly_diffs_stack)} 个月。---")

    if not composite_stack:
        print("\n错误: 未能成功处理任何指定年份，分析终止。")
        return
        
    final_composite_map = xr.concat(composite_stack, dim='year').mean(dim='year', skipna=True)
    print(f"\n--- 所有年份合成完毕！最终合成了 {len(processed_years_list)} 个年份 ---")

    # --- 3. 结果可视化 ---
    fig = plt.figure(figsize=(15, 8))
    # 将经度从 0-360 转换为 -180-180 以便绘图
    lon_shifted = np.where(lon > 180, lon - 360, lon)
    # 对数据和经度进行排序
    sort_idx = np.argsort(lon_shifted)
    lon_sorted = lon_shifted[sort_idx]
    map_sorted = final_composite_map.isel(lon=sort_idx)

    ax = fig.add_subplot(1, 1, 1, projection=ccrs.Robinson(central_longitude=0))
    ax.set_global()
    
    # 动态设定颜色映射范围
    max_abs_val = 0.2*np.nanmax(np.abs(map_sorted.values))
    levels = np.linspace(-max_abs_val, max_abs_val, 51)

    im = ax.contourf(lon_sorted, lat, map_sorted,
                     levels=levels, transform=ccrs.PlateCarree(),
                     cmap='RdBu_r', extend='both')
    
    ax.add_feature(cfeature.LAND, edgecolor='black', facecolor='#d9d9d9', zorder=1)
    ax.coastlines(linewidth=0.8)
    ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, linestyle='--',
                 xlocs=range(-180, 181, 60), ylocs=range(-90, 91, 30))

    cbar = fig.colorbar(im, ax=ax, orientation='horizontal', shrink=0.8, pad=0.08, aspect=40)
    cbar.set_label(f'合成年平均 {data_type} 变化率 ($J/m^2$/年)', fontsize=14)
    cbar.ax.tick_params(labelsize=12)

    title_str = f'{data_type} 特定年份合成变化率 ({len(processed_years_list)}个年份平均)'
    ax.set_title(title_str, fontsize=20, fontweight='bold', pad=20)
    
    plt.show()

# --- 如何使用这个函数的示例 ---
if __name__ == '__main__':
    # --- 【用户设置区】 ---
    # 这些设置直接来自于您的Matlab脚本
    
    # 1. 定义数据文件夹的根路径
    base_path    = 'D:\\SCIENCE\\atmospheric_physic\\daqi\\qixiangzhishu\\gmst\\data\\ohc\\dataall'
    
    # 2. 定义数据类型和文件名前缀
    data_type    = 'OHC'
    file_prefix  = 'OHC_IAP_0_6000m'
    
    # 3. 定义NC文件内部的数据变量名
    data_var_name = 'OHC2000' # 例如分析2000米深度
    
    # 4. 定义要分析的年份
    target_years = [1958, 1962, 2003, 2017]
    # --- 设置结束 ---
    
    try:
        plot_ohc_composite_map(
            base_path=base_path,
            data_type=data_type,
            file_prefix=file_prefix,
            data_var_name=data_var_name,
            target_years=target_years
        )
    except Exception as e:
        print(f"\n程序运行中发生未知错误: {e}")
        print("请确保Python环境已安装所需库 (xarray, numpy, matplotlib, cartopy, netcdf4)。")


# %%
