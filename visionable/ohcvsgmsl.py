
#%%
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pandas import Timestamp # 明确导入Timestamp类型，便于类型提示

def plot_event_timeline_comparison(ohc_dates: list[Timestamp], gmsl_dates: list[Timestamp]):
    """
    创建一个精美的事件时间轴图，对比OHC和GMSL急速上升期的发生时间。

    参数:
    ----------
    ohc_dates : list[Timestamp]
        一个包含OHC急速上升期年份的Timestamp对象列表。
    gmsl_dates : list[Timestamp]
        一个包含GMSL急速上升期年份的Timestamp对象列表。
    """
    # --- 1. 字体与风格设置 ---
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 配色方案
    colors = {
        'ohc': '#3B75AF',  # OHC使用蓝色系
        'gmsl': '#CD6607', # GMSL使用橙色系
        'common': '#C00000' # 共同事件使用强调红
    }

    # --- 2. 核心分析：找到共同事件 ---
    # 使用集合运算找到两个列表的交集
    common_events = sorted(list(set(ohc_dates) & set(gmsl_dates)))
    
    # --- 3. 可视化 ---
    fig, ax = plt.subplots(figsize=(20, 6))

    # 绘制中心时间轴线
    ax.axhline(0, color='black', xmin=0.05, xmax=0.95, lw=1.5, zorder=0)

    # 绘制 OHC 事件点
    ax.scatter(ohc_dates, [0.5] * len(ohc_dates), 
               s=100, color=colors['ohc'], alpha=0.7, 
               edgecolor='black', label=f'OHC 急速上升期 ({len(ohc_dates)}个)')
    
    # 绘制 GMSL 事件点
    ax.scatter(gmsl_dates, [-0.5] * len(gmsl_dates), 
               s=100, color=colors['gmsl'], alpha=0.7, 
               edgecolor='black', label=f'GMSL 急速上升期 ({len(gmsl_dates)}个)')

    # 【核心】高亮共同事件
    if common_events:
        for date in common_events:
            ax.scatter(date, 0.5, s=250, facecolors='none', edgecolors=colors['common'], linewidth=2.5)
            ax.scatter(date, -0.5, s=250, facecolors='none', edgecolors=colors['common'], linewidth=2.5)
            ax.plot([date, date], [0.4, -0.4], color=colors['common'], linestyle='--', lw=1.0)
        
    # --- 4. 美化图表 ---
    ax.yaxis.set_visible(False)
    
    # 动态设置X轴范围
    all_dates = ohc_dates + gmsl_dates
    start_year = min(all_dates).year - 5
    end_year = max(all_dates).year + 5
    ax.set_xlim(pd.to_datetime(f'{start_year}-01-01'), pd.to_datetime(f'{end_year}-01-01'))
    ax.xaxis.set_major_locator(mdates.YearLocator(20)) # 每20年一个主刻度
    ax.xaxis.set_minor_locator(mdates.YearLocator(5)) # 每5年一个次刻度
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.tick_params(axis='x', labelsize=12)

    for spine in ['left', 'right', 'top']:
        ax.spines[spine].set_visible(False)
        
    ax.text(0.01, 0.75, '海洋热含量 (OHC)', transform=ax.transAxes, fontsize=16, color=colors['ohc'], fontweight='bold')
    ax.text(0.01, 0.15, '全球海平面 (GMSL)', transform=ax.transAxes, fontsize=16, color=colors['gmsl'], fontweight='bold')

    # 创建图例
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label=f'OHC 急速上升期 ({len(ohc_dates)}个)', 
               markerfacecolor=colors['ohc'], alpha=0.7, markersize=10),
        Line2D([0], [0], marker='o', color='w', label=f'GMSL 急速上升期 ({len(gmsl_dates)}个)',
               markerfacecolor=colors['gmsl'], alpha=0.7, markersize=10),
    ]
    if common_events:
        legend_elements.append(
            Line2D([0], [0], marker='o', color='w', label=f'共同事件年 ({len(common_events)}个)', 
                   markeredgecolor=colors['common'], markerfacecolor='none', 
                   mew=2.5, markersize=12)
        )
    ax.legend(handles=legend_elements, loc='lower center', ncol=3, 
              bbox_to_anchor=(0.5, -0.35), frameon=False, fontsize=12)

    # 添加标题
    fig.suptitle('OHC 与 GMSL “急速上升期”事件的时间关联性分析', fontsize=22, fontweight='bold')
    
    plt.tight_layout(rect=[0, 0.1, 1, 0.95])
    plt.show()
#%%获得两者急速上升点
common_dates_ts_OHC = [
        Timestamp('1958-01-01 00:00:00'),
        Timestamp('1962-01-01 00:00:00'),
        Timestamp('2003-01-01 00:00:00'),
        Timestamp('2017-01-01 00:00:00')
    ]
common_dates_ts_GMSL = [
        Timestamp('1911-01-01 00:00:00'),
        Timestamp('1949-01-01 00:00:00'),
        Timestamp('2012-01-01 00:00:00')
    ]
#%%
# 2. 找到两个事件集的交集
plot_event_timeline_comparison(
        ohc_dates=common_dates_ts_OHC,
        gmsl_dates=common_dates_ts_GMSL
    )

# %%
