#%%导入库
from PyEMD import EMD, EEMD
from PyEMD.visualisation import Visualisation 
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, MaxNLocator, AutoMinorLocator
import matplotlib.dates as mdates
import warnings
from scipy.signal import hilbert

# 忽略警告
warnings.filterwarnings('ignore')

# 全局matplotlib配置
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans'] 
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 12

#%% 初始化EEMD
eemd = EEMD()
emd = eemd.EMD
emd.extrema_detection = 'parabol'

#%% 读取时间序列
df = pd.read_excel(r"D:\SCIENCE\大气物理\气象指数\gmst\GMSL.xlsx", header=0, index_col=0, names=["GMSL"])
# 正确解析年份索引
date = pd.to_datetime(df.index, format='%Y')
df_name = df.columns[0]
df = df['GMSL'].to_numpy()

# 数据预处理
df_mean = np.mean(df)
df_std = np.std(df)
df = (df - df_mean) / df_std  # 标准化

print(f"数据时间范围: {date[0]} 到 {date[-1]}")
print(f"数据点数: {len(date)}")
print(f"原始数据范围: [{df.min():.3f}, {df.max():.3f}]")

#%% 参数设置
t0 = date[0].year
dt = 1
N = df.size
t = np.arange(0, N) * dt + t0

#%% 不去趋势
df_norm = df.copy()

#%% EEMD分解绘图
eIMFs = eemd.eemd(df_norm, t)
nIMFs = eIMFs.shape[0]

plt.figure(figsize=(12, 9))
plt.subplot(nIMFs + 1, 1, 1)
plt.plot(t, df_norm, 'r', linewidth=2)
plt.ylabel("原始信号")
plt.title("EEMD分解结果")

for n in range(nIMFs):
    plt.subplot(nIMFs + 1, 1, n + 2)
    plt.plot(t, eIMFs[n], 'g', linewidth=2.0)
    plt.ylabel(f"eIMF {n + 1}")
    # 限制刻度数量以避免警告
    plt.locator_params(axis='y', nbins=5)
    plt.locator_params(axis='x', nbins=10)

plt.xlabel("年份")
plt.tight_layout()
plt.show()

#%% 分解结果可视化
imfs, res = eemd.get_imfs_and_residue()
vis = Visualisation()
vis.plot_imfs(imfs=imfs, residue=res, t=t, include_residue=True)
vis.plot_instant_freq(t, imfs=imfs)
vis.show()

#%% FFT分析
n_points = df_norm.size
sampling_interval = 1

# 进行 FFT
fft_vals = np.fft.fft(df_norm)
# 计算频率轴
fft_freq = np.fft.fftfreq(n_points, d=sampling_interval)
# 计算功率谱
power_spectrum = np.abs(fft_vals)**2

# 寻找峰值 - 只关心正频率部分
positive_freq_mask = fft_freq > 0
freqs = fft_freq[positive_freq_mask]
power = power_spectrum[positive_freq_mask]

# 找到功率最大的点的索引
dominant_freq_index = np.argmax(power)
# 找到主频率
dominant_freq = freqs[dominant_freq_index]
# 计算主周期
dominant_period = 1 / dominant_freq

print(f"FFT 分析出的主周期为: {dominant_period:.2f} 年")

# FFT功率谱绘图
plt.figure(figsize=(10, 5))
plt.plot(freqs, power, linewidth=2)
plt.title('信号的功率谱', fontsize=14, fontweight='bold')
plt.xlabel('频率 (1/年)', fontsize=12)
plt.ylabel('功率', fontsize=12)
plt.axvline(dominant_freq, color='r', linestyle='--', linewidth=2, 
            label=f'主频率: {dominant_freq:.3f}')
plt.legend(fontsize=10)
plt.grid(True, alpha=0.3)
# 限制刻度数量以避免警告
plt.locator_params(axis='both', nbins=8)
plt.tight_layout()
plt.show()

#%% 周期分析
print(f"数据采样率: {1/(t[1] - t[0]):.2f} Hz (点/年)\n")

# 存储每个IMF的平均周期
average_periods = []

for i, imf in enumerate(eIMFs):
    # 1. 对 IMF 进行希尔伯特变换
    analytic_signal = hilbert(imf)
    
    # 2. 计算瞬时相位
    instantaneous_phase = np.unwrap(np.angle(analytic_signal))
    
    # 3. 计算瞬时频率 (d(phase)/dt)
    sampling_rate = 1 / (t[1] - t[0])
    instantaneous_freq = (np.diff(instantaneous_phase) / (2.0 * np.pi) * sampling_rate)
    
    # 忽略频率过低或不稳定的边缘点，取中间稳定部分计算
    stable_part_freq = instantaneous_freq[10:-10]
    
    # 4. 从瞬时频率计算平均周期 (T = 1/f)
    if np.mean(stable_part_freq) > 1e-6:
        avg_period = 1 / np.mean(stable_part_freq)
    else:
        avg_period = np.inf  # 频率接近0，周期为无穷大（趋势项）
        
    average_periods.append(avg_period)
    
    print(f"eIMF {i + 1}:")
    print(f"  - 平均频率: {1/avg_period:.4f} cycles/year")
    print(f"  - 平均周期: {avg_period:.2f} years")

# 结果展示
print("\n--- 周期提取结果汇总 ---")
for i, period in enumerate(average_periods):
    print(f"eIMF {i + 1} 的代表周期是: {period:.2f} 年")

#%% 减去趋势
df_hat = df - (eIMFs[0])

#%% 最终绘图 - 时间序列对比
print(f"绘图时间范围: {date[0]} 到 {date[-1]}")
print(f"数据范围: df_hat [{df_hat.min():.3f}, {df_hat.max():.3f}], df_norm [{df_norm.min():.3f}, {df_norm.max():.3f}]")

fig, ax = plt.subplots(1, 1, figsize=(18, 8))

# 绘制数据线
ax.plot(date, df_hat, lw=2.5, label=f"{df_name}_hat", color='#1f77b4', zorder=3)
ax.plot(date, df_norm, lw=2.5, label=f"{df_name}", color='#ff7f0e', alpha=0.8, zorder=2)

# 为每一年添加红点标记
ax.scatter(date, df_hat, color='red', s=15, alpha=0.7, zorder=5, label='年度标记')
ax.scatter(date, df_norm, color='red', s=15, alpha=0.7, zorder=5)

# 设置网格 - 主网格和次网格
# 主网格（每5年和每0.5度）
ax.grid(True, which='major', alpha=0.4, linestyle='-', linewidth=1)
# 次网格（每年和每0.1度）
ax.grid(True, which='minor', alpha=0.2, linestyle=':', linewidth=0.5)

# 设置图例
ax.legend(loc="best", fontsize=12, framealpha=0.9)


# 设置刻度标签样式
ax.tick_params(axis='both', which='major', labelsize=12)
ax.tick_params(axis='x', rotation=45)
ax.tick_params(axis='both', which='minor', length=2)
ax.tick_params(axis='both', which='major', length=4)

# 设置标题和标签
ax.set_title(f"{df_name} 时间序列对比（年度红点标记）", 
             fontsize=16, fontweight='bold', pad=20)
ax.set_xlabel("年份", fontsize=14, fontweight='bold')
ax.set_ylabel("温度异常 (°C)", fontsize=14, fontweight='bold')
# 设置X轴刻度
ax.xaxis.set_major_locator(mdates.YearLocator(5))  # 每5年主刻度
ax.xaxis.set_minor_locator(mdates.YearLocator(1))  # 每年次刻度
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))  # 年份格式

# 设置Y轴范围和刻度
y_min, y_max = min(df_hat.min(), df_norm.min()), max(df_hat.max(), df_norm.max())
y_range = y_max - y_min
ax.set_ylim(y_min - 0.1 * y_range, y_max + 0.1 * y_range)  # 添加10%的边距

# 设置Y轴刻度
ax.yaxis.set_major_locator(MaxNLocator(10))  # 自动选择合适的主刻度数量
ax.yaxis.set_minor_locator(AutoMinorLocator(2))  # 在主刻度之间添加次刻度

# 优化布局
plt.tight_layout()
plt.show()

print("EEMD分析完成！")
# %%
