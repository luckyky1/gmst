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
