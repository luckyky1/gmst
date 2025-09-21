#%% 
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
GMST = pd.read_csv("../data/gmst.csv",header=None,index_col=0,names=['GMST','loose_GMST'])
GMST.index = pd.to_datetime(GMST.index)
# %% 定义向前差分
def ddf(df):
    m = len(df)
    n = np.zeros([m-1,1])
    for i in range(0,m-1):
        n[i,0] = (-df.iloc[i,0]+df.iloc[i+1,0])
    daten = df.index[1:]
    s = pd.DataFrame(n,columns = ['dgmst'],index = daten)
    return s

# %%向前差分
DGMST = ddf(GMST)
DGMST.head()
DGMST.shape
DGMST.to_csv('../data/DGMST.csv',header=None)
# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
def analyze_and_plot_rapid_rise(df: pd.DataFrame, column_name: str, k: float = 1.5):
    """
    分析时间序列数据以识别和可视化“急速上升期”。

    该函数会计算给定数据列的标准差，使用 k * std_dev 作为阈值来识别
    “急速上升期”，然后打印出这些点，并绘制一幅专业的分析图表。

    参数:
    ----------
    df : pd.DataFrame
        包含时间序列数据的DataFrame。索引必须是时间格式 (DatetimeIndex)。
    column_name : str
        df 中要被分析的数据列的名称。
    k : float, optional
        用于定义上升阈值的标准差乘数，默认为 1.5。

    返回:
    -------
    pd.DataFrame
        一个只包含被识别出的“急速上升期”数据的DataFrame。
    """
    # --- 1. 设置绘图风格与中文字体 ---
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial']  # 优先使用黑体以支持中文
    plt.rcParams['axes.unicode_minus'] = False  # 正常显示负号

    # --- 2. 数据分析与识别关键点 ---
    if column_name not in df.columns:
        raise ValueError(f"错误: 列 '{column_name}' 不在DataFrame中。")

    std_dev = df[column_name].std()
    upper_threshold = k * std_dev
    
    rapid_rise_points = df[df[column_name] > upper_threshold].copy()

    # --- 3. 打印“急速上升期”的结果 ---
    print("---" * 15)
    print(f"分析列: '{column_name}'")
    print(f"使用阈值: > {upper_threshold:.3f} °C/年 (k={k}, σ={std_dev:.3f})")
    print("---" * 15)
    if rapid_rise_points.empty:
        print("未检测到满足条件的急速上升期。")
    else:
        output_df = rapid_rise_points[[column_name]].copy()
        output_df.index = output_df.index.year
        output_df.columns = ['年温度变化 (°C/年)']
        print("识别出的急速上升期如下：")
        print(output_df)
    print("---" * 15)
    print("\n")

    # --- 4. 开始绘图 ---
    fig, ax = plt.subplots(figsize=(12, 7))

    # 根据正负值设置颜色
    colors = ['crimson' if x > 0 else 'royalblue' for x in df[column_name]]
    ax.bar(df.index, df[column_name], 
           width=250, 
           color=colors,
           alpha=0.6,
           edgecolor='black',
           linewidth=0.4,
           label='年际温度变化率')

    # --- 5. 优化图表样式和注释 ---
    ax.set_title(f'全球平均地表温度年际变化率分析 ({df.index.min().year}-{df.index.max().year})', fontsize=18, pad=20)
    ax.set_xlabel('年份', fontsize=12)
    ax.set_ylabel('年温度变化 (°C/年)', fontsize=12)

    ax.axhline(0, color='black', linestyle='-', linewidth=1)
    ax.axhline(upper_threshold, color='crimson', linestyle='--', linewidth=1.2, alpha=0.8, 
               label=f'急速上升阈值 (+{k}σ = {upper_threshold:.2f}°C)')

    # 优化坐标轴
    ax.xaxis.set_major_locator(mdates.YearLocator(20))
    ax.xaxis.set_minor_locator(mdates.YearLocator(5))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    plt.xticks(rotation=45, ha='right')

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='both', which='major', labelsize=11, direction='in', length=6)

    legend = ax.legend(loc='upper left', fontsize=11, frameon=False) 

    plt.figtext(0.9, 0.01, '数据来源: 您的计算结果', 
                horizontalalignment='right', 
                fontsize=9, 
                color='gray')

    plt.tight_layout()
    plt.show()
    
    return rapid_rise_points

# %%
time_rapid_rise_point = analyze_and_plot_rapid_rise(DGMST, 'dgmst',1.28)
# %%全球地图可视化
def composite_and_plot_dgmst(nc_file_path: str, time_points: list):
    """
    对指定年份列表进行温度变化率的合成分析并进行可视化。
    （已更新，可处理Timestamp类型的输入）
    """
    # --- 1. 设置绘图风格与中文字体 ---
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial']
    plt.rcParams['axes.unicode_minus'] = False

    # --- 2. 加载和预处理数据 ---
    print("--- 开始加载和预处理数据... ---")
    try:
        ds = xr.open_dataset(nc_file_path)
    except FileNotFoundError:
        print(f"错误: 找不到文件 '{nc_file_path}'。请检查文件路径。")
        return

    temp_var_name = 'tempanomaly'
    lat_coord_name = 'lat'
    lon_coord_name = 'lon'
    time_coord_name = 'time'
    
    print("数据加载完成。")
    
    # --- 3. 核心计算：合成分析 ---
    print(f"\n--- 开始对 {len(time_points)} 个指定年份进行合成分析 ---")
    
    composite_stack = []
    processed_years = []
    
    for time_obj in time_points: # 变量名改为 time_obj 以明确其为对象
        
        # --- 【关键修改】从Timestamp对象中提取年份整数 ---
        year_int = time_obj.year
        # --- 修改结束 ---

        print(f"--- 尝试处理年份: {year_int} ---")
        
        try:
            # 使用提取出的 year_int进行比较
            data_current_year = ds[temp_var_name].sel({time_coord_name: ds[time_coord_name].dt.year == year_int})
            data_prev_year = ds[temp_var_name].sel({time_coord_name: ds[time_coord_name].dt.year == (year_int - 1)})
            
            if len(data_current_year[time_coord_name]) < 12 or len(data_prev_year[time_coord_name]) < 12:
                print(f"  -> 跳过 {year_int} 年：该年或前一年的数据不足12个月。")
                continue
            
            mean_current = data_current_year.mean(dim=time_coord_name, skipna=True)
            mean_prev = data_prev_year.mean(dim=time_coord_name, skipna=True)
            annual_rate = mean_current - mean_prev
            
            composite_stack.append(annual_rate)
            processed_years.append(year_int)

        except (KeyError, IndexError):
            print(f"  -> 跳过 {year_int} 年：数据在该文件中不存在或选取失败。")
            continue
        
    if not composite_stack:
        print("错误: 未能成功处理任何指定年份，分析终止。")
        return
        
    final_composite_map = xr.concat(composite_stack, dim='year').mean(dim='year', skipna=True)
    print(f"\n--- 所有年份合成完毕！实际合成了 {len(processed_years)} 个年份 ---")
    print("实际参与合成的年份列表:", processed_years)

    # --- 4. 可视化 (此部分无变化) ---
    fig = plt.figure(figsize=(15, 8))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.Robinson(central_longitude=180))
    ax.set_global()
    
    lons = final_composite_map.coords[lon_coord_name]
    lats = final_composite_map.coords[lat_coord_name]
    max_abs_val = 0.4
    
    im = final_composite_map.plot.pcolormesh(
        ax=ax,
        transform=ccrs.PlateCarree(),
        cmap='RdBu_r',
        vmin=-max_abs_val,
        vmax=max_abs_val,
        add_colorbar=False
    )
    
    ax.add_feature(cfeature.LAND, edgecolor='black', facecolor='lightgray', zorder=1)
    ax.coastlines(linewidth=1.0)
    
    gl = ax.gridlines(draw_labels=True, linewidth=0.8, color='gray', alpha=0.5, linestyle='--',
                      xlocs=range(-180, 181, 60), ylocs=range(-90, 91, 30))
    gl.top_labels = False
    gl.right_labels = False

    cbar = fig.colorbar(im, ax=ax, orientation='horizontal', shrink=0.8, pad=0.05, aspect=40)
    cbar.set_label('合成年平均温度变化率 (°C/年)', fontsize=14)
    cbar.ax.tick_params(labelsize=12)

    title_str = f'GMST特定年份合成温度变化率 ({len(processed_years)} 个年份平均)'
    ax.set_title(title_str, fontsize=18, fontweight='bold', pad=20)
    
    plt.show()

# %%
composite_and_plot_dgmst("../data/gistemp1200_GHCNv4_ERSSTv5.nc", time_rapid_rise_point.index.tolist())
# %% 折线图
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def plot_gmst_with_rapid_rise_markers(gmst_series: pd.Series, rapid_rise_points: pd.DataFrame):
    """
    绘制全球平均地表温度距平的连续折线图，并在“急速上升期”点上进行标记。

    该函数会绘制原始温度序列、平滑后的长期趋势，并用醒目的红点
    高亮显示所有“急速上升期”的年份。

    参数:
    ----------
    gmst_series : pd.Series
        包含全球平均温度距平的时间序列数据。索引必须是时间格式 (DatetimeIndex)。
    rapid_rise_points : pd.DataFrame
        一个DataFrame，包含了被识别为“急速上升期”的数据点。
        这通常是上一个分析函数 `analyze_and_plot_rapid_rise` 的返回值。
    """
    # --- 1. 设置绘图风格与中文字体 ---
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial']
    plt.rcParams['axes.unicode_minus'] = False

    # --- 2. 数据准备 ---
    # 计算长期趋势线 (10年滑动平均)
    smoothed_series = gmst_series.rolling(window=10, center=True, min_periods=5).mean()
    
    # 提取用于标记的急速上升期年份的温度值
    # 我们需要在原始GMST序列中找到这些点的位置
    marker_points = gmst_series[gmst_series.index.isin(rapid_rise_points.index)]

    # --- 3. 开始绘图 ---
    fig, ax = plt.subplots(figsize=(12, 7))

    # 绘制原始年平均数据折线图：使用半透明的浅灰色
    ax.plot(gmst_series.index, gmst_series.values, 
            color='gray', 
            marker='o', markersize=4, linestyle='-', linewidth=1,
            alpha=0.5,
            label='年平均温度距平')

    # 绘制平滑后的趋势线：使用加粗的黑色虚线，突出长期趋势
    ax.plot(smoothed_series.index, smoothed_series.values, 
            color='black', 
            linestyle='--',
            linewidth=2.5, 
            label='10年滑动平均趋势')

    # 高亮“急速上升期”：在原始曲线上用醒目的红色散点进行标记
    ax.scatter(marker_points.index, marker_points.values, 
               color='crimson',
               s=100,             # 散点大小
               edgecolor='black',
               linewidth=1,
               zorder=5,         # zorder确保散点绘制在最上层
               label='急速上升期')

    # --- 4. 优化图表样式和注释 ---
    ax.set_title(f'全球平均地表温度变化分析 ({gmst_series.index.min().year}-{gmst_series.index.max().year})', fontsize=18, pad=20)
    ax.set_xlabel('年份', fontsize=12)
    ax.set_ylabel('温度距平 (°C)', fontsize=12)

    # 添加0度参考线
    ax.axhline(0, color='black', linestyle=':', linewidth=1.0, alpha=0.7)

    # 优化坐标轴
    ax.xaxis.set_major_locator(mdates.YearLocator(20))
    ax.xaxis.set_minor_locator(mdates.YearLocator(5))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    plt.xticks(rotation=45, ha='right')

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='both', which='major', labelsize=11, direction='in', length=6)

    legend = ax.legend(loc='upper left', fontsize=11, frameon=False) 

    plt.figtext(0.9, 0.01, '数据来源: GISTEMP v4 (模拟)', 
                horizontalalignment='right', 
                fontsize=9, 
                color='gray')

    plt.tight_layout()
    plt.show()

# %%
plot_gmst_with_rapid_rise_markers(GMST['GMST'], time_rapid_rise_point)
# %%两中方法
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

def plot_combined_impact_analysis(
    gmst_series: pd.Series, 
    rapid_rise_points: pd.DataFrame
):
    """
    在一个精美的图表中，综合展示“急速上升期”对全球温度序列的影响。
    （已修正核心计算逻辑）
    """
    # --- 1. 设置绘图风格与中文字体 ---
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial']
    plt.rcParams['axes.unicode_minus'] = False
    
    # --- 2. 核心计算：执行两种分析方案 ---
    adjusted_series_scheme1 = gmst_series.copy()
    adjusted_series_scheme2 = gmst_series.copy()
    
    rise_indices = [gmst_series.index.get_loc(t) for t in rapid_rise_points.index if t in gmst_series.index]
    
    # --- 方案一：剥离瞬时脉冲影响 ---
    for idx in sorted(rise_indices, reverse=True):
        if idx + 1 < len(gmst_series):
            diff = gmst_series.iloc[idx+1] - gmst_series.iloc[idx]
            adjusted_series_scheme1.iloc[idx+1:] -= diff

    # --- 【关键修正】方案二：评估长期持续性影响 ---
    for idx in sorted(rise_indices, reverse=True):
        if idx + 2 < len(gmst_series):
            # 差值计算方式不变
            diff = gmst_series.iloc[idx+2] - gmst_series.iloc[idx]
            # 【修正！】校正现在从事件发生后的第一年立即开始
            adjusted_series_scheme2.iloc[idx+1:] -= diff
            
    # --- 3. 准备标记点 (与之前相同) ---
    marker_indices_shifted = rapid_rise_points.index + pd.DateOffset(years=1)
    marker_points_shifted = gmst_series.reindex(marker_indices_shifted).dropna()

    # --- 4. 可视化 (与之前相同) ---
    fig, ax = plt.subplots(figsize=(14, 8))

    ax.plot(gmst_series.index, gmst_series, 
            label='原始温度序列', 
            color='royalblue', 
            linewidth=2, 
            zorder=3)
            
    ax.plot(adjusted_series_scheme1.index, adjusted_series_scheme1, 
            label='校正序列 (方案一: 剥离瞬时脉冲)', 
            color='seagreen', 
            linestyle='--', 
            linewidth=2.0, 
            zorder=2)
            
    ax.plot(adjusted_series_scheme2.index, adjusted_series_scheme2, 
            label='校正序列 (方案二: 评估长期影响)', 
            color='darkorange', 
            linestyle=':', 
            linewidth=2.0, 
            zorder=1)

    ax.scatter(marker_points_shifted.index, marker_points_shifted.values, 
               color='red', 
               s=60, 
               edgecolor='black', 
               linewidth=0.5,
               zorder=4, 
               label='急速上升期 (标记于次年)')
               
    ax.fill_between(gmst_series.index, 
                    gmst_series, 
                    adjusted_series_scheme2, 
                    color='gray', 
                    alpha=0.15, 
                    label='急速上升期的累积总影响')

    # --- 5. 美化图表和添加注释 (与之前相同) ---
    legend = ax.legend(loc='upper left', fontsize=11, ncol=2, fancybox=True, framealpha=0.7, title='图例')
    ax.set_title('“急速上升期”对全球温度序列影响的综合分析', fontsize=18, pad=20)
    ax.set_xlabel('年份', fontsize=12)
    ax.set_ylabel('温度距平 (°C)', fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='both', which='major', labelsize=11)
    ax.set_xlim(gmst_series.index.min(), gmst_series.index.max())

    final_original = gmst_series.iloc[-1]
    final_adjusted = adjusted_series_scheme2.iloc[-1]
    impact_value = final_original - final_adjusted
    impact_percent = (impact_value / abs(final_original)) * 100
    
    annotation_text = (
        f'量化影响分析 (方案二):\n'
        f'  - 原始序列最终值: {final_original:.2f}°C\n'
        f'  - 校正序列最终值: {final_adjusted:.2f}°C\n'
        f'  - “急速上升期”的累积贡献: {impact_value:.2f}°C ({impact_percent:.1f}%)'
    )
    ax.text(0.65, 0.05, annotation_text, 
            transform=ax.transAxes, 
            fontsize=10, 
            verticalalignment='bottom',
            bbox=dict(boxstyle='round,pad=0.5', fc='wheat', alpha=0.5))

    plt.tight_layout()
    plt.show()

# %%
plot_combined_impact_analysis(GMST['loose_GMST'], time_rapid_rise_point)
# %%
