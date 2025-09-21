#%%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
#%%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

# --- 1. 全局设置 ---
k = 1.28  # 根据您的脚本，GMST 使用 1.36 作为标准差倍数

# --- 2. 数据加载与准备 ---
try:
    gmst_eemd = pd.read_csv("../data/gmst_byEEMD.csv", header=0, index_col=0, parse_dates=True)
    gmst_oni = pd.read_csv("../data/gmst_bynoi.csv", header=0, index_col=0, parse_dates=True)
    
    # --- 【关键修复】采用更稳健的方式加载 gmst.csv ---
    # 步骤1: 先读取数据，不指定列名
    gmst_raw_temp = pd.read_csv("../data/gmst.csv", header=None, index_col=0)
    # 步骤2: 选取第一列数据，并将其重命名为 'GMST'
    gmst_raw = gmst_raw_temp.iloc[:, [0]] # 选取第一列，并保持为DataFrame格式
    gmst_raw.columns = ['GMST']
    gmst_raw.index = pd.to_datetime(gmst_raw.index)
    # --- 修复结束 ---

except FileNotFoundError as e:
    print(f"数据文件加载失败: {e}")
    print("请确保'../data/'路径下存在 gmst_byEEMD.csv, gmst_bynoi.csv, 和 gmst.csv 文件。")
    exit()
except IndexError:
    print("错误：读取'../data/gmst.csv'时发生索引错误。请确保该文件至少有两列（索引列和数据列）。")
    exit()

# --- 3. 数据差分 (优化) ---
def calculate_difference(series: pd.Series) -> pd.DataFrame:
    diff_series = series.diff().dropna()
    return pd.DataFrame(diff_series.values, columns=['dGMST'], index=diff_series.index)

d_gmst_eemd = calculate_difference(gmst_eemd.iloc[:, 0])
d_gmst_oni = calculate_difference(gmst_oni.iloc[:, 0])
d_gmst_raw = calculate_difference(gmst_raw['GMST'])

# --- 4. 识别急速上升期 ---
def find_rapid_rise_points(df, k_multiplier):
    std_dev = df.iloc[:, 0].std()
    threshold = k_multiplier * std_dev
    exceed_points = df[df.iloc[:, 0] >= threshold]
    return exceed_points, threshold

over_eemd, threshold_eemd = find_rapid_rise_points(d_gmst_eemd, k)
over_oni, threshold_oni = find_rapid_rise_points(d_gmst_oni, k)
over_raw, threshold_raw = find_rapid_rise_points(d_gmst_raw, k)

# --- 5. 分析并输出结果 ---
set_eemd = {ts.strftime('%Y-%m') for ts in over_eemd.index}
set_oni = {ts.strftime('%Y-%m') for ts in over_oni.index}
set_raw = {ts.strftime('%Y-%m') for ts in over_raw.index}
common_dates_str = sorted(list(set_eemd.intersection(set_oni, set_raw)))
common_dates_ts = [pd.to_datetime(d) for d in common_dates_str]

# 打印分析报告
print("=" * 60)
print(" GMST (全球平均地表温度) 急速上升期识别结果分析")
print("=" * 60)
print(f"\n1. 各方法识别出的急速上升年月 (共 {len(set_eemd)}, {len(set_oni)}, {len(set_raw)} 个):")
print(f"   - by EEMD: {sorted(list(set_eemd))}")
print(f"   - by ONI : {sorted(list(set_oni))}")
print(f"   - by Raw : {sorted(list(set_raw))}")
print("\n2. 所有方法共同识别出的急速上升年月:")
print(f"   - 共同点 ({len(common_dates_str)}个): {common_dates_str}")
print("=" * 60 + "\n")


# --- 6. 科研级可视化 ---

# 字体设置
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial'] 
plt.rcParams['axes.unicode_minus'] = False

# 专业配色方案
colors = {
    'eemd': '#3B75AF', 'oni': '#4E9C81', 'raw': '#CD6607',
    'highlight': '#FDB813', 'marker': '#C00000'
}

# 创建画布和子图
fig = plt.figure(figsize=(18, 10))
gs = gridspec.GridSpec(3, 1, hspace=0.05)
ax1 = plt.subplot(gs[0])
ax2 = plt.subplot(gs[1], sharex=ax1)
ax3 = plt.subplot(gs[2], sharex=ax1)

# 定义绘图参数
plot_params = {
    'A) EEMD处理后GMST': {'ax': ax1, 'data': d_gmst_eemd, 'over': over_eemd, 'thresh': threshold_eemd, 'color': colors['eemd']},
    'B) ONI影响校正后GMST': {'ax': ax2, 'data': d_gmst_oni, 'over': over_oni, 'thresh': threshold_oni, 'color': colors['oni']},
    'C) 原始GMST': {'ax': ax3, 'data': d_gmst_raw, 'over': over_raw, 'thresh': threshold_raw, 'color': colors['raw']}
}

# 循环绘制
for title, p in plot_params.items():
    ax, data, over, thresh, color = p['ax'], p['data'], p['over'], p['thresh'], p['color']
    ax.fill_between(data.index, data.iloc[:,0], 0, color=color, alpha=0.1)
    ax.plot(data.index, data, color=color, linewidth=1.5)
    ax.axhline(thresh, lw=1.2, color='gray', linestyle=':')
    ax.scatter(over.index, over, s=50, color=colors['marker'], edgecolor='white', linewidth=0.5, zorder=5)
    for date in common_dates_ts:
        ax.axvspan(date - pd.DateOffset(months=6), date + pd.DateOffset(months=6), 
                   color=colors['highlight'], alpha=0.4, zorder=0, edgecolor='none')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_ylabel("温度变化率 (°C/月)", fontsize=12)
    ax.tick_params(axis='y', labelsize=11)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    ax.text(0.02, 0.95, f'{title}\n识别出 {len(over)} 个事件', 
            transform=ax.transAxes, fontsize=14, verticalalignment='top',
            bbox=dict(boxstyle='round,pad=0.4', fc='white', alpha=0.6, ec='none'))

# 美化图表
plt.setp(ax1.get_xticklabels(), visible=False)
plt.setp(ax2.get_xticklabels(), visible=False)
ax3.set_xlabel('年份', fontsize=14)
ax3.tick_params(axis='x', rotation=0)

legend_elements = [
    Patch(facecolor=colors['highlight'], alpha=0.6, label=f'所有方法共同识别的年份 ({len(common_dates_ts)}个)'),
    Line2D([0], [0], marker='o', color='w', label='识别出的急速上升期', markerfacecolor=colors['marker'], markersize=8),
    Line2D([0], [0], color='gray', lw=1.5, linestyle=':', label=f'识别阈值 (k={k}σ)'),
]
fig.legend(handles=legend_elements, loc='lower center', ncol=3, bbox_to_anchor=(0.5, -0.02), fontsize=12, frameon=False)
fig.suptitle('不同方法下GMST“急速上升期”的对比分析', fontsize=24, fontweight='bold', y=1.02)
fig.text(0.5, 0.96, '三种方法在识别短期地表剧烈增温事件上的共性与差异', ha='center', fontsize=16, color='gray')
plt.tight_layout(rect=[0, 0.05, 1, 0.95])
plt.show()



# %% 97 05 77 
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def plot_gmst_comparison(k=1.36):
    """
    加载三种GMST时间序列（原始、ONI校正、EEMD处理），
    并将它们绘制在一张精美的、带有详细标注的科研级图表中。

    参数:
    ----------
    k : float, optional
        用于识别急速上升期的标准差倍数，默认为1.36。
    """
    # --- 1. 字体与风格设置 ---
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial']
    plt.rcParams['axes.unicode_minus'] = False

    # --- 2. 数据加载与准备 ---
    try:
        gmst_eemd = pd.read_csv("../data/gmst_byEEMD.csv", header=0, index_col=0, parse_dates=True).iloc[:, 0]
        gmst_oni = pd.read_csv("../data/gmst_bynoi.csv", header=0, index_col=0, parse_dates=True).iloc[:, 0]
        gmst_raw = pd.read_csv("../data/gmst.csv", header=None, index_col=0, usecols=[0], names=['GMST']).iloc[:, 0]
        gmst_raw.index = pd.to_datetime(gmst_raw.index)
    except FileNotFoundError as e:
        print(f"数据文件加载失败: {e}")
        return

    # --- 3. 可视化 ---
    fig, ax = plt.subplots(figsize=(16, 8))

    # 【配色方案】
    colors = {'raw': '#003366', 'oni': '#4E9C81', 'eemd': '#D2691E'}

    # 绘制三条核心曲线
    ax.plot(gmst_raw.index, gmst_raw, 
            color=colors['raw'], 
            linewidth=2.0, 
            label='A) 原始GMST序列 (包含所有信号)', 
            zorder=3)
            
    ax.plot(gmst_oni.index, gmst_oni, 
            color=colors['oni'], 
            linewidth=1.5, 
            linestyle='--', 
            label='B) 去除ENSO线性影响后', 
            zorder=2)
            
    ax.plot(gmst_eemd.index, gmst_eemd, 
            color=colors['eemd'], 
            linewidth=1.5, 
            linestyle=':', 
            label='C) 去除长期趋势后 (EEMD)', 
            zorder=1)

    # 【核心发现高亮】使用阴影区域展示ENSO的影响
    ax.fill_between(gmst_raw.index, 
                    gmst_raw, 
                    gmst_oni, 
                    where=gmst_raw > gmst_oni, 
                    color='red', alpha=0.15, interpolate=True,
                    label='ENSO等导致的增温效应')
    ax.fill_between(gmst_raw.index, 
                    gmst_raw, 
                    gmst_oni, 
                    where=gmst_raw < gmst_oni, 
                    color='blue', alpha=0.15, interpolate=True,
                    label='La Niña等导致的降温效应')
    
    # --- 4. 美化图表和添加注释 ---
    # 添加一个精美的图例
    legend = ax.legend(loc='upper left', fontsize=12, fancybox=True, framealpha=0.8)
    
    # 优化坐标轴和网格
    ax.set_title('全球平均地表温度(GMST)不同处理方法的对比分析', fontsize=20, fontweight='bold', pad=20)
    ax.set_xlabel('年份', fontsize=14)
    ax.set_ylabel('温度距平 (°C)', fontsize=14)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.axhline(0, color='black', lw=0.8, linestyle='-') # 0度参考线

    # 移除顶部和右侧的边框
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='both', which='major', labelsize=12)
    ax.set_xlim(gmst_raw.index.min(), gmst_raw.index.max())

    # 【文字注释】高亮一个强厄尔尼诺年，让图表自己讲故事
    anno_year = '1998'
    if anno_year in gmst_raw.index.year.astype(str):
        anno_date = pd.to_datetime(f'{anno_year}-06-01')
        raw_val = gmst_raw[anno_year].mean()
        oni_val = gmst_oni[anno_year].mean()
        ax.annotate(f'强厄尔尼诺年 ({anno_year})',
                    xy=(anno_date, raw_val),
                    xytext=(anno_date - pd.DateOffset(years=25), raw_val - 0.5),
                    fontsize=12,
                    arrowprops=dict(facecolor='black', arrowstyle='->', connectionstyle='arc3,rad=0.2'),
                    bbox=dict(boxstyle='round,pad=0.4', fc='yellow', alpha=0.3))
        # 添加指向性箭头
        ax.annotate(f'ENSO贡献\n约{raw_val - oni_val:.2f}°C',
                    xy=(anno_date, oni_val + (raw_val-oni_val)/2),
                    xytext=(anno_date + pd.DateOffset(years=5), oni_val - 0.2),
                    fontsize=11,
                    color='red',
                    arrowprops=dict(facecolor='red', edgecolor='red', arrowstyle='-[, widthB=1.5, lengthB=0.5', connectionstyle='angle,angleA=0,angleB=90,rad=0'))

    # 添加数据来源
    fig.text(0.98, 0.02, '数据来源: GISTEMP v4 及您的分析结果', 
             ha='right', fontsize=10, color='gray')

    plt.tight_layout()
    plt.show()

# --- 如何使用这个函数的示例 ---
if __name__ == '__main__':
    plot_gmst_comparison()
#%%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def plot_gmst_comparison():
    """
    加载三种GMST时间序列（原始、ONI校正、EEMD处理），
    并将它们绘制在一张精美的、带有详细标注的科研级图表中，
    以直观对比不同处理方法的效果。
    """
    # --- 1. 字体与风格设置 ---
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial'] # 优先使用黑体以支持中文
    plt.rcParams['axes.unicode_minus'] = False

    # --- 2. 数据加载与准备 (采用之前已修复的稳健方法) ---
    try:
        gmst_eemd = pd.read_csv("../data/gmst_byEEMD.csv", header=0, index_col=0, parse_dates=True).iloc[:, 0]
        gmst_oni = pd.read_csv("../data/gmst_bynoi.csv", header=0, index_col=0, parse_dates=True).iloc[:, 0]
        
        # 稳健地加载 gmst.csv
        gmst_raw_full = pd.read_csv("../data/gmst.csv", header=None, index_col=0)
        gmst_raw_series = gmst_raw_full.iloc[:, 0]
        gmst_raw = pd.DataFrame(gmst_raw_series)
        gmst_raw.columns = ['GMST']
        gmst_raw.index = pd.to_datetime(gmst_raw.index)
        gmst_raw = gmst_raw.iloc[:, 0] # 转换为Series以便后续操作

    except FileNotFoundError as e:
        print(f"数据文件加载失败: {e}")
        return
    except IndexError:
        print("错误：读取'../data/gmst.csv'时发生索引错误。请确保该文件至少有两列。")
        return

    # --- 3. 可视化 ---
    fig, ax = plt.subplots(figsize=(16, 8))

    # 【配色方案】
    colors = {'raw': '#003366', 'oni': '#4E9C81', 'eemd': '#D2691E'}

    # 绘制三条核心曲线
    ax.plot(gmst_raw.index, gmst_raw, 
            color=colors['raw'], 
            linewidth=2.0, 
            label='A) 原始GMST序列 (包含所有信号)', 
            zorder=3)
            
    ax.plot(gmst_oni.index, gmst_oni, 
            color=colors['oni'], 
            linewidth=1.5, 
            linestyle='--', 
            label='B) 去除ENSO线性影响后', 
            zorder=2)
            
    ax.plot(gmst_eemd.index, gmst_eemd, 
            color=colors['eemd'], 
            linewidth=1.5, 
            linestyle=':', 
            label='C) 去除长期趋势后 (EEMD)', 
            zorder=1)

    # 【核心发现高亮】使用阴影区域展示ENSO的影响
    ax.fill_between(gmst_raw.index, 
                    gmst_raw, 
                    gmst_oni, 
                    where=gmst_raw > gmst_oni, 
                    color='red', alpha=0.15, interpolate=True,
                    label='ENSO等导致的增温效应')
    ax.fill_between(gmst_raw.index, 
                    gmst_raw, 
                    gmst_oni, 
                    where=gmst_raw < gmst_oni, 
                    color='blue', alpha=0.15, interpolate=True,
                    label='La Niña等导致的降温效应')
    
    # --- 4. 美化图表和添加注释 ---
    legend = ax.legend(loc='upper left', fontsize=12, fancybox=True, framealpha=0.8)
    
    ax.set_title('全球平均地表温度(GMST)不同处理方法的对比分析', fontsize=20, fontweight='bold', pad=20)
    ax.set_xlabel('年份', fontsize=14)
    ax.set_ylabel('温度距平 (°C)', fontsize=14)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.axhline(0, color='black', lw=0.8, linestyle='-')

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='both', which='major', labelsize=12)
    ax.set_xlim(gmst_raw.index.min(), gmst_raw.index.max())

    # 【文字注释】高亮一个强厄尔尼诺年，让图表自己讲故事
    anno_year = '1998'
    if anno_year in gmst_raw.index.year.astype(str):
        anno_date = pd.to_datetime(f'{anno_year}-06-01')
        raw_val = gmst_raw[anno_year].mean()
        oni_val = gmst_oni[anno_year].mean()
        ax.annotate(f'强厄尔尼诺年 ({anno_year})',
                    xy=(anno_date, raw_val),
                    xytext=(anno_date - pd.DateOffset(years=30), raw_val - 0.6),
                    fontsize=12,
                    arrowprops=dict(facecolor='black', arrowstyle='->', connectionstyle='arc3,rad=0.2'),
                    bbox=dict(boxstyle='round,pad=0.4', fc='yellow', alpha=0.3))
        
        ax.annotate(f'ENSO贡献\n约{raw_val - oni_val:.2f}°C',
                    xy=(anno_date, oni_val + (raw_val-oni_val)/2),
                    xytext=(anno_date + pd.DateOffset(years=5), oni_val - 0.3),
                    fontsize=11,
                    color='red',
                    arrowprops=dict(facecolor='red', edgecolor='red', arrowstyle='-[, widthB=1.5, lengthB=0.5', connectionstyle='angle,angleA=0,angleB=90,rad=0'))

    fig.text(0.98, 0.02, '数据来源: GISTEMP v4 及您的分析结果', 
             ha='right', fontsize=10, color='gray')

    plt.tight_layout()
    plt.show()

# --- 如何使用这个函数的示例 ---
if __name__ == '__main__':
    plot_gmst_comparison()

#%%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

def remove_linear_signal(target_series: pd.Series, signal_series: pd.Series) -> pd.Series:
    """
    通过线性回归，从目标序列中移除一个信号序列的线性影响。
    该函数会移除 a*X + b 的影响，并恢复原始序列的平均值，以避免常数偏移。

    参数:
    ----------
    target_series : pd.Series
        要被校正的目标序列 (e.g., GMST, OHC)。
    signal_series : pd.Series
        作为驱动因子的信号序列 (e.g., ONI)。

    返回:
    -------
    pd.Series
        移除了信号线性影响后的新序列。
    """
    # 合并数据以对齐索引并移除缺失值
    df = pd.concat([target_series.rename('target'), signal_series.rename('signal')], axis=1).dropna()
    
    # 准备回归数据
    X = df[['signal']]
    y = df['target']
    
    # 训练线性回归模型
    model = LinearRegression()
    model.fit(X, y)
    
    # 预测信号的线性贡献 (a*X + b)
    linear_contribution = model.predict(X)
    
    # 从原始目标序列中减去线性贡献
    corrected_series = y - linear_contribution
    
    # 【核心修正】将校正后序列的平均值调整回原始序列的平均值
    final_series = corrected_series + y.mean()
    
    return final_series

def plot_timeseries_comparison(
    raw_series: pd.Series, 
    oni_corrected_series: pd.Series, 
    eemd_series: pd.Series,
    variable_name: str,
    units: str
):
    """
    将三个时间序列（原始、ONI校正、EEMD处理）绘制在一张精美的图中进行对比。
    """
    # 数据对齐
    df = pd.concat({
        'raw': raw_series,
        'oni_corrected': oni_corrected_series,
        'eemd': eemd_series
    }, axis=1)

    # 可视化
    fig, ax = plt.subplots(figsize=(16, 8))
    
    colors = {'raw': '#003366', 'oni': '#4E9C81', 'eemd': '#D2691E'}

    ax.plot(df.index, df['raw'], color=colors['raw'], linewidth=2.0, label=f'A) 原始 {variable_name} 序列', zorder=3)
    ax.plot(df.index, df['oni_corrected'], color=colors['oni'], linewidth=1.5, linestyle='--', label='B) 去除ENSO线性影响后 (已修正偏移)', zorder=2)
    ax.plot(df.index, df['eemd'], color=colors['eemd'], linewidth=1.5, linestyle=':', label='C) 去除长期趋势后 (EEMD)', zorder=1)

    ax.fill_between(df.index, df['raw'], df['oni_corrected'], where=df['raw'] > df['oni_corrected'], 
                    color='red', alpha=0.15, interpolate=True, label='厄尔尼诺等导致的增温效应')
    ax.fill_between(df.index, df['raw'], df['oni_corrected'], where=df['raw'] < df['oni_corrected'], 
                    color='blue', alpha=0.15, interpolate=True, label='拉尼娜等导致的降温效应')
    
    legend = ax.legend(loc='upper left', fontsize=12, fancybox=True, framealpha=0.8)
    ax.set_title(f'{variable_name} 不同处理方法的对比分析', fontsize=20, fontweight='bold', pad=20)
    ax.set_xlabel('年份', fontsize=14)
    ax.set_ylabel(f'距平 ({units})', fontsize=14)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.axhline(0, color='black', lw=0.8, linestyle='-')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='both', which='major', labelsize=12)
    ax.set_xlim(df.index.min(), df.index.max())

    fig.text(0.98, 0.02, '数据来源: 您的分析结果', ha='right', fontsize=10, color='gray')
    plt.tight_layout()
    plt.show()

# --- 主程序 ---
if __name__ == '__main__':
    # --- 1. 【字体修复】采用更兼容的字体列表 ---
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial']
    plt.rcParams['axes.unicode_minus'] = False
    
    # --- 2. 加载所有数据 ---
    try:
        # 假设 data1.csv 包含 ONI/NINO 指数
        climate_indices = pd.read_csv("../data/nino34_mean_real.csv", header=None,names=['ONI'], index_col=0, parse_dates=True)
        oni_series = climate_indices['ONI'] # 假设ONI指数在'ONI'列

        # GMST 数据
        gmst_eemd = pd.read_csv("../data/gmst_byEEMD.csv", header=0, index_col=0, parse_dates=True).iloc[:, 0]
        gmst_raw_full = pd.read_csv("../data/gmst.csv", header=None, index_col=0)
        gmst_raw = gmst_raw_full.iloc[:, 0]
        gmst_raw.index = pd.to_datetime(gmst_raw.index)

        # OHC 数据
        ohc_eemd = pd.read_csv("../data/OHC_byEEMD.csv", header=0, index_col=0, parse_dates=True).iloc[:, 0]
        ohc_raw_temp = pd.read_excel("../data/OHC.xlsx", header=None, index_col=0, usecols=[0, 1])
        ohc_raw_temp.columns = ['OHC']
        ohc_raw = ohc_raw_temp.iloc[:,0]
        ohc_raw.index = pd.to_datetime(ohc_raw.index)
        
        # GMSL 数据
        gmsl_eemd = pd.read_csv("../data/GMSL_byEEMD.csv", header=0, index_col=0, parse_dates=True).iloc[:, 0]
        gmsl_raw_temp = pd.read_excel("../data/GMSL.xlsx", header=None, index_col=0, usecols=[0, 1])
        gmsl_raw_temp.columns = ['GMSL']
        gmsl_raw = gmsl_raw_temp.iloc[:,0]
        gmsl_raw.index = pd.to_datetime(gmsl_raw.index)

    except FileNotFoundError as e:
        print(f"数据文件加载失败: {e}")
        exit()

    # --- 3. 【核心修正】为 OHC 和 GMSL 计算校正后的序列 ---
    print("--- 正在计算校正后的时间序列 (移除ONI线性影响)... ---")
    gmst_oni_corrected = remove_linear_signal(gmst_raw, oni_series)
    ohc_oni_corrected = remove_linear_signal(ohc_raw, oni_series)
    gmsl_oni_corrected = remove_linear_signal(gmsl_raw, oni_series)
    print("计算完成。")

    # --- 4. 调用函数，分别为每个变量绘图 ---
    print("\n--- 正在绘制 GMST 对比图 ---")
    plot_timeseries_comparison(
        raw_series=gmst_raw,
        oni_corrected_series=gmst_oni_corrected,
        eemd_series=gmst_eemd,
        variable_name='GMST',
        units='°C'
    )

    print("\n--- 正在绘制 OHC 对比图 ---")
    plot_timeseries_comparison(
        raw_series=ohc_raw,
        oni_corrected_series=ohc_oni_corrected,
        eemd_series=ohc_eemd,
        variable_name='OHC',
        units=r'$10^{22}$ J' # 【单位修正】使用LaTeX格式
    )

    print("\n--- 正在绘制 GMSL 对比图 ---")
    plot_timeseries_comparison(
        raw_series=gmsl_raw,
        oni_corrected_series=gmsl_oni_corrected,
        eemd_series=gmsl_eemd,
        variable_name='GMSL',
        units='mm'
    )


# %%
