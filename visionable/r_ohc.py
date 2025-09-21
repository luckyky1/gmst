#%%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
#%%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

# --- 1. 全局设置 ---
k = 1.28

# --- 2. 数据加载与准备 (逻辑不变) ---
try:
    ohc_eemd = pd.read_csv("../data/OHC_byEEMD.csv", header=0, index_col=0, parse_dates=True)
    ohc_oni = pd.read_csv("../data/OHC_bynoi.csv", header=0, index_col=0, parse_dates=True)
    ohc_raw_temp = pd.read_excel("../data/OHC.xlsx", header=None, index_col=0, usecols=[0, 1])
    ohc_raw_temp.columns = ['OHC']
    ohc_raw = ohc_raw_temp
    ohc_raw.index = pd.to_datetime(ohc_raw.index)
except FileNotFoundError as e:
    print(f"数据文件加载失败: {e}")
    exit()

# --- 3. 数据差分 (逻辑不变) ---
def calculate_difference(series: pd.Series) -> pd.DataFrame:
    diff_series = series.diff().dropna()
    return pd.DataFrame(diff_series.values, columns=['dOHC'], index=diff_series.index)

d_ohc_eemd = calculate_difference(ohc_eemd.iloc[:, 0])
d_ohc_oni = calculate_difference(ohc_oni.iloc[:, 0])
d_ohc_raw = calculate_difference(ohc_raw['OHC'])

# --- 4. 识别急速上升期 (逻辑不变) ---
def find_rapid_rise_points(df, k_multiplier):
    std_dev = df.iloc[:, 0].std()
    threshold = k_multiplier * std_dev
    exceed_points = df[df.iloc[:, 0] >= threshold]
    return exceed_points, threshold

over_eemd, threshold_eemd = find_rapid_rise_points(d_ohc_eemd, k)
over_oni, threshold_oni = find_rapid_rise_points(d_ohc_oni, k)
over_raw, threshold_raw = find_rapid_rise_points(d_ohc_raw, k)

# --- 5. 分析数据 (逻辑不变) ---
set_eemd = {ts.strftime('%Y-%m') for ts in over_eemd.index}
set_oni = {ts.strftime('%Y-%m') for ts in over_oni.index}
set_raw = {ts.strftime('%Y-%m') for ts in over_raw.index}
common_dates_str = sorted(list(set_eemd.intersection(set_oni, set_raw)))
common_dates_ts = [pd.to_datetime(d) for d in common_dates_str]
# (省略打印输出)

# --- 6. 科研级可视化 ---

# --- 【字体修复】 ---
# 优先使用支持中文的字体（如'SimHei'黑体），将英文字体作为备选。
# 这样可以确保在有中文的环境下，图表能被正确渲染。
# 注意：如果您的系统是macOS，可能需要将'SimHei'改为'PingFang SC'；
# 如果是Linux，可能需要改为'WenQuanYi Micro Hei'。
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial', 'Helvetica'] 
plt.rcParams['axes.unicode_minus'] = False # 确保负号可以正常显示
# --- 修复结束 ---

# 【配色方案】
colors = {
    'eemd': '#3B75AF',  # 沉稳蓝
    'oni': '#4E9C81',   # 青翠绿
    'raw': '#CD6607',   # 暖橙色
    'highlight': '#FDB813', # 醒目黄
    'marker': '#C00000' # 强调红
}

# 创建画布
fig = plt.figure(figsize=(18, 10))
gs = gridspec.GridSpec(3, 1, hspace=0.05) 

# 创建共享X轴的子图
ax1 = plt.subplot(gs[0])
ax2 = plt.subplot(gs[1], sharex=ax1)
ax3 = plt.subplot(gs[2], sharex=ax1)
axes = [ax1, ax2, ax3]

# 定义数据和绘图参数
plot_params = {
    'A) EEMD处理后OHC': {
        'ax': ax1, 'data': d_ohc_eemd, 'over_points': over_eemd, 
        'threshold': threshold_eemd, 'color': colors['eemd']
    },
    'B) ONI影响校正后OHC': {
        'ax': ax2, 'data': d_ohc_oni, 'over_points': over_oni, 
        'threshold': threshold_oni, 'color': colors['oni']
    },
    'C) 原始OHC': {
        'ax': ax3, 'data': d_ohc_raw, 'over_points': over_raw, 
        'threshold': threshold_raw, 'color': colors['raw']
    }
}

# 循环绘制
for title, params in plot_params.items():
    ax = params['ax']
    data = params['data']
    over_points = params['over_points']
    threshold = params['threshold']
    color = params['color']

    ax.fill_between(data.index, data.iloc[:,0], 0, color=color, alpha=0.1)
    ax.plot(data.index, data, color=color, linewidth=1.5)
    
    ax.axhline(threshold, lw=1.2, color='gray', linestyle=':')
    ax.scatter(over_points.index, over_points, s=50, color=colors['marker'], 
               edgecolor='white', linewidth=0.5, zorder=5)

    for date in common_dates_ts:
        ax.axvspan(date - pd.DateOffset(months=6), date + pd.DateOffset(months=6), 
                   color=colors['highlight'], alpha=0.4, zorder=0, edgecolor='none')

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('gray')
    ax.spines['bottom'].set_color('gray')
    
    ax.set_ylabel(r"变化率 ($10^{22}$ J/月)", fontsize=12)
    ax.tick_params(axis='both', labelsize=11, color='gray')
    ax.grid(axis='y', linestyle='--', alpha=0.5)

    ax.text(0.02, 0.95, f'{title}\n识别出 {len(over_points)} 个事件', 
            transform=ax.transAxes, fontsize=14, verticalalignment='top',
            bbox=dict(boxstyle='round,pad=0.4', fc='white', alpha=0.6, ec='none'))

plt.setp(ax1.get_xticklabels(), visible=False)
plt.setp(ax2.get_xticklabels(), visible=False)

ax3.set_xlabel('年份', fontsize=14)
ax3.tick_params(axis='x', rotation=0)

legend_elements = [
    Patch(facecolor=colors['highlight'], alpha=0.6, label=f'所有方法共同识别的年份 ({len(common_dates_ts)}个)'),
    Line2D([0], [0], marker='o', color='w', label='识别出的急速上升期',
           markerfacecolor=colors['marker'], markeredgecolor='white', markersize=8),
    Line2D([0], [0], color='gray', lw=1.5, linestyle=':', label='识别阈值 (k=1.28σ)'),
]
fig.legend(handles=legend_elements, loc='lower center', ncol=3, 
           bbox_to_anchor=(0.5, -0.02), fontsize=12, frameon=False)

fig.suptitle('不同方法下OHC“急速上升期”的对比分析', fontsize=24, fontweight='bold', y=1.02)
fig.text(0.5, 0.96, '三种方法在识别短期剧烈增温事件上的共性与差异', 
         ha='center', fontsize=16, color='gray')

plt.tight_layout(rect=[0, 0.05, 1, 0.95])
plt.show()

# %%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib_venn import venn3, venn3_circles
# --- 【关键修复】从matplotlib正确导入patheffects模块 ---
import matplotlib.patheffects as path_effects
# --- 修复结束 ---

# --- 1-4. 数据加载、处理与识别 (与上一版代码完全相同) ---

# --- 1. 全局设置 ---
k = 1.28

# --- 2. 数据加载与准备 ---
try:
    ohc_eemd = pd.read_csv("../data/OHC_byEEMD.csv", header=0, index_col=0, parse_dates=True)
    ohc_oni = pd.read_csv("../data/OHC_bynoi.csv", header=0, index_col=0, parse_dates=True)
    ohc_raw_temp = pd.read_excel("../data/OHC.xlsx", header=None, index_col=0, usecols=[0, 1])
    ohc_raw_temp.columns = ['OHC']
    ohc_raw = ohc_raw_temp
    ohc_raw.index = pd.to_datetime(ohc_raw.index)
except FileNotFoundError as e:
    print(f"数据文件加载失败: {e}")
    exit()

# --- 3. 数据差分 ---
def calculate_difference(series: pd.Series) -> pd.DataFrame:
    diff_series = series.diff().dropna()
    return pd.DataFrame(diff_series.values, columns=['dOHC'], index=diff_series.index)

d_ohc_eemd = calculate_difference(ohc_eemd.iloc[:, 0])
d_ohc_oni = calculate_difference(ohc_oni.iloc[:, 0])
d_ohc_raw = calculate_difference(ohc_raw['OHC'])

# --- 4. 识别急速上升期 ---
def find_rapid_rise_points(df, k_multiplier):
    std_dev = df.iloc[:, 0].std()
    threshold = k_multiplier * std_dev
    exceed_points = df[df.iloc[:, 0] >= threshold]
    return exceed_points, threshold

over_eemd, _ = find_rapid_rise_points(d_ohc_eemd, k)
over_oni, _ = find_rapid_rise_points(d_ohc_oni, k)
over_raw, _ = find_rapid_rise_points(d_ohc_raw, k)


# --- 5. 维恩图数据准备 (逻辑不变) ---
set_eemd = set(over_eemd.index.strftime('%Y-%m'))
set_oni = set(over_oni.index.strftime('%Y-%m'))
set_raw = set(over_raw.index.strftime('%Y-%m'))

subsets = (
    len(set_eemd - set_oni - set_raw),
    len(set_oni - set_eemd - set_raw),
    len((set_eemd & set_oni) - set_raw),
    len(set_raw - set_eemd - set_oni),
    len((set_eemd & set_raw) - set_oni),
    len((set_oni & set_raw) - set_eemd),
    len(set_eemd & set_oni & set_raw)
)
# (省略打印输出)

# --- 6. 科研级维恩图可视化 ---

# 【字体设置】
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial', 'Helvetica']
plt.rcParams['axes.unicode_minus'] = False

# 【配色方案】
colors = {
    'eemd': '#3B75AF',
    'oni': '#4E9C81',
    'raw': '#CD6607',
}

# 创建画布
plt.figure(figsize=(12, 12))
ax = plt.gca()

# 绘制维恩图
v = venn3(subsets=subsets, 
          set_labels=('EEMD 处理后 OHC', 'ONI 影响校正后 OHC', '原始 OHC'),
          set_colors=(colors['eemd'], colors['oni'], colors['raw']),
          alpha=0.8)

# 【样式优化】
for text in v.set_labels:
    if text:
        text.set_fontsize(16)
        text.set_fontweight('bold')

for text in v.subset_labels:
    if text:
        text.set_fontsize(18)
        text.set_fontweight('bold')
        text.set_color('white')
        # --- 【关键修复】使用正确导入的 path_effects ---
        plt.setp(text, path_effects=[
            path_effects.withStroke(linewidth=1.5, foreground='black')])
        # --- 修复结束 ---

c = venn3_circles(subsets=subsets, linestyle='solid', linewidth=1.5, color='white')
for circle in c:
    # --- 【关键修复】使用正确导入的 path_effects ---
    circle.set_path_effects([path_effects.withSimplePatchShadow(offset=(2,-2), alpha=0.3)])
    # --- 修复结束 ---

# 添加总标题和副标题
plt.title('三种方法识别“急速上升期”的重叠与差异', 
          fontsize=24, fontweight='bold', pad=40)
ax.text(0.5, 1.05, '维恩图量化分析三种时间序列处理方法的共识度', 
        ha='center', va='center', transform=ax.transAxes, 
        fontsize=16, color='gray')

plt.show()

# %%
common_dates_ts_OHC = list(common_dates_ts)
common_dates_ts_OHC

# %%
